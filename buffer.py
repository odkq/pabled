#!/usr/bin/env python
import curses
import re
from vy import Ex, StatusLine, Cursor, Viewport, Line, Highlighter, Char

class Buffer(Ex, StatusLine):
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
        if len(self.current_line()) <= 0:
            current_char = u' '
        else:
            current_char = self.current_line()[self.cursor.x].ch
        if current_char == u'\n':
            current_char = u'$'
        i = u'{}/{},{}/{} [{}] [{}]'.format(self.cursor.y, len(self.lines),
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
        # raise Exception(ch)
        self.display.print_in_statusline(40, '[{}]'.format(key.encode('utf-8')), 10)
        index = self.cursor.x
        self.insert_element(self.lines[self.cursor.y], index,
                            Char(key, curses.A_NORMAL))
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
        prog = re.compile(pattern)
        if reverse:
            ran = reversed(range(0, y - 1))
        else:
            ran = range(y + 1, len(self.lines))
        for i in ran:
            r = {}
            s, j = self.lines[i].get_string_and_refs(r, 0)
            # n = s.find(pattern)
            m = prog.search(s)
            if m is not None:
                self.display.print_in_statusline(0, u'/' + pattern, 20)
                self.cursor.x = m.start()
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
