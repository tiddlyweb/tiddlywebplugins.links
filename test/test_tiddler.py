
from tiddlywebplugins.links.parser import process_tiddler
from tiddlywebplugins.links.linksmanager import LinksManager

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.recipe import Recipe
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

    # cascade to deal with differently named files depending on 
    # anydbm impelementation
    try:
        os.unlink('links.db')
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

    # for @someone syntax to test correctly we need a corresponding
    # recipe
    module.store.put(Recipe('cdent_public'))


def test_simple_tiddler():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = 'I am NotYou, you [[are|you]]!'

    links = process_tiddler(tiddler)

    assert links[0] == ('NotYou', None)
    assert links[1] == ('you', None)

def test_space_only():
    tiddler = Tiddler('cow', 'barn')
    tiddler.text = '@cdent'

    links_manager.delete_links(tiddler)
    links_manager.update_database(tiddler)

    frontlinks = links_manager.read_frontlinks(tiddler)

    assert '@cdent:' in frontlinks

def test_store_tiddler():
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = 'I am NotYou, you [[are|you]]!'

    links_manager.delete_links(tiddler)
    links_manager.update_database(tiddler)

    frontlinks = links_manager.read_frontlinks(tiddler)

    assert 'barney:you' in frontlinks
    assert 'barney:NotYou' in frontlinks

    tiddler = Tiddler('you', 'barney')
    backlinks = links_manager.read_backlinks(tiddler)

    assert 'barney:hello' in backlinks

def test_stored_with_space():
    store.put(Bag('barney'))
    tiddler = Tiddler('hello', 'barney')
    tiddler.text = "I am NotYou@cdent, http://burningchrome.com/"

    store.put(tiddler)

    frontlinks = links_manager.read_frontlinks(tiddler)
    assert len(frontlinks) == 2, frontlinks

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

    http = httplib2.Http()
    response, content = http.request('http://0.0.0.0:8080/bags/bagone/tiddlers/tiddlerone/frontlinks.html')
    assert response['status'] == '200', content
    assert '<a href="http://cdent.0.0.0.0:8080/NotYou">NotYou</a>' in content, content
    assert '<a href="http://burningchrome.com/">http://burningchrome.com/</a>' in content

    bag = Bag('cdent_public')
    store.put(bag)
    tiddler = Tiddler('NotYou', 'cdent_public')
    tiddler.text = 'as BigPoo is'
    store.put(tiddler)

    response, content = http.request('http://0.0.0.0:8080/bags/cdent_public/tiddlers/NotYou/frontlinks')
    assert '<a href="/bags/cdent_public/tiddlers/BigPoo">BigPoo</a>' in content, content

    response, content = http.request('http://0.0.0.0:8080/bags/cdent_public/tiddlers/NotYou/backlinks')

    assert '<a href="/bags/barney/tiddlers/hello">hello</a>' in content
    assert '<a href="/bags/bagone/tiddlers/tiddlerone">tiddlerone</a>' in content

    # Use web delete, not store delete as web delete instantiates the tiddler
    #store.delete(Tiddler('hello', 'barney'))
    response, content = http.request('http://0.0.0.0:8080/bags/barney/tiddlers/hello', method='DELETE')
    assert response['status'] == '204'

    response, content = http.request('http://0.0.0.0:8080/bags/cdent_public/tiddlers/NotYou/backlinks')
 
    assert '<a href="/bags/barney/tiddlers/hello">hello</a>' not in content

    tiddler = Tiddler('monkey', 'barney')
    tiddler.text = '@cdent'
    store.put(tiddler)

    response, content = http.request('http://0.0.0.0:8080/bags/barney/tiddlers/monkey/frontlinks')

    assert response['status'] == '200', content
    assert '<a href="http://cdent.0.0.0.0:8080/">@cdent</a>' in content

def test_web_serialized():
    http = httplib2.Http()
    response, content = http.request('http://0.0.0.0:8080/bags/cdent_public/tiddlers/NotYou/backlinks.json')

    assert response['status'] == '200', content
