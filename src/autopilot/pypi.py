import tempfile
from unittest.mock import patch
from distutils.core import run_setup
from io import StringIO
from urllib.parse import urlparse
from pathlib import Path
from contextlib import contextmanager
import os

from urllib.error import HTTPError

import sarge

from distlib.index import PackageIndex
from distlib.util import HTTPSOnlyHandler
from distlib.metadata import Metadata
from distlib.locators import DirectoryLocator

from autopilot.exceptions import FatalError

# Wheels??
# https://gist.github.com/vsajip/4988471

# Manifest API to include data files??
# http://pythonhosted.org/distlib/tutorial.html#using-the-manifest-api

DIST_EXTENSIONS = {
    ".whl": "bdist_wheel",
    ".exe": "bdist_wininst",
    ".egg": "bdist_egg",
    ".bz2": "sdist",
    ".gz": "sdist",
    ".zip": "sdist",
}


def _get_passwd(cmd):
    command = sarge.capture_both(cmd)
    command.wait()
    passwd = command.stdout.text.strip()
    if command.returncode != 0:
        raise FatalError(
            'Command "{}" failed\n'
            'We cannot get a password\n'
            'stdout:\n{}\n'
            'stderr:\n{}\n'
            .format(cmd, passwd, command.stderr.text.strip()))
    return passwd


@contextmanager
def generate_dist(dist_dir=None, script_name='setup.py'):

    if dist_dir:
        current_wd = os.getcwd()
        os.chdir(dist_dir)

    try:

        with tempfile.TemporaryDirectory(prefix='ap_dist') as tmp_dir,\
             StringIO() as pkg_info:

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                dist = run_setup(script_name, ['sdist', '-d', tmp_dir,
                                               'bdist_wheel', '-d', tmp_dir])

            local_locator = DirectoryLocator(tmp_dir)
            filenames = [Path(urlparse(uri).path)
                         for uri in local_locator.get_project(dist.metadata.name)['digests'].keys()]

            dist.metadata.write_pkg_file(pkg_info)
            pkg_info.seek(0)
            metadata = Metadata(fileobj=pkg_info)
            yield metadata, filenames
    finally:
        if dist_dir:
            os.chdir(current_wd)


def pypi_upload(pypi_conf, use_https=True, dist_dir=None):
    index = PackageIndex(pypi_conf['url'])
    if use_https:
        index.ssl_verifier = HTTPSOnlyHandler('', False)
    index.username = pypi_conf['user']
    index.password = _get_passwd(pypi_conf['passeval'])

    with generate_dist(dist_dir) as (metadata, dist_files):
        for filename in dist_files:

            for _ in range(2):
                try:
                    response = index.upload_file(metadata, filename.as_posix(),
                                                 filetype=DIST_EXTENSIONS[filename.suffix])
                except HTTPError as err:
                    if err.code == 401:
                        raise FatalError('Unauthorized error, check your username and password')
                    if err.code != 403:
                        raise err
                    index.register(metadata)
                else:
                    break
