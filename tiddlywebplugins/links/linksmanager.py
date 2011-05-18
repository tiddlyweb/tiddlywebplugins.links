import anydbm
import os
 
from tiddlywebplugins.links.parser import process_tiddler, is_link

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
