#!/usr/bin/env python
import curses
from vy.line import Line

class Display:
    """ Abstract ncurses interface """
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.my, self.mx = self.stdscr.getmaxyx()
        self.status = Line(u' ' * (self.mx))

    def update_line(self, y, line):
        # If it is the last line, do not write in the last cell
        if y == (self.my - 1):
            r = self.mx - 1
        else:
            r = self.mx
        for i in range(r):
            if i < len(line):
                a = line[i].attr
                ch = line[i].ch
            else:
                ch = u' '
                a = curses.A_NORMAL
            if type(ch) == unicode:
                self.stdscr.addstr(y, i, ch.encode('utf-8'), a)
            elif type(ch) == str:
                self.stdscr.addstr(y, i, ch, a)

    def show(self, buffer):
        """ Refresh display after a motion command """
        for y in range(0, self.my - 1):
            n = y + buffer.viewport.y0
            self.update_line(y, buffer[n])
        self.update_line(self.my - 1, self.status)
        if buffer.mode != buffer.STATUS:
            rx = buffer.cursor.x - buffer.viewport.x0
            ry = buffer.cursor.y - buffer.viewport.y0
            self.stdscr.move(ry, rx)
        else:
            self.stdscr.move(self.my - 1, buffer.sx)
        self.stdscr.refresh()

    def status(self, line):
        self.stdscr.addnstr(self.my - 1, 0, line, self.mx - 1)

    def print_in_statusline(self, position, string, length):
        if position < 0:
            x = len(self.status) + position
        else:
            x = position
        for i in range(len(string)):
            c = string[i]
            self.status[x + i] = c
        for i in range(len(string), length):
            self.status[x + i] = ' '

    def clear_statusline(self):
        self.print_in_statusline(0, ' ', self.mx)

    def getkey(self):
        return get_char(self.stdscr)

    def getmaxy(self):
        return self.my


# Workaround for win.getch
# https://groups.google.com/forum/#!topic/comp.lang.python/Z9zjDwonQqY
# by Inigo Serna, modified to handle curses 'special keys'
def get_char(win):
    def get_check_next_byte():
        c = win.getch()
        if 128 <= c <= 191:
            return c
        else:
            raise UnicodeError

    bytes = []
    c = win.getch()
    if c < 32:
        # Control+char, return as is
        return c
    elif c <= 127:
        # 1 bytes
        bytes.append(c)
    elif 194 <= c <= 223:
        # 2 bytes
        bytes.append(c)
        bytes.append(get_check_next_byte())
    elif 224 <= c <= 239:
        # 3 bytes
        bytes.append(c)
        bytes.append(get_check_next_byte())
        bytes.append(get_check_next_byte())
    elif 240 <= c <= 244:
        # 4 bytes
        bytes.append(c)
        bytes.append(get_check_next_byte())
        bytes.append(get_check_next_byte())
        bytes.append(get_check_next_byte())
    else:   # Not an unicode string, but an encoded 'special key'
        return c
    buf = (''.join([chr(b) for b in bytes])).decode('utf-8')
    # raise Exception(buf.encode('utf-8'))
    return unicode(buf)

