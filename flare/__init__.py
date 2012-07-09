#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import itertools
from dateutil import rrule
from operator import itemgetter

from flask import Blueprint, current_app, render_template


flare = Blueprint('flare', __name__, template_folder='templates')


def day_view(year=None, month=None, day=None, template=None, query=None, processor=None):
    assert template
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()

    if query:
        items = current_app.data_providers.filter_items(**query)
    else:
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
    query = dict(frozen=False)
    return day_view(template='flare/day.html', query=query, **kwargs)


@flare.route('tasks/')
@flare.route('<int:year>/<int:month>/<int:day>/tasks/')
def day_tasks(**kwargs):
    query = dict(frozen=False)
    return day_view(template='flare/day_tasks.html', query=query,**kwargs)


@flare.route('notes/')
@flare.route('<int:year>/<int:month>/<int:day>/notes/')
def day_notes(**kwargs):
    query = dict(frozen=False)
    return day_view(template='flare/day_notes.html', query=query,**kwargs)


@flare.route('someday/')
def someday(**kwargs):
    query = dict(frozen=True)
    return day_view(template='flare/someday.html', query=query, **kwargs)


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
    now = datetime.datetime.utcnow()
    since = now - datetime.timedelta(days=depth)
    rule = rrule.rrule(rrule.DAILY, dtstart=since, until=now)
    dates = (x.date() for x in rule)
    history = []
    for date in dates:
        opened = current_app.data_providers.filter_items(opened=date)
        closed = current_app.data_providers.filter_items(closed=date)
        items = itertools.chain(opened, closed)
#        items = sorted(items, key=itemgetter('opened', 'closed'))
        history.append((date, items))
    return render_template('flare/item_timeline.html', history=history)
