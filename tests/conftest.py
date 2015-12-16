from io import StringIO
from unittest.mock import MagicMock
from pathlib import PurePath

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
