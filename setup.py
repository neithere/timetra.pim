#!/usr/bin/env python
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

import io
import os

from setuptools import setup, find_packages


try:
    from setuptools.command.easy_install import ScriptWriter
except ImportError:
    pass
else:
    # monkey-patch script writer template to enable bash completion
    # in 'console_scripts' entries
    ScriptWriter.template = '# PYTHON_ARGCOMPLETE_OK\n' + ScriptWriter.template


with io.open(os.path.join(os.path.dirname(__file__), 'README'), encoding='ascii') as f:
    readme = f.read()


from timetra.pim import __version__


setup(
    # overview
    name = 'timetra.pim',
    description = ('Personal Information Manager with CLI + YAML'),
    long_description = readme,

    # technical info
    version = __version__,
    packages = find_packages(),
    #provides = ['timetra'],
    install_requires = [
        'blessings==1.5',
        'Flask==0.10.1',
        'monk==0.11.2',
        'prettytable==0.7.2',
        'python-dateutil==2.2',
        'PyYAML==3.10',
        'pyxdg==0.25',
    ],
    # usage example: http://stackoverflow.com/a/18879288/68097
    extras_require = {
        # curses TUI
        'curses': [
            'urwid==1.1.1',
        ],
        # pim.web.providers.ttlbooks
        'ttlbooks': [
            'rdflib==3.2.1',
        ],
    },
    include_package_data = True,
    zip_safe = False,
    entry_points = {
        'console_scripts': [
            'timetra-pim=timetra.pim.app:main'
        ],
    },

    # copyright
    author = 'Andrey Mikhaylenko',
    author_email = 'neithere@gmail.com',
    license = 'GNU Lesser General Public License (LGPL), Version 3',

    # more info
    url = 'https://github.com/neithere/timetra.pim',
    download_url = 'https://github.com/neithere/timetra.pim/archive/master.zip',

    # categorization
    keywords = ('cli command line diary pim personal information task manager'),
    classifiers  = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
