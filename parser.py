import re
import sys
from pyparsing import Literal, Word, alphanums, Regex, Optional, SkipTo

space = (Literal('@').suppress() + Word(alphanums, alphanums + '-'))('space')

wikiword = (Regex(r'[A-Z][a-z]+(?:[A-Z][a-z]*)+')('link')
        + Optional(space.leaveWhitespace()))

link = (Literal("[[").suppress() + SkipTo(']]')('link')
        + Literal("]]").suppress() + Optional(space.leaveWhitespace()))

# What we care about in the content are links, or wikiwords, or bare
# spaces.
content = link ^ wikiword ^ space

def record_link(link):
    """
    Process a link token into a target and space tuple.
    """
    token, start, end = link
    link = token.get('link')
    space = token.get('space', [None])
    if link and '|' in link:
        label, target = link.split('|', 1)
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

    for c in content.scanString(data):
        links.append(record_link(c))

    return links


if __name__ == '__main__':
    print process_in()
