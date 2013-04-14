# -*- coding: utf-8 -*-
import codecs
import datetime
import os
import re

import docutils.core
import yaml

from .base import BaseDataProvider
from models import Concern as Item, Plan, Document

from settings import get_app_conf


__all__ = ['get_day_plans']


garbage = re.compile(r'^[\-=]+$')


def parse_task(line, src_ver, context=None, from_yesterday=False, fixed_time=False,
               waiting_for=False, deadline=None):
    item = {
        'text': line,
        'bigstone': False,
        'from_yesterday': from_yesterday,
        'fixed_time': fixed_time,
        'waiting_for': waiting_for,
        'contexts': [],
        'deadline': deadline,
    }

    if context:
        item['contexts'].append(context)

    meta_pattern = re.compile(r'(^|\s)(?P<data>\{.+?\})(\s|$)')
    if meta_pattern.search(item['text']):
        print 'META'
        raw_meta = meta_pattern.search(item['text']).group('data')
        print '  raw:', repr(raw_meta)
        meta = yaml.load(raw_meta)
        print '  parsed:', meta
        item.update(meta)
        item['text'] = meta_pattern.sub('', item['text'])


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
            effort = match_est.groups()[0]  # NOT group(0)! :(
        )

#    item['text'] = replace_hashtags(item['text'])
    return item


def extract_items(path, src_ver=2, day=None):

    sections = {
        1: {
            u'Календарь': {'deadline': day},
            u'Следующие действия': {},
        },
        2: {
            u'Календарь': {'deadline': day},
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
    try:
        files = os.listdir(day_dir)
    except OSError:
        return []
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
    return extract_items(today_path, src_ver=src_ver, day=date)


def get_rst_files_list(root_dir, subdir):
    directory = os.path.join(root_dir, subdir)
    files = (f for f in os.listdir(directory) if f.endswith('.rst'))
    files = (f if isinstance(f, unicode) else f.decode('utf-8') for f in files)
    return sorted(name for name, ext in (os.path.splitext(f) for f in files))


def split_meta_data(raw_data):
    sep = '\n---\n'
    if raw_data is None:
        return {}, None
    if sep in raw_data:
        raw_meta, _, data = raw_data.partition('\n---\n')
        meta = yaml.load(raw_meta)
        return meta, data
    else:
        return {}, raw_data


def get_rst_file_parts(root_dir, subdir, slug):
    raw_data = read_rst_file(root_dir, subdir, slug)
    meta, data = split_meta_data(raw_data)
    meta.update(slug=slug)
    return meta, data


def get_rst_files_list_annotated(root_dir, subdir):
    """ Returns a list of metadata dictionaries for ReST files.
    """
    names = get_rst_files_list(root_dir, subdir)
    for name in names:
        meta, data = get_rst_file_parts(root_dir, subdir, name)
        if 'title' in meta:
            yield Document(**meta)
        else:
            # Quick and dirty: instead of fully rendering each document, just
            # snatch the title from the most probable location. This will fail
            # on some documents but the list will be rendered *much* faster.
            lines = data.split('\n')
            if re.match(r'^[\-=~]+$', lines[0]):
                # ReST document heading is decorated above and below
                title = lines[1]
            else:
                # ReST document heading is probably decorated only below
                title = lines[0]
            yield Document(title=title, **meta)


def read_rst_file(root_dir, subdir, slug):
    directory = os.path.join(root_dir, subdir)
    path = u'{root}/{slug}.rst'.format(root=directory, slug=slug)
    if not os.path.exists(path):
        print 'NO FILE', path
        return None
    with codecs.open(path, encoding='utf-8') as f:
        return f.read()


def render_rst_file(root_dir, subdir, slug):
    meta, raw_document = get_rst_file_parts(root_dir, subdir, slug)
    if raw_document is None:
        print 'NO FILE, NO RAW DOC'
        return None  #meta
    conf = dict(
        initial_header_level=2,
    )
    doc = docutils.core.publish_parts(raw_document, writer_name='html',
                                      settings_overrides=conf)
    #for key in doc.keys():
    #    if key in ('whole', 'stylesheet'):
    #        continue
    #    print
    #    print '-- ', key
    #    print doc[key]
    #    print
    #    print

    # many documents start with a fieldlist; docutils treat it as
    # document metadata and cuts out from the rest of the body.
    # we don't need this and simply staple them together:
    body = '\n'.join((doc['docinfo'], doc['body']))
    # unescape some HTML entities used later on in hashtags
    # (dunno how to do it in a cleaner way)
    body = body.replace('&#64;', '@').replace('','')
    meta.update(body=body)
    if not 'title' in meta:
        meta.update(title=doc['title'])
    return meta


class ReStructuredTextFilesProvider(BaseDataProvider):
    def __init__(self, root_dir):
        self.root_dir = root_dir

    @staticmethod
    def _transform_task(item):
        if item.get('time'):
            assert item.get('deadline')
            date_time = datetime.datetime.combine(item['deadline'], item['time'])
        else:
            date_time = None

        return Plan(
            action = item['text'],
            status = item.get('state', 'todo'),
            effort = item.get('effort'),
            time = date_time,
            context = item['contexts'],
            srcmeta = item,
        )

    def get_items(self, date=None, skip_archived=False):
        if skip_archived:
            import warnings
            warnings.warn('ReStructuredTextFilesProvider does not support skip_archived')
        plans = list(self.get_plans(date or datetime.date.today()))
        # все задачи объединены под одной пустой целью
        return [
            Item(
                note = None,
                risk = None,
                need = None,
                plan = plans  #[self._transform_task(x) for x in items]
            )
        ]

    def get_plans(self, date):
        plans = get_day_plans(self.root_dir, date)
        return (self._transform_task(x) for x in plans)

    def get_document_list(self, category):
        return get_rst_files_list_annotated(self.root_dir, category)

    def get_document(self, category, slug):
        slug = slug if isinstance(slug, unicode) else slug.decode('utf-8')
        return render_rst_file(self.root_dir, category, slug)


def configure_provider():
    conf = get_app_conf()
    root_dir = conf.x_flow.SOURCE_RST_ROOT
    return ReStructuredTextFilesProvider(root_dir)
