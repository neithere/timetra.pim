# coding: utf-8
import datetime

from prettytable import PrettyTable

import finder
import formatting
import utils


def waiting():
    """ Displays open delegated actions.
    """
    table = PrettyTable()
    table.field_names = ['context', 'contact', 'action', 'pending duration']
    table.align = 'l'
    items = finder.get_concerns()
    for item in items:
        if item.closed or item.frozen:
            continue
        for plan in item.plan:
            if plan.delegated and not plan.closed:
                delta = utils.formatdelta.render_delta(
                    plan.opened,
                    plan.closed or datetime.datetime.utcnow())
                table.add_row([item.risk or item.need, plan.delegated, plan.action, delta])
    return table


def addressed(days=7):
    """ Displays problems addressed last week.
    """
    min_date = (datetime.datetime.now() - datetime.timedelta(days=days)).replace(hour=0, minute=0, second=0)

    table = PrettyTable()
    table.field_names = ['context', 'subject', 'c:new', 'c:clsd', 'p:new', 'p:clsd']
    table.align = 'l'
    table.align['c:new'] = 'r'
    table.align['p:new'] = 'r'

    MARK_NEED_OPEN   = '▵'
    MARK_NEED_CLOSED = '▴'
    MARK_PLAN_OPEN   = '▫'
    MARK_PLAN_CLOSED = '▪'

    def _collect():
        for c in concerns:
            c._is_new = False
            c._is_newly_closed = False
            c._new_todo = 0
            c._new_done = 0
            if c.opened and min_date <= utils.to_datetime(c.opened):
                c._is_new = True
            if c.closed and min_date <= utils.to_datetime(c.closed):
                c._is_newly_closed = True
            for p in c.plan:
                if p.opened and min_date <= utils.to_datetime(p.opened):
                    c._new_todo += 1
                if p.closed and min_date <= utils.to_datetime(p.closed):
                    c._new_done += 1
            if c._is_new or c._is_newly_closed or c._new_todo or c._new_done:
                yield c

    concerns = finder.get_concerns(include_closed=True)

    for c in sorted(_collect(), key=lambda x: utils.to_datetime(x.opened) if x.opened else datetime.datetime(1900,1,1)):
        table.add_row([
            c.context,
            formatting.textwrap.fill(c.risk or c.need, width=60),
            MARK_NEED_OPEN if c._is_new else '',
            MARK_NEED_CLOSED if c._is_newly_closed else '',
            (MARK_PLAN_OPEN*c._new_todo),
            (MARK_PLAN_CLOSED*c._new_done),
        ])

    return table


def solved(days=7):
    """ Displays problems solved last week.
    """
    min_date = (datetime.datetime.now() - datetime.timedelta(days=days)).replace(hour=0, minute=0, second=0)

    table = PrettyTable()
    table.field_names = ['date', 'subject', 'solved', 'actions', 'context']
    table.align = 'l'

    def _collect():
        for c in concerns:
            if c.closed and min_date <= utils.to_datetime(c.closed):
                yield c

    concerns = finder.get_concerns(include_closed=True)

    for c in sorted(_collect(), key=lambda x: utils.to_datetime(x.closed) if x.closed else datetime.datetime.now()):
        action_cnt = len([1 for p in c.plan if p.closed and min_date <= utils.to_datetime(p.closed)])
        table.add_row([
            utils.to_date(c.closed),
            formatting.textwrap.fill(c.risk or c.need, width=60),
            c.solved,
            ('+'*action_cnt),
            c.context
        ])

    return table


def done(days=7):
    """ Displays actions done last week.
    """
    min_date = (datetime.datetime.now() - datetime.timedelta(days=days)).replace(hour=0, minute=0, second=0)

    table = PrettyTable()
    table.field_names = ['date', 'action', 'status', 'context']
    table.align = 'l'

    def _collect():
        for c in concerns:
            for p in c.plan:
                if not p.delegated and p.closed and min_date <= utils.to_datetime(p.closed):
                    p.context = c.context
                    yield p

    concerns = finder.get_concerns(include_closed=True)

    for c in sorted(_collect(), key=lambda x: utils.to_datetime(x.closed) if x.closed else datetime.datetime.now()):
        table.add_row([
            utils.to_date(c.closed),
            formatting.textwrap.fill(c.action.strip()),
            c.status,
            c.context])

    return table


commands = [
    waiting,
    addressed,
    solved,
    done,
]
