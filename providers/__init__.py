# -*- coding: utf-8 -*-
import datetime
from monk import modeling


__all__ = ['Item']


def _unfold_list_of_dicts(value, default_key):
    """
    [{...}] → [{...}]
     {...}  → [{...}]
    u'xyz'  → [{default_key: u'xyz'}]
    """
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, unicode):
        return [{default_key: value}]
    if isinstance(value, list):
        if not all(isinstance(x, dict) for x in value):
            def _fix(x):
                return {default_key: x} if isinstance(x, unicode) else x
            return [_fix(x) for x in value]
    return value


def _unfold_to_list(value):
    if value and not isinstance(value, list):
        return [value]
    else:
        return value


class Model(modeling.TypedDictReprMixin,
            modeling.DotExpandedDictMixin,
            modeling.StructuredDictMixin,
            dict):

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        self._insert_defaults()
        self._make_dot_expanded()


class Log(Model):
    """ A log record.

    The :attr:`data` dictionary contains newly set values of the parent object.
    """
    structure = dict(
        time = datetime.datetime,
        note = unicode,
        data = dict,
    )


class Plan(Model):
    """ A planned activity.
    """
    STATUS_TODO = u'todo'
    STATUS_WAITING = u'waiting'

    structure = dict(
        action = unicode,
        status = STATUS_TODO,
        repeat = unicode,
        effort = unicode,
        context = [unicode],
        srcmeta = dict,
        log = [Log.structure]
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        if 'context' in data:
            data['context'] = _unfold_to_list(data['context'])

        super(Plan, self).__init__(**data)


class Item(Model):
    """ An item containing observation, problem definition, goal and plan.
    """
    MODE_OPEN = u'open'

    structure = dict(
        note = unicode,
        risk = unicode,
        need = unicode,
        haze = unicode,  # неясность; вопросы, требующие прояснения. mess, uncertainty
        plan = [Plan.structure],
        mode = MODE_OPEN,
        date = datetime.date,
        cost = dict(
            amount = float,
            currency = unicode,
        ),
        stakeholders = [unicode],
        important = False,
        opened = datetime.datetime,
        closed = datetime.datetime,
        log = [Log.structure]
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        # разворачиваем строку или словарь в список словарей
        data['plan'] = _unfold_list_of_dicts(data.get('plan'), 'action')

        # заворачиваем строку в список
        data['plan'] = [Plan(**x) for x in data['plan']]

        super(Item, self).__init__(**data)

    def has_next_action(self):
        if not self.plan:
            return False
        for plan in self.plan:
            if plan.status in (Plan.STATUS_TODO, Plan.STATUS_WAITING):
                return True
        return False


class Document(Model):
    """ An item with slug, title and body.
    """
    structure = dict(
        title = unicode,
        slug = unicode,
        body = unicode,
    )


class BaseDataProvider(object):
    """ All data providers should implement this interface.
    """
    def get_items(self, date=None):
        """ Returns a list of :class:`Item` objects for given date.

        :date: if not specified, current date is used.
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
        for provider in self.providers:
            try:
                meth = getattr(provider, meth_name)
                value = meth(*args, **kwargs)
            except NotImplementedError:
                pass
            else:
                if value:
                    return value

    def get_items(self, *args, **kwargs):
        """ Returns a list of :class:`Item` objects for given date.

        :date: if not specified, current date is used.
        """
        return self._collect('get_items', args, kwargs)

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
