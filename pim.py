#!/usr/bin/env python2
# coding: utf-8
# PYTHON_ARGCOMPLETE_OK
import os
import subprocess

import argh
import monk.validation

from settings import get_app_conf
import settings
import caching
import cli
from finder import CATEGORIES
import finder
import formatting
import processing
import reports
import stats




nice_errors = argh.wrap_errors(
    [monk.validation.ValidationError, TypeError, finder.PathDoesNotExist],
    processor=formatting.format_error)


@argh.arg('category', choices=list(CATEGORIES) + ['config'])
@argh.arg('pattern', nargs='?', default='')
@nice_errors
def show(category, pattern, count=False, detailed=False):
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
                            count=count, detailed=detailed):
        yield line



def _show_items(root_dir, model, sigil, pattern, count=False, detailed=False):
    assert '..' not in pattern, 'look at you, hacker!'
    assert not pattern.startswith('/'), 'look at you, hacker!'

    if pattern == '.':
        # use current directory as the pattern
        _, pattern = os.path.split(os.getcwdu())
        yield formatting.t.blue(u'from current directory: {0}'.format(pattern))

    detail, index, guessed_path = finder.find_items(root_dir, model, pattern)

    if guessed_path:
        # guessing may be confusing so we tell user what we've picked
        yield formatting.t.blue(u'guessed: {0}'.format(guessed_path))
        yield ''

    if detail:
        file_path, card_loader = detail
        try:
            card = card_loader()
            for line in formatting.format_card(file_path, card, model,
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

    pattern = pattern.decode('utf-8')

    if category == 'config':
        path = settings.get_conf_path()
    else:
        conf = get_app_conf()
        category_path = os.path.join(conf.index, category)
        path = os.path.join(category_path, pattern)
        if not os.path.exists(path):
            if os.path.exists(path + '.yaml'):
                path = path + '.yaml'
            else:
                guessed = finder.guess_file_path(category_path, pattern)
                if guessed:
                    path = guessed

    if not os.path.exists(path):
        raise finder.PathDoesNotExist(path)

    yield u'Editing {0}'.format(path)
    subprocess.Popen([editor, path]).wait()


if __name__ == '__main__':
    parser = argh.ArghParser()
    parser.add_commands([
        show,
        edit,
        # these should be reorganized:
        cli.serve,
    ])
    parser.add_commands(processing.commands, namespace='process')
    parser.add_commands(reports.commands, namespace='report')
    parser.add_commands(caching.commands, namespace='cache')
    parser.add_commands(stats.commands, namespace='stat')
    parser.dispatch()
