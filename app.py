#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime
import re

from flask import Flask

from flow import flow
from flow.providers import rstfiles
from flare import flare
from flare.providers import yamlfiles


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
        ('flare.day_full', u'Цепочки'),
    )

    app.register_blueprint(flow, url_prefix='/')
    app.register_blueprint(flare, url_prefix='/flare/')

    yaml_provider = yamlfiles.configure_provider(app)
    rst_provider = rstfiles.configure_provider(app)
    app.data_providers = [yaml_provider, rst_provider]

    @app.template_filter('hashtagify')
    def hashtags_filter(s):
        print 'replacing hashtags', s
        return replace_hashtags(s)

    app.jinja_env.globals['now'] = datetime.datetime.now

    return app


if __name__ == "__main__":
    app = make_app()
    app.run(port=6061)
