#!/usr/bin/env python
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
'''
test
Andy Mikhaylenko, 2012-07-01 and 2013-04-14

Based on a table navigator example by Ian Ward
http://mail-archive.com/urwid@lists.excess.org/msg00897.html
'''
# 3rd-party
import urwid

# this app
import finder


def curses_app(col_names, elems):
    def cols(values):
        return urwid.Columns([
            urwid.Text(unicode(x), wrap='clip') for x in values
        ])

    legend = cols(col_names)

    #status = urwid.Text(u'Feeling fine')

    class Row(urwid.WidgetWrap):
        def __init__(self, values):
            # wrap in AttrMap to hilight when selected
            super(Row, self).__init__(
                urwid.AttrMap(cols(values), None, 'reversed'))

        def selectable(self):
            # these widgets want the focus
            return True

        def keypress(self, size, key):
            # handle keys as you will
            return key

    rows = [Row(cells) for cells in elems]

    listbox = urwid.ListBox(urwid.SimpleListWalker(rows))
    top = urwid.Frame(listbox, header=legend)  #, footer=status)

    palette = [
        ('reversed', 'standout', '')
    ]

    urwid.MainLoop(top, palette).run()


def main():
    items = finder.get_concerns()

    #col_names = u'Type', u'Name', u'Opened'
    col_names = u'Name', u'Opened'
    elems = [#('risk' if x.risk else 'need',
             (x.risk or x.need,
              x.opened) for x in items]
    curses_app(col_names, elems)


if __name__ == '__main__':
    main()
