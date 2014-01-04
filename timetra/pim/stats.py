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

from datetime import datetime, timedelta
import os

import argh
from prettytable import PrettyTable

from .settings import get_app_conf, ConfigurationError
from . import finder
from . import formatting


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
    concerns_time_to_freeze = []
    plans_ttls = []
    plans_ttls_closed = []
    plans_time_to_freeze = []

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
                concerns_time_to_freeze.append(concern.frozen - concern.opened)
            else:
                concerns_active_cnt += 1

        if concern.plan:
            for plan in concern.plan:
                if plan.opened:
                    ttl = (plan.closed or datetime.utcnow()) - plan.opened
                    plans_ttls.append(ttl)
                    if plan.closed:
                        plans_ttls_closed.append(ttl)
                    else:
                        if concern.frozen:
                            plans_frozen_cnt += 1
                            plans_time_to_freeze.append(concern.frozen - plan.opened)
                        else:
                            plans_active_cnt += 1

    def format_ttl(deltas):
        if not deltas:
            return '—'
        avg = sum(deltas, timedelta()).days / len(deltas)
        return '{0} days'.format(avg)

    concerns_avg_ttl = format_ttl(concerns_ttls)
    concerns_avg_time_to_freeze = format_ttl(concerns_time_to_freeze)
    plans_avg_ttl = format_ttl(plans_ttls)
    concerns_avg_ttl_closed = format_ttl(concerns_ttls_closed)
    plans_avg_ttl_closed = format_ttl(plans_ttls_closed)
    plans_avg_time_to_freeze = format_ttl(plans_time_to_freeze)

    table = PrettyTable()
    table.field_names = ['type', 'total', 'active', 'frozen', 'ttl', 'ttc', 'ttf']
    table.add_row(['concerns', concerns_total_cnt, concerns_active_cnt,
                   concerns_frozen_cnt, concerns_avg_ttl, concerns_avg_ttl_closed,
                   concerns_avg_time_to_freeze])
    table.add_row(['plans', plans_total_cnt, plans_active_cnt,
                   plans_frozen_cnt, plans_avg_ttl, plans_avg_ttl_closed,
                   plans_avg_time_to_freeze])
    yield table
    yield ''
    yield 'Legend:'
    yield 'ttl = avg time to live (item age, whether it is closed or not yet)'
    yield 'ttc = avg time to close (how long does it take to close an item)'
    yield 'ttf = avg time to freeze (how long an item stays active until frozen)'


@argh.named('assets')
def stat_assets():
    return get_state_aggregate('assets')


@argh.named('projects')
def stat_projects():
    return get_state_aggregate('projects')


def get_state_aggregate(category):
    conf = get_app_conf()
    root = '{0}/{1}'.format(conf.index, category)
    detail, index, guessed_path = finder.find_items(root, finder.CATEGORIES[category], '')
    states = {}
    for path, loader in index:
        item = loader()
        states[item.state] = states.get(item.state, []) + [path]
    state_table = PrettyTable()
    state_table.field_names = ['state', 'count']
    state_table.align = 'l'
    for key, value in states.items():
        # show number of multiple entries or path to a single entry with this value
        if len(value) == 1:
            state_table.add_row([key, value[0]])
        else:
            state_table.add_row([key, len(value)])
    return state_table


commands = [ stat_files, stat_concerns, stat_assets, stat_projects ]
