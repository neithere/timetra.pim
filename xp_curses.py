'''
test
Andy Mikhaylenko, 2012-07-01

Based on a table navigator example by Ian Ward
http://mail-archive.com/urwid@lists.excess.org/msg00897.html
'''
import urwid

from providers import DataProvidersManager
from providers import yamlfiles
from providers import rstfiles

import conf


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


if __name__ == '__main__':
    yaml_provider = yamlfiles.YAMLFilesProvider(conf.SOURCE_YAML_ROOT)
    rst_provider = rstfiles.ReStructuredTextFilesProvider(conf.SOURCE_RST_ROOT)
    data_providers = DataProvidersManager([yaml_provider, rst_provider])
    items = data_providers.get_items()

    items = (x for x in items if (x.risk or x.need) and not x.closed)

    #col_names = u'Type', u'Name', u'Opened'
    col_names = u'Name', u'Opened'
    elems = [#('risk' if x.risk else 'need',
             (x.risk or x.need,
              x.opened) for x in items]
    curses_app(col_names, elems)
