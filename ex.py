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
import shlex
import sys
import re


class Commands:
    def __init__(self):
        # Retrieve all valid method names using introspection, leaving
        # out __init__() and ex()
        c = [d for d in dir(Commands) if hasattr(Commands.__dict__[d],
                                                 '__call__')]
        c = [d for d in c if d not in ['__init__', 'get_candidates']]
        self.commands = c

    def write(self, args, **kwargs):
        a = args[0]
        if len(a) == 0:
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
        raise Exception('substitute [' + str(args) + '|' + str(kwargs) + ']')

    def quit(self, args, **kwargs):
        sys.exit(0)

    def get_candidates(self, pattern):
        return [c for c in self.commands if c[:len(pattern)] == pattern]


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
        if range_match == None:
            return s, None
        rang = s[range_match.start():range_match.end()]
        s = s[range_match.end():]
        if rang == '%':
            return s, None
        rang = rang.split(',')
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
        function_name = self.get_candidates(cmd)[0]
        function = Commands.__dict__[function_name]
        # raise Exception(self.get_candidates(cmd)[0])
        # getattr(self, cmd)
        function(self, args, **kwargs)
