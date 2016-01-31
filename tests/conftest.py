import os
import subprocess
import tempfile
import shutil
import http.client

from io import StringIO
from urllib.request import urlopen
from urllib.error import URLError
from unittest.mock import MagicMock
from pathlib import PurePath, Path
from random import randint

import pytest

from sarge import run


@pytest.fixture
def reader(request):
    data = getattr(request, 'param', '')
    return MagicMock(wraps=PurePath(),
                     **{'open': MagicMock(),
                        'open.side_effect': lambda *args: StringIO(data)})


class MemoizeStringIO(StringIO):
    def __exit__(self, *exc):
        self.lastvalue = self.getvalue()
        return super().__exit__(*exc)


@pytest.fixture
def writer():

    def mock_div(self, *args, **kwargs):
        return self

    mock = MagicMock(wraps=PurePath(),
                     **{'open': MagicMock(),
                        'open.return_value': MemoizeStringIO()})
    mock.output = mock.open.return_value
    mock.__truediv__ = mock_div
    mock.__rtruediv__ = mock_div
    mock.__itruediv__ = mock_div

    return mock


@pytest.fixture
def empty_dir(request):
    tempdir = tempfile.TemporaryDirectory()

    def fin():
        tempdir.cleanup()
    request.addfinalizer(fin)

    return Path(tempdir.name)


@pytest.fixture
def dir_with_file(empty_dir):
    readme = empty_dir / 'readme.txt'
    with readme.open('w') as f:
        f.write('1')
    return empty_dir


@pytest.fixture
def git_dir(dir_with_file):
    run('git init', cwd=str(dir_with_file))
    run('git config user.email "you@example.com"', cwd=str(dir_with_file))
    run('git config user.name "You"', cwd=str(dir_with_file))
    run('git add .', cwd=str(dir_with_file))
    run('git commit -m "Initial commit"', cwd=str(dir_with_file))
    return dir_with_file


@pytest.fixture
def pypi_server(request):
    tempdir = tempfile.TemporaryDirectory(prefix='pypi_index_')
    sink = open(os.devnull, 'w')

    port = str(randint(10000, 65535))
    server_url = 'http://localhost:{}'.format(port)
    cmd = ['pypi-server', '-p', port, '-P', '.', '-a', '.', tempdir.name]
    server = subprocess.Popen(cmd, stdout=sink, stderr=sink)

    # wait for the server to start up
    response = None
    while response is None:
        try:
            response = urlopen(server_url)
        except URLError:
            pass
        except http.client.BadStatusLine:
            # see https://github.com/shazow/urllib3/issues/779
            port = str(randint(10000, 65535))
            server_url = 'http://localhost:{}'.format(port)
            cmd = ['pypi-server', '-p', port, '-P', '.', '-a', '.', tempdir.name]
            server = subprocess.Popen(cmd, stdout=sink, stderr=sink)

    def fin():
        if server and server.returncode is None:
            server.kill()
        tempdir.cleanup()
        sink.close()

    request.addfinalizer(fin)

    tempdir_path = Path(tempdir.name)

    return server_url, tempdir_path


@pytest.fixture
def fake_project_dir(request):
    here = os.path.abspath(os.path.dirname(__file__))
    fake_project = Path(here) / 'data' / 'fake_project'

    tempdir = tempfile.TemporaryDirectory(prefix='fake_project_')
    fake_project_copy = Path(tempdir.name) / 'fake_project'

    shutil.copytree(fake_project.as_posix(), fake_project_copy.as_posix())

    def fin():
        tempdir.cleanup()
    request.addfinalizer(fin)

    return fake_project_copy
