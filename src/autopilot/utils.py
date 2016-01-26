import os
import re
import distutils
import shutil
from contextlib import contextmanager
from pathlib import Path
from functools import lru_cache
from distutils.core import run_setup
from collections import deque, OrderedDict
from collections.abc import MutableMapping
from copy import deepcopy
from datetime import datetime
from itertools import islice

#import yaml
import ruamel.yaml as yaml
import sarge

from git import Repo
from git.exc import InvalidGitRepositoryError

from distlib.version import NormalizedVersion

from .pypi import pypi_upload
from .exceptions import FatalError
from .git import checkout_tag, git_push


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

    except InvalidGitRepositoryError:
        distutils.log.warn('warning: not a valid git repository, '
                           'autopilot file_finder not used')


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
    changelog = Path(dest_dir) if isinstance(dest_dir, str) else dest_dir
    changelog /= 'CHANGES.rst'

    linenr = get_header(original)

    with original.open('rt') as src, changelog.open('wt') as dst:
        for line in islice(src, 0, linenr):
            dst.write(line)

        if release:
            src.readline()
            line = '{} ({})\n'.format(version, datetime.now().strftime('%Y-%m-%d'))
            dst.write(line)
            dst.write('-' * (len(line) - 1))
            dst.write('\n')
            src.readline()
        else:
            line = '{} (unreleased)\n'.format(version)
            dst.write(line)
            dst.write('-' * (len(line) - 1))
            dst.write('\n\n- Nothing changed yet\n\n\n')

        for line in src:
            dst.write(line)

    return changelog.as_posix()


def get_header(changelog):
    """Return line number of the first version-like header.  We check for
    patterns like '2.10 (unreleased)', so with either 'unreleased' or a date
    between parenthesis as that's the format we're using.  As an alternative,
    we support an alternative format used by some zope/plone paster templates:
    '2.10 - unreleased' or '2.10 ~ unreleased' Note that new headers are in our
    preferred form (so 'version (date)').
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
    with changelog.open('rt') as f:
        for line_number, line in enumerate(f):
            match = pattern.search(line)
            alt_match = alt_pattern.search(line)
            if match or alt_match:
                return line_number


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

    # Update changelog and version

    changelog_path = project_dir /'CHANGES.rst'
    version_path = project_dir / 'src' / project_name / '__init__.py'

    new_changelog = update_changelog(changelog_path, dest_dir=tmp_dir, version=release_version)
    new_version = update_version_file(original=version_path, project_name=project_name,
                                      dest_dir=tmp_dir, version=release_version)

    shutil.copyfile(new_changelog, changelog_path.as_posix())
    shutil.copyfile(new_version, version_path.as_posix())

    # Create relase commit and tag

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
        git_push(repo, release_version)

    pypi = extra_config['upload_to_pypi'].lower()
    if pypi != 'nope':
        pypi_servers = {k.lower(): v for k ,v in pypi_servers.items()}
        with checkout_tag(repo, release_version):
            pypi_upload(pypi_conf=pypi_servers[pypi])
