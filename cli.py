#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

from argh import dispatch_commands


def serve(port=6061):
    import web
    app = web.make_app()
    app.run(port=port)


def main():
    dispatch_commands([serve])


if __name__ == '__main__':
    main()
