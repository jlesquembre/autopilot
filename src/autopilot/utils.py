import os
import re
import distutils
import shutil
import tempfile
import xmlrpc.client
from contextlib import contextmanager
from pathlib import Path
from functools import lru_cache
from distutils.core import run_setup
from distutils.command.register import register
from collections import deque, OrderedDict
from collections.abc import MutableMapping
from copy import deepcopy
from datetime import datetime
from unittest.mock import patch

#import yaml
import ruamel.yaml as yaml
import sarge
from git import Repo, Blob
import git.exc
from requests.exceptions import HTTPError

from twine.commands.upload import upload as twine_upload

from distlib.version import NormalizedVersion

from .exceptions import FatalError


@lru_cache()
def get_licenses():
    license_dir = get_data_dir() / 'licenses'
    licenses = sorted([l.name for l in license_dir.iterdir()])

    user_licenses = get_user_config_dir() / 'licenses'
    if user_licenses.is_dir():
        licenses.extend([l.name for l in user_licenses.iterdir()])

    return licenses


def get_license_index(name):
    try:
        return [i.lower() for i in get_licenses()].index(name.lower())
    except ValueError:
        raise FatalError(
            'Check your autopilot configuration ({config_path})\n'
            '"{name}" is not a valid license name\n\n'
            'Valid licenses:\n'
            '  {licenses}'.format(config_path=get_user_config_path(),
                                  name=name,
                                  licenses='\n  '.join(get_licenses())))


# See: http://stackoverflow.com/a/24088493/799785
#TODO FIXME modifies d2
#TODO if is a list, append elements
#TODO case insensitive keys!!
#def merge_config(d1, d2):
#    '''
#    Update two dicts of dicts recursively,
#    if either mapping has leaves that are non-dicts,
#    the second's leaf overwrites the first's.
#    '''
#    for k, v in d1.items():
#        if k in d2:
#            if all(isinstance(e, MutableMapping) for e in (v, d2[k])):
#                d2[k] = merge_config(v, d2[k])
#            # we could further check types and merge as appropriate here.
#    d3 = d1.copy()
#    d3.update(d2)
#    return d3


def merge_config(d1, d2):
    '''Merges to config dicts. Key values are case insensitive for merging,
    but the value of d1 is remembered.
    '''
    result = deepcopy(d1)
    elements = deque()
    elements.append((result, d2))

    while elements:
        old, new = elements.popleft()

        new = OrderedDict([(k.lower(), (k, v)) for k, v in new.items()])
        visited_keys = []

        for k, old_value in old.items():
            klow = k.lower()
            if klow in new:
                new_key, new_value = new[klow]
                visited_keys.append(new_key)
                if all(isinstance(e, MutableMapping) for e in (old_value, new_value)):
                    elements.append((old_value, new_value))
                else:
                    old[k] = deepcopy(new_value)

        for k, v in new.values():
            if k not in visited_keys:
                old[k] = deepcopy(v)

    return result


#def set_if_none(d, key, value):
#    '''
#    If the value of one key in a dict is None, set it to a different value
#    '''
#    if d[key] is None:
#        d[key] = value

def stdout(command):
    return sarge.capture_stdout(command).stdout.text.strip()


def set_if_none(user_config, config, key, value):
    '''
    If the value of the key in is None, and doesn't exist on the user config,
    set it to a different value
    '''

    keys = key.split('.')
    for k in keys[:-1]:
        try:
            user_config = user_config[k]
        except KeyError:
            user_config = {}

        config = config[k]

    key = keys[-1]

    if key not in user_config and not config[key]:
        config[key] = value



def setuptools_file_finder(dirname):

    try:
        repo = Repo(os.getcwd())

        # README.txt (or README), setup.py (or whatever you called your setup
        # script), and setup.cfg are included by default, see:
        # https://docs.python.org/3/distutils/sourcedist.html#specifying-the-files-to-distribute
        yield from ('CHANGELOG.rst', 'LICENSE', '.gitignore')

        #yield from (item.path for item in repo.tree().traverse()
        #            if type(item) is Blob and item.path.startswith('src'))
        yield from (item.path for _, item in repo.index.iter_blobs()
                    if item.path.startswith('src'))

        # git add -N --dry-run  src/aa
        yield from (item for item in repo.untracked_files
                    if item.startswith('src'))

    except git.exc.InvalidGitRepositoryError:
        distutils.log.warn('warning: not a valid git repository, '
                           'autopilot file_finder not used')


def init_repo(path, **kwargs):
    repo = Repo.init(str(path))
    repo.index.add(repo.untracked_files)

    cw = repo.config_writer()
    cw.set_value('user', 'name', kwargs.get('user_name', ''))
    cw.set_value('user', 'email', kwargs.get('user_email', ''))
    cw.release()

    if kwargs.get('initial_commit'):
        print('Do initial commit...')
        repo.index.commit('Initial commit')
    else:
        print('Next step:')
        print('git commit -m "Initial commit"')


def get_data_dir():
    return Path(__file__).parent / 'data'


def get_user_config_dir():
    return Path(os.getenv('XDG_CONFIG_HOME', '~/.config' )).expanduser() / 'autopilot'


def get_user_config_path():
    return get_user_config_dir() / 'config.yml'


def get_config():
    config_path = get_user_config_path()

    try:
        with config_path.open() as f:
            user_config = yaml.load(f, Loader=yaml.RoundTripLoader)
    except FileNotFoundError:
        print('WARNING: No user config file found at:\n'
              '{}'.format(config_path))
        user_config = {}

    with (get_data_dir() / 'default_config.yml').open() as f:
        default_config = yaml.load(f, Loader=yaml.RoundTripLoader)

    config = merge_config(default_config, user_config)

    config['new_project']['license'] = get_license_index(config['new_project']['license'])
    set_if_none(user_config, config, 'new_project.default_dir', os.getcwd())

    # TODO set cwd to dir where we want to create the project
    set_if_none(user_config, config, 'author.name', stdout('git config --get user.name'))
    set_if_none(user_config, config, 'author.email', stdout('git config --get user.email'))

    set_if_none(user_config, config, 'editor', os.environ.get('EDITOR','vim'))

    config['pypi_list'] = _get_pypi_list(config['pypi_servers'])
    config['release']['upload'] = _get_pypi_list_index(config['pypi_servers'], config['release']['upload'])
    return config


def _get_pypi_list_index(pypi_list, name):
    if name.lower() == 'nope':
        return 0
    for i, index in enumerate(pypi_list, start=1):
        if index.lower() == name.lower():
            return i
    raise FatalError('Check your autopilot configuration ({})\n'
                     '"{name}" is not a valid license name\n'.format(
                         get_user_config_path()))


def _get_pypi_list(pypi_servers):
    try:
        pypi_list = ['Nope']
        for key, values in pypi_servers.items():
            pypi_list.append(key)
    except:
        raise FatalError(
            'Check your autopilot configuration ({config_path})\n'
            '"pypi_servers" section is not valid\n\n'
            'Valid "pypi_servers" example:\n\n'
            'pypi_servers:\n'
            '  PyPI:\n'
            '    user: guido\n'
            '    passeval: pass pypi\n'
            '    url: https://pypi.python.org/pypi\n'.format(config_path=get_user_config_path()))

    return pypi_list



def get_dist_metadata():
    try:
        dist = run_setup('setup.py', stop_after='init')
    except FileNotFoundError:
        raise FatalError('Error: "setup.py" not found in current directory')

    meta = dist.metadata
    return {'project_name': meta.name, 'current_version': meta.version}


def is_repo_clean(repo_path=None, master=True):
    try:
        path = repo_path if repo_path else os.getcwd()
        repo = Repo(path)
    except git.exc.InvalidGitRepositoryError:
        raise FatalError('ERROR: No git repository found at "{}"'.format(path))

    if master and repo.active_branch.name != 'master':
        raise FatalError('ERROR: Usually your active branch should be master'
                         ' before you do a new release.\n'
                         'If you are sure you want to do a release from this'
                         ' branch, use the "--no-master" flag:\n\n'
                         'ap release --no-master\n')

    if repo.is_dirty():
        raise FatalError('ERROR: Your working tree contains modifications'
                         ' which have not been committed')


def get_next_versions(version):
    version = get_next_version(version)
    return version, get_next_dev_version(version)


def get_next_version(version):
    version = NormalizedVersion(version)._release_clause
    return '.'.join(map(str, version))


def get_next_dev_version(version):
    version = NormalizedVersion(version)._release_clause
    version = version[:-1] + (version[-1] + 1,)
    return '{}.dev0'.format('.'.join(map(str, version)))


def update_changelog(original, dest_dir, version, release=True):

    # TODO check if original really exists
    changelog = Path(dest_dir) / 'CHANGES.rst'

    header = get_header(original)

    with original.open('rt') as src, changelog.open('wt') as dst:
        for line_number, line in enumerate(src):
            if line_number == header['line']:
                date = datetime.now().strftime('%Y-%m-%d') if release else 'unreleased'
                line = '{} ({})\n'.format(version, date)
                dst.write(line)
                dst.write('-' * (len(line) - 1 ))
                dst.write('\n')
                #- Nothing changed yet
            elif line_number == header['line'] + 1:
                pass
            else:
                dst.write(line)

    return changelog.as_posix()


def get_header(changelog):
    """Return list of dicts with version-like headers.
    We check for patterns like '2.10 (unreleased)', so with either
    'unreleased' or a date between parenthesis as that's the format we're
    using. Just fix up your first heading and you should be set.
    As an alternative, we support an alternative format used by some
    zope/plone paster templates: '2.10 - unreleased' or '2.10 ~ unreleased'
    Note that new headers that zest.releaser sets are in our preferred
    form (so 'version (date)').
    """
    pattern = re.compile(r"""
    (?P<version>.+)  # Version string
    \(               # Opening (
    (?P<date>.+)     # Date
    \)               # Closing )
    \W*$             # Possible whitespace at end of line.
    """, re.VERBOSE)
    alt_pattern = re.compile(r"""
    ^                # Start of line
    (?P<version>.+)  # Version string
    \ [-~]\          # space dash/twiggle space
    (?P<date>.+)     # Date
    \W*$             # Possible whitespace at end of line.
    """, re.VERBOSE)
    #headings = []
    #line_number = 0
    with changelog.open('rt') as f:
        for line_number, line in enumerate(f):
            match = pattern.search(line)
            alt_match = alt_pattern.search(line)
            if match:
                return {'line': line_number,
                        'version': match.group('version').strip(),
                        'date': match.group('date'.strip())}
                #headings.append(result)
                #logger.debug("Found heading: %r", result)
            if alt_match:
                return {'line': line_number,
                        'version': alt_match.group('version').strip(),
                        'date': alt_match.group('date'.strip())}
                #headings.append(result)
                #logger.debug("Found alternative heading: %r", result)
            #line_number += 1
    #return headings


def update_version_file(original, dest_dir, version, project_name, release=True):

    new = Path(dest_dir) / '__init__.py'

    pattern = re.compile(r'__version__\s*=\s*(.*)')

    with original.open('rt') as src, new.open('wt') as dst:
        for line in src:
            if pattern.search(line):
                dst.write("__version__ = '{}'\n".format(version))
            else:
                dst.write(line)

    return new.as_posix()


def release(project_name, project_dir, tmp_dir, release_version, next_dev_version, pypi_servers, **extra_config):

    # Update changelog

    changelog_path = project_dir /'CHANGES.rst'
    version_path = project_dir / 'src' / project_name / '__init__.py'

    new_changelog = update_changelog(changelog_path, dest_dir=tmp_dir, version=release_version)
    new_version = update_version_file(original=version_path, project_name=project_name,
                                      dest_dir=tmp_dir, version=release_version)

    shutil.copyfile(new_changelog, changelog_path.as_posix())
    shutil.copyfile(new_version, version_path.as_posix())

    repo = Repo(project_dir.as_posix())
    paths = [p.as_posix() for p in (changelog_path, version_path)]
    repo.index.add(paths)
    repo.index.commit('Release {}'.format(release_version))
    repo.create_tag(release_version, message='Tagging {}'.format(release_version))


    # Post-release, back to development
    new_changelog = update_changelog(changelog_path, dest_dir=tmp_dir,
            version=get_next_version(next_dev_version), release=False)
    new_version = update_version_file(original=version_path, project_name=project_name,
                                      dest_dir=tmp_dir, version=next_dev_version)

    shutil.copyfile(new_changelog, changelog_path.as_posix())
    shutil.copyfile(new_version, version_path.as_posix())
    repo.index.add(paths)
    repo.index.commit('Back to development')

    if extra_config['git_push']:
        _git_push(repo, release_version)

    pypi = extra_config['upload_to_pypi'].lower()
    if pypi != 'nope':
        pypi_servers = {k.lower(): v for k ,v in pypi_servers.items()}
        with checkout_tag(repo, release_version):
            _pypi_upload(repo, pypi_servers[pypi])


@contextmanager
def checkout_tag(repo, tag):
    branch = repo.active_branch.name
    repo.git.checkout(tag)
    try:
        yield
    finally:
        repo.git.checkout(branch)


def _git_push(repo, last_tag):
    try:
        p = sarge.run('git push --follow-tags')
        #sarge.run('git push --tags')
        p.wait()
        if p.returncode != 0:
            raise Exception('Git error')
    except:
        # Other way to get the last tag:
        # last_tag = sorted(repo.tags, key=lambda t: t.commit.committed_date)[-1].name
        repo.delete_tag(last_tag)
        # git reset --hard
        repo.head.reset('HEAD~2', index=True, working_tree=True)

        raise FatalError(
            'Error pushing changes to remote. Abort release and undo changes.')


def _pypi_upload(repo, pypi_conf):

    with tempfile.TemporaryDirectory(prefix='ap_dist') as tmp_dir, \
         patch('twine.commands.upload.get_config') as mock:

        mock.return_value = {'repo': {'repository': pypi_conf['url']}}

        print('Generate distribution:\n'
              'python setup.py sdist bdist_wheel\n' )
        #sarge.run('python setup.py sdist -d {0} bdist_wheel -d {0}'.format(tmp_dir))
        dist = run_setup('setup.py', ['sdist', '-d', tmp_dir,
                                      'bdist_wheel', '-d', tmp_dir])

        #passwd = sarge.get_stdout(pypi_conf['passeval']).strip()
        command = sarge.capture_both(pypi_conf['passeval'])
        command.wait()
        passwd = command.stdout.text.strip()
        if command.returncode != 0:
            raise FatalError(
                'Command "{}" failed\n'
                'We cannot get a password\n'
                'stdout:\n{}\n'
                'stderr:\n{}\n'
                .format(pypi_conf['passeval'], passwd, command.stderr.text.strip()))

        for _ in range(2):
            try:
                # NOTE twine > 1.5.0 add a new argument, config_file. None should be ok
                #      config_file=None
                twine_upload(dists=[p.as_posix() for p in Path(tmp_dir).iterdir()],
                             repository='repo', sign=None, identity=None,
                             username=pypi_conf['user'], password=passwd,
                             comment=None, sign_with=None)
            except HTTPError as err:
                if err.response.status_code == 401:
                    raise FatalError('Unauthorized error, check your username and password')
                if err.response.status_code != 403:
                    raise err
                _pypi_register(pypi_conf['user'], passwd, pypi_conf['url'])
            else:
                break


def _get_pkg_roles(url, name):

    client = xmlrpc.client.ServerProxy(url)
    return dict(client.package_roles(name))


def _pypi_register(user, passwd, repo):

    dist = run_setup('setup.py', stop_after='init')

    reg = register(dist)

    reg.username = user
    reg.password = passwd
    reg.repository = repo
    reg.has_config = True
    reg.realm = 'pypi'

    reg.send_metadata()
