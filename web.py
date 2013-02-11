#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from collections import namedtuple
import datetime
from dateutil.relativedelta import relativedelta
import docutils
import re

from flask import Flask

from providers import DataProvidersManager, rstfiles, yamlfiles, ttlbooks
from flow import flow
from flare import flare
import utils.formatdelta

from settings import get_app_conf


# hashtag-related stuff should be done via template filters
hashtags = (
    dict(sigil='@', url_base='/contacts/', css='user'),
    dict(sigil='#', url_base='/projects/', css='folder-open'),
    dict(sigil='%', url_base='/assets/', css='briefcase'),
    dict(sigil='\?', url_base='/reference/', css='book'),
)
regex_to_css = []
for hashtag in hashtags:
    regex = re.compile(ur'(^|[>\(\s]){0}([A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9_\-]+)'.format(hashtag['sigil']))
    template = ur'\1<a href="{0}\2"><i class="icon-{1}"></i>&nbsp;\2</a>'.format(
        hashtag['url_base'], hashtag['css'])
    regex_to_css.append((regex, template))


def replace_hashtags(text):

    for regex, template in regex_to_css:
        text = re.sub(regex, template, text)
    return text

def rst_to_html(text):
    """ Returns a HTML representation of given ReST string.
    """
    if not '\n\n' in text:
        # ignore single-line items (a better way would be to only parse inline
        # markup in such cases but it needs some research)
        return text

    conf = dict(
        initial_header_level=2,
    )
    doc = docutils.core.publish_parts(text, writer_name='html',
                                      settings_overrides=conf)
    # many documents start with a fieldlist; docutils treat it as
    # document metadata and cuts out from the rest of the body.
    # we don't need this and simply staple them together:
    body = '\n'.join((doc['docinfo'], doc['body']))
    # unescape some HTML entities used later on in hashtags
    # (dunno how to do it in a cleaner way)
    body = body.replace('&#64;', '@').replace('','')

    return body

def make_app():
    app = Flask(__name__)

    pim_conf = get_app_conf()
    app.config.update(pim_conf.flask)

    Item = namedtuple('Item', 'endpoint label icon')
    Dropdown = namedtuple('Dropdown', 'label items')
    divider = None

    app.config.NAV_ITEMS = (
        Item('flare.day_notes', u'Входящие', 'inbox'),
        Item('flare.item_index', u'Заботы', 'pushpin'),  # concerns
        divider,
        Item('flow.project_index', u'Проекты', 'folder-open'),
        Item('flow.asset_index', u'Имущество', 'briefcase'),
        Item('flow.contact_index', u'Контакты', 'user'),
        Item('flow.reference_index', u'Справка', 'book'),
        divider,
        Dropdown(u'More', (
            Item('flare.day_tasks', u'Планы', 'tasks'),
            #---
            Item('flow.context_index', u'Контексты', 'map-marker'),
            #---
            Item('flare.item_timeline', u'Лента', ''),
            Item('flare.day_full', u'Цепочки', ''),
            Item('flare.someday', u'Когда-нибудь', ''),
        ))
    )

    app.register_blueprint(flow, url_prefix='/')
    app.register_blueprint(flare, url_prefix='/flare/')

    yaml_provider = yamlfiles.configure_provider()
    rst_provider = rstfiles.configure_provider()
    books_provider = ttlbooks.configure_provider()
    app.data_providers = DataProvidersManager([yaml_provider, rst_provider,
                                               books_provider])

    @app.template_filter('hashtagify')
    def hashtags_filter(s):
        return replace_hashtags(s)

    @app.template_filter('capfirst')
    def capfirst_filter(value):
        return value[0].upper() + value[1:] if value else value

    app.template_filter('render_rst')(rst_to_html)

    app.jinja_env.globals['now'] = datetime.datetime.utcnow
    app.jinja_env.globals['relativedelta'] = relativedelta
    app.jinja_env.globals['render_delta'] = utils.formatdelta.render_delta

    return app


if __name__ == "__main__":
    app = make_app()
    app.run(port=6061)
