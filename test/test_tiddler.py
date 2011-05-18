
from tiddlywebplugins.links import process_tiddler, LinksManager, init

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlywebplugins.utils import get_store
from tiddlyweb.config import config
from tiddlyweb.web import serve

import os

from wsgi_intercept import httplib2_intercept
import wsgi_intercept
import httplib2

def setup_module(module):

    module.store = get_store(config)

    try:
        os.unlink('frontlinks.db')
        os.unlink('backlinks.db')
    except OSError:
        pass  # not there
    module.links_manager = LinksManager()

    try:
        shutil.rmtree('store')
    except:
        pass
    
    def app():
        return serve.load_app()
    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('0.0.0.0', 8080, app)


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

def test_web_front():
    bag = Bag('bagone')
    store.put(bag)
    tiddler = Tiddler('tiddlerone', 'bagone')
    tiddler.text = "I am NotYou@cdent, http://burningchrome.com/"
    store.put(tiddler)

    links_manager.update_database(tiddler)

    http = httplib2.Http()
    response, content = http.request('http://0.0.0.0:8080/bags/bagone/tiddlers/tiddlerone/frontlinks')
    print 'TODO'
    print content

    bag = Bag('cdent_public')
    store.put(bag)
    tiddler = Tiddler('NotYou', 'cdent_public')
    tiddler.text = 'as BigPoo is'
    store.put(tiddler)

    links_manager.update_database(tiddler)

    response, content = http.request('http://0.0.0.0:8080/bags/cdent_public/tiddlers/NotYou/frontlinks')
    print 'NotYou frontlinks'
    print content
    response, content = http.request('http://0.0.0.0:8080/bags/cdent_public/tiddlers/NotYou/backlinks')
    print 'NotYou backlinks'
    print content
