from autopilot import pypi


def test_upload(pypi_server):
    # TODO upload real package
    url, local_dir = pypi_server
    assert type(pypi_server) is tuple
    assert len(pypi_server) == 2
    assert local_dir.is_dir()
    assert local_dir.exists()
    assert len(list(local_dir.iterdir())) == 0

    pypi.pypi_upload({'url': url,
                      'user': 'user',
                      'passeval': 'echo pass'
                      })
