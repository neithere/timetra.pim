#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import itertools

from flask import Blueprint, current_app, render_template
#from timetra import storage as timetra_storage

flow = Blueprint('flow', __name__, template_folder='templates')


def get_document_list(category):
    return current_app.data_providers.get_document_list(category)


def get_document(category, slug):
    return current_app.data_providers.get_document(category, slug)


def get_agenda(pattern):
    date = datetime.date.today()
    items = current_app.data_providers.get_items(date)
    filtered = []
    for item in items:
        if item.need and pattern in item.need:
            filtered.append(item)
            break
        if item.plan and any(pattern in x.action for x in item.plan):
            filtered.append(item)
            break
    # TODO: return whole items (needs fixing document templates)
    return itertools.chain(*(x.plan for x in filtered if x.plan))


@flow.route('/')
@flow.route('<int:year>/<int:month>/<int:day>/')
def day_view(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    plans = current_app.data_providers.get_plans(date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('flow/index.html', plans=plans, date=date, prev=prev, next=next)


@flow.route('contexts/')
def context_index():
    date = datetime.date.today()
    plans = current_app.data_providers.get_plans(date)
    grouped = (p.context for p in plans if 'context' in p)
    slugs = list(set(itertools.chain(*grouped)))
    contexts = ({'title': x, 'slug': x} for x in slugs)
    return render_template('flow/context_index.html', contexts=contexts)


@flow.route('contexts/<slug>/')
def context_detail(slug):
    date = datetime.date.today()
    plans = current_app.data_providers.get_plans(date)
    filtered = (p for p in plans if 'context' in p and slug in p.context)
    item = {'title': slug, 'slug': slug}
    return render_template('flow/context_detail.html', item=item, plans=filtered)


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