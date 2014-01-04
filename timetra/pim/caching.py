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

import atexit
import os
import shelve

import xdg.BaseDirectory

from . import compat
from . import loading


__all__ = ['get_cached_yaml_file']


APP_NAME = 'pim'    # settings.APP_NAME


cache_dir = xdg.BaseDirectory.save_cache_path(APP_NAME)
cache_path = cache_dir + '/yaml_files.db'
try:
    cache = shelve.open(cache_path)
except:
    os.remove(cache_path)
    cache = shelve.open(cache_path)

# http://stackoverflow.com/questions/2180946/really-weird-issue-with-shelve-python
# (got this issue even on Python 2.7.4)
atexit.register(lambda: cache.close())


def get_cached_yaml_file(path, model):
    #results = tmpl_cache.get(key=search_param, createfunc=load_card)
    time_key = compat.encode(u'changed:{0}'.format(path))
    data_key = compat.encode(u'content:{0}'.format(path))
    mtime_cache = cache.get(time_key)
    mtime_file = os.stat(path).st_mtime
    if mtime_cache == mtime_file:
        data = cache[data_key]
    else:
        data = loading.load_card(path, model)
        cache[data_key] = data
        cache[time_key] = mtime_file
    #cache.close()
    return data


def reset():
    try:
        cache.close()
    except:
        pass
    os.remove(cache_path)


commands = [ reset ]
