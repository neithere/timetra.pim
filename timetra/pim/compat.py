import sys


PY3 = sys.version_info >= (3,)


def fix_strings_to_unicode(data):
    """ Recursively converts all `str` items to `unicode` within given dict.
    Motivation: PyYAML for Python 2.x interprets ASCII-only strings as bytes.
    """
    if PY3:
        return data

    if isinstance(data, str):
        return data.decode('utf-8')

    if isinstance(data, (list, tuple)):
        return [fix_strings_to_unicode(x) for x in data]

    if isinstance(data, dict):
        new_data = {}
        for k,v in data.items():
            new_data[k] = fix_strings_to_unicode(v)
        data = new_data

    return data


def decode(value):
    if PY3:
        return value
    else:
        value.decode('utf-8')


def encode(value):
    if PY3:
        return value
    else:
        return value.encode('utf-8')
