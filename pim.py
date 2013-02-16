#!/usr/bin/env python2
# coding: utf-8
# PYTHON_ARGCOMPLETE_OK
import datetime
import os
import subprocess

import argh
import monk.validation
from prettytable import PrettyTable

from settings import get_app_conf, ConfigurationError
import settings
import cli
from finder import CATEGORIES
import finder
import formatting
import utils


@argh.wrap_errors([ConfigurationError], processor=formatting.format_error)
def examine():
    conf = get_app_conf()

    yield 'examining {conf.index}...'.format(conf=conf)

    files_by_ext = {}

    vcs_dirs = '/.hg', '/.git', '/.svn'
    vcs_files = '.hgignore', '.gitignore'

    for root, dirs, files in os.walk(conf.index):
        if any(x in root for x in vcs_dirs):
            continue

        if any(x in root for x in conf.x_ignore):
            continue

        for name in files:
            if name in vcs_files:
                continue

#            yield root, files
            _, ext = os.path.splitext(name)
            files_by_ext.setdefault(ext, []).append(os.path.join(root, name))

        #yaml_files = [f for f in files if f.endswith('.yaml')]

#    yield files_by_ext
    for ext, files in files_by_ext.iteritems():
        yield '{ext}: {count}'.format(ext=(ext or 'no extension'), count=len(files))
        if len(files) < 10:    # <- an arbitrary threshold for marginal formats
            for f in files:
                yield '    {0}'.format(f)


nice_errors = argh.wrap_errors(
    [monk.validation.ValidationError, TypeError, finder.PathDoesNotExist],
    processor=formatting.format_error)


@argh.arg('category', choices=list(CATEGORIES) + ['config'])
@argh.arg('pattern', nargs='?', default='')
@nice_errors
def show(category, pattern, count=False, detailed=False):
    if category == 'config':
        for line in showconfig():
            yield line
        return

    if category not in CATEGORIES:
        raise ValueError('expected category from {0}'
                         .format(', '.join(CATEGORIES)))
    model = CATEGORIES[category]['model']
    sigil = CATEGORIES[category]['sigil']
    for line in _show_items(category, model, sigil, pattern,
                            count=count, detailed=detailed):
        yield line



def _show_items(root_dir, model, sigil, pattern, count=False, detailed=False):
    assert '..' not in pattern, 'look at you, hacker!'
    assert not pattern.startswith('/'), 'look at you, hacker!'

    if pattern == '.':
        # use current directory as the pattern
        _, pattern = os.path.split(os.getcwdu())
        yield formatting.t.blue(u'from current directory: {0}'.format(pattern))

    detail, index, guessed_path = finder.find_items(root_dir, model, pattern)

    if guessed_path:
        # guessing may be confusing so we tell user what we've picked
        yield formatting.t.blue(u'guessed: {0}'.format(guessed_path))
        yield ''

    if detail:
        file_path, card_loader = detail
        try:
            card = card_loader()
            for line in formatting.format_card(file_path, card, model):
                yield line
        except Exception as e:
            raise type(e)(u'{0}: {1}'.format(file_path, e))

    for file_path, card_loader in index:
        slug = formatting.format_slug(root_dir, file_path)
        yield slug
        if detailed:
            try:
                card = card_loader()
                for line in formatting.format_card(slug, card, model):
                    yield line
            except Exception as e:
                raise type(e)(u'{0}: {1}'.format(file_path, e))

def showconfig():
    conf = get_app_conf()
    for line in formatting.format_struct(conf):
        yield line


@argh.arg('category', choices=list(CATEGORIES) + ['config'])
@argh.arg('pattern', nargs='?', default='')
@nice_errors
def edit(category, pattern):
    editor = os.getenv('EDITOR')
    assert editor, 'env variable $EDITOR must be set'

    if category == 'config':
        path = settings.get_conf_path()
    else:
        conf = get_app_conf()
        category_path = os.path.join(conf.index, category)
        path = os.path.join(category_path, pattern)
        if not os.path.exists(path):
            if os.path.exists(path + '.yaml'):
                path = path + '.yaml'
            else:
                guessed = finder.guess_file_path(category_path, pattern)
                if guessed:
                    path = guessed

    if not os.path.exists(path):
        raise finder.PathDoesNotExist(path)

    yield 'Editing {0}'.format(path)
    subprocess.Popen([editor, path]).wait()


def prepend(char, text):
    return u'{0} {1}'.format(char, text)


def indent(text):
    return prepend(text, ' ')


def concerns(warm=False, acute=False, listing=False):
    """ Displays a list of active risks and needs.
    """
    table = PrettyTable()

    table.field_names = ['context', 'subject', 'plans', 'next action']

    table.align['context'] = 'l'
    table.align['subject'] = 'l'
    table.align['plans'] = 'r'
    table.align['next action'] = 'l'

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

        text = crop(text)

        # FIXME based on a HACK in finder.collect_concerns
        plans_cnt = len(item.plan)
        plans_open_cnt = len([1 for p in item.plan if not p.closed])
        plans_repr = u'{0} ({1})'.format(plans_cnt, plans_open_cnt)

        next_action = None
        for plan in item.plan:
            if not plan.closed:
                next_action = crop(plan.action)
                break

        if listing:
            yield prepend('*', text)
            yield prepend('    [ ]', next_action)
        else:
            table.add_row([item.context or '-', text, plans_repr,
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


def report_waiting():
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


def report_addressed(days=7):
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


def report_solved(days=7):
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


def report_done(days=7):
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


if __name__ == '__main__':
    argh.dispatch_commands([
        examine,
        show,
        edit,
        # these should be nested (?):
        concerns,
        plans,
        report_waiting,
        report_addressed,
        report_solved,
        report_done,
        # these should be reorganized:
        cli.serve,
    ])
