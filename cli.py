#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

from argh import dispatch_commands
from blessings import Terminal

from providers import DataProvidersManager
from providers import yamlfiles
from providers import rstfiles

from flare import multikeysort

from settings import get_app_conf


t = Terminal()


def prepend(char, text):
    return u'{0} {1}'.format(char, text)


def indent(text):
    return prepend(text, ' ')


def get_needs():
    conf = get_app_conf()
    yaml_provider = yamlfiles.YAMLFilesProvider(conf.x_flow.SOURCE_YAML_ROOT)
    rst_provider = rstfiles.ReStructuredTextFilesProvider(conf.x_flow.SOURCE_RST_ROOT)
    data_providers = DataProvidersManager([yaml_provider, rst_provider])

    items = data_providers.get_items()
    items = (x for x in items if (x.risk or x.need) and not x.closed)
    items = list(multikeysort(items, ['-acute', '-risk', 'frozen']))

    return items


def needs(warm=False, acute=False):
    """ Displays a list of active risks and needs.
    """
    items = get_needs()
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
        if item.project:
            project_label = t.blue(item.project)
            text = prepend(project_label, text)
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


def plans(need_mask):
    """ Displays plans for the need that matches given mask.
    """
    items = get_needs()
    mask = need_mask.decode('utf-8').lower()
    for item in items:
        if (item.risk and mask in item.risk.lower()) or (item.need and mask in item.need.lower()):
            yield item.risk or item.need
            for plan in item.plan:
                yield u'[{0.status}] {0.action}'.format(plan)
            return
    else:
        yield 'Nothing found.'


def serve(port=6061):
    import web
    app = web.make_app()
    app.run(port=port)


def main():
    dispatch_commands([needs, plans, serve])


if __name__ == '__main__':
    main()
