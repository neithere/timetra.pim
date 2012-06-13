#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime

from flask import Blueprint, Flask, current_app, render_template

from providers import yamlfiles, rstfiles


def make_app(conf_path='conf.py'):
    app = Flask(__name__)

    app.config.from_pyfile(conf_path)
    app.config.NAV_ITEMS = (
        ('flare.day_full', u'Планы'),
    )

    app.register_blueprint(flare, url_prefix='/')

    yaml_provider = yamlfiles.configure_provider(app)
    rst_provider = rstfiles.configure_provider(app)
    app.data_providers = [yaml_provider, rst_provider]

    return app


flare = Blueprint('flare', __name__)


def collect_needs(date):
    """ Returns a list of needs and respective tasks collected from all
    available data providers.
    """
    items = []
    for provider in current_app.data_providers:
        items.extend(provider.get_day_plans(date))
    return items


@flare.route('/')
@flare.route('<int:year>/<int:month>/<int:day>/')
def day_full(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    #root = app.config['SOURCE_YAML_ROOT']
    #items = yamlfiles.get_day_plans(root, date)
    items = collect_needs(date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('day.html', items=items, date=date, prev=prev, next=next)


@flare.route('<int:year>/<int:month>/<int:day>/tasks/')
def day_tasks(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    items = collect_needs(date)
    #items = []
    #for provider in app.data_providers:
    #    items.extend(provider.get_day_plans(date))
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('day_tasks.html', items=items, date=date, prev=prev, next=next)


if __name__ == "__main__":
    app = make_app()
    app.run(port=6062)
