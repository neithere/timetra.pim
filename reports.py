# coding: utf-8
import datetime

from prettytable import PrettyTable

import finder
import formatting
import utils


def prepend(char, text):
    return u'{0} {1}'.format(char, text)


def indent(text):
    return prepend(text, ' ')


def concerns(warm=False, acute=False, listing=False, fullnames=False):
    """ Displays a list of active risks and needs.
    """
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
        if warm and item.frozen:
            continue
        text = item.risk or item.need
#        if item.acute:
#            text = formatting.t.bold(text)
#        if item.risk:
#            text = formatting.t.red(text)
        #if item.project:
        #    project_label = formatting.t.blue(item.project)
        #    text = prepend(project_label, text)

        def crop(string, width=40):
            if len(string) > width*2:
                string = u'{0}…'.format(string[:width*2-1])
            return formatting.textwrap.fill(string, width=width)

        if listing:
            ctx = formatting.t.blue(item.context)
            text = prepend(ctx, text)

            crop = lambda x: x

        text = crop(text, width=COLUMN_WIDTH_NEED)

        # FIXME based on a HACK in finder.collect_concerns
        plans_cnt = len(item.plan)
        plans_open_cnt = len([1 for p in item.plan if not p.closed])
        MARK_PLAN_OPEN   = u'▫'
        MARK_PLAN_CLOSED = u'▪'
        plans_repr = u'{0}{1}'.format(MARK_PLAN_CLOSED * (plans_cnt - plans_open_cnt),
                                      MARK_PLAN_OPEN * plans_open_cnt)

        next_action = None
        for plan in item.plan:
            if not plan.closed:
                if plan.delegated:
                    _text = u'@{0}: {1}'.format(plan.delegated, plan.action)
                else:
                    _text = plan.action
                next_action = crop(_text, width=COLUMN_WIDTH_PLAN)
                break

        if listing:
            yield prepend('*', text)
            yield prepend('    [ ]', next_action)
        else:
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


def plans(need_mask):  #, plan_mask=None):
    """ Displays plans for the need that matches given mask.
    """
    items = finder.get_concerns()
    mask = need_mask.decode('utf-8').lower()
    for item in items:
        risk_matches = item.risk and mask in item.risk.lower()
        need_matches = item.need and mask in item.need.lower()

        if risk_matches or need_matches:
            yield item.context
            for line in formatting.format_concern(item):
                yield line
            yield ''


def waiting():
    """ Displays open delegated actions.
    """
    table = PrettyTable()
    table.field_names = ['pending duration', 'contact', 'action', 'concern']
    table.align = 'l'
    items = finder.get_concerns()
    plans = []
    for item in items:
        if item.closed or item.frozen:
            continue
        for plan in item.plan:
            if plan.delegated and not plan.closed:
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


commands = [
    concerns,
    plans,
    waiting,
    addressed,
    solved,
    done,
]
