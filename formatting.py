# -*- coding: utf-8 -*-
import textwrap
from blessings import Terminal

t = Terminal()


def format_error(err):
    return t.red(unicode(m))


def format_struct(data):
    for k in sorted(data):
        v = data[k]
        if isinstance(v, dict):
            yield _wrap_pair(k, '')
            for kk in sorted(v):
                yield _wrap_pair(kk, v[kk], indent='    ')
        elif isinstance(v, list) and v: #and len(v) > 1:
            yield _wrap_pair(k, v[0])
            for x in v[1:]:
                yield _wrap_pair('', x, indent='    ')
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
