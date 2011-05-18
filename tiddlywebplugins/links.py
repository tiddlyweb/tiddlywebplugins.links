"""
Routines for maintain a links database about links
between tiddlers. Managed as a forward links database
but used as a backlinks database.
"""

import sys
from pyparsing import Literal, Word, alphanums, Regex, Optional, SkipTo

SPACE = (Literal('@').suppress() + Word(alphanums, alphanums + '-'))('space')

WIKIWORD = (Regex(r'[A-Z][a-z]+(?:[A-Z][a-z]*)+')('link')
        + Optional(SPACE.leaveWhitespace()))

LINK = (Literal("[[").suppress() + SkipTo(']]')('link')
        + Literal("]]").suppress() + Optional(SPACE.leaveWhitespace()))

HTTP = Regex(r"(?:file|http|https|mailto|ftp|irc|news|data):[^\s'\"]+(?:/|\b)")('link')

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


def process_data(data):
    """
    Take the text in data and scan for links.
    """
    links = []

    for token in CONTENT.scanString(data):
        links.append(record_link(token))

    return links


if __name__ == '__main__':
    print process_in()
