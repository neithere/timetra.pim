# coding: utf-8

from __future__ import print_function
import functools
import os

import models
import settings
import formatting
#from flare import multikeysort
import caching
import loading



CATEGORIES = {
    'contacts': dict(model=models.CONTACT, sigil='@'),
    'assets': dict(model=models.ASSET, sigil='$'),
    'projects': dict(model=models.PROJECT, sigil='#'),
    'reference': dict(model={}, sigil='?'),
}


class PathDoesNotExist(ValueError):
    pass


def guess_file_path(index_path, pattern):
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
        slug = loading.fix_str_to_unicode(slug).lower()

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




def make_card_loader(fpath, model):
    return functools.partial(caching.get_cached_yaml_file, fpath, model)


def find_items(root_dir, model, pattern):
    # init return vars
    detail = None
    index = []
    guessed_path = None

    conf = settings.get_app_conf()

    pattern = loading.fix_str_to_unicode(pattern)

    index_path = os.path.join(conf.index, root_dir)
    if not os.path.exists(index_path):
        raise PathDoesNotExist(os.path.abspath(index_path))

    path = os.path.join(index_path, pattern)
    file_path = path + '.yaml'

    dir_exists = os.path.isdir(path)
    file_exists = os.path.isfile(file_path)

    if not any([dir_exists, file_exists]):
        file_path = guess_file_path(index_path, pattern)
        if file_path:
            file_exists = True
            guessed_path = file_path
        else:
            raise PathDoesNotExist(file_path)

    if file_exists:
        detail = file_path, make_card_loader(file_path, model)

    if dir_exists:
        files = collect_files(path)

        #if count:
        #    yield 'Found {0} documents'.format(len(list(files)))
        #    return

        for file_path in files:
            loader = make_card_loader(file_path, model)
            index.append((file_path, loader))

    return detail, index, guessed_path


def collect_files(path):
    def _walk():
        for root, dirs, files in os.walk(path):
            for f in sorted(files):
                if f.endswith('.yaml'):
                    yield loading.fix_str_to_unicode(os.path.join(root, f))
    return sorted(_walk())


def collect_concerns():
    for category in CATEGORIES:
        model = CATEGORIES[category]['model']
        detail, index, _ = find_items(category, model, pattern='')
        combined = ([detail] if detail else []) + (index or [])
        for path, loader in combined:
            card = loader()
            concerns = card.get('concerns', [])
            for concern in concerns:
                # HACK
                concern.context_card = card
                sigil = CATEGORIES[category]['sigil']
                concern.context = sigil + formatting.format_slug(category, path,
                                                                 nocolour=True)

                yield concern


def get_concerns(include_closed=False):
    items = collect_concerns()
    items = (x for x in items if (x.risk or x.need)
                             and (include_closed or not x.closed))
    #items = list(multikeysort(items, ['-acute', '-risk', 'frozen']))
    # XXX based on HACK in collect_concerns
    items = list(sorted(items, key=lambda x: x.context))
    return items
