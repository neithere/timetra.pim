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

import xdg.BaseDirectory
import yaml

from . import finder
from . import formatting
from . import loading
from . import settings
from .utils import getch
from .models import Concern


data_dir = xdg.BaseDirectory.save_data_path(settings.APP_NAME)
data_path = data_dir + '/overview_picked.yaml'


PICKED_MODEL = {'concerns': [Concern.structure]}


def get_prev_picked():
    if os.path.exists(data_path):
        data = loading.load_card(data_path, PICKED_MODEL)
        return data['concerns']
    else:
        return []


def save_picked(concerns):
    with open(data_path, 'w') as f:
        yaml.dump({'concerns': concerns}, f)


def overview(warm=False, acute=False):
    """ Displays concerns one by one, letting user to pick or postpone them.
    """
    prev_picked = get_prev_picked()
    if prev_picked:
        yield 'Show previously picked concerns? (enter = yes)'
        if getch() == '\r':
            for concern in prev_picked:
                yield '\n'.join(formatting.format_concern(concern))

        yield 'Keep previously picked concerns? (enter = yes)'
        if getch() == '\r':
            return

    concerns = finder.get_concerns()
    # TODO: acute/warm should be displayed first
    chosen = []
    for concern in concerns:
        if acute and not concern.acute:
            continue
        if warm and concern.frozen:
            continue
        yield ''
        yield concern.context
        yield '\n'.join(formatting.format_concern(concern))
        #if argh.confirm('pick for today', default=False):
        yield ''
        yield u'> пропустить (пробел) | выбрать (enter) | стоп (esc)'
        ret = getch()
        if ret == '\r':      # enter
            chosen.append(concern)
        elif ret == '\x1b':    # esc
            break
        elif ret == ' ':
            continue
        else:
            raise ValueError(u'unknown option "{0}"'.format(ret))

    yield ''
    yield '--- CHOSEN:'
    yield ''
    for concern in chosen:
        yield '\n'.join(formatting.format_concern(concern))

    yield 'Keep newly picked concerns?'
    if getch() == '\r':
        save_picked(chosen)


commands = [overview]
