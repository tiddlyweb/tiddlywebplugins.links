"""
Routines for maintain a links database about links
between tiddlers. Managed as a forward links database
but used as a backlinks database.
"""

import anydbm
import os
import re
import sys
from pyparsing import Literal, Word, alphanums, Regex, Optional, SkipTo

URL_PATTERN = r"(?:file|http|https|mailto|ftp|irc|news|data):[^\s'\"]+(?:/|\b)"

SPACE = (Literal('@').suppress() + Word(alphanums, alphanums + '-'))('space')

WIKIWORD = (Regex(r'[A-Z][a-z]+(?:[A-Z][a-z]*)+')('link')
        + Optional(SPACE.leaveWhitespace()))

LINK = (Literal("[[").suppress() + SkipTo(']]')('link')
        + Literal("]]").suppress() + Optional(SPACE.leaveWhitespace()))

HTTP = Regex(URL_PATTERN)('link')

# What we care about in the content are links, or wikiwords, or bare
# space names.
CONTENT = LINK ^ WIKIWORD ^ HTTP ^ SPACE


def record_link(link):
    """
    Process a link token into a target and space tuple.
    """
    token, _, _ = link
    link = token.get('link')
    space = token.get('space', [None])
    if link and '|' in link:
        _, target = link.split('|', 1)
    elif link:
        target = link
    else:
        target = None
    return (target, space[0])


def process_in():
    """
    Read stdin, return list of link, space tuples.
    """
    return process_data(sys.stdin.read())


def process_tiddler(tiddler):
    """
    Send tiddler text to be processed.
    """
    return process_data(tiddler.text)


def process_data(data):
    """
    Take the text in data and scan for links.
    """
    links = []

    for token in CONTENT.scanString(data):
        links.append(record_link(token))

    return links

class LinksManager(object):

    def __init__(self, environ=None):
        if environ is None:
            environ = {}
        self.environ = environ

    def update_database(self, tiddler):
        links = process_tiddler(tiddler)
        self._update_frontlinks(links, tiddler)
        self._update_backlinks(links, tiddler)

    def read_frontlinks(self, tiddler):
        return self._read_links('frontlinks', tiddler)

    def read_backlinks(self, tiddler):
        return self._read_links('backlinks', tiddler)

    def _read_links(self, type, tiddler):
        database = self._open_database(type)
        tiddler_key = '%s:%s' % (tiddler.bag, tiddler.title)
        try:
            return database[tiddler_key].split('\0')
        except KeyError:
            return []

    def _update_backlinks(self, links, tiddler):
        database = self._open_database('backlinks')
        target_value = '%s:%s' % (tiddler.bag, tiddler.title)

        for target, space in links:
            if _is_link(target):
                continue
            if space:
                key = '%s_public:%s' % (space, target)
            else:
                key = '%s:%s' % (tiddler.bag, target)
            try:
                back_targets = database[key].decode('UTF-8').split('\0')
            except KeyError:
                back_targets = []
            if key not in back_targets:
                back_targets.append(target_value)
                database[key] = '\0'.join(back_targets).encode('UTF-8')

    def _update_frontlinks(self, links, tiddler):
        database = self._open_database('frontlinks')
        key = '%s:%s' % (tiddler.bag, tiddler.title)
        # Remove existing data
        try:
            del database[key]
        except KeyError:
            pass
        front_targets = []
        for target, space in links:
            if space:
                target_value = '%s_public:%s' % (space, target)
            elif _is_link(target):
                target_value = target
            else:
                target_value = '%s:%s' % (tiddler.bag, target)
            front_targets.append(target_value)
        targets = '\0'.join(front_targets).encode('UTF-8')
        database[key] = targets

    def _open_database(self, path):
        if not os.path.isabs(path):
            path = os.path.join(self.environ.get('tiddlyweb.config', {})
                    .get('root_dir', ''), path)
        return anydbm.open(path, 'c')


def _is_link(target):
    """
    True if target is a URL.
    """
    return re.match(URL_PATTERN, target)


if __name__ == '__main__':
    print process_in()
