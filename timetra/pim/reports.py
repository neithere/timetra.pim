# coding: utf-8
#
#    Timetra is a time tracking application and library.
#    Copyright © 2010-2014  Andrey Mikhaylenko
#
#    This file is part of Timetra.
#
#    Timetra is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Timetra is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with Timetra.  If not, see <http://gnu.org/licenses/>.
#

import datetime

import argh
from prettytable import PrettyTable

from . import finder
from . import formatting
from . import utils


def _ucfirst(string):
    if not string:
        return string    # None or empty string
    return string[0].upper() + string[1:]


def _crop(string, width=40):
    if len(string) > width * 2:
        string = u'{0}…'.format(string[:width * 2 - 1])
    return formatting.textwrap.fill(string, width=width)


def _get_plans_repr(concern):
    # FIXME based on a HACK in finder.collect_concerns
    plans_cnt = len(concern.plan)
    plans_open_cnt = len([1 for p in concern.plan if not p.closed])
    MARK_PLAN_OPEN   = u'▫'
    MARK_PLAN_CLOSED = u'▪'
    return u'{0}{1}'.format(MARK_PLAN_CLOSED * (plans_cnt - plans_open_cnt),
                            MARK_PLAN_OPEN * plans_open_cnt)


def prepend(char, text):
    return u'{0} {1}'.format(char, text)


def indent(text):
    return prepend(text, ' ')


def concerns(frozen_only=False, warm_only=False, acute=False, listing=False,
             fullnames=False, calendar_included=False):
    """ Displays a list of active risks and needs.
    """
    if frozen_only and warm_only:
        raise RuntimeError('cannot combine --frozen-only and --warm-only')

    table = PrettyTable()

    table.field_names = ['context', 'subject', 'plans', 'next action']

    table.align['context'] = 'l'
    table.align['subject'] = 'l'
    table.align['plans'] = 'r'
    table.align['next action'] = 'l'

    COLUMN_WIDTH_NEED = 45
    COLUMN_WIDTH_PLAN = 60

    items = finder.get_concerns()
    for item in items:
        if acute and not item.acute:
            continue
        if frozen_only and not item.is_frozen():
            continue
        if warm_only and item.is_frozen():
            continue
        text = _ucfirst(item.risk or item.need)
#        if item.acute:
#            text = formatting.t.bold(text)
#        if item.risk:
#            text = formatting.t.red(text)
        #if item.project:
        #    project_label = formatting.t.blue(item.project)
        #    text = prepend(project_label, text)

        if listing:
            ctx = formatting.t.blue(item.context)
            text = prepend(ctx, text)
        else:
            text = _crop(text, width=COLUMN_WIDTH_NEED)

        plans_repr = _get_plans_repr(item)

        next_action = None
        for plan in item.plan:
            if not plan.closed:
                _text = plan.action

                if plan.delegated:
                    _text = u'@{0}: {1}'.format(plan.delegated, _ucfirst(_text))
                else:
                    _text = _ucfirst(_text)

                if plan.time:
                    if plan.time.date == datetime.date.today():
                        _text = u'due TODAY: {0}'.format(_text)
                    else:
                        if calendar_included:
                            _text = u'due {0}: {1}'.format(plan.time.strftime('%Y-%m-%d %H:%M UTC'), _text)
                        else:
                            continue

                if listing:
                    next_action = _text
                else:
                    next_action = _crop(_text, width=COLUMN_WIDTH_PLAN)

                break

        if listing:
            yield prepend('*', text)
            yield prepend('    [ ]', next_action)
        else:
            # based on HACK in finder
            context = item.context_card.name if fullnames else item.context

            table.add_row([context or '-', text, plans_repr,
                           next_action or '—'])

        #if item.plan:
        #    if not item.has_next_action():
        #        yield indent(u'запланировать')
        #    if not item.has_completed_action():
        #        yield indent(u'приступить')
        #    if item.is_waiting():
        #        yield indent(u'напомнить')
        #else:
        #    yield indent(u'запланировать')

    if not listing:
        yield table


def someday(fullnames=False):
    """ Displays a list of frozen concerns.
    """
    # NOTE: this is based on concerns() and probably awaits refactoring

    table = PrettyTable()
    table.field_names = ['context', 'subject', 'plans', 'revive']
    table.align = 'l'

    COLUMN_WIDTH_CONCERN = 80

    concerns = finder.get_concerns()
    for concern in concerns:
        if concern.closed or not concern.is_frozen():
            continue

        text = concern.risk or concern.need
        text = _crop(text, width=COLUMN_WIDTH_CONCERN)

        plans_repr = _get_plans_repr(concern)

        # based on HACK in finder
        context = concern.context_card.name if fullnames else concern.context

        table.add_row([context or '-', text, plans_repr, concern.revive or '—'])

    return table


@argh.arg('-C', '--exclude-context')
def plans(need_mask=None, plan_mask=None, context=None, exclude_context=None,
          fullnames=False, active_only=False, full=False):
    """ Displays plans for the need that matches given mask.
    """
    contexts = context.split(',') if context else []
    exclude_contexts = exclude_context.split(',') if exclude_context else []
    items = finder.get_concerns()
    need_mask = need_mask.decode('utf-8').lower() if need_mask else u''
    plan_mask = plan_mask.decode('utf-8').lower() if plan_mask else u''
    for item in items:
        if need_mask:
            risk_matches = item.risk and need_mask in item.risk.lower()
            need_matches = item.need and need_mask in item.need.lower()
            if not risk_matches and not need_matches:
                continue

        if active_only and (item.closed or item.is_frozen()):
            continue

        # FIXME problem: this should only show plans for given context but it
        # displays the whole concern with all plans because of the way
        # formatting is done below

        if plan_mask:
            # match → take
            matched = False
            for plan in item.plan:
                if plan_mask in plan.action:
                    matched = True
                    break
            if not matched:
                continue

        if contexts:
            # match → take
            matched = False
            for plan in item.plan:
                if plan.context and any(c in plan.context for c in contexts):
                    matched = True
                    break
            if not matched:
                continue

        if exclude_contexts:
            # match → skip
            matched = False
            for plan in item.plan:
                if plan.context and any(c in plan.context for c in exclude_contexts):
                    matched = True
                    break
            if matched:
                continue

        if fullnames:
            yield item.context_card.name
        else:
            yield item.context

        # TODO: show only matching plans for concern
        for line in formatting.format_concern(item, full=full):
            yield line
        yield ''


def waiting(contact=None):
    """ Displays open delegated actions.
    """
    table = PrettyTable()
    table.field_names = ['pending duration', 'contact', 'action', 'concern']
    table.align = 'l'
    items = finder.get_concerns()
    plans = []
    for item in items:
        if item.closed or item.is_frozen():
            continue
        for plan in item.plan:
            if plan.delegated and not plan.closed:
                if contact and contact != plan.delegated:
                    continue
                plans.append((item, plan))
    for item, plan in sorted(plans, key=lambda pair: pair[1].opened):
        delta = utils.formatdelta.render_delta(
            plan.opened,
            plan.closed or datetime.datetime.utcnow())
        table.add_row([delta, plan.delegated, plan.action, item.risk or item.need])
    return table


def addressed(days=7, fullnames=False):
    """ Displays problems addressed last week.
    """
    min_date = (datetime.datetime.now() - datetime.timedelta(days=days)).replace(hour=0, minute=0, second=0)

    table = PrettyTable()
    table.field_names = ['context', 'subject', 'concern', 'p:new', 'p:clsd']
    table.align = 'l'
    table.align['c:new'] = 'r'
    table.align['p:new'] = 'r'

    MARK_CONCERN_OPEN   = '○'
    MARK_CONCERN_CLOSED = '●'
    MARK_CONCERN_OPEN_THEN_CLOSED = '◉'
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
        marks = {
            (True, True):  MARK_CONCERN_OPEN_THEN_CLOSED,
            (True, False): MARK_CONCERN_OPEN,
            (False, True): MARK_CONCERN_CLOSED,
            (False, False): '',
        }
        mark = marks[(c._is_new, c._is_newly_closed)]

        table.add_row([
            c.context_card.name if fullnames else c.context,
            formatting.textwrap.fill(c.risk or c.need, width=60),
            mark,
            (MARK_PLAN_OPEN*c._new_todo),
            (MARK_PLAN_CLOSED*c._new_done),
        ])

    return table


def solved(days=7, fullnames=False):
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
            c.context_card.name if fullnames else c.context
        ])

    return table


def done(days=7, fullnames=False):
    """ Displays actions done last week.
    """
    min_date = (datetime.datetime.now() - datetime.timedelta(days=days)).replace(hour=0, minute=0, second=0)

    table = PrettyTable()
    table.field_names = ['date', 'action', 'status', 'context']
    table.align = 'l'

    concerns = finder.get_concerns(include_closed=True)

    def _collect():
        for c in concerns:
            for p in c.plan:
                if not p.delegated and p.closed and min_date <= utils.to_datetime(p.closed):
                    p.context = c.context_card.name if fullnames else c.context
                    yield p

    for c in sorted(_collect(), key=lambda x: utils.to_datetime(x.closed) if x.closed else datetime.datetime.now()):
        table.add_row([
            utils.to_date(c.closed),
            formatting.textwrap.fill(c.action.strip()),
            c.status,
            c.context])

    return table


def events(no_upcoming=False, no_overdue=False, fullnames=False, full=False):
    """ Displays plans with a fixed date/time.
    """
    now = datetime.datetime.utcnow()

    table = PrettyTable()
    table.field_names = ['type', 'delta', 'action', 'concern', 'context']
    table.align = 'l'

    concerns = finder.get_concerns()
    for concern in concerns:
        for plan in concern.plan:

            if plan.closed:
                continue

            if not plan.time:
                continue

            if no_overdue and plan.time < now:
                continue

            if no_upcoming and now < plan.time:
                continue

            kind = 'overdue' if plan.time < now else 'future'
            table.add_row([kind, utils.formatdelta.render_delta(plan.time),
                           _crop(plan.action),
                           concern.risk or concern.need,
                           concern.context])

    if table._rows:
        return table


def upcoming():
    "Displays plans with a fixed future date/time."
    return events(no_overdue=True)


def overdue():
    "Displays plans with a fixed past date/time."
    return events(no_upcoming=True)


commands = [
    concerns,
    someday,
    plans,
    waiting,
    addressed,
    solved,
    done,

    events,
    upcoming,
    overdue
]
