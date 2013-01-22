#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import argh
from blessings import Terminal
from monk.modeling import DotExpandedDict
from monk.validation import validate_structure, ValidationError
from monk import manipulation
import os
import subprocess
import textwrap
import yaml
import xdg.BaseDirectory

import models


APP_NAME = 'pim'


t = Terminal()


class ConfigurationError(RuntimeError):
    pass


def get_app_conf():
    filename = APP_NAME + '.yaml'
    path = os.path.join(xdg.BaseDirectory.xdg_config_home, filename)

    if not os.path.exists(path):
        raise ConfigurationError('File {0} not found'.format(path))

    defaults = {
        'index': '~/pim',
        #'configs': {},
        'x_ignore': list,   # TODO: remove this as soon as all is YAML?
        'contacts': 'contacts.yaml',
    }

    with open(path) as f:
        conf = yaml.load(f)

    conf = manipulation.merged(defaults, conf)
    try:
        validate_structure(defaults, conf)
    except ValidationError as e:
        raise ConfigurationError('Configuration: {0}'.format(e))

    expandable = ('index',)
    for k in expandable:
        conf[k] = os.path.expanduser(conf[k])

    return DotExpandedDict(conf)


def _fix_str_to_unicode(data):
    """ Converts all `str` items to `unicode` within given dict.
    Motivation: PyYAML for Python 2.x interprets ASCII-only strings as bytes.
    """
    if isinstance(data, str):
        return data.decode('utf-8')

    if isinstance(data, (list, tuple)):
        return [_fix_str_to_unicode(x) for x in data]

    if isinstance(data, dict):
        new_data = {}
        for k,v in data.items():
            new_data[k] = _fix_str_to_unicode(v)
        data = new_data

    return data


@argh.wrap_errors([ConfigurationError], processor=lambda m: t.red(unicode(m)))
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



@argh.wrap_errors([ValidationError], processor=lambda m: t.red(unicode(m)))
def contacts(count=False, *labels):
    for line in _show_items('contacts.yaml', models.CARD, '@', labels, count):
        yield line


def assets(count=False, *labels):
    for line in _show_items('assets.yaml', models.ASSET, '%', labels, count):
        yield line


def _check_label_matches(label, patterns):
    if not patterns:
        return True

    for pattern in patterns:
        if label == pattern:
            return True
        if pattern.endswith('/') and label.startswith(pattern):
            # e.g. pattern="device/" and label="device/phone/nokia"
            return True


def _show_items(file_name, model, sigil, labels, count=False):
    conf = get_app_conf()

    labels = _fix_str_to_unicode(labels)

    index_path = os.path.join(conf.index, file_name)

    with open(index_path) as f:
        cards = yaml.load(f)  #, unicode=True)

    total_cnt = 0
    for label, card in cards.iteritems():
        if not _check_label_matches(label, labels):
            continue

        if count:
            total_cnt += 1
            continue

        card = _fix_str_to_unicode(card)

        try:
            validate_structure(model, card)
        except (ValidationError, TypeError) as e:
            raise type(e)(u'{label}: {e}'.format(label=label, e=e))

        yield ''
        yield t.bold(u'{sigil}{label}'.format(sigil=sigil, label=label))
        for k,v in card.iteritems():
            if isinstance(v, dict):
                yield _wrap_pair(k, '')
                for kk, vv in v.iteritems():
                    yield _wrap_pair(kk, vv, indent='    ')
            elif isinstance(v, list) and v: #and len(v) > 1:
                yield _wrap_pair(k, v[0])
                for x in v[1:]:
                    yield _wrap_pair('', x, indent='    ')
            else:
                yield _wrap_pair(k, v)
    if count:
        yield 'Found {0} items'.format(total_cnt)

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


def showconfig():
    for k,v in get_app_conf().iteritems():
        yield u'{k}: {v}'.format(k=k, v=t.bold(unicode(v)))


if __name__ == '__main__':
    argh.dispatch_commands([
        showconfig,
        examine,
        assets,
        contacts,
    ])
