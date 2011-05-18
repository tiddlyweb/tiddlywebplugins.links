"""
Routines for maintain a links database about links
between tiddlers. Managed as a forward links database
but used as a backlinks database.
"""

import anydbm
import os
import sys

from tiddlyweb.web.util import get_route_value
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers
from tiddlyweb.store import StoreError, HOOKS
from tiddlyweb.web.sendtiddlers import send_tiddlers

from tiddlywebplugins.links.parser import process_tiddler, is_link


def init(config):
    if 'selector' in config:
        base = '/bags/{bag_name:segment}/tiddlers/{tiddler_name:segment}'
        config['selector'].add(base + '/backlinks[.{format}]',
                GET=get_backlinks)
        config['selector'].add(base + '/frontlinks[.{format}]',
                GET=get_frontlinks)


def tiddler_change_hook(store, tiddler):
    """
    Update the links database with data from this tiddler.

    TODO: work with other renderable types, not just tiddlywiki text.
    """
    if not tiddler.type or tiddler.type == 'None':
        links_manager = LinksManager(store.environ)
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


def _get_links(environ, start_response, type):
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
    title = '%s for %s' % (type, tiddler_title)

    tiddler = Tiddler(tiddler_title, bag_name)
    try:
        tiddler = store.get(tiddler)
    except StoreError, exc:
        raise HTTP404('No such tiddler: %s:%s, %s' % (tiddler.bag,
            tiddler.title, exc))

    links_manager = LinksManager(environ)

    try:
        links = getattr(links_manager, 'read_%s' % type)(tiddler)
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
            tiddler = Tiddler(title, bag)
            try:
                tiddler = store.get(tiddler)
            except StoreError:
                # fake the existence of the tiddler
                tiddler.store = store
        tiddlers.add(tiddler)

    return send_tiddlers(environ, start_response, tiddlers=tiddlers)


class LinksManager(object):
    """
    A container class for the functionality for managing a 
    front and backlinks database. The primary purpose is to
    encapsulate an 'environ' and provide the forward opportunity
    to subclass for different types of storage.
    """

    def __init__(self, environ=None):
        """
        Establish an environ for this instance.
        """
        if environ is None:
            environ = {}
        self.environ = environ

    def update_database(self, tiddler):
        """
        Update the front and back links databases with the provided
        tiddler.
        """
        links = process_tiddler(tiddler)
        self._update_frontlinks(links, tiddler)
        self._update_backlinks(links, tiddler)

    def read_frontlinks(self, tiddler):
        """
        Return a list of forward links from this tiddler.
        """
        return self._read_links('frontlinks', tiddler)

    def read_backlinks(self, tiddler):
        """
        Return a list of links to this tiddler.
        """
        return self._read_links('backlinks', tiddler)

    def _read_links(self, type, tiddler):
        """
        Read a database to get the value at a key generated from
        the provided tiddler.
        """
        database = self._open_database(type)
        tiddler_key = '%s:%s' % (tiddler.bag, tiddler.title)
        tiddler_key = tiddler_key.encode('utf-8')
        try:
            return database[tiddler_key].split('\0')
        except KeyError:
            return []

    def _update_backlinks(self, links, tiddler):
        """
        Update the backlinks database.
        """
        database = self._open_database('backlinks')
        target_value = '%s:%s' % (tiddler.bag, tiddler.title)

        for target, space in links:
            if is_link(target):
                continue
            if space:
                key = '%s_public:%s' % (space, target)
            else:
                key = '%s:%s' % (tiddler.bag, target)
            key = key.encode('utf-8')
            try:
                back_targets = database[key].decode('UTF-8').split('\0')
            except KeyError:
                back_targets = []
            if key not in back_targets:
                back_targets.append(target_value)
                database[key] = '\0'.join(back_targets).encode('UTF-8')

    def _update_frontlinks(self, links, tiddler):
        """
        Update the frontlinks database.
        """
        database = self._open_database('frontlinks')
        key = '%s:%s' % (tiddler.bag, tiddler.title)
        key = key.encode('utf-8')
        # Remove existing data
        try:
            del database[key]
        except KeyError:
            pass
        front_targets = []
        for target, space in links:
            if space:
                target_value = '%s_public:%s' % (space, target)
            elif is_link(target):
                target_value = target
            else:
                target_value = '%s:%s' % (tiddler.bag, target)
            front_targets.append(target_value)
        targets = '\0'.join(front_targets).encode('UTF-8')
        database[key] = targets

    def _open_database(self, path):
        """
        Open an anydbm database file. If the path is not
        absolute and root_dir is set in config, make the 
        path absolute.
        """
        if not os.path.isabs(path):
            path = os.path.join(self.environ.get('tiddlyweb.config', {})
                    .get('root_dir', ''), path)
        return anydbm.open(path, 'c')
