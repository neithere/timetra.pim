#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import re

from flask import Flask

from providers import DataProvidersManager, rstfiles, yamlfiles
from flow import flow
from flare import flare


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


def make_app(conf_path='conf.py'):
    app = Flask(__name__)

    app.config.from_pyfile(conf_path)
    app.config.NAV_ITEMS = (
        ('flow.day_view', u'Планы'),
        ('flow.project_index', u'Проекты'),
        ('flow.asset_index', u'Имущество'),
        ('flow.contact_index', u'Контакты'),
        ('flow.reference_index', u'Справка'),
        ('flow.someday', u'Когда-нибудь'),
        ('flow.context_index', u'Контексты'),
        ('flare.day_full', u'Цепочки'),
        ('flare.item_index', u'Элементы'),
    )

    app.register_blueprint(flow, url_prefix='/')
    app.register_blueprint(flare, url_prefix='/flare/')

    yaml_provider = yamlfiles.configure_provider(app)
    rst_provider = rstfiles.configure_provider(app)
    app.data_providers = DataProvidersManager([yaml_provider, rst_provider])

    @app.template_filter('hashtagify')
    def hashtags_filter(s):
        return replace_hashtags(s)

    @app.template_filter('capfirst')
    def capfirst_filter(value):
        return value[0].upper() + value[1:] if value else value

    app.jinja_env.globals['now'] = datetime.datetime.now

    return app


if __name__ == "__main__":
    app = make_app()
    app.run(port=6061)
