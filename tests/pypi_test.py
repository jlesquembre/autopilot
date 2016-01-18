import os

from urllib.error import URLError

import pytest

from distlib.index import PackageIndex

from autopilot import pypi


def test_restore_cwd(fake_project_dir):
    cwd = os.getcwd()
    with pypi.generate_dist(fake_project_dir.as_posix()) as (metadata, dist_files):
        pass
    assert cwd == os.getcwd()


def test_generate_dist(fake_project_dir):
    with pypi.generate_dist(fake_project_dir.as_posix()) as (metadata, dist_files):
        assert metadata.name == 'fake_project'
        assert len(dist_files) == 2
        for dist_file in dist_files:
            assert dist_file.exists()
            assert dist_file.is_file()


def test_https_default(pypi_server, fake_project_dir):
    url, local_dir = pypi_server
    with pytest.raises(URLError) as excinfo:
        pypi.pypi_upload({'url': url,
                          'user': 'user',
                          'passeval': 'echo pass'
                          }, dist_dir=fake_project_dir.as_posix())
    assert 'Unexpected HTTP request on what should be a secure connection' in str(excinfo.value)


def test_upload(pypi_server, fake_project_dir):
    url, local_dir = pypi_server
    assert local_dir.is_dir()
    assert local_dir.exists()
    assert len(list(local_dir.iterdir())) == 0

    pypi.pypi_upload({'url': url,
                      'user': 'user',
                      'passeval': 'echo pass'
                      }, use_https=False, dist_dir=fake_project_dir.as_posix())

    files = [f.name for f in local_dir.iterdir()]
    assert len(files) == 2
    assert 'fake_project-1.0.0-py2.py3-none-any.whl' in files
    assert 'fake_project-1.0.0.tar.gz' in files
