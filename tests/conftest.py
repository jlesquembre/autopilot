import os
import subprocess
import tempfile
import socket

from io import StringIO
from urllib.request import urlopen
from urllib.error import URLError
from unittest.mock import MagicMock
from pathlib import PurePath, Path

import pytest


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


def get_open_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('',0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port


@pytest.fixture
def pypi_server(request):
    tempdir = tempfile.TemporaryDirectory(prefix='pypi_index_')
    port = get_open_port()
    server_url = 'http://localhost:{}'.format(port)
    sink = open(os.devnull, 'w')
    #cmd = ['pypi-server', '-P', 'passwords', 'packages']
    cmd = ['pypi-server', '-p', str(port), tempdir.name]
    server = subprocess.Popen(cmd, stdout=sink, stderr=sink)
                              #,cwd=HERE)
    # wait for the server to start up
    response = None
    while response is None:
        try:
            response = urlopen(server_url)
        except URLError:
            pass

    def fin():
        if server and server.returncode is None:
            server.kill()
        tempdir.cleanup()
        sink.close()

    request.addfinalizer(fin)

    tempdir_path = Path(tempdir.name)

    passfile = tempdir_path / 'passwords'
    if not passfile.exists():
        with passfile.open('w') as f:
            f.write('user:pass\n')

    return server_url, tempdir_path
