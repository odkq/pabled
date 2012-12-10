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
import pygments
import pygments.lexers
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
            attributes = buffer[n]['attributes'][buffer.viewport['x0']:]
            text = buffer[n]['text'][buffer.viewport['x0']:]
            if len(attributes) != len(text):
                raise Exception
            for i in range(self.mx):
                if i < len(text):
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

# Default color scheme following vim defaults to
# have something to start with. It is interesting to
# observe the rough fiddling to get all the Name.*
# vim recognizes right in pygments (specially the
# distintion between self, wich is a 'pseudo builtin'
# and is not highlighted by vim and None, wich has the
# same type and _is_ highlighted by vim ... no way to
# workaround that :>

defcolschema = """Text white black
Whitespace black yellow
Error white red
Keyword.Namespace magenta black
Keyword yellow black
Name.Class cyan black
Name.Function cyan black
Name.Exception green black
Name.Builtin.Pseudo white black
Name.Builtin cyan black
Name white black
Literal.String.Escape magenta black
Literal red black
String red black
Number red black
Punctuation white black
Comment blue black
Other red black"""


class Highlighter:
    """ Class that fills the ncurses attributes of a text using Pygments """
    def __init__(self, buffer):
        self.b = buffer
        self.token_colors = {}
        # first scan uses all the text to determine the lexer
        t = self.b.extract_text(0, buffer.length())
        try:
            self.lexer = pygments.lexers.guess_lexer(t['text'])
        except pygments.util.ClassNotFound:
            # No lexer found
            self.lexer = None
        # ncurses colors table
        self.__colors = {'black': 0, 'red': 1, 'green': 2,
        'yellow': 3, 'blue': 4, 'magenta': 5, 'cyan': 6, 'white': 7}
        # default color scheme
        self.setcolorschema(defcolschema)

    def setcolorschema(self, text):
        i = 1   # First color pair settable is 1, 0 is fixed to white on black
        for token in text.split('\n'):
            tk = token.split()
            curses.init_pair(i, self.__colors[tk[1]], self.__colors[tk[2]])
            c = pygments.token.string_to_tokentype('Token.' + tk[0])
            self.token_colors[c] = {'color': curses.color_pair(i)}
            i += 1

    def __get_attribute_for_token_type(self, tokentype):
        ''' 'split' the token into it's hierarchy and search for
             it in order in the loaded dictionary '''
        types = tokentype.split()
        if types == None:
            return curses.color_pair(0)
        types.reverse()
        for tt in types:
            try:
                attribute = self.token_colors[tt]['color']
                return attribute
            except KeyError:
                pass
        return curses.color_pair(1)

    def scan(self, since, to):
        t = self.b.extract_text(since, to)
        index = 0
        for tokentype, value in self.lexer.get_tokens(t['text']):
            attribute = self.__get_attribute_for_token_type(tokentype)
            for i in range(len(value)):
                if (i + index) < len(t['attributes']):
                    t['attributes'][i + index] = attribute
            index += len(value)
        self.b.insert_text(t)


class Buffer:
    """ Loaded file with associated c and viewport positions """
    def __init__(self, x1, y1):
        self.lines = []
        self.cursor = {'x': 0, 'y': 0, 'max': 0}
        self.viewport = {'x0': 0, 'y0': 0, 'x1': x1, 'y1': y1}
        self.high = None

    def open(self, path):
        self.lines = []
        for l in open(path).readlines():
            self.lines.append({'text': l[:-1],
                    'attributes': ([curses.A_NORMAL] * (len(l) - 1))})

        self.high = Highlighter(self)
        self.high.scan(0, len(self.lines))

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
        """ Any deliberate movement left or right should reset the max """
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

    def extract_text(self, since, to):
        """ Return a dictionary with the addresses passed and
            a raw buffer "text" from a range of lines
            This text can be modified by a external function
            and reinserted with insert_text in place
        """
        t = ''
        a = []
        for n in range(since, to):
            t += self[n]['text'] + '\n'
            for at in self[n]['attributes']:
                a.append(at)
            a.append(curses.A_NORMAL)
            # +1 for the \n so both text and attributes have same length
        if len(t) != len(a):
            raise Exception(str(len(t)) + ' ' + str(len(a)) + ' ' + str(a))
        return {'since': since, 'to': to, 'text': t[:-1], 'attributes': a[:-1]}

    def insert_text(self, text):
        """ Fill the text and attributes in place """
        lines = text['text'].split('\n')
        if len(lines) != (text['to'] - text['since']):
            raise Exception
        index = text['since']
        cindex = 0
        for line in lines:
            attributes = text['attributes'][cindex:(cindex + len(line))]
            if len(attributes) != len(line):
                raise Exception
            cindex += len(line) + 1  # skip the padding curses.A_NORMAL
            self.lines[index] = {'text': line, 'attributes': attributes}
            index += 1


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


# default keybindings
def main(stdscr, argv):
    d = Display(stdscr)
    b = Buffer(d.mx - 1, d.my - 2)
    k = Keys()
    vy = Vy(d)
    b.open(argv[1])
    vy.add_buffer(b)
    vy.set_current(b)

    # Command mode commands
    k.bind(['k', '-', curses.KEY_UP, 16], b.cursor_up)
    k.bind(['j', '+', curses.KEY_DOWN, 14], b.cursor_down)
    k.bind(['h', curses.KEY_LEFT], b.cursor_left)
    k.bind(['l', ' ', curses.KEY_RIGHT], b.cursor_right)
    k.bind('/', vy.search)
    d.show(b)

    while True:
        c = d.getkey()
        k.process(c)
        d.status(str(b.cursor) + str(b.viewport) + str(int(c)))
        d.show(b)


if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
