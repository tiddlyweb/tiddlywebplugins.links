"""
Routines for maintain a links database about links
between tiddlers. Managed as a forward links database
but used as a backlinks database.
"""

import logging

from tiddlyweb.control import determine_bag_from_recipe
from tiddlyweb.manage import make_command
from tiddlyweb.web.util import get_route_value, encode_name
from tiddlyweb.web.http import HTTP404, HTTP400
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import PermissionsError
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers
from tiddlyweb.store import StoreError, HOOKS
from tiddlyweb.web.sendtiddlers import send_tiddlers

from tiddlywebplugins.utils import get_store

from tiddlywebplugins.links.linksmanager import LinksManager
from tiddlywebplugins.links.parser import is_link

from tiddlywebplugins.tiddlyspace.spaces import space_uri
from tiddlywebplugins.tiddlyspace.space import Space


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
                tiddler = store.get(tiddler)  # we must get text
                links_manager.delete_links(tiddler)
                if not tiddler.type or tiddler.type == 'None':
                    links_manager.update_database(tiddler)


def tiddler_put_hook(store, tiddler):
    """
    Update the links database with data from this tiddler.
    """
    links_manager = LinksManager(store.environ)
    links_manager.delete_links(tiddler)
    if not tiddler.type or tiddler.type == 'None':
        links_manager.update_database(tiddler)


def tiddler_delete_hook(store, tiddler):
    """
    Remove links data associated with deleted tiddler.
    """
    links_manager = LinksManager(store.environ)
    links_manager.delete_links(tiddler)


# Establish hooks
HOOKS['tiddler']['put'].append(tiddler_put_hook)
HOOKS['tiddler']['delete'].append(tiddler_delete_hook)


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
    collection_title = '%s for %s' % (linktype, tiddler_title)

    link = environ['SCRIPT_NAME']
    try:
        extension = environ['tiddlyweb.extension']
        link = link.rsplit('.%s' % extension)[0]
    except KeyError:
        pass

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
        tiddlers = Tiddlers(title=collection_title)
    else:
        tiddlers = Tiddlers(title=collection_title, store=store)
    tiddlers.link = link

    for link in links:
        if is_link(link):
            tiddler = _link_tiddler(link, store)
        else:
            container, title = link.split(':', 1)
            if not title:  # plain space link
                if container.startswith('@'):
                    container = container[1:] + '_public'
                space = Space.name_from_recipe(container)
                uri = space_uri(environ, space)
                tiddler = _link_tiddler(uri, store, '@%s' % space)
                tiddler.recipe = container
            elif title:
                try:
                    if container == bag_name:
                        raise ValueError
                    space = Space.name_from_recipe(container)
                    tiddler = Tiddler(title)
                    tiddler.recipe = container
                    uri = space_uri(environ, space)
                    uri += encode_name(title)
                    tiddler.fields['_canonical_uri'] = uri
                    tiddler.store = store
                except ValueError:
                    try:
                        recipe = Recipe(container)
                        recipe = store.get(recipe)
                        bag = determine_bag_from_recipe(recipe, tiddler,
                                environ)
                        bag_name = bag.name
                    except StoreError:
                        bag_name = container
                    tiddler = Tiddler(title, bag_name)
                    try:
                        tiddler = store.get(tiddler)
                    except StoreError:
                        # fake the existence of the tiddler
                        tiddler.store = store
        if _is_readable(environ, tiddler):
            tiddlers.add(tiddler)

    return send_tiddlers(environ, start_response, tiddlers=tiddlers)


def _link_tiddler(uri, store, title=None):
    """
    Create an artificial tiddler to represent a link.
    """
    if not title:
        title = uri
    tiddler = Tiddler(title)
    tiddler.text = uri
    tiddler.fields['_canonical_uri'] = uri
    tiddler.store = store
    return tiddler


def _is_readable(environ, tiddler):
    """
    Return true if recipe.policy read allows, and
    bag.policy read allows, or if neither bag or recipe
    is set.
    """
    store = environ['tiddlyweb.store']
    usersign = environ['tiddlyweb.usersign']
    if tiddler.recipe:
        try:
            recipe = store.get(Recipe(tiddler.recipe))
        except StoreError:
            return False
        try:
            recipe.policy.allows(usersign, 'read')
        except PermissionsError:
            return False

    if tiddler.bag:
        try:
            bag = store.get(Bag(tiddler.bag))
        except StoreError:
            return False
        try:
            bag.policy.allows(usersign, 'read')
        except PermissionsError:
            return False

    return True
