# -*- coding: utf-8 -*-

import utils  # XXX для yamlfiles; надо бы переместить


class DataProvidersManager(object):
    """ A simplified API for a set of data providers.
    """
    def __init__(self, providers):
        self.providers = providers

    def _collect(self, meth_name, args, kwargs):
        for provider in self.providers:
            try:
                meth = getattr(provider, meth_name)
                elems = meth(*args, **kwargs)
            except NotImplementedError:
                pass
            else:
                for elem in elems:
                    yield elem

    def _get_first(self, meth_name, args, kwargs):
        #print 'available providers:', self.providers
        for provider in self.providers:
            #print 'trying', provider
            try:
                meth = getattr(provider, meth_name)
                value = meth(*args, **kwargs)
            except NotImplementedError:
                #print '  not implemented'
                pass
            else:
                #print '  got value', value
                if value:
                    #print '  value accepted'
                    return value

    def get_items(self, *args, **kwargs):
        """ Returns a list of :class:`Item` objects for given date.

        :date: if not specified, current date is used.
        """
        return self._collect('get_items', args, kwargs)

    def filter_items(self, *args, **kwargs):
        """ Returns a list of :class:`Item` objects for given date.

        :opened: a date; default is None.
        :closed: a date; default is None.
        """
        if 'opened' in args:
            kwargs['opened'] = utils.to_date(kwargs['opened'])
        if 'closed' in args:
            kwargs['closed'] = utils.to_date(kwargs['closed'])
        return self._collect('filter_items', args, kwargs)

    def get_plans(self, *args, **kwargs):
        """ Returns a list of :class:`Plan` objects for given date.

        :date: if not specified, current date is used.
        """
        return self._collect('get_plans', args, kwargs)

    def get_document_list(self, *args, **kwargs):
        """ Returns a list of documents under given category.
        """
        return self._collect('get_document_list', args, kwargs)

    def get_document(self, *args, **kwargs):
        """ Returns document with given slug under given category.
        """
        return self._get_first('get_document', args, kwargs)
