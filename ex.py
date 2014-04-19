#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 ex - Implementation of very few ex (: ) commands

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
import random
import shlex
import copy
import sys
import re

from hellfire import game_2048


class Commands:
    def __init__(self):
        # Retrieve all valid method names using introspection, leaving
        # out __init__() and get_candidates()
        c = [d for d in dir(Commands) if hasattr(Commands.__dict__[d],
                                                 '__call__')]
        c = [d for d in c if d not in ['__init__', 'get_candidates',
                                       'get_range']]
        self.commands = c
        self.yankring = []

    def write(self, args, **kwargs):
        a = args[0]
        if a is None:
            path = self.path
        else:
            path = a
        f = open(path, 'w')
        for l in self.lines:
            for char in l.chars:
                if not (char.ch == u'\n' and l.noeol):
                    f.write(char.ch.encode('utf-8'))
        f.close()
        self.display.print_in_statusline(0, '-- wrote ' + path + '--', 20)

    def get_current_range(self, args, **kwargs):
        if 'range' in kwargs:
            first_line = kwargs['range'][0]
            last_line = kwargs['range'][1]
        else:   # Current line
            # If there is a visual selection, use that range
            if self.visual_cursor is not None:
                first_line, last_line = self.get_visual_range()
                last_line += 1  # Somehow this is needed
                # Reset visual selection
                self.set_visual()
            else:
                first_line = self.cursor.y
                last_line = first_line + 1
        return first_line, last_line

    # [range]d[elete]
    def delete(self, args, **kwargs):
        ''' delete the lines specified '''
        first_line, last_line = self.get_current_range(kwargs)
        ndeleted = 0
        if len(self.yankring) != 0:
            self.yankring = []
        for n in range(first_line, last_line):
            self.yankring.append(self.lines[first_line])
            del self.lines[first_line]
            if self.cursor.y >= first_line:
                self.cursor.y -= 1
            ndeleted += 1
        s = 'deleted {} lines'.format(ndeleted)
        self.display.print_in_statusline(0, s, len(s))
        self.cursor_and_viewport_adjustement()
        self.move_to_first_non_blank('d')

    # [range]y[yank]
    def yank(self, args, **kwargs):
        ''' delete the lines specified '''
        first_line, last_line = self.get_current_range(kwargs)
        if len(self.yankring) != 0:
            self.yankring = []
        for n in range(first_line, last_line):
            self.yankring.append(self.lines[n])
        nyanked = len(self.yankring)
        s = 'yanked {} lines'.format(nyanked)
        self.display.print_in_statusline(0, s, len(s))
        #self.cursor_and_viewport_adjustement()
        #self.move_to_first_non_blank('d')

    # [range]p[aste]
    def paste(self, args, **kwargs):
        ''' Paste can not make use of any range, but whatever '''
        y = self.cursor.y
        self.lines = (self.lines[:(y + 1)] + copy.deepcopy(self.yankring) +
                      self.lines[(y + 1):])
        npasted = len(self.yankring)
        self.cursor.y += npasted
        s = 'pasted {} lines'.format(npasted)
        self.display.print_in_statusline(0, s, len(s))

    # [range]s[ubstitute]/{pattern}/{string}/[flags] [count]
    def substitute(self, args, **kwargs):
        array = self.split_with_backslash(args[0])
        flags = ''
        if len(array) == 0:
            return
        elif len(array) == 1:
            string = ''
        elif len(array) >= 2:
            string = array[1]
        if len(array) == 3:
            flags = array[2]
        pattern = array[0]
        if 'range' in kwargs:
            first_line = kwargs['range'][0]
            last_line = kwargs['range'][1]
        else:   # Current line
            first_line = self.cursor.y
            last_line = first_line + 1
        replacements = 0
        lines_replaced = 0
        last_cursor = [-1, -1]
        for i in range(first_line, last_line):
            x = 0
            line_replaced = False
            while True:
                start, end = self.find(i, x, pattern)
                if start is None:
                    break
                last_cursor[0] = start
                self.lines[i].replace(start, end, string)
                replacements += 1
                line_replaced = True
                last_cursor[1] = i
                if flags != 'g':
                    break
            if line_replaced:
                lines_replaced += 1
        s = '{} replacements in {} lines'.format(replacements, lines_replaced)
        self.display.print_in_statusline(0, s, len(s))
        # Move cursor to the start of the last replacement
        if last_cursor[0] != -1:
            self.cursor.x = last_cursor[0]
            self.cursor.y = last_cursor[1]
            self.cursor_and_viewport_adjustement()
        # start, end = find(self, index, x, pattern=None):

    def quit(self, args, **kwargs):
        sys.exit(0)

    def get_candidates(self, pattern):
        return [c for c in self.commands if c[:len(pattern)] == pattern]

    def get_centered_pad(self, width, height):
        pad = curses.newpad(height, width)
        maxy, maxx = self.display.getmaxyx()
        if maxx < width or maxy < height:
            return
        if (maxx < (width + 2)) or (maxy < (height + 2)):
            sminrow = 0
            smincol = 0
            smaxrow = height - 1
            smaxcol = width - 1
        else:
            sminrow = (maxy / 2) - 12
            smincol = (maxx / 2) - 40
            smaxrow = (height - 1) + sminrow
            smaxcol = (width - 1) + smincol
            mpad = curses.newpad(height + 3, width + 2)
            for x in range(width + 1):
                mpad.addstr(0, x, '─')
                try:
                    mpad.addstr(height + 1, x, '─')
                except:
                    raise Exception('x {} height {}'.format(x, height))
            for y in range(height + 1):
                mpad.addstr(y, 0, '│')
                try:
                    mpad.addstr(y, width + 1, '│')
                except:
                    raise Exception('y {} width {}'.format(y, width))
            mpad.addstr(0, 0, '╭')
            mpad.addstr(height + 1, 0, '╰')
            mpad.addstr(0, width + 1, '╮')
            mpad.addstr(height + 1, width + 1, '╯')

            # mpad.refresh()
            mpad.refresh(0, 0, sminrow - 1, smincol - 1, smaxrow + 1,
                         smaxcol + 1)

        return pad, sminrow, smincol, smaxrow, smaxcol

    def game2048(self, args, **kwargs):
        pad, sminrow, smincol, smaxrow, smaxcol = self.get_centered_pad(80, 23)
        game_2048(pad, False, True, sminrow, smincol, smaxrow, smaxcol)
        self.display.show(self)
        return

    def hellfire(self, args, **kwargs):
        ''' Show hellfire!!
            Ripped from msimpson's
            https://gist.github.com/msimpson/1096950 '''
        screen = self.display.stdscr
        height, width = self.display.getmaxyx()
        height = height - 1  # Preserve statusline
        size = width * height
        char = [" ", ".", ":", "^", "*", "x", "s", "S", "#", "$"]
        b = []

        curses.init_pair(41, 0, 0)
        curses.init_pair(42, 1, 0)
        curses.init_pair(43, 3, 0)
        curses.init_pair(44, 4, 0)
        # screen.clear
        for i in range(size+width+1):
            b.append(0)
        while 1:
            self.display.refresh()
            for i in range(int(width/9)):
                b[int((random.random() * width) + width * (height - 1))] = 65
            for i in range(size):
                    b[i] = int((b[i] + b[i+1] + b[i + width] +
                                b[i + width + 1])/4)
                    color = (4 if b[i] > 15 else (3 if b[i] > 9 else
                                                 (2 if b[i] > 4 else 1)))
                    if(i < size - 1):
                        c = char[(9 if b[i] > 9 else b[i])]
                        attr = curses.color_pair(color + 40) | curses.A_BOLD
                        if c != ' ':
                            screen.addstr(int(i / width), i % width,
                                          c, attr)
            screen.refresh()
            screen.timeout(30)
            if (screen.getch() != -1):
                break


class Ex(Commands):
    ''' ex (:) commands handling. Extracted from Buffer for
        convenience '''
    def __init__(self):
        Commands.__init__(self)
        self.history = []

    def get_range_cmd_arg(self, s):
        s, rang = self.get_range(s)
        delimiter = s.find('/')
        if delimiter == -1:
            delimiter = s.find('|')
            if delimiter == -1:
                return rang, s, None
        return rang, s[:delimiter], s[delimiter:]
        # '[10,20]', 's', '/foo/bar/'

    def get_range(self, s):
        # Extract range [i.e] 10,20 in 10,20s/foo/bar/
        range_match = re.search('\d+?,\d*\d+?|%|\d+', s)
        if range_match is None:
            # If there is a visual selection, use that range
            if self.visual_cursor is not None:
                rang0, rang1 = self.get_visual_range()
                # Reset visual selection
                self.set_visual()
                return s, [rang0, rang1 + 1]
            return s, None
        rang = s[range_match.start():range_match.end()]
        s = s[range_match.end():]
        if rang == '%':     # All lines
            return s, [0, len(self.lines)]
        rang = rang.split(',')
        if (int(rang[0]) <= 0):
            return
        rang[0] = int(rang[0]) - 1
        if len(rang) == 1:
            rang.append(rang[0] + 1)
        else:
            rang[1] = int(rang[1])
        return s, rang  # 's/foo/bar/' [10, 20]

    def ex(self, line):
        if line == '':
            return
        s = shlex.split(line)
        rang, cmd, arg = self.get_range_cmd_arg(s[0])
        if arg is not None:
            args = [arg] + s[1:]
        else:
            args = [arg] + s[1:]
        kwargs = {}
        if rang is not None:
            kwargs['range'] = rang
        try:
            function_name = self.get_candidates(cmd)[0]
        except IndexError:
            return
        function = Commands.__dict__[function_name]
        # raise Exception(self.get_candidates(cmd)[0])
        # getattr(self, cmd)
        function(self, args, **kwargs)

    def split_with_backslash(self, pattern):
        # TODO: Why /foo\/bar/ only arrives if entering /foo\\/bar/ ?
        answers = []
        answer = ''
        i = 0
        back = False
        if pattern is None:
            return answers
        # raise Exception(pattern)
        while i < len(pattern):
            c = pattern[i]
            if c == u'/' and not back:
                if answer != '':
                    answers.append(answer)
                    answer = ''
            elif i == (len(pattern) - 1):
                answer += c
                answers.append(answer)
            elif c == u'\\' and not back:
                back = True
            elif back:
                answer += c
                back = False
            else:
                answer += c
            i += 1
        return answers
