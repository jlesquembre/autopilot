from datetime import datetime as dt
from unittest.mock import patch

import pytest

from autopilot.utils import get_header, update_changelog




@pytest.mark.parametrize('reader,line', [
('''\
Changelog for autopilot
=======================


0.2.1 (unreleased)
------------------

- Some message
''', 4),

('''\
0.2.1 (unreleased)
------------------
''', 0),

('''\

0.2.1 (2015-01-01)
------------------
''', 1),

     ], indirect=['reader'])
def test_get_header(reader, line):
    result = get_header(reader)
    assert result['line'] == line


@pytest.mark.parametrize('reader,output,version,release', [
('''\
Changelog for autopilot
=======================
0.2.1 (unreleased)
------------------

- Message
''', '''\
Changelog for autopilot
=======================
1.0.0 (2015-12-12)
------------------

- Message
''', '1.0.0', True),
# ##
('''\
0.2.1 (unreleased)
------------------
''', '''\
1.0.0 (2015-12-12)
------------------
''', '1.0.0', True),
# ##
('''\
0.2.1 (unreleased)
------------------
- Message

0.1.0 (2014-12-01)
------------------
''', '''\
1.0.0 (2015-12-12)
------------------
- Message

0.1.0 (2014-12-01)
------------------
''', '1.0.0', True),
# ##
('''\
0.2.1 (2015-01-01)
------------------
- Message

0.1.0 (2014-12-01)
------------------
''', '''\
1.0.0 (unreleased)
------------------

- Nothing changed yet


0.2.1 (2015-01-01)
------------------
- Message

0.1.0 (2014-12-01)
------------------
''', '1.0.0', False),
    ], indirect=['reader'])
def test_update_changelog(reader, writer, output, version, release):

    with patch('autopilot.utils.datetime', **{'now.return_value': dt(2015, 12, 12)}):
        update_changelog(reader, writer, version, release)
        assert writer.output.lastvalue == output
