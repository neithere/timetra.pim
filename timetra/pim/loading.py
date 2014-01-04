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

from monk.validation import validate
from monk.errors import ValidationError
from monk.modeling import DotExpandedDict
from monk.manipulation import merged as merge_defaults
import yaml

from . import compat
from . import models


def load_card(path, model):
    with open(path) as f:
        raw_card = yaml.load(f)

    card = compat.fix_strings_to_unicode(raw_card)

    if not card:
        return

    # populate defaults
    card = merge_defaults(model, card)

    card = DotExpandedDict(card)

    try:
        # XXX HACK
        card.concerns = [models.Concern(**x) for x in card.get('concerns') or []]

        validate(model, card)
    except (ValidationError, TypeError) as e:
        safe_path = compat.encode(path)
        raise type(e)('{path}: {e}'.format(path=safe_path, e=e))

    return card
