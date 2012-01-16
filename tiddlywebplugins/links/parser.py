
import re
import sys

from pyparsing import Literal, Word, alphanums, Regex, Optional, SkipTo, Or

### Establish Parser Rules
URL_PATTERN = r"(?:file|http|https|mailto|ftp|irc|news|data):[^\s'\"]+(?:/|\b)"
SPACE = (Literal('@').suppress() + Word(alphanums, alphanums + '-'))('space')
WIKIWORD = (Regex(r'[A-Z][a-z]+(?:[A-Z][a-z]*)+')('link')
        + Optional(SPACE.leaveWhitespace()))
LINK = (Literal("[[").suppress() + SkipTo(']]')('link')
        + Literal("]]").suppress() + Optional(SPACE.leaveWhitespace()))
NONWIKISPACE = Word(alphanums, alphanums)('link') + SPACE.leaveWhitespace()
HTTP = Regex(URL_PATTERN)('link')

# What we care about in the content are links, or wikiwords, or bare
# space names.
CONTENT = Or([LINK, WIKIWORD, HTTP, SPACE, NONWIKISPACE])


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


def is_link(target):
    """
    True if target is a URL.
    """
    return re.match(URL_PATTERN, target)


if __name__ == '__main__':
    print process_in()
