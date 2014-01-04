#!/usr/bin/env python
# coding: utf-8
# PYTHON_ARGCOMPLETE_OK
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

import os
import subprocess

import argh
import monk.errors

from .settings import get_app_conf
from . import settings
from . import caching
from .finder import CATEGORIES
from . import finder
from . import formatting
from . import processing
from . import reports
from . import stats
from . import compat


nice_errors = argh.wrap_errors(
    [monk.errors.ValidationError, TypeError, finder.PathDoesNotExist],
    processor=formatting.format_error)


@argh.arg('category', choices=list(CATEGORIES) + ['config'])
@argh.arg('pattern', nargs='?', default='')
@nice_errors
def show(category, pattern, count=False, detailed=False, full=False):
    # NOTE: --detailed shows *everything* including nested fields like concerns
    # (and they look horrible), while --full is passed down to the formatter to
    # print a more complete version of a long field, however some fields may be
    # hidden with --full.  Yes, this is confusing.  Yes, it needs refactoring.

    if category == 'config':
        for line in showconfig():
            yield line
        return

    if category not in CATEGORIES:
        raise ValueError('expected category from {0}'
                         .format(', '.join(CATEGORIES)))
    model = CATEGORIES[category]['model']
    sigil = CATEGORIES[category]['sigil']
    for line in _show_items(category, model, sigil, pattern,
                            count=count, detailed=detailed, full=full):
        yield line



def _show_items(root_dir, model, sigil, pattern, count=False, detailed=False, full=False):
    assert '..' not in pattern, 'look at you, hacker!'
    assert not pattern.startswith('/'), 'look at you, hacker!'

    if pattern == '.':
        # use current directory as the pattern
        _, pattern = os.path.split(os.getcwdu())
        yield formatting.t.blue(u'from current directory: {0}'.format(pattern))

    detail, index, guessed_path = finder.find_items(root_dir, model, pattern)

    if count:
        yield 1 if detail else len(index)
        return

    if guessed_path:
        # guessing may be confusing so we tell user what we've picked
        yield formatting.t.blue(u'guessed: {0}'.format(guessed_path))
        yield ''

    if detail:
        file_path, card_loader = detail
        try:
            card = card_loader()
            for line in formatting.format_card(file_path, card, model, full=full,
                                               hide_long_fields = not detailed):
                yield line
        except Exception as e:
            raise type(e)(u'{0}: {1}'.format(file_path, e))

    for file_path, card_loader in index:
        slug = formatting.format_slug(root_dir, file_path)
        yield slug
        if detailed:
            try:
                card = card_loader()
                for line in formatting.format_card(slug, card, model):
                    yield line
            except Exception as e:
                raise type(e)(u'{0}: {1}'.format(file_path, e))

def showconfig():
    conf = get_app_conf()
    for line in formatting.format_struct(conf):
        yield line


@argh.arg('category', choices=list(CATEGORIES) + ['config'])
@argh.arg('pattern', nargs='?', default='')
@nice_errors
def edit(category, pattern):
    editor = os.getenv('EDITOR')
    assert editor, 'env variable $EDITOR must be set'

    pattern = compat.decode(pattern)

    if category == 'config':
        path = settings.get_conf_path()
    else:
        conf = get_app_conf()
        category_path = os.path.join(conf.index, category)
        path = os.path.join(category_path, pattern)

        # prefer files to directories
        if os.path.exists(path + '.yaml'):
            path = path + '.yaml'

        if not os.path.exists(path):
            guessed = finder.guess_file_path(category_path, pattern)
            if guessed:
                path = guessed

    if not os.path.exists(path):
        raise finder.PathDoesNotExist(path)

    yield u'Editing {0}'.format(path)
    subprocess.Popen([editor, path]).wait()


@argh.named('serve')
def web_serve(port=6061):
    import web
    app = web.make_app()
    app.run(port=port)


def main():
    parser = argh.ArghParser()
    parser.add_commands([
        show,
        edit,
    ])
    parser.add_commands(processing.commands, namespace='process')
    parser.add_commands(reports.commands, namespace='report')
    parser.add_commands(caching.commands, namespace='cache')
    parser.add_commands(stats.commands, namespace='stat')
    parser.add_commands([web_serve], namespace='web')
    parser.dispatch()


if __name__ == '__main__':
    main()
