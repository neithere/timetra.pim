# -*- coding: utf-8 -*-
import os
import textwrap

from blessings import Terminal

from settings import get_app_conf


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
            name = concern.risk or concern.need or concern.note

            if concern.closed:
                state = '+'
            elif concern.frozen:
                state = '*'
            elif concern.acute:
                state = '!'
            else:
                state = ' '

            colors = {
                ' ': t.yellow,
                '+': t.green,
                '!': t.red,
                '*': t.blue,
            }
            wrapper = colors[state]
            yield wrapper(u'    [{0}] {1}'.format(state, t.bold(name)))
            for plan in concern.plan:
                # the logic here should be more complex, involving status field
                # concern itself also may not have "closed" but solved=True
                # here we just make sure 80% of cases work fine
                pstate = '+' if plan.closed else ' '
                pwrapper = colors['+' if pstate == '+' else state]
                #pwrapper = formatting.t.green if pstate == 'x' else formatting.t.yellow
                pname = plan.action or '?'
                if '\n' in pname:
                    pname = pname.strip().partition('\n')[0] + u' [...]'
                pname = '\n'.join(textwrap.wrap(
                    pname, initial_indent='', subsequent_indent=12*' '))
                if plan.get('delegated'):
                    pname = u'@{0}: {1}'.format(plan['delegated'], pname)
                yield pwrapper(u'        [{0}] {1}'.format(pstate, pname))
        yield ''


