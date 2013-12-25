#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 vy - a small vi clone

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
        self.status_a = list([curses.A_NORMAL] * (self.mx - 3))
        self.status_t = list([' '] * (self.mx - 3))

    def update_line(self, y, attributes, text):
        if len(attributes) != len(text):
            raise Exception('{} {}'.format(len(attributes), len(text)))
        # If it is the last line, do not write in the last cell
        if y == (self.my - 1):
            r = self.mx - 1
        else:
            r = self.mx
        for i in range(r):
            if i < len(text):
                a = attributes[i]
                ch = text[i]
            else:
                ch = u' '
                a = curses.A_NORMAL
            self.stdscr.addstr(y, i, ch, a)
            #raise Exception('addch [{}] [{}] [{}] [{}]'.format(y, i, ch, a))

    def show(self, buffer):
        """ Refresh display after a motion command """
        for y in range(0, self.my - 1):
            n = y + buffer.viewport['y0']
            try:
                attributes = buffer[n]['attributes'][buffer.viewport['x0']:]
                text = buffer[n]['text'][buffer.viewport['x0']:]
            except IndexError:  # End of file
                attributes = [curses.A_NORMAL]
                text = '~'
            self.update_line(y, attributes, text)
        self.update_line(self.my - 1, self.status_a, self.status_t)
        rx = buffer.cursor['x'] - buffer.viewport['x0']
        ry = buffer.cursor['y'] - buffer.viewport['y0']
        self.stdscr.move(ry, rx)
        self.stdscr.refresh()

    def status(self, line):
        # position, line, length):
        self.stdscr.addnstr(self.my - 1, 0, line, self.mx - 1)

    def print_in_statusline(self, position, string, length):
        if position < 0:
            x = len(self.status_t) + position
        else:
            x = position
        # fill = ''.join([' ' * length])
        for i in range(len(string)):
            c = string[i]
            self.status_t[x + i] = c
        for i in range(len(string), length):
            self.status_t[x + i] = ' '
        # self.stdscr.addnstr(self.my - 1, x, string, length)

    def getkey(self):
        return get_char(self.stdscr)

    def getmaxy(self):
        return self.my


# Workaround for win.getch
# https://groups.google.com/forum/#!topic/comp.lang.python/Z9zjDwonQqY
# by Inigo Serna, modified to handle keys
def get_char(win):
    def get_check_next_byte():
        c = win.getch()
        if 128 <= c <= 191:
            return c
        else:
            raise UnicodeError

    bytes = []
    c = win.getch()
    if c <= 127:
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
    buf = ''.join([chr(b) for b in bytes])
    buf = buf.decode('utf-8')
    return buf


class Keys:
    """ Map c keys or key arrays to functions """
    def __init__(self):
        self.methods = {}
        self.default = {}
        self.methods[Buffer.COMMAND] = {}
        self.methods[Buffer.INSERT] = {}

    def bind(self, mode, key, method):
        if type(key) in (tuple, list):
            for i in key:
                self.bind(mode, i, method)
            return
        if type(mode) in (tuple, list):
            for m in mode:
                self.bind(m, key, method)
            return
        if type(key) == str:
            key = ord(key)
        if key is None:
            self.default[mode] = method
        else:
            self.methods[mode][key] = method

    def process(self, key, mode):
        try:
            method = self.methods[mode][key]
        except KeyError:
            method = self.default[mode]
        method(key)

    def setmode(self, mode):
        self.mode = mode

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
Name.Class green black
Name.Function green black
Name.Exception magenta black
Name.Builtin.Pseudo white black
Name.Builtin yellow black
Name white black
Literal.String.Escape red black
Literal red black
String cyan black
Number magenta black
Punctuation yellow black
Comment cyan black
Other red black"""


class Highlighter:
    """ Fills the ncurses attributes of a text using Pygments """
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
                         'yellow': 3, 'blue': 4, 'magenta': 5,
                         'cyan': 6, 'white': 7}
        # default color scheme
        self.setcolorschema(defcolschema)

    def setcolorschema(self, text):
        i = 1   # First color pair settable is 1, 0 is fixed to white on black
        for token in text.split('\n'):
            tk = token.split()
            c = pygments.token.string_to_tokentype('Token.' + tk[0])
            curses.init_pair(i, self.__colors[tk[1]], self.__colors[tk[2]])
            self.token_colors[c] = {'color': curses.color_pair(i)}
            i += 1

    def __get_attribute_for_token_type(self, tokentype):
        ''' 'split' the token into it's hierarchy and search for
             it in order in the loaded dictionary '''
        types = tokentype.split()
        if types is None:
            return curses.color_pair(0)
        types.reverse()
        for tt in types:
            try:
                attribute = self.token_colors[tt]['color']
                return attribute
            except KeyError:
                pass
        return curses.A_NORMAL
        # curses.color_pair(0)

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
    COMMAND = 0
    INSERT = 1
    """ Loaded file with associated c and viewport positions """
    def __init__(self, x1, y1, display):
        self.lines = []
        self.cursor = {'x': 0, 'y': 0, 'max': 0}
        self.viewport = {'x0': 0, 'y0': 0, 'x1': x1, 'y1': y1}
        self.height = y1
        self.high = None
        self.mode = self.COMMAND
        self.display = display

    def open(self, path):
        self.lines = []
        for l in open(path).readlines():
            self.lines.append({'text': list((l[:-1]).decode('utf-8')),
                               'attributes': ([curses.A_NORMAL] *
                                              (len(l) - 1))})

        self.high = Highlighter(self)
        self.high.scan(0, len(self.lines))

    def __getitem__(self, n):
        return self.lines[n]

    def length(self):
        return len(self.lines)

    def current_line(self):
        try:
            return self.lines[self.cursor['y']]['text']
        except IndexError:
            return ['']

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

    def cursor_up(c, k):
        if not c.cursor['y'] == 0:
            c.cursor['y'] -= 1
            c.__cursor_and_viewport_adjustement()

    def cursor_down(c, k):
        if (c.length() - 1) > c.cursor['y']:
            c.cursor['y'] += 1
            c.__cursor_and_viewport_adjustement()

    def __cursor_max_reset(c):
        """ Any deliberate movement left or right should reset the max """
        c.cursor['max'] = c.cursor['x']

    def cursor_left(c, k):
        if not c.cursor['x'] == 0:
            c.cursor['x'] -= 1
            c.__cursor_max_reset()
            c.__cursor_and_viewport_adjustement()

    def cursor_right(c, k):
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
            t += (''.join(self[n]['text'])) + '\n'
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
            raise Exception('insert_text(): lines to insert != range')
        index = text['since']
        cindex = 0
        for line in lines:
            attributes = text['attributes'][cindex:(cindex + len(line))]
            if len(attributes) != len(line):
                raise Exception('insert_text(): attributes != line')
            cindex += len(line) + 1  # skip the padding curses.A_NORMAL
            # Reinsert line as a list of chars (not string)
            self.lines[index] = {'text': list(line), 'attributes': attributes}
            index += 1

    def page_forward(self, key):
        ''' Avpag and move cursor vi-alike '''
        delta = self.height - 1
        if ((self.viewport['y0'] + delta) > len(self.lines)):
            delta = (len(self.lines) - self.viewport['y0'] - 1)
        self.viewport['y0'] += delta
        self.viewport['y1'] += delta
        self.cursor['y'] = self.viewport['y0']
        self.__cursor_and_viewport_adjustement()

    def page_backwards(self, key):
        delta = self.height - 1
        if ((self.viewport['y0'] - delta) < 0):
            delta = self.viewport['y0']
        self.viewport['y0'] -= delta
        self.viewport['y1'] -= delta
        if (self.viewport['y1'] > (len(self.lines) - 1)):
            self.cursor['y'] = len(self.lines) - 1
        else:
            self.cursor['y'] = self.viewport['y1']
        self.__cursor_and_viewport_adjustement()

    def cursor_to_eol(self, key):
        ''' Move Cursor to End-of-Line '''
        eol = len(self.current_line())
        self.cursor['x'] = (eol - 1) if eol > 0 else 0
        # End of line means end of all lines, thus ...
        self.cursor['max'] = self.cursor['x'] + 65536

    def cursor_to_bol(self, key):
        ''' Move to First Character in Line '''
        self.cursor['x'] = 0

    def refresh_status(self, display, ch):
        if type(ch) == unicode:
            ch = ch.encode('utf-8')

        if len(self.current_line()) <= 0:
            current_char = ' '
        else:
            current_char = self.current_line()[self.cursor['x']]
        i = '{}/{},{}/{} [{}] [{}]'.format(self.cursor['y'], len(self.lines),
                                           self.cursor['x'],
                                           len(self.current_line()),
                                           current_char, ch)
        display.print_in_statusline(-30, i, 30)

    def insert(self, key):
        if self.mode == self.COMMAND:
            self.mode = self.INSERT
            self.display.print_in_statusline(0, '-- INSERT --', 20)
        elif self.mode == self.INSERT:
            self.mode = self.COMMAND
            self.display.print_in_statusline(0, '-- COMMAND --', 20)

    def insert_element(self, array, position, element):
        array.append(' ')
        i = len(array) - 1
        while True:
            array[i] = array[i - 1]
            i -= 1
            if i == position:
                break
        array[position] = element

    def insert_char(self, key):
        char = key.encode('utf-8')
        #.('utf-8')
        self.display.print_in_statusline(40, '[{}]'.format(char), 10)
        # current_line = self.lines[self.cursor['y']]['text']
        index = self.cursor['x']
        self.insert_element(self.lines[self.cursor['y']]['text'], index, char)
        self.insert_element(self.lines[self.cursor['y']]['attributes'], index,
                            curses.A_NORMAL)
        self.cursor_right('@')

    def error(self, key):
        pass


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
    k.bind(b.COMMAND, [u'h', curses.KEY_LEFT], b.cursor_left)
    k.bind(b.COMMAND, [u'l', u' ', curses.KEY_RIGHT], b.cursor_right)
    k.bind(b.COMMAND, [curses.KEY_NPAGE, 6], b.page_forward)
    k.bind(b.COMMAND, [curses.KEY_PPAGE, 2], b.page_backwards)
    k.bind(b.COMMAND, [u'$', 70], b.cursor_to_eol)
    k.bind(b.COMMAND, [u'0', 72], b.cursor_to_bol)
    k.bind(b.COMMAND, [u'i'], b.insert)
    k.bind(b.COMMAND, [u'/'], vy.search)
    # Default command for the rest of keys
    k.bind(b.COMMAND, None, b.error)

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
    # Default comman for the rest of keys (insert char)
    k.bind(b.INSERT, None, b.insert_char)

    d.show(b)

    while True:
        key = d.getkey()
        k.process(key, b.mode)
        b.refresh_status(d, key)
        d.show(b)

if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
