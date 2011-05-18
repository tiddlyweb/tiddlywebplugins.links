
from tiddlywebplugins.links import process_tiddler, LinksManager

from tiddlyweb.model.tiddler import Tiddler

import os

def setup_module(module):
    try:
        os.unlink('frontlinks.db')
        os.unlink('backlinks.db')
    except OSError:
        pass  # not there
    module.links_manager = LinksManager()


def test_simple_tiddler():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = 'I am NotYou, you [[are|you]]!'

    links = process_tiddler(tiddler)

    assert links[0] == ('NotYou', None)
    assert links[1] == ('you', None)

def test_store_tiddler():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = 'I am NotYou, you [[are|you]]!'

    links_manager.update_database(tiddler)

    frontlinks = links_manager.read_frontlinks(tiddler)
    print frontlinks

    assert 'barney:you' in frontlinks
    assert 'barney:NotYou' in frontlinks

    tiddler = Tiddler('you', 'barney')
    backlinks = links_manager.read_backlinks(tiddler)
    print backlinks

    assert 'barney:hello' in backlinks

def test_stored_with_space():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = "I am NotYou@cdent, http://burningchrome.com/"

    links_manager.update_database(tiddler)

    frontlinks = links_manager.read_frontlinks(tiddler)
    assert len(frontlinks) == 2, frontlinks
    print frontlinks

    tiddler = Tiddler('NotYou', 'cdent_public')
    backlinks = links_manager.read_backlinks(tiddler)
    assert len(backlinks) == 1, backlinks
    assert 'barney:hello' in backlinks
