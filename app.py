#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import codecs
import datetime
import os
import re

from flask import Flask, render_template
#from timetra import storage as timetra_storage


app = Flask(__name__)


garbage = re.compile(r'^[\-=]+$')


def parse_task_v1(line, context=None, from_yesterday=False, fixed_time=False, waiting_for=False):
    if context:
        line = u'{line} {context}'.format(line=line, context=context)
    item = {
        'text': line,
        'bigstone': False,
        'from_yesterday': from_yesterday,
        'fixed_time': fixed_time,
        'waiting_for': waiting_for,
    }
    if '**BIGSTONE**' in line:
        item.update(
            text = item['text'].replace('**BIGSTONE**', ''),
            bigstone = True
        )
    states = {'[ ]': 'todo', '[x]': 'done'}
    for token, state in states.items():
        if token in item['text']:
            item.update(
                text = item['text'].replace(token, ''),
                state = state
            )
    if ':doc:' in item['text']:
        html_root = app.config['SOURCE_HTML_ROOT']
        item['text'] = re.sub(r':doc:`(.+?)`',
                              r'<a href="file://{0}\1.html">\1</a>'.format(html_root),
                              item['text'])

    time_pattern = re.compile(r'^\s*(\d{2}):(\d{2}) ')
    match_time = time_pattern.match(item['text'])
    if match_time:
        item.update(
            text = re.sub(time_pattern, '', item['text']),
            time = datetime.time(*(int(x) for x in match_time.groups()))
        )

    est_pattern = re.compile(r'\((\d+[hm])\)')
    match_est = est_pattern.search(item['text'])
    if match_est:
        item.update(
            text = re.sub(est_pattern, '', item['text']),
            estimate = match_est.groups()[0]  # NOT group(0)! :(
        )

    contexts = 'pc', 'home', 'city'
    item['text'] = re.sub(r'@({0})'.format('|'.join(contexts)),
                          r'<span class="label"><i class="icon-white icon-globe"></i> \1</span>',
                          item['text'])
    item['text'] = re.sub(r'@([A-Za-z][A-Za-z0-9\-]+)',
                          r'<a href="#"><i class="icon-user"></i> \1</a>',
                          item['text'])
    item['text'] = re.sub(r'#([A-Za-z][A-Za-z0-9\-]+)',
                          r'<a href="#"><i class="icon-tasks"></i> \1</a>',
                          item['text'])
    return item


def parse_task_v2(line, from_yesterday=False, fixed_time=False, waiting_for=False):
    item = {
        'text': line,
        'bigstone': False,
        'from_yesterday': from_yesterday,
        'fixed_time': fixed_time,
        'waiting_for': waiting_for,
    }
    if '**BIGSTONE**' in line:
        item['text'] = item['text'].replace('**BIGSTONE**', '')
        item['bigstone'] = True
    states = {'_': 'todo', 'x': 'done'}
    state = states.get(item['text'][0])
    if state:
        item['text'] = item['text'][1:].strip()
        item['state'] = state
    if ':doc:' in item['text']:
        html_root = app.config['SOURCE_HTML_ROOT']
        item['text'] = re.sub(r':doc:`(.+?)`',
                              r'<a href="file://{0}\1.html">\1</a>'.format(html_root),
                              item['text'])

    time_pattern = re.compile(r'^\s*(\d{2}):(\d{2}) ')
    match_time = time_pattern.match(item['text'])
    if match_time:
        item.update(
            text = re.sub(time_pattern, '', item['text']),
            time = datetime.time(*(int(x) for x in match_time.groups())),
            fixed_time = True
        )

    est_pattern = re.compile(r'\((\d+[hm])\)')
    match_est = est_pattern.search(item['text'])
    if match_est:
        item.update(
            text = re.sub(est_pattern, '', item['text']),
            estimate = match_est.groups()[0]  # NOT group(0)! :(
        )


    contexts = 'pc', 'home', 'city'
    item['text'] = re.sub(r'@({0})'.format('|'.join(contexts)),
                          r'<span class="label"><i class="icon-white icon-globe"></i> \1</span>',
                          item['text'])
    item['text'] = re.sub(r'@([A-Za-z][A-Za-z0-9\-]+)',
                          r'<a href="#"><i class="icon-user"></i> \1</a>',
                          item['text'])
    item['text'] = re.sub(r'#([A-Za-z][A-Za-z0-9\-]+)',
                          r'<a href="#"><i class="icon-tasks"></i> \1</a>',
                          item['text'])
    return item


def extract_rst(date=None):
    date = date or datetime.date.today()  # XXX beware UTC vs local time
    root = app.config['SOURCE_RST_ROOT']
    day_dir = '{root}/{date.year}/{date.month:0>2}'.format(root=root, date=date)
    files = os.listdir(day_dir)
    docs = [f for f in files if f.endswith('.rst')]
    print docs
    today_fn = '{date.day:0>2}.rst'.format(date=date)
    print today_fn
    if today_fn not in docs:
        return []
    today_path = os.path.join(day_dir, today_fn)
    if date < datetime.date(2011,10,21):
        parse = extract_rst_v1
    else:
        parse = extract_rst_v2
    return parse(today_path)


def extract_rst_v1(path):

    sections = (u'Следующие действия', u'Календарь')
    sections_props = {
        u'Календарь': {'fixed_time': True},
#        u'Перенесенное со вчера': {'from_yesterday': True},
        u'Следующие действия': {},
#        u'Ожидание': {'waiting_for': True},
    }
#    data = dict((s,[]) for s in sections)
    data = []
    section = None
    context = None
    prev = None
    with codecs.open(path, encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip('\n')
            if not line.strip():
                continue
            elif garbage.match(line):
                continue
            elif line == u'нет':
                continue
            elif line in sections:
                print 'OK SECT', line
                # possible remainder from another section
                if prev:
                    data.append(parse_task_v1(prev, context, **sections_props[section]))
                    prev = None
                section = line
            elif line.startswith('@'):
                context = line
            elif line.startswith(' ') and not line.strip().startswith('['):
                # prev item continued
                print 'OK CONT', line
                assert prev
                prev= ' '.join([prev, line.strip()])
            elif section:
                print 'OK TASK', line
                if prev:
                    data.append(parse_task_v1(prev, context, **sections_props[section]))
                prev = line
            else:
                print "FAIL Don't know how to treat line", repr(line)
        # possible remainder
        if prev:
            data.append(parse_task_v1(prev, context, **sections_props[section]))

    return data


def extract_rst_v2(path):
    sections = {
        u'Календарь': {'fixed_time': True},
        u'Перенесенное со вчера': {'from_yesterday': True},
        u'Ежедневные дела': {},
        u'Разовые дела': {},
        u'Ожидание': {'waiting_for': True},
    }
    data = []
    section = None
    prev = None
    with codecs.open(path, encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip('\n')
            if not line.strip():
                continue
            elif garbage.match(line):
                continue
            elif line == u'нет':
                continue
            elif line in sections:
                print 'OK SECT', line
                # possible remainder from another section
                if prev:
                    data.append(parse_task_v2(prev, **sections[section]))
                    prev = None
                section = line
            elif line.startswith(' '):
                # prev item continued
                print 'OK CONT', line
                assert prev
                prev= ' '.join([prev, line.strip()])
            elif section:
                print 'OK TASK', line
                if prev:
                    data.append(parse_task_v2(prev, **sections[section]))
                prev = line
            else:
                print "FAIL Don't know how to treat line", repr(line)
        # possible remainder
        if prev:
            data.append(parse_task_v2(prev, **sections[section]))

    return data


@app.route('/')
@app.route('/<int:year>/<int:month>/<int:day>')
def day_view(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()
    items = extract_rst(date)
    prev = date - datetime.timedelta(days=1)
    next = date + datetime.timedelta(days=1)
    return render_template('index.html', items=items, date=date, prev=prev, next=next)


if __name__ == "__main__":
    app.config.from_pyfile('conf.py')
    app.run()
