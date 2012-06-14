# -*- coding: utf-8 -*-
import codecs
import datetime
import os
import yaml

from . import Item


def get_day_plans(root_dir, date=None):
    date = date or datetime.date.today()  # XXX beware UTC vs local time
    day_dir = '{root}/{date.year}/{date.month:0>2}'.format(root=root_dir, date=date)
    try:
        files = os.listdir(day_dir)
    except OSError:
        return []
    docs = [f for f in files if f.endswith('.yaml')]
    today_fn = '{date.day:0>2}.yaml'.format(date=date)
    if today_fn not in docs:
        return []
    today_path = os.path.join(day_dir, today_fn)
    with codecs.open(today_path, encoding='utf-8') as f:
        return yaml.load(f.read())


def capfirst(value):
    return value[0].upper() + value[1:] if value else value


class YAMLFilesProvider:
    def __init__(self, root_dir):
        self.root_dir = root_dir

    @staticmethod
    def _transform_item(item):
        item = dict(item)
        for key in ('idea', 'note', 'risk', 'need'):
            if item.get(key):
                item[key] = capfirst(item[key])
        return Item(**item)

    def get_day_plans(self, date):
        items = get_day_plans(self.root_dir, date)
        return [self._transform_item(x) for x in items]


def configure_provider(app):
    root_dir = app.config['SOURCE_YAML_ROOT']
    return YAMLFilesProvider(root_dir)
