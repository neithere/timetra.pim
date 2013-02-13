# -*- coding: utf-8 -*-
import datetime
import os
import textwrap

from blessings import Terminal

from settings import get_app_conf
import utils.formatdelta


t = Terminal()


def format_error(err):
    return t.red(u'{0.__class__.__name__}: {0}'.format(err))


def format_struct(data, skip=[]):
    for k in sorted(data):
        if k in skip:
            continue
        v = data[k]
        if isinstance(v, dict):
            yield _wrap_pair(k, '')
            for kk in sorted(v):
                yield _wrap_pair(kk, v[kk], indent='    ')
        elif isinstance(v, list) and v: #and len(v) > 1:
            yield _wrap_pair(k, v[0])
            for x in v[1:]:
                yield _wrap_pair('', x, indent=' '*len(k))
        else:
            yield _wrap_pair(k, v)


def _wrap_pair(k, v, indent=''):
    v = t.yellow(unicode(v))
    # for reference:
    # >>> import textwrap
    # >>> help(textwrap.TextWrapper)
    return textwrap.fill(u'{k}: {v}'.format(k=k, v=v),
                         initial_indent='    '+indent,
                         subsequent_indent='          '+indent,
                         break_long_words=False,
                         fix_sentence_endings=True)


def format_slug(root_dir, file_path, nocolour=False):
    conf = get_app_conf()
    index_path = os.path.join(conf.index, root_dir)
    # display relative path without extension and with bold slug
    directory, file_name = os.path.split(file_path)
    slug, _ = os.path.splitext(file_name)
    if not directory or directory == index_path:
        path_repr = ''
    else:
        path_repr = os.path.relpath(directory, index_path)
    colour = (lambda x:x) if nocolour else t.bold
    return os.path.join(path_repr, colour(slug))


def format_card(label, card, model):
    for line in format_struct(card, skip=['concerns', 'note']):
        yield line
    yield ''

    # XXX HACK
    concerns = card.get('concerns')
    if concerns:
        yield ''
        for concern in concerns:
            for line in format_concern(concern):
                yield line
            yield ''


colors = {
    ' ': t.yellow,
    '+': t.green,
    '!': t.red,
    '*': t.blue,
}

def format_concern(concern):
    name = concern.risk or concern.need or concern.note

    if concern.closed:
        state = '+'
    elif concern.frozen:
        state = '*'
    elif concern.acute:
        state = '!'
    else:
        state = ' '

    wrapper = colors[state]
    yield wrapper(u'    [{0}] {1}'.format(state, t.bold(name)))
    if concern.reqs:
        for req in concern.reqs:
            yield wrapper(u'    ---> сначала: {0}'.format(req))
    for plan in concern.plan:
        yield format_plan(plan, indent=8*' ')


def format_plan(plan, concern_state=' ', indent=''):
    # the logic here should be more complex, involving status field
    # concern itself also may not have "closed" but solved=True
    # here we just make sure 80% of cases work fine
    state = '+' if plan.closed else ' '
    wrapper = colors['+' if state == '+' else concern_state]
    #pwrapper = formatting.t.green if pstate == 'x' else formatting.t.yellow
    name = plan.action or '?'
    if '\n' in name:
        name = name.strip().partition('\n')[0] + u' [...]'
    name = '\n'.join(textwrap.wrap(
        name, initial_indent='', subsequent_indent=indent+'    '))
    if plan.get('delegated'):
        waiting = utils.formatdelta.render_delta(
            plan['opened'],
            plan['closed'] or datetime.datetime.utcnow())
        name = u'@{0}: {1} (ожидание {2})'.format(plan['delegated'], name, waiting)
    return wrapper(u'{0}[{1}] {2}'.format(indent, state, name))
