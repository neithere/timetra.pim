#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import subprocess

import argh
from monk.validation import validate_structure, ValidationError
import os
import yaml

from settings import get_app_conf, ConfigurationError
import settings
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


nice_errors = argh.wrap_errors(
    [ValidationError, TypeError, PathDoesNotExist],
    processor=formatting.format_error)


CATEGORIES = {
    'contacts': dict(model=models.CARD, sigil='@'),
    'assets': dict(model=models.ASSET, sigil='$'),
    'projects': dict(model=models.PROJECT, sigil='#'),
    'reference': dict(model={}, sigil='?'),
}

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



def _guess_file_path(index_path, pattern):
    "Expects a slug, returns the first file path that matches the slug"
    files = collect_files(index_path)

    first_dir_startswith = None
    first_startswith = None
    first_endswith = None

    # all tests below are case-insensitive
    pattern = pattern.lower()

    for file_path in files:
        directory, file_name = os.path.split(file_path)
        slug, _ = os.path.splitext(file_name)
        slug = _fix_str_to_unicode(slug).lower()

        if slug == pattern:
            return file_path

        # `/foo/bar` matches `/foo/bar-123.yaml`
        # (precise path chunk; may yield directories though)
        relative_path = os.path.relpath(file_path, index_path)
        if not first_dir_startswith and relative_path.lower().startswith(pattern):
            first_dir_startswith = file_path

        # `bar` matches `/foo/bar-123.yaml`
        # (like above but prone to picking stuff from unexpected branches)
        if not first_startswith and slug.startswith(pattern):
            first_startswith = file_path

        # `quux` matches `/foo/bar-quux.yaml`
        if not first_endswith and slug.endswith(pattern):
            first_endswith = file_path

    return first_dir_startswith or first_startswith or first_endswith or None


def _show_items(root_dir, model, sigil, pattern, count=False, detailed=False):
    assert '..' not in pattern, 'look at you, hacker!'
    assert not pattern.startswith('/'), 'look at you, hacker!'

    conf = get_app_conf()

    pattern = _fix_str_to_unicode(pattern)

    index_path = os.path.join(conf.index, root_dir)
    if not os.path.exists(index_path):
        raise PathDoesNotExist(os.path.abspath(index_path))

    path = os.path.join(index_path, pattern)
    file_path = path + '.yaml'

    dir_exists = os.path.isdir(path)
    file_exists = os.path.isfile(file_path)

    if not any([dir_exists, file_exists]):
        file_path = _guess_file_path(index_path, pattern)
        if file_path:
            file_exists = True

            # guessing may be confusing so we tell user what we've picked
            yield formatting.t.blue(u'guessed: {0}'.format(file_path))
            yield ''
        else:
            raise PathDoesNotExist(file_path)

    if file_exists:
        with open(file_path) as f:
            card = yaml.load(f)
        try:
            for line in format_card(file_path, card, model):
                yield line
        except Exception as e:
            raise type(e)(u'{0}: {1}'.format(file_path, e))

    if dir_exists:
        files = collect_files(path)

        if count:
            yield 'Found {0} documents'.format(len(list(files)))
            return

        for file_path in files:
            # display relative path without extension and with bold slug
            directory, file_name = os.path.split(file_path)
            slug, _ = os.path.splitext(file_name)
            if not directory or directory == index_path:
                path_repr = ''
            else:
                path_repr = os.path.relpath(directory, index_path)
            yield os.path.join(path_repr, formatting.t.bold(slug))

            if detailed:
                with open(file_path) as f:
                    card = yaml.load(f)
                try:
                    for line in format_card(slug, card, model):
                        yield line
                except Exception as e:
                    raise type(e)(u'{0}: {1}'.format(file_path, e))


def collect_files(path):
    def _walk():
        for root, dirs, files in os.walk(path):
            for f in sorted(files):
                if f.endswith('.yaml'):
                    yield _fix_str_to_unicode(os.path.join(root, f))
    return sorted(_walk())


def format_card(label, raw_card, model):
    card = _fix_str_to_unicode(raw_card)

    if not card:
        yield '    EMPTY'
        return

    try:
        validate_structure(model, card)
    except (ValidationError, TypeError) as e:
        label = _fix_str_to_unicode(label)
        raise type(e)(u'{label}: {e}'.format(label=label, e=e))

    # XXX HACK
    if 'concerns' in card:
        concerns = card.pop('concerns')
    else:
        concerns = None

    for line in formatting.format_struct(card):
        yield line
    yield ''

    # XXX HACK
    if concerns:
        yield ''
        for concern in concerns:
            name = concern.get('risk', concern.get('need', concern.get('note')))

            if concern.get('closed'):
                state = '+'
            elif concern.get('frozen'):
                state = '*'
            elif concern.get('acute'):
                state = '!'
            else:
                state = ' '

            colors = {
                ' ': formatting.t.yellow,
                '+': formatting.t.green,
                '!': formatting.t.red,
                '*': formatting.t.blue,
            }
            wrapper = colors[state]
            yield wrapper(u'    [{0}] {1}'.format(state, formatting.t.bold(name)))
            plans = concern.get('plan', [])
            for plan in plans:
                # the logic here should be more complex, involving status field
                # concern itself also may not have "closed" but solved=True
                # here we just make sure 80% of cases work fine
                pstate = '+' if plan.get('closed') else ' '
                pwrapper = colors['+' if pstate == '+' else state]
                #pwrapper = formatting.t.green if pstate == 'x' else formatting.t.yellow
                pname = plan.get('action', '?')
                if '\n' in pname:
                    pname = pname.strip().partition('\n')[0] + u' [...]'
                if plan.get('delegated'):
                    pname = u'@{0}: {1}'.format(plan['delegated'], pname)
                yield pwrapper(u'        [{0}] {1}'.format(pstate, pname))
        yield ''


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
                guessed = _guess_file_path(category_path, pattern)
                if guessed:
                    path = guessed

    if not os.path.exists(path):
        raise PathDoesNotExist(path)

    yield 'Editing {0}'.format(path)
    subprocess.Popen([editor, path]).wait()


if __name__ == '__main__':
    argh.dispatch_commands([
        examine,
        show,
        edit,
        # these should be reorganized:
        cli.needs,
        cli.plans,
        cli.serve,
    ])
