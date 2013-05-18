# coding: utf-8

import os

import argh
from prettytable import PrettyTable

from settings import get_app_conf, ConfigurationError
import finder
import formatting


@argh.named('files')
@argh.wrap_errors([ConfigurationError], processor=formatting.format_error)
def stat_files(long=False):
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

            _, ext = os.path.splitext(name)
            files_by_ext.setdefault(ext, []).append(os.path.join(root, name))

    for ext, files in files_by_ext.iteritems():
        yield '{ext}: {count}'.format(ext=(ext or 'no extension'), count=len(files))
        if long or len(files) < 10:    # <- an arbitrary threshold for marginal formats
            for f in files:
                yield u'    {0}'.format(f)


@argh.named('concerns')
def stat_concerns():
    concerns_total_cnt = 0
    concerns_active_cnt = 0
    concerns_frozen_cnt = 0
    plans_total_cnt = 0
    plans_active_cnt = 0
    plans_frozen_cnt = 0
    for concern in finder.get_concerns(include_closed=True):
        concerns_total_cnt += 1
        plans_total_cnt += len(concern.plan or [])
        if not concern.closed:
            if concern.is_frozen():
                concerns_frozen_cnt += 1
                plans_frozen_cnt += len(concern.plan or [])
            else:
                concerns_active_cnt += 1
                plans_active_cnt += len(concern.plan or [])

    table = PrettyTable()
    table.field_names = ['type', 'total', 'active', 'frozen']
    table.add_row(['concerns', concerns_total_cnt, concerns_active_cnt, concerns_frozen_cnt])
    table.add_row(['plans', plans_total_cnt, plans_active_cnt, plans_frozen_cnt])
    return table


commands = [ stat_files, stat_concerns ]
