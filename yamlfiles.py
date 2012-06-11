# -*- coding: utf-8 -*-
import codecs
import datetime
import os
import yaml


def get_day_plans(root_dir, date=None):
    date = date or datetime.date.today()  # XXX beware UTC vs local time
    day_dir = '{root}/{date.year}/{date.month:0>2}'.format(root=root_dir, date=date)
    try:
        files = os.listdir(day_dir)
    except OSError:
        return []
    docs = [f for f in files if f.endswith('.yaml')]
    print docs
    today_fn = '{date.day:0>2}.yaml'.format(date=date)
    print today_fn
    if today_fn not in docs:
        return []
    today_path = os.path.join(day_dir, today_fn)
    with codecs.open(today_path, encoding='utf-8') as f:
        return yaml.load(f.read())
