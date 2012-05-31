#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime

from flask import Flask, render_template
#from timetra import storage as timetra_storage

import rstfiles


app = Flask(__name__)


@app.route('/')
@app.route('/<int:year>/<int:month>/<int:day>')
def day_view(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_day_plans(root, date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('index.html', items=items, date=date, prev=prev, next=next)


if __name__ == "__main__":
    app.config.from_pyfile('conf.py')
    app.run(port=6061)
