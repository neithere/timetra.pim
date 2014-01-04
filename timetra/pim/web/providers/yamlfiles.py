# -*- coding: utf-8 -*-
import codecs
import datetime
import itertools
import os
import yaml

from .base import BaseDataProvider
from models import Concern as Item, Document
from . import utils

from settings import get_app_conf


ARCHIVE_FILENAMES = ('archive.yaml',)

# future pim-view stuff
IGNORED_FILENAMES = ('contacts.yaml', 'assets.yaml', 'projects.yaml',
                     'schema.yaml')


def load_path(path):
    """ Возвращает структуру данных, полученную из указанного YAML-файла.
    Если файл не найден, возвращает `None`.
    """
    try:
        with codecs.open(path, encoding='utf-8') as f:
            return yaml.load(f.read())
    except IOError:
        return None


# FIXME удалить эту функцию, перенеся старые данные
def get_items_for_day(root_dir, date=None):
    """ Возвращает записи для указанного (или сегодняшнего) дня.
    """
    date = date or datetime.date.today()  # XXX beware UTC vs local time
    day_dir = '{root}/{date.year}/{date.month:0>2}'.format(root=root_dir, date=date)
    path = os.path.join(day_dir, '{date.day:0>2}.yaml'.format(date=date))
    return load_path(path) or []


def get_current_items(root_dir, skip_archived=False):
    """ Возвращает записи из текущего набора.
    """
    all_names = (x for x in os.listdir(root_dir) if x.endswith('.yaml'))
    names = (x for x in all_names if x not in IGNORED_FILENAMES)
    if skip_archived:
        filtered = (x for x in names if x not in ARCHIVE_FILENAMES)
    else:
        filtered = names
    paths = (os.path.join(root_dir, x) for x in filtered)
    return itertools.chain(*(load_path(x) for x in paths))


class YAMLFilesProvider(BaseDataProvider):
    def __init__(self, root_dir):
        self.root_dir = root_dir

    @staticmethod
    def _transform_item(item):
        item = {'note': item} if isinstance(item, unicode) else item
        return Item(**item)

    def get_items(self, date=None, skip_archived=False):
        #items = get_items_for_day(self.root_dir, date)
        items = get_current_items(self.root_dir, skip_archived=skip_archived) #, date)
        items = (self._transform_item(x) for x in items)
        if date:
            items = (x for x in items
                if (utils.to_date(x.opened) <= date if x.opened else True) and
                   (utils.to_date(x.closed) >= date if x.closed else True)
            )
        return list(items)

    def filter_items(self, opened=None, closed=None, frozen=None):
        items = get_current_items(self.root_dir)
        items = (self._transform_item(x) for x in items)
        if opened:
            items = (x for x in items
                if x.opened and utils.to_date(opened) == utils.to_date(x.opened)
            )
        if closed:
            items = (x for x in items
                if x.closed and utils.to_date(closed) == utils.to_date(x.closed)
            )
        if frozen is not None:
            print('filtering', bool(frozen))
            items = (x for x in items
                if bool(frozen) == bool(x.frozen)
            )
        return list(items)

    def get_plans(self, date=None):
        items = self.get_items(date)
        for item in items:
            for task in item.plan:
                yield task

#    def get_document_list(self, category):
#        return [Document(title='Foo', slug='foo')]


def configure_provider():
    conf = get_app_conf()
    root_dir = conf.x_flow.SOURCE_YAML_ROOT
    return YAMLFilesProvider(root_dir)
