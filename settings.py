# -*- coding: utf-8 -*-
"""
PIM application configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import yaml
import xdg.BaseDirectory
from monk.modeling import DotExpandedDict
from monk import manipulation
from monk.validation import optional, validate_structure, ValidationError


APP_NAME = 'pim'


class ConfigurationError(RuntimeError):
    pass


def get_app_conf():
    filename = APP_NAME + '.yaml'
    path = os.path.join(xdg.BaseDirectory.xdg_config_home, filename)

    if not os.path.exists(path):
        raise ConfigurationError('File {0} not found'.format(path))

    defaults = {
        'index': '~/pim',
        #'configs': {},
        'x_ignore': list,   # TODO: remove this as soon as all is YAML?
        'contacts': 'contacts.yaml',
        # from older cli.py
        'x_flask': dict,
        'x_flow': optional({
            'SOURCE_HTML_ROOT': str,
            'SOURCE_RST_ROOT': str,
            'SOURCE_TTLBOOKS_ROOT': str,
            'SOURCE_YAML_ROOT': str,
        }),
    }

    with open(path) as f:
        conf = yaml.load(f)

    conf = manipulation.merged(defaults, conf)
    try:
        validate_structure(defaults, conf)
    except ValidationError as e:
        raise ConfigurationError('Configuration: {0}'.format(e))

    expandable = ('index',)
    for k in expandable:
        conf[k] = os.path.expanduser(conf[k])

    return DotExpandedDict(conf)

