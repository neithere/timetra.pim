# coding: utf-8
#
#    Timetra is a time tracking application and library.
#    Copyright © 2010-2014  Andrey Mikhaylenko
#
#    This file is part of Timetra.
#
#    Timetra is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Timetra is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with Timetra.  If not, see <http://gnu.org/licenses/>.
#
"""
PIM application configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import sys
import xdg.BaseDirectory
from monk.modeling import DotExpandedDict
from monk.schema import optional

from . import caching


PY3 = sys.version_info >= (3,)
if PY3:
    unicode = str

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

