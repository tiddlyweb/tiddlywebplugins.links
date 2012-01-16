

from tiddlywebplugins.links.parser import process_data


def test_wikilink():
    links = process_data('I had a WikiLink once')

    assert links[0] == ('WikiLink', None)

def test_freelink_no_target():
    links = process_data('You should not use [[free links]]')

    assert links[0] == ('free links', None)

def test_freelink_target():
    links = process_data('You should not use [[free links|FreeLinks]]')

    assert links[0] == ('FreeLinks', None)

def test_freelink_href():
    links = process_data('You should not use [[free links|http://cdent-mt.tiddlyspace.com/Collaboration%20Requires%20Goals]]')

    assert links[0] == ('http://cdent-mt.tiddlyspace.com/Collaboration%20Requires%20Goals', None)

def test_plain_href():
    links = process_data('I link to http://burningchrome.com/ all the time')

    assert links[0] == ('http://burningchrome.com/', None)

def test_punct_href():
    links = process_data('I link to http://burningchrome.com/too, all the time')

    assert links[0] == ('http://burningchrome.com/too', None)

def test_anchor_href():
    links = process_data('I link to http://burningchrome.com/too#this, all the time')

    assert links[0] == ('http://burningchrome.com/too#this', None)

def test_query_href():
    links = process_data('I link to http://burningchrome.com/too?q=pie, all the time')

    assert links[0] == ('http://burningchrome.com/too?q=pie', None)

def test_spacelink():
    links = process_data('Stop by, say hi to @cdent, yes?')

    assert links[0] == (None, 'cdent')

def test_wiki_spacelink():
    links = process_data('I had a WikiLink@cdent once')

    assert links[0] == ('WikiLink', 'cdent')

def test_freelink_no_target_spacelink():
    links = process_data('You should not use [[free links]]@cdent')

    assert links[0] == ('free links', 'cdent')

def test_freelink_target_spacelink():
    links = process_data('You should not use [[free links|FreeLinks]]@cdent-mt, okay?')

    assert links[0] == ('FreeLinks', 'cdent-mt')

def test_nonwiki_spacelink():
    links = process_data('I had not know that this@cdent-mt ought to work.')

    assert links[0] == ('this', 'cdent-mt')

def test_combo():
    links = process_data('All TheTime [[we are]] [[wanting|compound needs]] @things, [[you know]]@cart?')
    assert links[0] == ('TheTime', None)
    assert links[1] == ('we are', None)
    assert links[2] == ('compound needs', None)
    assert links[3] == (None, 'things')
    assert links[4] == ('you know', 'cart')
