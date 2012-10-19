#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from argh import command, dispatch_command
from blessings import Terminal

from providers import DataProvidersManager
from providers import yamlfiles
from providers import rstfiles

from flare import multikeysort

import conf


t = Terminal()


def prepend(char, text):
    return u'{0} {1}'.format(char, text)


def indent(text):
    return prepend(text, ' ')


@command
def main(warm=False, acute=False):
    """ Displays a list of active risks and needs.
    """
    yaml_provider = yamlfiles.YAMLFilesProvider(conf.SOURCE_YAML_ROOT)
    rst_provider = rstfiles.ReStructuredTextFilesProvider(conf.SOURCE_RST_ROOT)
    data_providers = DataProvidersManager([yaml_provider, rst_provider])

    items = data_providers.get_items()
    items = (x for x in items if (x.risk or x.need) and not x.closed)
    items = list(multikeysort(items, ['-acute', '-risk', 'frozen']))
    for item in items:
        if acute and not item.acute:
            continue
        if warm and item.frozen:
            continue
        text = item.risk or item.need
        if item.acute:
            text = t.bold(text)
        if item.risk:
            text = t.red(text)
        yield prepend('*', text)
        #if item.plan:
        #    if not item.has_next_action():
        #        yield indent(u'запланировать')
        #    if not item.has_completed_action():
        #        yield indent(u'приступить')
        #    if item.is_waiting():
        #        yield indent(u'напомнить')
        #else:
        #    yield indent(u'запланировать')


if __name__ == '__main__':
    dispatch_command(main)
