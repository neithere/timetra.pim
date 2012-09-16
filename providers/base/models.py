# -*- coding: utf-8 -*-
import datetime
from monk import modeling

from . import utils   # for Item.sorted_plans


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
    STATUS_DONE = u'done'
    STATUS_CANCELLED = u'cancelled'

    structure = dict(
        action = unicode,
        status = STATUS_TODO,
        repeat = unicode,
        effort = unicode,
        context = [unicode],
        srcmeta = dict,
        delegated = unicode,
        log = [Log.structure],
        opened = datetime.datetime,
        closed = datetime.datetime,
        result = unicode,  # комментарий о результате выполнения действия: грабли, особенности, ...
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        if 'context' in data:
            data['context'] = _unfold_to_list(data['context'])

        super(Plan, self).__init__(**data)


class Item(Model):
    """ An item containing observation, problem definition, goal and plan.
    """
    structure = dict(
        note = unicode,
        risk = unicode,
        need = unicode,
        haze = unicode,  # неясность; вопросы, требующие прояснения. mess, uncertainty
        plan = [Plan.structure],
        date = datetime.date,
        cost = dict(
            amount = float,
            currency = unicode,
        ),
        stakeholders = [unicode],
        project = unicode,
        acute = False,
        opened = datetime.datetime,
        closed = datetime.datetime,
        solved = False,
        frozen = datetime.datetime,  # if not None, it's someday/maybe
        # TODO:
        # * проблема/потребность со временем: не меняется / усугубляется / ослабевает
        log = [Log.structure]
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        # разворачиваем строку или словарь в список словарей
        data['plan'] = _unfold_list_of_dicts(data.get('plan'), 'action')

        # заворачиваем строку в список
        data['plan'] = [Plan(**x) for x in data['plan']]

        super(Item, self).__init__(**data)

    def _check_has_plan(self, status):
        status_list = (status,) if isinstance(status, unicode) else status
        if not self.plan:
            return False
        for plan in self.plan:
            if plan.status in status_list:
                return True
        return False

    def has_next_action(self):
        return self._check_has_plan((Plan.STATUS_TODO, Plan.STATUS_WAITING))

    def has_completed_action(self):
        return self._check_has_plan(Plan.STATUS_DONE)

    def is_waiting(self):
        if self.plan:
            if any(x.delegated for x in self.plan if not x.closed):
                return True
        return self._check_has_plan(Plan.STATUS_WAITING)

    def sorted_plans(self):
        if not self.plan:
            return []
        return sorted(self.plan, key=lambda x: utils.to_datetime(x.closed or
                                               datetime.datetime.now()))

    @property
    def completed_percentage(self):
        if not self.plan:
            return 0
        total_cnt = len([x for x in self.plan])
        if not total_cnt:
            return 0
        closed_cnt = len([x for x in self.plan if x.closed])
        return (float(closed_cnt) / total_cnt) * 100


class Document(Model):
    """ An item with slug, title and body.
    """
    structure = dict(
        title = unicode,
        slug = unicode,
        body = unicode,
        categories = [unicode],
    )
