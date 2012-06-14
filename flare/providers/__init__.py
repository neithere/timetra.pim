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
            return [{default_key: x} if isinstance(x, unicode) else x for x in value]
    return value


def _unfold_list(value):
    if value and not isinstance(value, list):
        return [value]
    else:
        return value


class Item(modeling.TypedDictReprMixin,
           modeling.DotExpandedDictMixin,
           modeling.StructuredDictMixin,
           dict):
    """ An item containing observation, problem definition, goal and plan.
    """
    structure = dict(
        note = unicode,
        risk = unicode,
        need = unicode,
        plan = [
            dict(
                action = unicode,
                status = u'todo',
                repeat = unicode,
                effort = unicode,
                context = [unicode],
                srcmeta = dict,
            )
        ],
        mode = u'open',
        date = datetime.date,
        stakeholders = [unicode],
        important = False,
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        # разворачиваем строку или словарь в список словарей
        data['plan'] = _unfold_list_of_dicts(data.get('plan'), 'action')

        # заворачиваем строку в список
        if data['plan']:
            tasks = []
            for task in data['plan']:
                if task.get('context'):
                    task['context'] = _unfold_list(task['context'])
                tasks.append(task)
            data['plan'] = tasks

        super(Item, self).__init__(**data)
