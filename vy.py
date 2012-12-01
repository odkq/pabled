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
            width = self.mx
            self.stdscr.addnstr(y, 0, buffer[n], width)
            self.stdscr.clrtoeol()
        self.stdscr.move(buffer.cursor['y'], buffer.cursor['x'])
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
    """ Loaded file with associated cursor and viewport positions """
    def __init__(self):
        self.lines = []
        self.cursor = {'x': 0, 'y': 0, 'max': 0}
        self.viewport = {'x0': 0, 'y0': 0, 'x1': 0, 'y1': 0}

    def open(self, path):
        self.lines = []
        for l in open(path).readlines():
            self.lines.append(l[:-1])

    def __getitem__(self, n):
        return self.lines[n]

    def length(self):
        return len(self.lines)

    def current_line(self):
        return self.lines[self.cursor['y']]


class Vy:
    def __init__(self, display):
        self.display = display
        self.buffers = []
        self.y = 0

    def add_buffer(self, buffer):
        self.buffers.append(buffer)

    def set_current(self, buffer):
        self.current = buffer

    def cursor_adjustement(self):
        c = self.current
        # If the next line does not have enough characters
        # for the cursor to be positioned on the same x,
        # adjust it and store the last position in cursor[2]
        if c.cursor['max'] > c.cursor['x']:
            if len(c.current_line()) >= c.cursor['max']:
                c.cursor['x'] = c.cursor['max']
            else:
                c.cursor['x'] = len(c.current_line())
        else:
            if len(c.current_line()) < c.cursor['x']:
                c.cursor['max'] = c.cursor['x']
                c.cursor['x'] = len(c.current_line())

    def cursor_up(self):
        c = self.current
        if c.cursor['y'] == 0:
            return
        self.current.cursor['y'] -= 1
        self.cursor_adjustement()

    def cursor_down(self):
        c = self.current
        if c.length() <= self.current.cursor['y']:
            return
        self.current.cursor['y'] += 1
        self.cursor_adjustement()

    def cursor_left(self):
        c = self.current
        if c.cursor['x'] == 0:
            return
        c.cursor['x'] -= 1
        c.cursor['max'] = c.cursor['x']

    def cursor_right(self):
        c = self.current
        if len(c.current_line()) == (c.cursor['x'] - c.viewport['x0']):
            return
        c.cursor['x'] = c.cursor['x'] + 1
        c.cursor['max'] = c.cursor['x']

    def search(self):
        pass


def main(stdscr, argv):
    d = Display(stdscr)
    b = Buffer()
    k = Keys()
    vy = Vy(d)
    b.open(argv[1])
    vy.add_buffer(b)
    vy.set_current(b)

    # Command mode commands
    k.bind(['k', curses.KEY_UP], vy.cursor_up)
    k.bind(['j', curses.KEY_DOWN], vy.cursor_down)
    k.bind(['h', curses.KEY_LEFT], vy.cursor_left)
    k.bind(['l', curses.KEY_RIGHT], vy.cursor_right)
    k.bind('/', vy.search)
    d.show(b)

    while True:
        c = d.getkey()
        k.process(c)
        vy.y = d.show(b)


if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
