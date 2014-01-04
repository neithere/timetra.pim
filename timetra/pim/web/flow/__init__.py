#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import itertools

from flask import Blueprint, current_app, render_template, request
#from timetra import storage as timetra_storage

flow = Blueprint('flow', __name__, template_folder='templates')


def get_document_list(category):
    return current_app.data_providers.get_document_list(category)


def get_document(category, slug):
    return current_app.data_providers.get_document(category, slug)


def get_agenda(category, slug):
    category_to_hashtag = {
        'assets': '%',
        'projects': '#',
        'contacts': '@',
        'reference': '?',
    }
    hashtag = category_to_hashtag.get(category)
    pattern = hashtag + slug
    date = datetime.date.today()
    items = current_app.data_providers.get_items(date)
    filtered = []
    for item in items:
        # NOTE: тут мы добавляем сразу весь item, но, скажем, в agenda по
        # водопроводчику не надо запихивать весь список задач по ремонту дома,
        # достаточно именно одной задачи, в которой упомянут этот
        # водопроводчик.
        # С другой стороны, если со срезом связана не задача, а сущность более
        # высокого уровня (риск/потребность), то надо эту сущность выводить как
        # есть.
        # Значит, нужны два списка: риски/потребности и планы, т.е., "цели" и "действия".

        append = False

        if category == 'contacts' and slug in item.stakeholders:
            append = True
        if category == 'projects' and slug == item.project:
            #print 'INCLUDE project explicit'
            #print '  ', (item.need or item.risk)
            append = True
        if item.need and pattern in item.need:
            #print 'INCLUDE pattern in item.need'
            append = True
        if item.plan and any(pattern in x.action for x in item.plan):
            #print 'INCLUDE pattern in item.plan.*.action'
            #print '  ', '|'.join(x.action for x in item.plan)
            append = True

        if not (item.risk or item.need):
            # skip notes (and such stuff, if any possible)
            append = False

        if append:
            filtered.append(item)

    if filtered:
        return {
            'concerns': itertools.chain(x for x in filtered),
            'plans': itertools.chain(*(x.plan for x in filtered if x.plan)),
        }
    else:
        return None


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
    tag = request.values.get('item_category')
    if tag:
        items = (x for x in items if tag in x.categories)
    return render_template('flow/asset_index.html', items=items)


@flow.route('assets/<slug>/')
def asset_detail(slug):
    item = get_document('assets', slug)
    agenda = get_agenda('assets', slug)
    return render_template('flow/asset_detail.html', item=item, agenda=agenda)


@flow.route('contacts/')
def contact_index():
    items = get_document_list('contacts')
    return render_template('flow/contact_index.html', items=items)


@flow.route('contacts/<slug>/')
def contact_detail(slug):
    item = get_document('contacts', slug)
    agenda = get_agenda('contacts', slug)
    return render_template('flow/contact_detail.html', item=item, agenda=agenda)


@flow.route('projects/')
def project_index():
    items = get_document_list('projects')
    return render_template('flow/project_index.html', items=items)


@flow.route('projects/<slug>/')
def project_detail(slug):
    item = get_document('projects', slug)
    agenda = get_agenda('projects', slug)
    return render_template('flow/project_detail.html', item=item, agenda=agenda)


@flow.route('reference/')
def reference_index():
    items = get_document_list('reference')
    return render_template('flow/reference_index.html', items=items)


@flow.route('reference/<slug>/')
def reference_detail(slug):
    item = get_document('reference', slug)
    agenda = get_agenda('reference', slug)
    return render_template('flow/reference_detail.html', item=item, agenda=agenda)
