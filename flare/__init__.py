#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime

from flask import Blueprint, current_app, render_template


flare = Blueprint('flare', __name__, template_folder='templates')


def day_view(year=None, month=None, day=None, template=None):
    assert template
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    items = current_app.data_providers.get_items(date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template(template, items=items, date=date, prev=prev, next=next)


@flare.route('/')
@flare.route('<int:year>/<int:month>/<int:day>/')
def day_full(**kwargs):
    return day_view(template='flare/day.html', **kwargs)


@flare.route('<int:year>/<int:month>/<int:day>/tasks/')
def day_tasks(**kwargs):
    return day_view(template='flare/day_tasks.html', **kwargs)


@flare.route('<int:year>/<int:month>/<int:day>/notes/')
def day_notes(**kwargs):
    return day_view(template='flare/day_notes.html', **kwargs)


@flare.route('items/')
def item_index(**kwargs):
    items = current_app.data_providers.get_items(date=None)
    items = (x for x in items if ('need' in x and x.need) or
                                 ('risk' in x and x.risk))
    return render_template('flare/item_index.html', items=items)


@flare.route('items/<text>/')
def item_detail(text):
    # очевидный костыль: поскольку нет идентификаторов у items, используем
    # текст элементов item'а
    items = current_app.data_providers.get_items(date=None)
    chosen_item = None
    for item in items:
        if text in (item.need, item.risk):
            chosen_item = item
            break
    return render_template('flare/item_detail.html', item=chosen_item)
