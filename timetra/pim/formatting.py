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

import os
import textwrap

from blessings import Terminal

from . import compat
from .settings import get_app_conf
from .utils.formatdelta import render_delta


if compat.PY3:
    unicode = str


POSSIBLY_TOO_LONG_FIELDS = ['concerns', 'note']


t = Terminal()


def format_error(err):
    return t.red(u'{0.__class__.__name__}: {0}'.format(err))


def format_struct(data, skip=[]):
    for k in sorted(data):
        if k in skip:
            continue
        v = data[k]
        if isinstance(v, dict):
            yield _wrap_pair(k, None)
            for kk in sorted(v):
                yield _wrap_pair(kk, v[kk], indent='  ')
        elif isinstance(v, list) and v: #and len(v) > 1:
            yield _wrap_pair(k, v[0])
            for x in v[1:]:
                yield _wrap_pair(' '*len(k), x, indent='')
        else:
            if not v:
                continue
            yield _wrap_pair(k, v)


def _wrap_pair(k, v, indent=''):
    if v is None:
        return t.yellow(u'{indent}{k} ↴'.format(indent=indent, k=k))
    else:
        prefix = t.yellow(u'{indent}{k}:'.format(indent=indent, k=k))
        subsequent_indent = indent + ' '*len(k) + '  '
        #                                         ^^^^ for the ": " part
        value = unicode(_safe_wrap(v, subsequent_indent=subsequent_indent))
        return u'{prefix} {value}'.format(prefix=prefix, value=value)


def _safe_wrap(value, indent='', subsequent_indent=''):
    "Wraps text unless it's an URL"

    value = unicode(value)

    if value.startswith('http://'):
        return u'{indent}{value}'.format(indent=indent, value=value)

    # for reference:
    # >>> import textwrap
    # >>> help(textwrap.TextWrapper)
    return textwrap.fill(value,
                         initial_indent=indent,
                         subsequent_indent=subsequent_indent,
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


def format_card(label, card, model, hide_long_fields=True, full=False):
    skip = POSSIBLY_TOO_LONG_FIELDS if hide_long_fields else []
    for line in format_struct(card, skip=skip):
        yield line
    yield ''

    # XXX HACK
    concerns = card.get('concerns')
    if concerns:
        yield ''
        for concern in concerns:
            for line in format_concern(concern, full=full):
                yield line
            yield ''


STATE_OPEN = ' '
STATE_SOLVED = '+'
STATE_ACUTE = '!'
STATE_FROZEN = '*'
STATE_CANCELLED = '-'

colors = {
    STATE_OPEN: t.yellow,
    STATE_SOLVED: t.green,
    STATE_ACUTE: t.red,
    STATE_FROZEN: t.blue,
    STATE_CANCELLED: t.blue,
}

def format_concern(concern, full=False):
    name = concern.risk or concern.need or concern.note

    if concern.closed:
        state = STATE_SOLVED
    elif concern.is_frozen():
        state = STATE_FROZEN
    elif concern.acute:
        state = STATE_ACUTE
    else:
        state = STATE_OPEN

    wrapper = colors[state]
    yield wrapper(u'    [{0}] {1}'.format(state, t.bold(name)))

    if concern.closed or concern.is_frozen():
        return

    if concern.reqs:
        for req in concern.reqs:
            yield wrapper(u'    ---> сначала: {0}'.format(req))
    if concern.get('refers'):
        for i, category in enumerate(concern.refers):
            yield wrapper(u'        re {category}: {items}'.format(
                category = category,
                items = ', '.join(concern.refers[category])))
    for plan in concern.plan:
        yield format_plan(plan, indent=8*' ', concern_state=state, full=full)


def format_plan(plan, concern_state=' ', indent='', full=False):
    # the logic here should be more complex, involving status field
    # concern itself also may not have "closed" but solved=True
    # here we just make sure 80% of cases work fine
    if plan.closed:
        if plan.status == 'cancelled':
            state = STATE_CANCELLED
        else:
            state = STATE_SOLVED
    else:
        state = STATE_OPEN

    wrapper = colors[STATE_SOLVED if concern_state == STATE_SOLVED else state]
    #pwrapper = formatting.t.green if pstate == 'x' else formatting.t.yellow
    name = plan.action or '?'
    if not full and '\n' in name:
        name = name.strip().partition('\n')[0] + u' [...]'
    name = '\n'.join(textwrap.wrap(
        name, initial_indent='', subsequent_indent=indent+'    '))

    if plan.get('delegated'):
        waiting = render_delta(plan.opened, plan.closed)
        name = u'@{0}: {1} (ожидание {2})'.format(plan.delegated, name, waiting)

    if full:
        if plan.get('time'):
            name = u'{0}\n{1}    {2} UTC ({3})'.format(name, indent, plan.time,
                                                       render_delta(plan.time))

        if plan.get('reqs'):
            name = u'{0}\n{1}    ! иметь: {2}'.format(name, indent, ', '.join(plan.reqs))

        if plan.get('context'):
            name = u'{0}\n{1}    when&where: {2}'.format(name, indent, ', '.join(plan.context))

        if plan.get('refers'):
            refers = []
            for i, category in enumerate(plan.refers):
                refers.append(wrapper(u're {category}: {items}'.format(
                    category = category,
                    items = ', '.join(plan.refers[category]))))
            lines = (u'{0}    {1}'.format(indent, x) for x in refers)
            name = u'{0}\n{1}'.format(name, '\n'.join(lines))

        if plan.get('result'):

            result = plan.result
            if '\n' in result:
                lines = (u'{0}      {1}'.format(indent, line)
                        for line in result.split('\n') )#if line)
                result = '\n' + '\n'.join(lines)
            name = u'{0}\n{1}    result: {2}'.format(name, indent, result)

    if not full and plan.get('result'):
        name = u'{0} [→ …]'.format(name)

    return wrapper(u'{0}[{1}] {2}'.format(indent, state, name))
