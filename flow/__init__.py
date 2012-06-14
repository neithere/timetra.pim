#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime

from flask import Blueprint, current_app, render_template
#from timetra import storage as timetra_storage

from providers import rstfiles


flow = Blueprint('flow', __name__, template_folder='templates')


def collect_plans(date):
    """ Returns a list of tasks collected from all available data providers.
    """
    items = []
    for provider in current_app.data_providers:
        for item in provider.get_day_plans(date):
            if item['plan']:
                items.extend(item['plan'])
    return items


def get_document_list(category):
    root = current_app.config['SOURCE_RST_ROOT']
    return rstfiles.get_rst_files_list_annotated(root, category)


def get_document(category, slug):
    root = current_app.config['SOURCE_RST_ROOT']
    return rstfiles.render_rst_file(root, category, slug)


def get_agenda(pattern):
    date = datetime.date.today()
    all_items = collect_plans(date)
    items = [item for item in all_items if pattern in item['action']]
    return items


@flow.route('/')
@flow.route('<int:year>/<int:month>/<int:day>/')
def day_view(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    items = collect_plans(date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('flow/index.html', items=items, date=date, prev=prev, next=next)


@flow.route('assets/')
def asset_index():
    items = get_document_list('assets')
    return render_template('flow/asset_index.html', items=items)


@flow.route('assets/<slug>/')
def asset_detail(slug):
    item = get_document('assets', slug)
    agenda = get_agenda('%'+slug)
    return render_template('flow/asset_detail.html', item=item, agenda=agenda)


@flow.route('contacts/')
def contact_index():
    items = get_document_list('contacts')
    return render_template('flow/contact_index.html', items=items)


@flow.route('contacts/<slug>/')
def contact_detail(slug):
    item = get_document('contacts', slug)
    agenda = get_agenda('@'+slug)
    return render_template('flow/contact_detail.html', item=item, agenda=agenda)


@flow.route('projects/')
def project_index():
    items = get_document_list('projects')
    return render_template('flow/project_index.html', items=items)


@flow.route('projects/<slug>/')
def project_detail(slug):
    item = get_document('projects', slug)
    agenda = get_agenda('#'+slug)
    return render_template('flow/project_detail.html', item=item, agenda=agenda)


@flow.route('reference/')
def reference_index():
    items = get_document_list('reference')
    return render_template('flow/reference_index.html', items=items)


@flow.route('reference/<slug>/')
def reference_detail(slug):
    item = get_document('reference', slug)
    agenda = get_agenda('?'+slug)
    return render_template('flow/reference_detail.html', item=item, agenda=agenda)


@flow.route('someday/')
def someday():
    item = get_document('', 'someday')
    return render_template('flow/someday.html', item=item)
