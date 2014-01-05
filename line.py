#!/usr/bin/env python
"""
 line - Line, Char, Viewport, Cursor definitions

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
import curses


def insert_element(array, position, element):
    i = len(array) - 1
    array.append(array[i])
    while i > position:
        array[i] = array[i - 1]
        i -= 1
    array[position] = element


def delete_element(array, position):
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
        # Store wether the string do not end in \n (only
        # the last line can fit in that, and append the \n
        if string[-1] != u'\n':
            self.noeol = True
            string += u'\n'
        else:
            self.noeol = False
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
            #try:
            self.chars[key].ch = value
            #except IndexError:
                #pass
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

    def replace(self, start, end, string):
        refs = {}
        ''' Replace from start to end position with the contents of string '''
        for delindex in reversed(range(start, end)):
            try:
                del self.chars[delindex]
            except:
                s, i = self.get_string_and_refs(refs, 0)
                msg = '{}:{} -> {} in \'{}\' index {}'
                raise Exception(msg.format(start, end, string, s, delindex))
        for insertidx in range(start, start + len(string)):
            c = string[insertidx - start]
            insert_element(self, insertidx, Char(unicode(c), curses.A_NORMAL))

    def split(self, position):
        ''' Return a new line from position to the end '''
        r = Line(u'\n')
        r.chars = self.chars[position:]
        self.chars = self.chars[:position] + [Char(u'\n', None)]
        return r

    def last_index(self, mode):
        ''' Return last indexable character in line.
            This is from o to len(self.chars) removing the last '\n' '''
        if mode == 0:   # Buffer.COMMAND
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
