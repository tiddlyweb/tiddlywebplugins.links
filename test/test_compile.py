


def test_compile():
    try:
        import tiddlywebplugins.links
        assert True
    except ImportError as exc:
        assert False, exc
