#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import re

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


def get_agenda(pattern):
    date = datetime.date.today()
    root = app.config['SOURCE_RST_ROOT']
    all_items = rstfiles.get_day_plans(root, date)
    items = [item for item in all_items if pattern in item['text']]
    return items


@app.route('/assets/')
def asset_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_asset_list(root)
    return render_template('asset_index.html', items=items)


@app.route('/assets/<slug>/')
def asset_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_asset(root, slug=slug)
    agenda = get_agenda('%'+slug)
    return render_template('asset_detail.html', item=item, agenda=agenda)


@app.route('/contacts/')
def contact_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_contact_list(root)
    return render_template('contact_index.html', items=items)


@app.route('/contacts/<slug>/')
def contact_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_contact(root, slug=slug)
    agenda = get_agenda('@'+slug)
    return render_template('contact_detail.html', item=item, agenda=agenda)


@app.route('/projects/')
def project_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_project_list(root)
    return render_template('project_index.html', items=items)


@app.route('/projects/<slug>/')
def project_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_project(root, slug=slug)
    agenda = get_agenda('#'+slug)
    return render_template('project_detail.html', item=item, agenda=agenda)


@app.route('/reference/')
def reference_index():
    root = app.config['SOURCE_RST_ROOT']
    items = rstfiles.get_reference_list(root)
    return render_template('reference_index.html', items=items)


@app.route('/reference/<slug>/')
def reference_detail(slug):
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.get_reference(root, slug=slug)
    agenda = get_agenda('?'+slug)
    return render_template('reference_detail.html', item=item, agenda=agenda)


@app.route('/someday/')
def someday():
    root = app.config['SOURCE_RST_ROOT']
    item = rstfiles.render_rst_file(root, '', 'someday')
    return render_template('someday.html', item=item)


# hashtag-related stuff should be done via template filters
hashtags = (
    dict(sigil='@', url_base='/contacts/', css='user'),
    dict(sigil='#', url_base='/projects/', css='tasks'),
    dict(sigil='%', url_base='/assets/', css='briefcase'),
    dict(sigil='\?', url_base='/reference/', css='book'),
)
regex_to_css = []
for hashtag in hashtags:
    regex = re.compile(r'(^|[>\(\s]){0}([A-Za-z][A-Za-z0-9_\-]+)'.format(hashtag['sigil']))
    template = r'\1<a href="{0}\2"><i class="icon-{1}"></i>&nbsp;\2</a>'.format(
        hashtag['url_base'], hashtag['css'])
    regex_to_css.append((regex, template))


def replace_hashtags(text):

    for regex, template in regex_to_css:
        text = re.sub(regex, template, text)
    return text


@app.template_filter('hashtagify')
def hashtags_filter(s):
    print 'replacing hashtags', s
    return replace_hashtags(s)


if __name__ == "__main__":
    app.config.from_pyfile('conf.py')
    app.config.NAV_ITEMS = (
        ('day_view', u'Планы'),
        ('project_index', u'Проекты'),
        ('asset_index', u'Имущество'),
        ('contact_index', u'Контакты'),
        ('reference_index', u'Справка'),
        ('someday', u'Когда-нибудь'),
    )
    app.run(port=6061)
