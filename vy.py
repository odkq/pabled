import curses
import sys


class Display:
    def __init__(self, stdscr):
        self.cursor = [0, 0]
        self.stdscr = stdscr

    def show(self, buf, first_line):
        my, mx = self.stdscr.getmaxyx()
        if (first_line > buf.length() - my):
            first_line = buf.length() - my
        if (first_line < 0):
            first_line = 0
        for y in range(0, my):
            n = first_line + y
            width = mx
            # The last character in the bottom right ?
            if y == my - 1:
                width -= 1  # non addressable
            self.stdscr.addnstr(y, 0, buf[n], width)
            self.stdscr.clrtoeol()
        self.stdscr.refresh()
        return first_line

    def getkey(self):
        return self.stdscr.getch()


class Keys:
    """ Map cursor keys or key arrays to functions """
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
    def __init__(self):
        self.lines = []

    def open(self, path):
        self.lines = []
        for l in open(path).readlines():
            self.lines.append(l[:-1])

    def __getitem__(self, n):
        return self.lines[n]

    def length(self):
        return len(self.lines)


class Vy:
    def __init__(self, display):
        self.display = display
        self.y = 0

    def set_viewable(self, buffer):
        self.viewable = buffer

    def cursor_up(self):
        self.y -= 1

    def cursor_down(self):
        self.y += 1


def main(stdscr, argv):
    d = Display(stdscr)
    b = Buffer()
    k = Keys()
    vy = Vy(d)
    b.open(argv[1])
    vy.set_viewable(b)

    k.bind(['k', curses.KEY_UP], vy.cursor_up)
    k.bind(['j', curses.KEY_DOWN], vy.cursor_down)
    d.show(b, 0)
    while True:
        c = d.getkey()
        k.process(c)
        vy.y = d.show(b, vy.y)


if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
