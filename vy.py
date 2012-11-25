import atexit
import curses
import time
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
            self.stdscr.addnstr(y, 0, buf.line(n), width)
            self.stdscr.clrtoeol()
        self.stdscr.refresh()
        return first_line

    def getkey(self):
        return self.stdscr.getch()


class Buffer:
    def __init__(self):
        self.lines = []

    def open(self, path):
        self.lines = []
        for l in open(path).readlines():
            self.lines.append(l[:-1])

    def line(self, n):
        return self.lines[n]

    def length(self):
        return len(self.lines)


def main(stdscr, argv):
    d = Display(stdscr)
    b = Buffer()
    b.open(argv[1])
    y = 0
    while True:
        y = d.show(b, y)
        c = d.getkey()
        if c == ord('k'):
            y -= 1
        if c == ord('j'):
            y += 1
        if c == ord('q'):
            break

if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
