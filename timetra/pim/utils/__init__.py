# -*- coding: utf-8 -*-
from datetime import date, datetime, time
import sys
import termios
import tty


def to_date(obj):
    if isinstance(obj, datetime):
        return obj.date()
    if isinstance(obj, date):
        return obj
    raise TypeError('expected date or datetime, got {0}'.format(obj))


def to_datetime(obj):
    if isinstance(obj, datetime):
        return obj
    if isinstance(obj, date):
        return datetime.combine(obj, time(0))
    raise TypeError('expected date or datetime, got {0}'.format(obj))


def getch():
    # see http://code.activestate.com/recipes/134892/
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch
