# -*- coding: utf-8 -*-
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from collections import namedtuple


Part = namedtuple('Part', 'value name')


def render_delta(dt1, dt2, stack_depth=2):
    delta = relativedelta(dt2, dt1)

    stack = []

    if delta.years:
        stack.append(Part(delta.years, 'years'))

    if delta.months:
        stack.append(Part(delta.months, 'months'))

    if delta.days:
        stack.append(Part(delta.days, 'days'))

    if delta.hours:
        stack.append(Part(delta.hours, 'hours'))

    if delta.minutes:
        stack.append(Part(delta.minutes, 'minutes'))

    parts = stack[:stack_depth]
    if parts:
        return ' '.join('{0.value} {0.name}'.format(p) for p in parts)
    else:
        return u'just now'
