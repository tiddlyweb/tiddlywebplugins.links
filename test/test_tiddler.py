
from tiddlywebplugins.links import (process_tiddler, update_database,
        read_frontlinks, read_backlinks)

from tiddlyweb.model.tiddler import Tiddler

import os

def setup_module(module):
    os.unlink('frontlinks.db')
    os.unlink('backlinks.db')


def test_simple_tiddler():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = 'I am NotYou, you [[are|you]]!'

    links = process_tiddler(tiddler)

    assert links[0] == ('NotYou', None)
    assert links[1] == ('you', None)

def test_store_tiddler():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = 'I am NotYou, you [[are|you]]!'

    update_database(tiddler)

    frontlinks = read_frontlinks(tiddler)
    print frontlinks

    assert 'barney:you' in frontlinks
    assert 'barney:NotYou' in frontlinks

    tiddler = Tiddler('you', 'barney')
    backlinks = read_backlinks(tiddler)
    print backlinks

    assert 'barney:hello' in backlinks

def test_stored_with_space():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = "I am NotYou@cdent, http://burningchrome.com/"

    update_database(tiddler)

    frontlinks = read_frontlinks(tiddler)
    assert len(frontlinks) == 2, frontlinks
    print frontlinks

    tiddler = Tiddler('NotYou', 'cdent_public')
    backlinks = read_backlinks(tiddler)
    assert len(backlinks) == 1, backlinks
    assert 'barney:hello' in backlinks
