from autopilot import utils

def test_get_next_version():
    assert utils.get_next_version('1.0.0') == '1.0.1'
    assert utils.get_next_version('1.0.0', release_type='minor') == '1.1.0'
    assert utils.get_next_version('1.0.0', release_type='major') == '2.0.0'

    assert utils.get_next_version('1.0.0', dev=True) == '1.0.1.dev0'
    assert utils.get_next_version('1.0.0', dev=True, release_type='minor') == '1.1.0.dev0'
    assert utils.get_next_version('1.0.0', dev=True, release_type='major') == '2.0.0.dev0'

    assert utils.get_next_version('1.0.0.dev0') == '1.0.0'  # NO
    assert utils.get_next_version('1.0.0.dev0', release_type='minor') == '1.1.0'
    assert utils.get_next_version('1.0.0.dev0', release_type='major') == '2.0.0'
