#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime

from flask import Blueprint, current_app, render_template


flare = Blueprint('flare', __name__, template_folder='templates')


def collect_needs(date):
    """ Returns a list of needs and respective tasks collected from all
    available data providers.
    """
    items = []
    for provider in current_app.data_providers:
        items.extend(provider.get_day_plans(date))
    return items


def day_view(year=None, month=None, day=None, template=None):
    assert template
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    items = collect_needs(date)
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
