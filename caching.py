# coding: utf-8
import os
import shelve

import xdg.BaseDirectory

import loading


__all__ = ['get_cached_yaml_file']


APP_NAME = 'pim'    # settings.APP_NAME


cache_dir = xdg.BaseDirectory.save_cache_path(APP_NAME)
cache_path = cache_dir + '/yaml_files.db'
try:
    cache = shelve.open(cache_path)
except:
    os.remove(cache_path)
    cache = shelve.open(cache_path)


def get_cached_yaml_file(path, model):
    #results = tmpl_cache.get(key=search_param, createfunc=load_card)
    time_key = u'changed:{0}'.format(path).encode('utf-8')
    data_key = u'content:{0}'.format(path).encode('utf-8')
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
