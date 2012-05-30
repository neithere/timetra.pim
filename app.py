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


def extract_rst(date=None):
    date = date or datetime.datetime.now().date()
    root = app.config['SOURCE_RST_ROOT']
    day_dir = '{root}/{date.year}/{date.month:0>2}'.format(root=root, date=date)
    files = os.listdir(day_dir)
    docs = [f for f in files if f.endswith('.rst')]
    print docs
    today_fn = '{date.day:0>2}.rst'.format(date=date)
    print today_fn
    sections = (u'Календарь', u'Перенесенное со вчера',  u'Разовые дела',
                u'Ожидание')
    if today_fn in docs:
        today_path = os.path.join(day_dir, today_fn)
        data = dict((s,[]) for s in sections)
        section = None
        prev = None
        with codecs.open(today_path, encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip('\n')
                if not line.strip():
                    continue
                elif garbage.match(line):
                    continue
                elif line == u'нет':
                    continue
                elif line in data:
                    print 'OK', line
                    section = line
                elif line.startswith(' '):
                    # prev item continued
                    print 'X prev continued:', line
                    assert prev
                    prev['text'] = ' '.join([prev['text'], line.strip()])
                elif section:
                    print 'OK', line
                    if prev:
                        data[section].append(prev)
                    item = {
                        'text': line,
                        'bigstone': False,
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

                    prev = item
                else:
                    print "Don't know how to treat line", line
            # possible remainder
            if prev:
                data[section].append(prev)

        return [(s, data[s]) for s in sections]


@app.route('/')
@app.route('/<int:year>/<int:month>/<int:day>')
def hello(year=None, month=None, day=None):
    if year and month and day:
        date = datetime.date(year, month, day)
    else:
        date = None
    sections = extract_rst(date)
    return render_template('index.html', sections=sections)


if __name__ == "__main__":
    app.config.from_pyfile('conf.py')
    app.run()
