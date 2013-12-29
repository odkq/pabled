#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import pygments
import pygments.lexers
import curses
import sys


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
            self.stdscr.addstr(y, i, ch, a)
            #raise Exception('addch [{}] [{}] [{}] [{}]'.format(y, i, ch, a))

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
        # position, line, length):
        self.stdscr.addnstr(self.my - 1, 0, line, self.mx - 1)

    def print_in_statusline(self, position, string, length):
        if position < 0:
            x = len(self.status) + position
        else:
            x = position
        # fill = ''.join([' ' * length])
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
        self.methods[Buffer.STATUS] = {}

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
    """ Fills the ncurses of the text using Pygments """
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
                (t['refs'][i + index]).attr = attribute
                # if (i + index) < len(t['attributes']):
            index += len(value)


class Char:
    ''' Encapsulate both a character (as a unicode string)
        and it's attributes '''
    def __init__(self, ch, attr):
        if ch.__class__.__name__ != 'unicode':
            raise Exception(ch.__class__.__name__ + ' -> ' + str(ch))
        else:
            self.ch = ch
        if attr is None:
            self.attr = curses.A_NORMAL
        else:
            self.attr = attr


class Line:
    ''' Class wrapping a line '''
    def __init__(self, string, attrs=None):
        self.chars = []
        if string[-1] != u'\n':
            self.noeol = True
            string += u'\n'
        i = 0
        lists = list(string)
        while True:
            try:
                if attrs is not None:
                    attr = attrs[i]
                else:
                    attr = curses.A_NORMAL
                char = Char(lists[i], attr)
                self.chars.append(char)
            except IndexError:
                break
            i += 1

    def get_string_and_refs(self, refs, index):
        ''' Return the line as an string and update
            a dictionary of 'references' with pairs of
            'position': Char. This is used by the Highlighter '''
        s = []
        for c in self.chars:
            s.append(c.ch)
            refs[index] = c
            index += 1
        return (''.join(s), index)

    def __getitem__(self, n):
        ''' Return the Char of a certain position '''
        return self.chars[n]

    def __setitem__(self, key, value):
        ''' Set the character for a position. If passed an array
            of [char, attribute], set also the attribute. If
            passed a Char object, simply assign it'''
        if type(value) == list:
            self.chars[key].ch = value[0]
            self.chars[key].attr = value[1]
        elif value.__class__.__name__ == 'Char':
            self.chars[key] = value
        else:
            try:
                self.chars[key].ch = value
            except IndexError:
                pass
                # raise Exception(key)

    def __len__(self):
        return len(self.chars)

    def __delitem__(self, key):
        del self.chars[key]

    def append(self, ch):
        return self.chars.append(ch)

    def add(self, line, trim=False):
        # Join another line
        # If the line to append only contains the '\n', do nothing
        if len(line) <= 1:
            return
        # First delete the last '\n'
        del self.chars[-1]
        for char in line:   # Trim only for a join
            if trim:
                if char.ch == u' ' or char.ch == u'\t':
                    continue
                else:
                    self.chars.append(Char(u' ', None))  # Append one space
                    trim = False
            self.chars.append(char)

    def split(self, position):
        ''' Return a new line from position to the end '''
        r = Line(u'\n')
        r.chars = self.chars[position:]
        self.chars = self.chars[:position] + [Char(u'\n', None)]
        return r

    def last_index(self, mode):
        ''' Return last indexable character in line.
            This is from o to len(self.chars) removing the last '\n' '''
        if mode == Buffer.COMMAND:
            return len(self.chars) - 2
        else:
            return len(self.chars) - 1

class Cursor:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.max = 0

class Viewport:
    def __init__(self, x1, y1):
        self.x0 = self.y0 = 0
        self.x1 = x1
        self.y1 = y1

class Buffer:
    COMMAND = 0
    INSERT = 1
    STATUS = 2
    """ Loaded file with associated c and viewport positions """
    def __init__(self, x1, y1, display):
        self.lines = []
        self.cursor = Cursor()
        self.viewport = Viewport(x1, y1)
        self.height = y1
        self.high = None
        self.mode = self.COMMAND
        self.display = display
        self.regexp = None

    def open(self, path):
        self.lines = []
        for l in open(path).readlines():
            # l[:-1]
            line = Line((l).decode('utf-8'))
            self.lines.append(line)

        self.high = Highlighter(self)
        self.high.scan(0, len(self.lines))

    def __getitem__(self, n):
        try:
            return self.lines[n]
        except IndexError:
            return Line('~'.decode('utf-8'))

    def length(self):
        return len(self.lines)

    def current_line(self):
        try:
            return self.lines[self.cursor.y]
        except IndexError:
            return ['']

    def __cursor_adjustement(c):
        """ If the next line does not have enough characters
            or the cursor to be positioned on the same x,
            adjust it and store the last position in cursor.max
            restore position to cursor.max if after moving to
            the new line it fits
        """
        li = c.current_line().last_index(c.mode)
        if li == -1:
            c.cursor.x = 0
        elif c.cursor.max > c.cursor.x:
            if li >= c.cursor.max:
                c.cursor.x = c.cursor.max
            else:
                c.cursor.x = li
        elif li < c.cursor.x:
            c.cursor.max = c.cursor.x
            c.cursor.x = li

    def __viewport_adjustement(c):
        if c.cursor.x > c.viewport.x1:
            delta = c.cursor.x - c.viewport.x1
            c.viewport.x0 += delta
            c.viewport.x1 += delta
        elif c.cursor.x < c.viewport.x0:
            delta = c.viewport.x0 - c.cursor.x
            c.viewport.x1 -= delta
            c.viewport.x0 -= delta
        if c.cursor.y > c.viewport.y1:
            delta = c.cursor.y - c.viewport.y1
            c.viewport.y0 += delta
            c.viewport.y1 += delta
        elif c.cursor.y < c.viewport.y0:
            delta = c.viewport.y0 - c.cursor.y
            c.viewport.y1 -= delta
            c.viewport.y0 -= delta

    def __cursor_and_viewport_adjustement(c):
        c.__cursor_adjustement()
        c.__viewport_adjustement()

    def cursor_up(c, k):
        if not c.cursor.y == 0:
            c.cursor.y -= 1
            c.__cursor_and_viewport_adjustement()

    def cursor_down(c, k):
        if (c.length() - 1) > c.cursor.y:
            c.cursor.y += 1
            c.__cursor_and_viewport_adjustement()

    def __cursor_max_reset(c):
        """ Any deliberate movement left or right should reset the max """
        c.cursor.max = c.cursor.x

    def cursor_left(c, k):
        if not c.cursor.x == 0:
            c.cursor.x -= 1
            c.__cursor_max_reset()
            c.__cursor_and_viewport_adjustement()

    def cursor_right(c, k):
        if (c.current_line().last_index(c.mode) > (c.cursor.x -
                                                   c.viewport.x0)):
            c.cursor.x = c.cursor.x + 1
            c.__cursor_max_reset()
            c.__cursor_and_viewport_adjustement()

    def extract_text(self, since, to):
        """ Return a dictionary with the addresses passed and
            a raw buffer "text" from a range of lines
            This text can be modified by a external function
            and reinserted with insert_text in place
        """
        t = ''
        refs = {}
        index = 0
        for n in range(since, to):
            string, index = self.lines[n].get_string_and_refs(refs, index)
            t += string
        return {'since': since, 'to': to, 'text': t, 'refs': refs}
        # +1 for the \n so both text and attributes have same length

    def page_forward(self, key):
        ''' Avpag and move cursor vi-alike '''
        delta = self.height - 1
        if ((self.viewport.y0 + delta) > len(self.lines)):
            delta = (len(self.lines) - self.viewport.y0 - 1)
        self.viewport.y0 += delta
        self.viewport.y1 += delta
        self.cursor.y = self.viewport.y0
        self.__cursor_and_viewport_adjustement()

    def page_backwards(self, key):
        delta = self.height - 1
        if ((self.viewport.y0 - delta) < 0):
            delta = self.viewport.y0
        self.viewport.y0 -= delta
        self.viewport.y1 -= delta
        if (self.viewport.y1 > (len(self.lines) - 1)):
            self.cursor.y = len(self.lines) - 1
        else:
            self.cursor.y = self.viewport.y1
        self.__cursor_and_viewport_adjustement()

    def cursor_to_eol(self, key):
        ''' Move Cursor to End-of-Line '''
        eol = self.current_line().last_index(self.mode)
        self.cursor.x = eol if eol >= 0 else 0
        # End of line means end of all lines, thus ...
        self.cursor.max = self.cursor.x + 65536

    def cursor_to_bol(self, key):
        ''' Move to First Character in Line '''
        self.cursor.x = 0
        self.cursor.max = 0

    def refresh_status(self, display, ch):
        if type(ch) == unicode:
            ch = ch.encode('utf-8')

        if len(self.current_line()) <= 0:
            current_char = u' '
        else:
            current_char = self.current_line()[self.cursor.x].ch
        if current_char == '\n':
            current_char = '$'
        i = '{}/{},{}/{} [{}] [{}]'.format(self.cursor.y, len(self.lines),
                                           self.cursor.x,
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
            # Adjust cursor if it is over the '\n'
            if self.cursor.x > self.current_line().last_index(self.mode):
                self.cursor.x = self.current_line().last_index(self.mode)

    def append(self, key):
        # Supposedly we are in COMMAND mode when this is run, so
        self.insert(key)
        self.cursor_right(key)

    def insert_element(self, array, position, element):
        i = len(array) - 1
        array.append(array[i])
        while i > position:
            array[i] = array[i - 1]
            i -= 1
        array[position] = element

    def delete_element(self, array, position):
        l = len(array) - 1
        if l == 0:      # Only the last '\n'
            # TODO: Join lines
            return
        if position == l:
            # TODO: Join lines
            return
        i = l
        t = array[i]
        while True:
            array[i] = t
            i -= 1
            if i == position:
                break
            t = array[i]
        if position != l:
            del array[position]

    def insert_char(self, key):
        # ch = key.encode('utf-8')
        ch = key
        self.display.print_in_statusline(40, '[{}]'.format(ch), 10)
        index = self.cursor.x
        self.insert_element(self.lines[self.cursor.y], index,
                            Char(ch, curses.A_NORMAL))
        self.cursor_right('@')
        self.__cursor_and_viewport_adjustement()

    def delete_char_at_cursor(self, key):
        index = self.cursor.x
        l = len(self.current_line())
        if l == 1:
            del self.lines[self.cursor.y]
            # self.cursor_down(key)
        elif index == (l - 1):
            self.delete_char_before_cursor(key)
        else:
            self.delete_element(self.lines[self.cursor.y], index)

    def delete_char_before_cursor(self, key):
        x = self.cursor.x
        if x == 0:
            # If we are in the first character, move up and join
            y = self.cursor.y
            if y == 0:
                return
            self.cursor_up(key)
            # I would prefer to use join(), but join trims
            y = self.cursor.y
            self.cursor_to_eol(key)
            self.lines[y].add(self.lines[y + 1], False)
            del self.lines[y + 1]
            return
        self.cursor.x -= 1
        self.delete_char_at_cursor(key)

    def join(self, key):
        # Join has many inconsistences; what happens when you join
        # in an empty line? what happens when you join an empty line?
        y = self.cursor.y
        # Move to eol if not already there
        self.cursor_to_eol(key)
        self.lines[y].add(self.lines[y + 1], True)
        del self.lines[y + 1]

    def enter(self, key):
        y = self.cursor.y
        new_line = self.lines[y].split(self.cursor.x)
        self.lines = self.lines[:(y + 1)] + [new_line] + self.lines[(y + 1):]
        self.cursor.x = 0
        self.cursor.max = 0
        self.cursor.y += 1
        self.__cursor_and_viewport_adjustement()

    def tab(self, key):
        # Move to the next tab stop
        x = self.cursor.x
        nspaces = 4 - (x % 4)
        for i in range(nspaces):
            self.insert_char(u' ')

    def status_first(self):
        return self.display.status[0].ch

    def status(self, key):
        self.mode = self.STATUS
        self.display.clear_statusline()
        self.display.print_in_statusline(0, key, 1)
        self.sx = 1

    def status_up(self, key):
        # TODO Filtered history up
        pass

    def status_down(self, key):
        # TODO Filtered history down
        pass

    def status_left(self, key):
        if self.sx > 1:
            self.sx -= 1
        pass

    def status_right(self, key):
        if self.sx < self.display.mx - 2:
            self.sx +=1
        pass

    def status_enter(self, key):
        # Extract status string
        refs = {}
        s, i = self.display.status.get_string_and_refs(refs, 1)
        s = s[1:].rstrip()
        #raise Exception('status_first: [' +  str(self.status_first()) +
        #                '] string: [' + string + ']')
        first = self.status_first()
        if first == u'/':
            self.search(s)
        elif first == u'?':
            self.search(s, True)
        elif first == u':':
            self.ex(s)
        self.status_cancel(key)

    def status_cancel(self, key):
        self.mode = self.COMMAND
        self.display.clear_statusline()

    def status_tab(self, key):
        # TODO autocompletion
        pass

    def status_insert(self, key):
        self.insert_element(self.display.status, self.sx,
                            Char(key, curses.A_NORMAL))
        self.status_right('@')

    def status_backspace(self, key):
        if self.sx == 1:
            self.status_cancel(key)
        self.sx -= 1
        self.status_delete(key)

    def status_delete(self, key):
        l = len(self.display.status)
        if l == 1:
           return
        if self.sx  == l - 1:
            self.status_backspace(key)
        else:
            self.delete_element(self.display.status, self.sx)

    def search(self, pattern=None, reverse=False):
        y = self.cursor.y
        if pattern == None:
            if self.regexp == None:
                self.display.print_in_statusline(0,'-- No regexp --', 20)
                return
            else:
                pattern = self.regexp
        else:
            self.regexp = pattern
        if reverse:
            ran = reversed(range(0, y - 1))
        else:
            ran = range(y + 1, len(self.lines))
        for i in ran:
            r = {}
            s, j = self.lines[i].get_string_and_refs(r, 0)
            n = s.find(pattern)
            if n != -1:
                self.cursor.x = n
                self.cursor.y = i
                self.__cursor_and_viewport_adjustement()
                return
        self.display.print_in_statusline(0, '-- Not found --', 20)

    def repeat_find_forward(self, key):
        self.search()

    def repeat_find_backward(self, key):
        self.search(reverse=True)

    def error(self, key):
        pass

class Commands:
    def __init__(self):
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

if len(sys.argv) < 2:
    print ('Usage: vy <file>')
    sys.exit(0)

curses.wrapper(main, sys.argv)
