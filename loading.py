# coding: utf-8

from monk.validation import validate_structure, ValidationError
from monk.modeling import DotExpandedDict
import yaml

import models


def fix_str_to_unicode(data):
    """ Converts all `str` items to `unicode` within given dict.
    Motivation: PyYAML for Python 2.x interprets ASCII-only strings as bytes.
    """
    if isinstance(data, str):
        return data.decode('utf-8')

    if isinstance(data, (list, tuple)):
        return [fix_str_to_unicode(x) for x in data]

    if isinstance(data, dict):
        new_data = {}
        for k,v in data.items():
            new_data[k] = fix_str_to_unicode(v)
        data = new_data

    return data


def load_card(path, model):
    with open(path) as f:
        raw_card = yaml.load(f)

    card = fix_str_to_unicode(raw_card)

    if not card:
        return

    card = DotExpandedDict(card)
    # XXX HACK
    if 'concerns' in card:
        card.concerns = [models.Concern(**x) for x in card.concerns]

    try:
        validate_structure(model, card)
    except (ValidationError, TypeError) as e:
        raise type(e)(u'{path}: {e}'.format(path=path, e=e))

    return card
