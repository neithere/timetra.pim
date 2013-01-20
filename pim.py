#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argh
from blessings import Terminal
import datetime
from monk.modeling import DotExpandedDict
from monk.validation import validate_structure, optional, ValidationError
import os
import subprocess
import textwrap
import yaml
import xdg.BaseDirectory


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
    }

    with open(path) as f:
        conf = yaml.load(f)

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
    conf = get_app_conf()

    labels = _fix_str_to_unicode(labels)

    index_path = os.path.join(conf.index, 'contacts.yaml')
    #cards_path = os.path.join(conf.index, 'contacts')

    card_struct = {
        'name': unicode,
        'full_name': optional(unicode),
        'urls': optional([unicode]),
        'addr': optional(unicode),
        'tels': optional([unicode]),
        'mail': optional([unicode]),
        'note': optional(unicode),
        'nick': optional(unicode),
        'born': optional(datetime.date),
        'related': optional([unicode]),    # hashtags
        'first_contact': optional(datetime.date),
        'org': optional(unicode),
        'timetable': optional(unicode),
    }
    with open(index_path) as f:
        cards = yaml.load(f)  #, unicode=True)

    total_cnt = 0
    for label, card in cards.iteritems():
        if labels and not label in labels:
            continue

        if count:
            total_cnt += 1
            continue

        card = _fix_str_to_unicode(card)

        try:
            validate_structure(card_struct, card)
        except (ValidationError, TypeError) as e:
            raise ValidationError(u'{label}: {e}'.format(label=label, e=e))

        yield ''
        yield t.bold(u'@{0}'.format(label))
        for k,v in card.iteritems():
            yield textwrap.fill(u'{k}: {v}'.format(k=k, v=v),
                                initial_indent='    ',
                                subsequent_indent='          ')
    if count:
        yield 'Found {0} items'.format(total_cnt)


if __name__ == '__main__':
    argh.dispatch_commands([
        examine,
        contacts
    ])
