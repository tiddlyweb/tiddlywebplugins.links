import re
import sys
from pyparsing import *

space = (Literal('@').suppress() + Word(alphanums, alphanums + '-'))('space')

wikiword = Regex(r'[A-Z][a-z]+([A-Z][a-z]+)+', flags=re.UNICODE)('link') + Optional(space)

link = (Literal("[[").suppress() + SkipTo(']]')('link')
        + Literal("]]").suppress()) + Optional(space)

def record_link(link):
    """
    Split a free link into lable and target
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
    data = sys.stdin.read()

    links = []
    for p in link.scanString(data):
        links.append(record_link(p))

    for w in wikiword.scanString(data):
        links.append(record_link(w))

    for s in space.scanString(data):
        links.append(record_link(s))

    return links

if __name__ == '__main__':
    print process_in()
