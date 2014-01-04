# coding: utf-8
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
