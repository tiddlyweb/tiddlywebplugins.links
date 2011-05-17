import re
import sys
from pyparsing import *

space = '@' + Word(alphanums + '-')

wikiword = (Regex(r'[A-Z][a-z]+([A-Z][a-z]+)+', flags=re.UNICODE) + Optional(space)('link')

link = ((Literal("[[").suppress() + SkipTo(']]')
        + Literal("]]").suppress()) + Options(space))('link')

def record_free_link(link):
    """
    Split a free link into lable and target
    """
    token, start, end = link
    token = token[0]
    if '|' in token:
        label, target = token.split('|', 1)
    else:
        target = token
    return target


def record_wiki_link(link):
    token, start, end = link
    token = token[0]
    target = token
    return target


def process_in():
    data = sys.stdin.read()

    links = []
    for p in link.scanString(data):
        links.append(record_free_link(p))

    for w in wikiword.scanString(data):
        links.append(record_wiki_link(w))

    print links


if __name__ == '__main__':
    process_in()
