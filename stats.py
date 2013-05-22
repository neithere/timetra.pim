# coding: utf-8

from datetime import datetime, timedelta
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

    concerns_ttls = []
    concerns_ttls_closed = []
    plans_ttls = []
    plans_ttls_closed = []

    for concern in finder.get_concerns(include_closed=True):
        concerns_total_cnt += 1
        plans_total_cnt += len(concern.plan or [])

        if concern.opened:
            ttl = (concern.closed or datetime.utcnow()) - concern.opened
            concerns_ttls.append(ttl)
            if concern.closed:
                concerns_ttls_closed.append(ttl)

        if not concern.closed:
            if concern.is_frozen():
                concerns_frozen_cnt += 1
                plans_frozen_cnt += len(concern.plan or [])
            else:
                concerns_active_cnt += 1
                plans_active_cnt += len(concern.plan or [])

        if concern.plan:
            for plan in concern.plan:
                if plan.opened:
                    ttl = (plan.closed or datetime.utcnow()) - plan.opened
                    plans_ttls.append(ttl)
                    if plan.closed:
                        plans_ttls_closed.append(ttl)

    def format_ttl(deltas):
        if not deltas:
            return '—'
        avg = sum(deltas, timedelta()).days / len(deltas)
        return '{0} days'.format(avg)

    concerns_avg_ttl = format_ttl(concerns_ttls)
    plans_avg_ttl = format_ttl(plans_ttls)
    concerns_avg_ttl_closed = format_ttl(concerns_ttls_closed)
    plans_avg_ttl_closed = format_ttl(plans_ttls_closed)

    table = PrettyTable()
    table.field_names = ['type', 'total', 'active', 'frozen', 'ttl', 'ttc']
    table.add_row(['concerns', concerns_total_cnt, concerns_active_cnt,
                   concerns_frozen_cnt, concerns_avg_ttl, concerns_avg_ttl_closed])
    table.add_row(['plans', plans_total_cnt, plans_active_cnt,
                   plans_frozen_cnt, plans_avg_ttl, plans_avg_ttl_closed])
    yield table
    yield ''
    yield 'Legend:'
    yield 'ttl = avg time to live (item age, whether it is closed or not yet)'
    yield 'ttc = avg time to close (how long does it take to close an item)'


commands = [ stat_files, stat_concerns ]
