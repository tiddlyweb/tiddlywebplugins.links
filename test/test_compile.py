


def test_compile():
    try:
        import tiddlywebplugins.links
        assert True
    except ImportError, exc:
        assert False, exc
