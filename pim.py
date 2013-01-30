#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import argh
from monk.validation import validate_structure, ValidationError
import os
import yaml

from settings import get_app_conf, ConfigurationError
import cli
import models
import formatting


def _fix_str_to_unicode(data):
    """ Converts all `str` items to `unicode` within given dict.
    Motivation: PyYAML for Python 2.x interprets ASCII-only strings as bytes.
    """
    if isinstance(data, str):
        return data.decode('utf-8')

    if isinstance(data, (list, tuple)):
        return [_fix_str_to_unicode(x) for x in data]

    if isinstance(data, dict):
        new_data = {}
        for k,v in data.items():
            new_data[k] = _fix_str_to_unicode(v)
        data = new_data

    return data


@argh.wrap_errors([ConfigurationError], processor=formatting.format_error)
def examine():
    conf = get_app_conf()

    yield 'examining {conf.index}...'.format(conf=conf)

    files_by_ext = {}

    vcs_dirs = '/.hg', '/.git', '/.svn'
    vcs_files = '.hgignore', '.gitignore'

    for root, dirs, files in os.walk(conf.index):
        if any(x in root for x in vcs_dirs):
            continue

        if any(x in root for x in conf.x_ignore):
            continue

        for name in files:
            if name in vcs_files:
                continue

#            yield root, files
            _, ext = os.path.splitext(name)
            files_by_ext.setdefault(ext, []).append(os.path.join(root, name))

        #yaml_files = [f for f in files if f.endswith('.yaml')]

#    yield files_by_ext
    for ext, files in files_by_ext.iteritems():
        yield '{ext}: {count}'.format(ext=(ext or 'no extension'), count=len(files))
        if len(files) < 10:    # <- an arbitrary threshold for marginal formats
            for f in files:
                yield '    {0}'.format(f)


class PathDoesNotExist(ValueError):
    pass


CATEGORIES = {
    'contacts': dict(model=models.CARD, sigil='@'),
    'assets': dict(model=models.ASSET, sigil='$'),
    'projects': dict(model=models.PROJECT, sigil='#'),
    'reference': dict(model={}, sigil='?'),
}

@argh.arg('pattern', nargs='?', default='')
@argh.arg('category', choices=list(CATEGORIES))
@argh.wrap_errors([ValidationError, PathDoesNotExist],
                  processor=formatting.format_error)
def view(category, pattern, count=False, detailed=False):
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

    conf = get_app_conf()

    pattern = _fix_str_to_unicode(pattern)

    index_path = os.path.join(conf.index, root_dir)
    if not os.path.exists(index_path):
        raise PathDoesNotExist(os.path.abspath(index_path))

    path = os.path.join(index_path, pattern)

    dir_exists = os.path.isdir(path)
    file_exists = os.path.isfile(path+'.yaml')

    if not any([dir_exists, file_exists]):
        raise PathDoesNotExist(path)

    if file_exists:
        with open(path + '.yaml') as f:
            card = yaml.load(f)
        for line in format_card(path, card, model):
            yield line

    if dir_exists:
        files = collect_files(path)

        if count:
            yield 'Found {0} documents'.format(len(list(files)))
            return

        for file_path in files:
            # display relative path without extension and with bold slug
            directory, filename = os.path.split(file_path)
            slug, _ = os.path.splitext(filename)
            if directory == index_path:
                path_repr = ''
            else:
                path_repr = os.path.relpath(directory, index_path)
            yield os.path.join(path_repr, formatting.t.bold(slug))

            if detailed:
                with open(file_path) as f:
                    card = yaml.load(f)
                for line in format_card(slug, card, model):
                    yield line


def collect_files(path):
    for root, dirs, files in os.walk(path):
        for f in sorted(files):
            if f.endswith('.yaml'):
                yield os.path.join(root, f)



def format_card(label, raw_card, model):
    card = _fix_str_to_unicode(raw_card)

    if not card:
        yield '    EMPTY'
        return

    try:
        validate_structure(model, card)
    except (ValidationError, TypeError) as e:
        raise type(e)(u'{label}: {e}'.format(label=label, e=e))

    for line in formatting.format_struct(card):
        yield line
    yield ''


def showconfig():
    conf = get_app_conf()
    for line in formatting.format_struct(conf):
        yield line


if __name__ == '__main__':
    argh.dispatch_commands([
        showconfig,
        examine,
        view,
        # these should be reorganized:
        cli.needs,
        cli.plans,
        cli.serve,
    ])
