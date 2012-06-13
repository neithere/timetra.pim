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
                context = unicode,
            )
        ],
        mode = u'open',
        date = datetime.date,
        stakeholders = [unicode],
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        data['plan'] = _unfold_list_of_dicts(data.get('plan'), 'action')

        super(Item, self).__init__(**data)
