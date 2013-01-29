#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import argh
from monk.validation import validate_structure, ValidationError
import os
import subprocess
import yaml

from settings import get_app_conf, ConfigurationError
import cli
import models
import formatting


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



@argh.wrap_errors([ValidationError], processor=formatting.format_error)
def contacts(count=False, detailed=False, *labels):
    for line in _show_items('contacts.yaml', models.CARD, '@', labels,
                            count=count, detailed=detailed):
        yield line


def assets(count=False, detailed=False, *labels):
    for line in _show_items('assets.yaml', models.ASSET, '$', labels,
                            count=count, detailed=detailed):
        yield line


def projects(count=False, detailed=False, *labels):
    for line in _show_items('projects.yaml', models.ASSET, '#', labels,
                            count=count, detailed=detailed):
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


def _show_items(file_name, model, sigil, patterns, count=False, detailed=False):
    conf = get_app_conf()

    patterns = _fix_str_to_unicode(patterns)

    index_path = os.path.join(conf.index, file_name)

    with open(index_path) as f:
        cards = yaml.load(f)  #, unicode=True)

    total_cnt = 0
    for label in sorted(cards):

        if not _check_label_matches(label, patterns):
            continue

        if count:
            total_cnt += 1
            continue

        if '/' in label:
            parts = label.split('/')
            label_repr = '/'.join(parts[:-1] + [formatting.t.bold(parts[-1])] )
        else:
            label_repr = formatting.t.bold(label)
        yield u'{sigil}{label}'.format(sigil=sigil, label=label_repr)

        if detailed:
            for line in format_card(label, cards[label], model):
                yield line

    if count:
        yield 'Found {0} items'.format(total_cnt)


def format_card(label, raw_card, model):
    card = _fix_str_to_unicode(raw_card)

    if not card:
        yield '    EMPTY'
        return

    try:
        validate_structure(model, card)
    except (ValidationError, TypeError) as e:
        raise type(e)(u'{label}: {e}'.format(label=label, e=e))

    for line in formatting.format_struct(card):
        yield line
    yield ''


def showconfig():
    conf = get_app_conf()
    for line in formatting.format_struct(conf):
        yield line


if __name__ == '__main__':
    argh.dispatch_commands([
        showconfig,
        examine,
        assets,
        contacts,
        projects,
        # these should be reorganized:
        cli.needs,
        cli.plans,
        cli.serve,
    ])
