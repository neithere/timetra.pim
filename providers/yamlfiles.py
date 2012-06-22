# -*- coding: utf-8 -*-
import codecs
import datetime
import os
import yaml

from . import BaseDataProvider, Item
from . import utils


def load_path(path):
    """ Возвращает структуру данных, полученную из указанного YAML-файла.
    Если файл не найден, возвращает `None`.
    """
    try:
        with codecs.open(path, encoding='utf-8') as f:
            return yaml.load(f.read())
    except IOError:
        return None


def get_items_for_day(root_dir, date=None):
    """ Возвращает записи для указанного (или сегодняшнего) дня.
    """
    date = date or datetime.date.today()  # XXX beware UTC vs local time
    day_dir = '{root}/{date.year}/{date.month:0>2}'.format(root=root_dir, date=date)
    path = os.path.join(day_dir, '{date.day:0>2}.yaml'.format(date=date))
    return load_path(path) or []


def get_current_items(root_dir):
    """ Возвращает записи из текущего набора.
    """
    path = os.path.join(root_dir, 'items.yaml')
    return load_path(path)


class YAMLFilesProvider(BaseDataProvider):
    def __init__(self, root_dir):
        self.root_dir = root_dir

    @staticmethod
    def _transform_item(item):
        item = {'note': item} if isinstance(item, unicode) else item
        return Item(**item)

    def get_items(self, date=None):
        #items = get_items_for_day(self.root_dir, date)
        items = get_current_items(self.root_dir) #, date)
        items = (self._transform_item(x) for x in items)
        if date:
            items = (x for x in items
                if (utils.to_date(x.opened) <= date if x.opened else True) and
                   (utils.to_date(x.closed) >= date if x.closed else True)
            )
        return list(items)


    def get_plans(self, date=None):
        items = self.get_items(date)
        for item in items:
            for task in item.plan:
                yield task

#    def get_document_list(self, category):
#        return [Document(title='Foo', slug='foo')]


def configure_provider(app):
    root_dir = app.config['SOURCE_YAML_ROOT']
    return YAMLFilesProvider(root_dir)
