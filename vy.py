#!/usr/bin/env python
"""
 vy - a small vi clone with some extras
 Copyright (C) 2012 Pablo Martin <pablo@odkq.com>

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
import sys


class Display:
    """ Abstract ncurses interface """
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.my, self.mx = self.stdscr.getmaxyx()

    def show(self, buffer):
        """ Refresh display after a motion command """
        for y in range(0, self.my - 1):
            n = y + buffer.viewport['y0']
            text = buffer[n]['text'][buffer.viewport['x0']:]
            attributes = None
            if buffer[n]['attributes'] != None:
                attributes = buffer[n]['attributes'][buffer.viewport['x0']:]
            text = buffer[n]['text'][buffer.viewport['x0']:]
            for i in range(self.mx):
                if i < len(text):
                    if attributes == None:
                        a = curses.A_NORMAL
                    else:
                        a = attributes[i]
                    ch = text[i]
                else:
                    ch = ' '
                    a = curses.A_NORMAL
                self.stdscr.addch(y, i, ch, a)
        rx = buffer.cursor['x'] - buffer.viewport['x0']
        ry = buffer.cursor['y'] - buffer.viewport['y0']
        self.stdscr.move(ry, rx)
        self.stdscr.refresh()

    def status(self, line):
        self.stdscr.addstr(self.my - 1, 0, line, self.mx - 1)

    def getkey(self):
        return self.stdscr.getch()


class Keys:
    """ Map c keys or key arrays to functions """
    def __init__(self):
        self.methods = [None] * curses.KEY_MAX

    def bind(self, key, method):
        if type(key) in (tuple, list):
            for i in key:
                self.bind(i, method)
            return
        if type(key) == str:
            key = ord(key)
        self.methods[key] = method

    def process(self, key):
        if not self.methods[key]:
            return 0
        method = self.methods[key]
        method()


class Buffer:
    """ Loaded file with associated c and viewport positions """
    def __init__(self, x1, y1):
        self.lines = []
        self.cursor = {'x': 0, 'y': 0, 'max': 0}
        self.viewport = {'x0': 0, 'y0': 0, 'x1': x1, 'y1': y1}

    def open(self, path):
        self.lines = []
        for l in open(path).readlines():
            self.lines.append({'text': l[:-1], 'attributes': None})

    def __getitem__(self, n):
        return self.lines[n]

    def length(self):
        return len(self.lines)

    def current_line(self):
        return self.lines[self.cursor['y']]['text']

    def __cursor_adjustement(c):
        """ If the next line does not have enough characters
            or the cursor to be positioned on the same x,
            adjust it and store the last position in cursor['max']
            restore position to cursor['max'] if after moving to
            the new line it fits
        """
        if len(c.current_line()) == 0:
            c.cursor['x'] = 0
        elif c.cursor['max'] > c.cursor['x']:
            if len(c.current_line()) >= c.cursor['max']:
                c.cursor['x'] = c.cursor['max']
            else:
                c.cursor['x'] = len(c.current_line()) - 1
        elif (len(c.current_line()) - 1) < c.cursor['x']:
            c.cursor['max'] = c.cursor['x']
            c.cursor['x'] = len(c.current_line()) - 1

    def __viewport_adjustement(c):
        if c.cursor['x'] > c.viewport['x1']:
            delta = c.cursor['x'] - c.viewport['x1']
            c.viewport['x0'] += delta
            c.viewport['x1'] += delta
        elif c.cursor['x'] < c.viewport['x0']:
            delta = c.viewport['x0'] - c.cursor['x']
            c.viewport['x1'] -= delta
            c.viewport['x0'] -= delta
        if c.cursor['y'] > c.viewport['y1']:
            delta = c.cursor['y'] - c.viewport['y1']
            c.viewport['y0'] += delta
            c.viewport['y1'] += delta
        elif c.cursor['y'] < c.viewport['y0']:
            delta = c.viewport['y0'] - c.cursor['y']
            c.viewport['y1'] -= delta
            c.viewport['y0'] -= delta

    def __cursor_and_viewport_adjustement(c):
        c.__cursor_adjustement()
        c.__viewport_adjustement()

    def cursor_up(c):
        if not c.cursor['y'] == 0:
            c.cursor['y'] -= 1
            c.__cursor_and_viewport_adjustement()

    def cursor_down(c):
        if (c.length() - 1) > c.cursor['y']:
            c.cursor['y'] += 1
            c.__cursor_and_viewport_adjustement()

    def __cursor_max_reset(c):
        """ Any deliverated movement left or right should reset the max """
        c.cursor['max'] = c.cursor['x']

    def cursor_left(c):
        if not c.cursor['x'] == 0:
            c.cursor['x'] -= 1
            c.__cursor_max_reset()
            c.__cursor_and_viewport_adjustement()

    def cursor_right(c):
        if (len(c.current_line()) - 1) > (c.cursor['x'] - c.viewport['x0']):
            c.cursor['x'] = c.cursor['x'] + 1
            c.__cursor_max_reset()
            c.__cursor_and_viewport_adjustement()


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
    b = Buffer(d.mx - 1, d.my - 2)
    k = Keys()
    vy = Vy(d)
    b.open(argv[1])
    vy.add_buffer(b)
    vy.set_current(b)

    # Command mode commands
    k.bind(['k', curses.KEY_UP], b.cursor_up)
    k.bind(['j', curses.KEY_DOWN], b.cursor_down)
    k.bind(['h', curses.KEY_LEFT], b.cursor_left)
    k.bind(['l', curses.KEY_RIGHT], b.cursor_right)
    k.bind('/', vy.search)
    d.show(b)

    while True:
        c = d.getkey()
        k.process(c)
        d.status(str(b.cursor) + str(b.viewport))
        d.show(b)


if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
