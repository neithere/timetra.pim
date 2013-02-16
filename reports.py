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
    table.field_names = ['context', 'subject', 'new', 'solved', 'todo', 'done']
    table.align = 'l'

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
                if c.closed and min_date <= utils.to_datetime(c.closed):
                    c._new_done += 1
            if c._is_new or c._is_newly_closed or c._new_todo or c._new_done:
                yield c

    concerns = finder.get_concerns(include_closed=True)

    for c in sorted(_collect(), key=lambda x:x.opened):
        table.add_row([
            c.context,
            c.risk or c.need,
            '+' if c._is_new else '',
            'x' if c._is_newly_closed else '',
            ('+'*c._new_todo),
            ('x'*c._new_done),
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
            if c.closed and min_date <= c.closed:
                yield c

    concerns = finder.get_concerns(include_closed=True)

    for c in sorted(_collect(), key=lambda x:x.closed):
        action_cnt = len([1 for p in c.plan if p.closed and min_date <= p.closed])
        table.add_row([
            c.closed.date(),
            c.risk or c.need,
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
                if not p.delegated and p.closed and min_date <= p.closed:
                    p.context = c.context
                    yield p

    concerns = finder.get_concerns(include_closed=True)

    for c in sorted(_collect(), key=lambda x:x.closed):
        table.add_row([
            c.closed.date(),
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
