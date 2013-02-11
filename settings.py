# -*- coding: utf-8 -*-
"""
PIM application configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import xdg.BaseDirectory
from monk.modeling import DotExpandedDict
from monk.validation import optional

import caching


APP_NAME = 'pim'

__CACHE = {}


class ConfigurationError(RuntimeError):
    pass


def get_conf_path():
    filename = APP_NAME + '.yaml'
    return os.path.join(xdg.BaseDirectory.xdg_config_home, filename)


def get_app_conf():
    if __CACHE.get('app_conf'):
        return __CACHE['app_conf']

    path = get_conf_path()

    if not os.path.exists(path):
        raise ConfigurationError('File {0} not found'.format(path))

    defaults = {
        'index': unicode,  # e.g. ~/pim
        #'configs': {},
        'x_ignore': list,   # TODO: remove this as soon as all is YAML?
        # from older cli.py
        'flask': dict,
        'x_flow': optional({
            'SOURCE_HTML_ROOT': unicode,
            'SOURCE_RST_ROOT': unicode,
            'SOURCE_TTLBOOKS_ROOT': unicode,
            'SOURCE_YAML_ROOT': unicode,
        }),
    }

#    with open(path) as f:
#        conf = yaml.load(f)

    conf = caching.get_cached_yaml_file(path, defaults)

#    conf = manipulation.merged(defaults, conf)
#    try:
#        validate_structure(defaults, conf)
#    except ValidationError as e:
#        raise ConfigurationError('Configuration: {0}'.format(e))

    expandable = ('index',)
    for k in expandable:
        conf[k] = os.path.expanduser(conf[k])

    result = DotExpandedDict(conf)
    __CACHE['app_conf'] = result
    return result

