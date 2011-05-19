"""
Routines for maintain a links database about links
between tiddlers. Managed as a forward links database
but used as a backlinks database.
"""

import logging

from tiddlyweb.manage import make_command
from tiddlyweb.web.util import get_route_value
from tiddlyweb.web.http import HTTP404, HTTP400
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers
from tiddlyweb.store import StoreError, HOOKS
from tiddlyweb.web.sendtiddlers import send_tiddlers

from tiddlywebplugins.utils import get_store

from tiddlywebplugins.links.linksmanager import LinksManager
from tiddlywebplugins.links.parser import is_link


def init(config):
    """
    Add the back and front links handlers.
    """
    if 'selector' in config:
        base = '/bags/{bag_name:segment}/tiddlers/{tiddler_name:segment}'
        config['selector'].add(base + '/backlinks[.{format}]',
                GET=get_backlinks)
        config['selector'].add(base + '/frontlinks[.{format}]',
                GET=get_frontlinks)

    @make_command()
    def refreshlinksdb(args):
        """Refresh the back and front links database."""
        store = get_store(config)

        links_manager = LinksManager(store.environ)
        for bag in store.list_bags():
            logging.debug('updating links for tiddlers in bag: %s', bag.name)
            for tiddler in store.list_bag_tiddlers(bag):
                tiddler = store.get(tiddler) #  we must get text
                links_manager.delete_links(tiddler)
                if not tiddler.type or tiddler.type == 'None':
                    links_manager.update_database(tiddler)


def tiddler_change_hook(store, tiddler):
    """
    Update the links database with data from this tiddler.

    TODO: work with other renderable types, not just tiddlywiki text.
    """
    links_manager = LinksManager(store.environ)
    links_manager.delete_links(tiddler)
    if not tiddler.type or tiddler.type == 'None':
        links_manager.update_database(tiddler)


# Establish hooks
HOOKS['tiddler']['put'].append(tiddler_change_hook)
HOOKS['tiddler']['delete'].append(tiddler_change_hook)


def get_backlinks(environ, start_response):
    """
    Return backlinks as a list of tiddlers.
    """
    return _get_links(environ, start_response, 'backlinks')


def get_frontlinks(environ, start_response):
    """
    Return frontlinks as a list of tiddlers.
    """
    return _get_links(environ, start_response, 'frontlinks')


def _get_links(environ, start_response, linktype):
    """
    Form the links as tiddlers and then send them 
    to send_tiddlers. This allows us to use the 
    serialization and filtering subsystems on the
    lists of links.
    """
    bag_name = get_route_value(environ, 'bag_name')
    tiddler_title = get_route_value(environ, 'tiddler_name')
    store = environ['tiddlyweb.store']
    filters = environ['tiddlyweb.filters']
    title = '%s for %s' % (linktype, tiddler_title)

    tiddler = Tiddler(tiddler_title, bag_name)
    try:
        tiddler = store.get(tiddler)
    except StoreError, exc:
        raise HTTP404('No such tiddler: %s:%s, %s' % (tiddler.bag,
            tiddler.title, exc))

    links_manager = LinksManager(environ)

    try:
        links = getattr(links_manager, 'read_%s' % linktype)(tiddler)
    except AttributeError, exc:
        raise HTTP400('invalid links type: %s' % exc)

    if filters:
        tiddlers = Tiddlers(title=title)
    else:
        tiddlers = Tiddlers(title=title, store=store)

    for link in links:
        if is_link(link):
            tiddler = Tiddler(link, 'temp')
            tiddler.text = link
            tiddler.fields['_canonical_uri'] = link
            tiddler.store = store
        else:
            bag, title = link.split(':', 1)
            if title:
                tiddler = Tiddler(title, bag)
                try:
                    tiddler = store.get(tiddler)
                except StoreError:
                    # fake the existence of the tiddler
                    tiddler.store = store
            else:
                continue #  skip space targets (for now)
        tiddlers.add(tiddler)

    return send_tiddlers(environ, start_response, tiddlers=tiddlers)
