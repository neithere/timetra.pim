#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import itertools
from dateutil import rrule
from operator import itemgetter

from flask import Blueprint, current_app, render_template, request


flare = Blueprint('flare', __name__, template_folder='templates')


def multikeysort(items, columns):
    """ See http://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys
    (author: hughdbrown)
    """
    comparers = [((itemgetter(col[1:].strip()), -1)
                  if col.startswith('-') else
                  (itemgetter(col.strip()), 1))
                  for col in columns]
    def comparer(left, right):
        for fn, mult in comparers:
            # `None` values are tolerated and treated as "less than any other"
            null_matrix = {(True, True): 0,
                           (True, False): -1,
                           (False, True): 1}
            values = fn(left) is None, fn(right) is None
            if values in null_matrix:
                return mult * null_matrix[values]
            else:
                result = cmp(fn(left), fn(right))
                if result:
                    return mult * result
        else:
            return 0
    return sorted(items, cmp=comparer)


def day_view(year=None, month=None, day=None, template=None, query=None,
             processor=None, skip_archived=False):
    assert template
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()

    if query:
        items = current_app.data_providers.filter_items(**query)
    else:
        items = current_app.data_providers.get_items(date,
                                                     skip_archived=skip_archived)

    if processor:
        items = processor(items)
    items = list(multikeysort(items, ['-acute', 'frozen']))
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
    filter_acute = lambda xs: (x for x in xs if x.acute)
    filter_warm = lambda xs: (x for x in xs if not x.frozen)
    if request.values.get('acute'):
        processor = lambda xs: filter_items(filter_acute(xs))
    elif request.values.get('warm'):
        processor = lambda xs: filter_items(filter_warm(xs))
    else:
        processor = filter_items
    return day_view(template='flare/item_index.html', processor=processor,
                    skip_archived=True, **kwargs)


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
