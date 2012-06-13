#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import re

from flask import Flask, render_template
#from timetra import storage as timetra_storage

import yamlfiles


app = Flask(__name__)


@app.route('/')
@app.route('/<int:year>/<int:month>/<int:day>/')
def day_full(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    root = app.config['SOURCE_YAML_ROOT']
    items = yamlfiles.get_day_plans(root, date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('day.html', items=items, date=date, prev=prev, next=next)


@app.route('/<int:year>/<int:month>/<int:day>/tasks/')
def day_tasks(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    root = app.config['SOURCE_YAML_ROOT']
    items = yamlfiles.get_day_plans(root, date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('day_tasks.html', items=items, date=date, prev=prev, next=next)


if __name__ == "__main__":
    app.config.from_pyfile('conf.py')
    app.config.NAV_ITEMS = (
        ('day_full', u'Планы'),
    )
    app.run(port=6062)
