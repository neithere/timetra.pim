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


@app.route('/assets/')
def asset_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_asset_list(root)
    return render_template('asset_index.html', items=items)


@app.route('/assets/<slug>/')
def asset_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_asset(root, slug=slug)
    return render_template('asset_detail.html', item=item, slug=slug)


@app.route('/contacts/')
def contact_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_contact_list(root)
    return render_template('contact_index.html', items=items)


@app.route('/contacts/<slug>/')
def contact_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_contact(root, slug=slug)
    return render_template('contact_detail.html', item=item, slug=slug)


@app.route('/projects/')
def project_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_project_list(root)
    return render_template('project_index.html', items=items)


@app.route('/projects/<slug>/')
def project_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_project(root, slug=slug)
    return render_template('project_detail.html', item=item, slug=slug)


@app.route('/reference/')
def reference_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_reference_list(root)
    return render_template('reference_index.html', items=items)


@app.route('/reference/<slug>/')
def reference_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_reference(root, slug=slug)
    return render_template('reference_detail.html', item=item, slug=slug)


if __name__ == "__main__":
    app.config.from_pyfile('conf.py')
    app.run(port=6061)
