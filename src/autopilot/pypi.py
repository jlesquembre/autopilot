import tempfile
from unittest.mock import patch
from distutils.core import run_setup
from io import StringIO

from urllib.error import HTTPError

import sarge

from distlib.index import PackageIndex
from distlib.util import HTTPSOnlyHandler
from distlib.metadata import Metadata

from autopilot.exceptions import FatalError

# Wheels??
# https://gist.github.com/vsajip/4988471

# Manifest API to include data files??
# http://pythonhosted.org/distlib/tutorial.html#using-the-manifest-api

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


def pypi_upload(pypi_conf):

    with tempfile.TemporaryDirectory(prefix='ap_dist') as tmp_dir:

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            dist = run_setup('setup.py', ['sdist', '-d', tmp_dir,
                                          'bdist_wheel', '-d', tmp_dir])

        metadata = Metadata(path='src/{}.egg-info/PKG-INFO'.format(dist.get_name()))
        metadata.validate()  # This raises a DistlibException (either MetadataMissingError
                             # or MetadataInvalidError) if the metadata isn't valid.

        index = PackageIndex(pypi_conf['url'])
        #verifier = HTTPSOnlyHandler('/path/to/root/certs.pem')
        verifier = HTTPSOnlyHandler('', False)
        index.ssl_verifier = verifier

        index.username = pypi_conf['user']
        index.password = _get_passwd(pypi_conf['passeval'])

        #if not in register:
        #index.register(metadata)
        #archive_name = '{}/{}-{}.tar.gz'.format(tmp_dir, metadata.name.replace('-', '_'), metadata.version)
        archive_name = '{}/{}-{}.tar.gz'.format(tmp_dir, metadata.name, metadata.version)

        for _ in range(2):
            try:
                response = index.upload_file(metadata, archive_name)
            except HTTPError as err:
                if err.code == 401:
                    raise FatalError('Unauthorized error, check your username and password')
                if err.code != 403:
                    raise err
                index.register(metadata)
            else:
                break


        #response = index.upload_file(metadata, archive_name,
        #                             filetype='bdist_dumb',
        #                             pyversion='2.6')
