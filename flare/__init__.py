#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import itertools
from dateutil import rrule
from operator import itemgetter

from flask import Blueprint, current_app, render_template


flare = Blueprint('flare', __name__, template_folder='templates')


def day_view(year=None, month=None, day=None, template=None, processor=None):
    assert template
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    items = current_app.data_providers.get_items(date)
    if processor:
        items = processor(items)
    items = list(sorted(items, key=itemgetter('important'), reverse=True))
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template(template, items=items, date=date, prev=prev, next=next)


@flare.route('/')
@flare.route('<int:year>/<int:month>/<int:day>/')
def day_full(**kwargs):
    return day_view(template='flare/day.html', **kwargs)


@flare.route('tasks/')
@flare.route('<int:year>/<int:month>/<int:day>/tasks/')
def day_tasks(**kwargs):
    return day_view(template='flare/day_tasks.html', **kwargs)


@flare.route('notes/')
@flare.route('<int:year>/<int:month>/<int:day>/notes/')
def day_notes(**kwargs):
    return day_view(template='flare/day_notes.html', **kwargs)


@flare.route('items/')
@flare.route('<int:year>/<int:month>/<int:day>/items/')
def item_index(**kwargs):
    filter_items = lambda xs: (x for x in xs if x.need or x.risk)
    return day_view(template='flare/item_index.html', processor=filter_items,
                    **kwargs)


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


@flare.route('timeline/')
def item_timeline():
    depth = 5
    since = datetime.datetime.utcnow() - datetime.timedelta(days=depth)
    rule = rrule.rrule(rrule.DAILY, dtstart=since, count=depth)
    dates = (x.date() for x in rule)
    history = []
    for date in dates:
        opened = current_app.data_providers.filter_items(opened=date)
        closed = current_app.data_providers.filter_items(closed=date)
        items = itertools.chain(opened, closed)
#        items = sorted(items, key=itemgetter('opened', 'closed'))
        history.append((date, items))
    return render_template('flare/item_timeline.html', history=history)
