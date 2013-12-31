#!/usr/bin/env python
"""
 ex - Implementation of ex (: ) commands

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


class Ex:
    ''' ex (:) commands handling. Extracted from Buffer for
        convenience '''
    def __init__(self):
        self.history = []

    def ex(self, line):
        s = shlex.split(line)
        cmd = s[0]
        args = s[1:]
        function = getattr(self, cmd)
        function(args)

    def write(self, *args):
        a = args[0]
        if len(a) == 0:
            self.display.print_in_statusline(0, '-- write default --', 20)
        else:
            self.display.print_in_statusline(0, '-- write ' + a[0] + '--', 20)

