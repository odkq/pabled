#!/usr/bin/env python
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
import shlex
import sys
import re

from hellfire import game_2048


class Commands:
    def __init__(self):
        # Retrieve all valid method names using introspection, leaving
        # out __init__() and get_candidates()
        c = [d for d in dir(Commands) if hasattr(Commands.__dict__[d],
                                                 '__call__')]
        c = [d for d in c if d not in ['__init__', 'get_candidates']]
        self.commands = c

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

    def game2048(self, args, **kwargs):
        pad = curses.newpad(25, 80)
        maxy, maxx = self.display.getmaxyx()
        if maxx < 80 or maxy < 25:
            return
        if maxx == 80:
            sminrow = 0
            smincol = 0
            smaxrow = 24
            smaxcol = 79
        elif maxx > 82:
            #sminrow = 0
            #smincol = 0
            #smaxrow = 24
            #smaxcol = 79
            sminrow = (maxy / 2) - 12
            smincol = (maxx / 2) - 40
            smaxrow = 24 + sminrow
            smaxcol = 79 + smincol
        game_2048(pad, False, True, sminrow, smincol, smaxrow, smaxcol)
        self.display.show(self)
        return

        #  These loops fill the pad with letters; this is
        # explained in the next section
        for y in range(0, 25):
            for x in range(0, 80):
                try:
                    pad.addch(y, x, ord('a') + (x*x+y*y) % 26)
                except curses.error:
                    pass

        #  Displays a section of the pad in the middle of the screen
        pad.refresh(0, 0, 0, 0, 24, 79)
        pad.refresh()
        pad.getch()
        # self.display.getkey()


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
