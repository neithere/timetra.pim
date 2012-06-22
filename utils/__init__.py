# -*- coding: utf-8 -*-
from datetime import date, datetime, time


def to_date(obj):
    if isinstance(obj, datetime):
        return obj.date()
    if isinstance(obj, date):
        return obj
    raise TypeError('expected date or datetime, got {0}'.format(obj))


def to_datetime(obj):
    print 'to_datetime', obj
    if isinstance(obj, datetime):
        return obj
    if isinstance(obj, date):
        return datetime.combine(obj, time(0))
    raise TypeError('expected date or datetime, got {0}'.format(obj))



