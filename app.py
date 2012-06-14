#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import datetime

from flask import Flask

from flare import flare
from flare.providers import yamlfiles, rstfiles


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

    app.jinja_env.globals['now'] = datetime.datetime.now

    return app


if __name__ == "__main__":
    app = make_app()
    app.run(port=6062)
