#!/usr/bin/env python
"""
 vy - a small vi clone

 Copyright (C) 2012, 2013 Pablo Martin <pablo@odkq.com>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import curses
import locale
import sys

from vy import Buffer, Display, Keys


class Vy:
    def __init__(self, display):
        self.display = display
        self.buffers = []
        self.y = 0

    def add_buffer(self, buffer):
        self.buffers.append(buffer)

    def set_current(self, buffer):
        self.current = buffer

    def search(self):
        pass


def main(stdscr, argv):
    d = Display(stdscr)
    b = Buffer(d.mx - 1, d.my - 2, d)
    k = Keys()
    vy = Vy(d)
    b.open(argv[1])
    b.refresh_status(d, '@')
    vy.add_buffer(b)
    vy.set_current(b)

    # Command mode commands
    k.bind(b.COMMAND, [u'k', u'-', curses.KEY_UP, 16], b.cursor_up)
    k.bind(b.COMMAND, [u'j', u'+', curses.KEY_DOWN, 14, 10], b.cursor_down)
    k.bind(b.COMMAND, [u'h', curses.KEY_LEFT, 8], b.cursor_left)
    k.bind(b.COMMAND, [u'l', u' ', curses.KEY_RIGHT], b.cursor_right)
    k.bind(b.COMMAND, [curses.KEY_NPAGE, 6], b.page_forward)
    k.bind(b.COMMAND, [curses.KEY_PPAGE, 2], b.page_backwards)
    k.bind(b.COMMAND, [u'$', 70], b.cursor_to_eol)
    k.bind(b.COMMAND, [u'0', 72], b.cursor_to_bol)
    k.bind(b.COMMAND, [u'i'], b.insert)
    k.bind(b.COMMAND, [u'x'], b.delete_char_at_cursor)
    k.bind(b.COMMAND, [u'X'], b.delete_char_before_cursor)
    k.bind(b.COMMAND, [u'J'], b.join)
    k.bind(b.COMMAND, [u'a'], b.append)
    k.bind(b.COMMAND, [u'n'], b.repeat_find_forward)
    k.bind(b.COMMAND, [u'N'], b.repeat_find_backward)

    # Enter 'Status' mode with this commands
    k.bind(b.COMMAND, [u'/'], b.status)
    k.bind(b.COMMAND, [u'?'], b.status)
    k.bind(b.COMMAND, [u':'], b.status)
    # Default command for the rest of keys
    k.bind(b.COMMAND, None, b.error)

    # Statusline commands
    k.bind(b.STATUS, [curses.KEY_UP], b.status_up)
    k.bind(b.STATUS, [curses.KEY_DOWN], b.status_down)
    k.bind(b.STATUS, [curses.KEY_LEFT], b.status_left)
    k.bind(b.STATUS, [curses.KEY_RIGHT], b.status_right)
    k.bind(b.STATUS, [10], b.status_enter)
    k.bind(b.STATUS, [27], b.status_cancel)
    k.bind(b.STATUS, [9], b.status_tab)
    k.bind(b.STATUS, [curses.KEY_BACKSPACE], b.status_backspace)
    k.bind(b.STATUS, [curses.KEY_DC], b.status_delete)
    k.bind(b.STATUS, None, b.status_insert)

    # Insert mode commands
    k.bind(b.INSERT, [curses.KEY_UP], b.cursor_up)
    k.bind(b.INSERT, [curses.KEY_DOWN], b.cursor_down)
    k.bind(b.INSERT, [curses.KEY_LEFT], b.cursor_left)
    k.bind(b.INSERT, [curses.KEY_RIGHT], b.cursor_right)
    k.bind(b.INSERT, [curses.KEY_NPAGE], b.page_forward)
    k.bind(b.INSERT, [curses.KEY_PPAGE], b.page_backwards)
    k.bind(b.INSERT, [70], b.cursor_to_eol)
    k.bind(b.INSERT, [72], b.cursor_to_bol)
    k.bind(b.INSERT, [27], b.insert)
    k.bind(b.INSERT, [curses.KEY_DC], b.delete_char_at_cursor)
    k.bind(b.INSERT, [curses.KEY_BACKSPACE, 8], b.delete_char_before_cursor)
    k.bind(b.INSERT, [10], b.enter)
    k.bind(b.INSERT, [9], b.tab)
    # Default comman for the rest of keys (insert char)
    k.bind(b.INSERT, None, b.insert_char)

    d.show(b)

    while True:
        key = d.getkey()
        k.process(key, b.mode)
        if b.mode != b.STATUS:
            b.refresh_status(d, key)
        d.show(b)


# Entry point in setup.py for the /usr/bin/vy script
def main_curses():
    if len(sys.argv) < 2:
        print ('Usage: vy <file>')
        sys.exit(0)

    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(main, sys.argv)
