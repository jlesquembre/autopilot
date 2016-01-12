import tempfile
from unittest.mock import patch
from distutils.core import run_setup
from io import StringIO
from urllib.parse import urlparse
from pathlib import Path

from urllib.error import HTTPError

import sarge

from distlib.index import PackageIndex
from distlib.util import HTTPSOnlyHandler
from distlib.metadata import Metadata, LegacyMetadata
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


#KEYWORDS_TO_NOT_FLATTEN = set(["gpg_signature", "content"])
#
#def _convert_data_to_list_of_tuples(data):
#    data_to_send = []
#    for key, value in data.items():
#        if (key in KEYWORDS_TO_NOT_FLATTEN or
#                not isinstance(value, (list, tuple))):
#            data_to_send.append((key, value))
#        else:
#            for item in value:
#                data_to_send.append((key, item))
#    return data_to_send


def pypi_upload(pypi_conf):

    with tempfile.TemporaryDirectory(prefix='ap_dist') as tmp_dir:

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            dist = run_setup('setup.py', ['sdist', '-d', tmp_dir,
                                          'bdist_wheel', '-d', tmp_dir])

        with StringIO() as pkg_info:
            dist.metadata.write_pkg_file(pkg_info)
            pkg_info.seek(0)
            # TODO use LegacyMetadata(1.1)
            metadata = Metadata(fileobj=pkg_info)

        #metadata._legacy = LegacyMetadata(mapping=metadata_dict)
        #metadata.update(metadata_dict)

        index = PackageIndex(pypi_conf['url'])
        #verifier = HTTPSOnlyHandler('/path/to/root/certs.pem')
        verifier = HTTPSOnlyHandler('', False)
        index.ssl_verifier = verifier

        index.username = pypi_conf['user']
        index.password = _get_passwd(pypi_conf['passeval'])

        #if not in register:
        #index.register(metadata)
        #archive_name = '{}/{}-{}.tar.gz'.format(tmp_dir, metadata.name.replace('-', '_'), metadata.version)

        #archive_name = '{}/{}-{}.tar.gz'.format(tmp_dir, metadata.name, metadata.version)

        for filename in filenames:

            for _ in range(2):
                #meta = pkginfo.SDist(filename.as_posix())
                #meta_dict = {k: getattr(mym, k)  for k in mym.iterkeys()}
                try:
                    response = index.upload_file(metadata, filename.as_posix(), filetype=DIST_EXTENSIONS[filename.suffix])
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

if __name__ == '__main__':
    pypi_upload({
        'url': 'https://testpypi.python.org/pypi',
        'user': 'jlesquembre',
        'passeval': 'pass pypi/test',
        }
        )

