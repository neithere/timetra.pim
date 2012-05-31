# -*- coding: utf-8 -*-
import codecs
import datetime
import os
import re


__all__ = ['get_day_plans']


garbage = re.compile(r'^[\-=]+$')

hashtag_to_css = {
    '@': 'user',      # contact
    '#': 'tasks',     # project
    '%': 'briefcase', # asset
}
regex_to_css = []
for hashtag, css_class in hashtag_to_css.items():
    regex = re.compile(r'(^|[^\w]){0}([A-Za-z][A-Za-z0-9_\-]+)'.format(hashtag))
    template = r'\1<a href="#"><i class="icon-{0}"></i>&nbsp;\2</a>'.format(css_class)
    regex_to_css.append((regex, template))


def replace_hashtags(text):

    for regex, template in regex_to_css:
        text = re.sub(regex, template, text)
    return text


def parse_task(line, src_ver, context=None, from_yesterday=False, fixed_time=False,
               waiting_for=False):
    item = {
        'text': line,
        'bigstone': False,
        'from_yesterday': from_yesterday,
        'fixed_time': fixed_time,
        'waiting_for': waiting_for,
        'contexts': [],
    }

    if context:
        item['contexts'].append(context)

    if '**BIGSTONE**' in line:
        item.update(
            text = item['text'].replace('**BIGSTONE**', ''),
            bigstone = True
        )

    # this is hack; ideally we should make a dedicated sigil
    # currently @context clashes with @contact
    contexts = 'pc', 'home', 'city', 'phone'
    for c in contexts:
        pattern = re.compile(r'([^\w])@({0})'.format(c))
        if pattern.search(item['text']):
            item['contexts'].append(c)
            item['text'] = pattern.sub('', item['text'])

    if src_ver == 1:
        states = {'[ ]': 'todo', '[x]': 'done'}
        for token, state in states.items():
            if token in item['text']:
                item.update(
                    text = item['text'].replace(token, ''),
                    state = state
                )
    elif src_ver == 2:
        states = {'_': 'todo', 'x': 'done'}
        state = states.get(item['text'][0])
        if state:
            item['text'] = item['text'][1:].strip()
            item['state'] = state
#        if ':doc:' in item['text']:
#            html_root = app.config['SOURCE_HTML_ROOT']
#            item['text'] = re.sub(r':doc:`(.+?)`',
#                                  r'<a href="file://{0}\1.html">\1</a>'.format(html_root),
#                                  item['text'])
    else:
        raise ValueError('unknown version {0}'.format(src_ver))

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


    item['text'] = replace_hashtags(item['text'])
    return item


def extract_items(path, src_ver=2):

    sections = {
        1: {
            u'Календарь': {'fixed_time': True},
            u'Следующие действия': {},
        },
        2: {
            u'Календарь': {'fixed_time': True},
            u'Перенесенное со вчера': {'from_yesterday': True},
            u'Ежедневные дела': {},
            u'Разовые дела': {},
            u'Ожидание': {'waiting_for': True},
        }
    }
    assert src_ver in sections

    section = None
    context = None
    prev = None

    def prepare_task():
        extra_props = sections[src_ver][section]
        return parse_task(prev, src_ver, context=context, **extra_props)

    with codecs.open(path, encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip('\n')
            if not line.strip():
                continue
            elif garbage.match(line):
                continue
            elif line == u'нет':
                continue
            elif line in sections[src_ver]:
                print 'OK SECT', line
                # possible remainder from another section
                if prev:
                    yield prepare_task()
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
                    yield prepare_task()
                prev = line
            else:
                print "FAIL Don't know how to treat line", repr(line)
        # possible remainder
        if prev:
            yield prepare_task()


def get_day_plans(root_dir, date=None):
    date = date or datetime.date.today()  # XXX beware UTC vs local time
    day_dir = '{root}/{date.year}/{date.month:0>2}'.format(root=root_dir, date=date)
    files = os.listdir(day_dir)
    docs = [f for f in files if f.endswith('.rst')]
    print docs
    today_fn = '{date.day:0>2}.rst'.format(date=date)
    print today_fn
    if today_fn not in docs:
        return []
    today_path = os.path.join(day_dir, today_fn)
    if date < datetime.date(2011, 10, 21):
        src_ver = 1
    else:
        src_ver = 2
    return extract_items(today_path, src_ver=src_ver)
