#!/usr/bin/env python
"""
 vy - a small vi-lish editor

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
import inspect
import curses
import locale
import sys

from hellfire import Buffer, Display, Keys


class Vy:
    def __init__(self, display):
        self.display = display
        self.buffers = []
        self.y = 0

    def add_buffer(self, buf):
        self.buffers.append(buf)

    def set_current(self, buf):
        self.current = buf

    def search(self):
        pass


def set_command_mode_keys(keys, buf):
    cmds = [
        # Command mode commands
        [[u'k', u'-', curses.KEY_UP, 16], 'cursor_up'],
        [[u'j', u'+', curses.KEY_DOWN, 14, 10], 'cursor_down'],
        [[u'h', curses.KEY_LEFT, 8], 'cursor_left'],
        [[u'l', u' ', curses.KEY_RIGHT], 'cursor_right'],
        [[curses.KEY_NPAGE, 6], 'page_forward'],
        [[curses.KEY_PPAGE, 2], 'page_backwards'],
        [[u'$', 70], 'cursor_to_eol'],
        [[72], 'cursor_to_bol'],  # 0 is handled by the set_count callback
        [[u'i'], 'insert'],
        [[u'x'], 'delete_char_at_cursor'],
        [[u'X'], 'delete_char_before_cursor'],
        [[u'J'], 'join'],
        [[u'a'], 'append'],
        [[u'n'], 'repeat_find_forward'],
        [[u'N'], 'repeat_find_backward'],
        [[u'/'], 'status'],
        [[u'?'], 'status'],
        [[u':'], 'status'],
        [[u'N'], 'repeat_find_backward'],
        [[u'V'], 'visual'],
        [[u'dd'], 'delete_line'],
        [None, 'error']
    ]
    bind_array(keys, Buffer.COMMAND, cmds, buf)


def set_status_mode_keys(keys, buf):
    cmds = [
        [[curses.KEY_UP], 'status_up'],
        [[curses.KEY_DOWN], 'status_down'],
        [[curses.KEY_LEFT], 'status_left'],
        [[curses.KEY_RIGHT], 'status_right'],
        [[10], 'status_enter'],
        [[27], 'status_cancel'],
        [[9], 'status_tab'],
        [[curses.KEY_BACKSPACE], 'status_backspace'],
        [[curses.KEY_DC], 'status_delete'],
        [None, 'status_insert']
    ]
    bind_array(keys, Buffer.STATUS, cmds, buf)


def set_insert_mode_keys(keys, buf):
    cmds = [
        # Insert mode commands
        [[curses.KEY_UP], 'cursor_up'],
        [[curses.KEY_DOWN], 'cursor_down'],
        [[curses.KEY_LEFT], 'cursor_left'],
        [[curses.KEY_RIGHT], 'cursor_right'],
        [[curses.KEY_NPAGE], 'page_forward'],
        [[curses.KEY_PPAGE], 'page_backwards'],
        [[70], 'cursor_to_eol'],
        [[72], 'cursor_to_bol'],
        [[27], 'insert'],
        [[curses.KEY_DC], 'delete_char_at_cursor'],
        [[curses.KEY_BACKSPACE, 8], 'delete_char_before_cursor'],
        [[10], 'enter'],
        [[9], 'tab'],
        # Default command for the rest of keys (insert char'],
        [None, 'insert_char']
    ]
    bind_array(keys, Buffer.INSERT, cmds, buf)


def bind_array(keys, mode, cmds, buf):
    for cmd in cmds:
        members = inspect.getmembers(buf, predicate=inspect.ismethod)
        for name, method in members:
            if name == cmd[1]:
                keys.bind(mode, cmd[0], method)
                break
        else:
            raise Exception('method {} does not exist'.format(cmd[1]))


def main(stdscr, argv):
    display = Display(stdscr)
    buf = Buffer(display.mx - 1, display.my - 2, display)
    keys = Keys()
    vy = Vy(display)
    buf.open(argv[1])
    buf.refresh_status(display, '@')
    vy.add_buffer(buf)
    vy.set_current(buf)
    set_command_mode_keys(keys, buf)
    set_status_mode_keys(keys, buf)
    set_insert_mode_keys(keys, buf)

    display.show(buf)

    while True:
        key = display.getkey()
        keys.process(key, buf.mode)
        if buf.mode != buf.STATUS:
            buf.refresh_status(display, key)
        display.show(buf)


# Entry point in setup.py for the /usr/bin/vy script
def main_curses():
    if len(sys.argv) < 2:
        print ('Usage: hf <file>')
        sys.exit(0)

    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(main, sys.argv)
