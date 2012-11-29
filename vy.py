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
            n = y + buffer.viewport[0]
            width = self.mx
            self.stdscr.addnstr(y, 0, buffer[n], width)
            self.stdscr.clrtoeol()
        self.stdscr.refresh()
        return

    def status(self, line):
        self.stdscr.addstr(self.my, 0, line, self.mx - 1)

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
    """ Loaded file with cursor and viewport """
    def __init__(self):
        self.lines = []
        self.cursor = [0, 0]
        self.viewport = [0, 0]

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
        self.buffers = []
        self.y = 0

    def add_buffer(self, buffer):
        self.buffers.append(buffer)

    def set_current(self, buffer):
        self.current = buffer

    def cursor_up(self):
        self.current.viewport[0] -= 1

    def cursor_down(self):
        self.current.viewport[0] += 1

    def cursor_left(self):
        pass

    def cursor_right(self):
        pass


def main(stdscr, argv):
    d = Display(stdscr)
    b = Buffer()
    k = Keys()
    vy = Vy(d)
    b.open(argv[1])
    vy.add_buffer(b)
    vy.set_current(b)

    k.bind(['k', curses.KEY_UP], vy.cursor_up)
    k.bind(['j', curses.KEY_DOWN], vy.cursor_down)
    k.bind(['h', curses.KEY_LEFT], vy.cursor_left)
    k.bind(['l', curses.KEY_RIGHT], vy.cursor_right)

    d.show(b)

    while True:
        c = d.getkey()
        k.process(c)
        vy.y = d.show(b)


if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
