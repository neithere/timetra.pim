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

from __future__ import print_function
import functools
import os

from . import compat
from . import models
from . import settings
from . import formatting
#from flare import multikeysort
from . import caching



CATEGORIES = {
    'contacts': dict(model=models.contact_schema, sigil='@'),
    'assets': dict(model=models.asset_schema, sigil='$'),
    'projects': dict(model=models.project_schema, sigil='#'),
    'reference': dict(model={}, sigil='?'),
}


class PathDoesNotExist(ValueError):
    pass


def guess_file_path(index_path, pattern):
    "Expects a slug, returns the first file path that matches the slug"
    files = collect_files(index_path)

    first_dir_startswith = None
    first_slug_startswith = None
    first_slug_endswith = None
    first_slug_contains = None
    first_path_endswith = None
    first_path_contains = None

    # all tests below are case-insensitive
    pattern = pattern.lower()

    for file_path in files:
        directory, file_name = os.path.split(file_path)
        slug, _ = os.path.splitext(file_name)
        slug = compat.fix_strings_to_unicode(slug).lower()
        file_path_no_ext = os.path.splitext(file_path)[0]

        if slug == pattern:
            return file_path

        # `/foo/bar` matches `/foo/bar-123.yaml`
        # (precise path chunk; may yield directories though)
        relative_path = os.path.relpath(file_path, index_path)
        if not first_dir_startswith and relative_path.lower().startswith(pattern):
            first_dir_startswith = file_path

        # `bar` matches `/foo/bar-123.yaml`
        # (like above but prone to picking stuff from unexpected branches)
        if not first_slug_startswith and slug.startswith(pattern):
            first_slug_startswith = file_path

        # `quux` matches `/foo/bar-quux.yaml`
        if not first_slug_endswith and slug.endswith(pattern):
            first_slug_endswith = file_path

        # `bar` matches `/foo/embargo.yaml`
        if not first_slug_contains and pattern in slug:
            first_slug_contains = file_path

        # `bar/quux` matches `/foo/bar/quux.yaml`
        if not first_path_endswith and file_path_no_ext.endswith(pattern):
            first_path_endswith = file_path

        # `bar/quux` matches `/foo/bar/quux-123.yaml`
        if not first_path_contains and not pattern.endswith('/') and pattern in file_path_no_ext:
            first_path_contains = file_path


    return (first_dir_startswith or first_slug_startswith or first_slug_endswith
            or first_slug_contains or first_path_endswith or first_path_contains
            or None)




def make_card_loader(fpath, model):
    return functools.partial(caching.get_cached_yaml_file, fpath, model)


def find_items(root_dir, model, pattern):
    # init return vars
    detail = None
    index = []
    guessed_path = None

    conf = settings.get_app_conf()

    pattern = compat.fix_strings_to_unicode(pattern)

    index_path = os.path.join(conf.index, root_dir)
    if not os.path.exists(index_path):
        raise PathDoesNotExist(os.path.abspath(index_path))

    path = os.path.join(index_path, pattern)
    file_path = path + '.yaml'

    dir_exists = os.path.isdir(path)
    file_exists = os.path.isfile(file_path)

    if not any([dir_exists, file_exists]):
        guessed_path = guess_file_path(index_path, pattern)
        if guessed_path:
            file_exists = True
            file_path = guessed_path
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
                    yield compat.fix_strings_to_unicode(os.path.join(root, f))
    return sorted(_walk())


def collect_concerns():
    for category in CATEGORIES:
        model = CATEGORIES[category]['model']
        detail, index, _ = find_items(category, model, pattern='')
        combined = ([detail] if detail else []) + (index or [])
        for path, loader in combined:
            card = loader()
            assert card, path
            concerns = card.get('concerns') or []
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
