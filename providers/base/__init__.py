# -*- coding: utf-8 -*-


class BaseDataProvider(object):
    """ All data providers should implement this interface.
    """
    def get_items(self, date=None, skip_archived=False):
        """ Returns a list of :class:`Item` objects for given date.

        :date: if not specified, current date is used.
        """
        raise NotImplementedError

    def filter_items(self, opened=None, closed=None, frozen=None):
        """ Returns a list of :class:`Item` objects for given date.

        :opened: a date; default is None.
        :closed: a date; default is None.
        :frozen: a bool; default is None (no filtration at all).
        """
        raise NotImplementedError

    def get_plans(self, date=None):
        """ Returns a list of :class:`Plan` objects for given date.

        :date: if not specified, current date is used.
        """
        raise NotImplementedError

    def get_document_list(self, category):
        """ Returns a list of documents under given category.
        """
        raise NotImplementedError

    def get_document(self, category, slug):
        """ Returns document with given slug under given category.
        """
        raise NotImplementedError
