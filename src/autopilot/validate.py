from pathlib import Path

from git import Repo

from distlib.version import NormalizedVersion, UnsupportedVersionError

from .exceptions import InvalidOption

def validate_new_project(values, config=None):

    directory = values['directory']
    name = values['project_name']

    check_name(name)
    check_directory(name, directory)

    return values

def validate_release(values, config=None):

    check_versions(values)
    check_remote(values, config)
    check_upload(values, config)
    return values


def check_name(name):
    if len(name) < 1:
        raise InvalidOption('Provide a name for the project!')


def check_directory(name, directory):
    if len(directory) < 1:
        raise InvalidOption('Provide a name for the directory!')

    directory = Path(directory)

    if not directory.exists():
        raise InvalidOption('Directory "{}" doesn\'t exist!'.format(directory))

    if (directory / name).exists():
        raise InvalidOption('Project "{}" already'
                            ' exists on "{}"!'.format(name, directory))


def check_versions(values):
    try:
        current_version = NormalizedVersion(values['current_version'])
        release_version = NormalizedVersion(values['release_version'])
        next_dev_version = NormalizedVersion(values['next_dev_version'])
    except UnsupportedVersionError as e:
        raise InvalidOption(str(e))

    if current_version >= release_version:
        raise InvalidOption('Release version ({}) must be bigger\nthan current'
                            ' version ({})'.format(release_version, current_version))

    if release_version >= next_dev_version:
        raise InvalidOption('Next dev version ({}) must be bigger\nthan release'
                            ' version ({})'.format(next_dev_version, release_version))

    if release_version.is_prerelease:
        raise InvalidOption('Release version cannot be a prerelease')

    if not next_dev_version.is_prerelease:
        raise InvalidOption('Next dev version must be a prerelease')


def check_remote(values, config):
    if values['git_push']:
        repo = Repo(config['project_dir'].as_posix())
        try:
            origin = repo.remotes.origin
        except:
            raise InvalidOption("Remote 'origin' doesn't exist.\n"
                                "Can't do a 'git push'"  )

        # TODO maybe is easier asume that this is going to work, and revert the
        # changes if push fails, in that case, remove the following code

        # Before fetch, check that we can reach the remote server
        # http://stackoverflow.com/a/1405340/799785
        # http://unix.stackexchange.com/a/30146/27359

        # To check if a key is encrypted:
        # http://unix.stackexchange.com/a/528/27359

        # Check options for some host
        # ssh -G github.com | grep identity

        #origin.fetch()
        #if list(repo.iter_commits('master..origin/master')):
        #    raise InvalidOption("There are changes on the remote\n"
        #                        "Merge them before the release")

def check_upload(values, config):
    pypi_name = values['upload_to_pypi']
    if pypi_name != 'Nope':
        pypi = config['pypi_servers'][pypi_name]
        #import pudb; pudb.set_trace()
        if not pypi.get('user') or not pypi.get('passeval') or not pypi.get('url'):
             raise InvalidOption(
                "To upload the release to a PyPI repository ({}),\n"
                "provide an user, a password and an url on the config file"
                .format(pypi_name))
