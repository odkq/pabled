#!/usr/bin/env python
"""
 visual - visual mode handling

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
from hellfire import Cursor


class Visual:
    def __init__(self):
        self.visual_cursor = None

    def in_visual_range(self, line, column):
        ''' Return wether we are in the visual range or not '''
        if self.visual_cursor is None:
            return False
        start_y = min(self.cursor.y, self.visual_cursor.y)
        end_y = max(self.cursor.y, self.visual_cursor.y)
        start_x = min(self.cursor.x, self.visual_cursor.x)
        end_x = max(self.cursor.x, self.visual_cursor.x)
        if line not in range(start_y, end_y + 1):
            return False
        if self.visual_cursor_line:
            return True     # No more comparisons on V selection
        s = 'start_y {} end_y {} start_x {} end_x {}'
        s = s.format(start_y, end_y, start_x, end_x)
        self.display.print_in_statusline(0, s, 60)
        if self.cursor.y == self.visual_cursor.y:
            if self.cursor.x == self.visual_cursor.x:
                return False
            if column not in range(start_x, end_x + 1):
                return False
            return True
        if line == self.visual_cursor.y:
            if self.cursor.y > self.visual_cursor.y:
                return column > self.visual_cursor.x
            else:
                return column < self.visual_cursor.x
        elif line == self.cursor.y:
            if self.cursor.y > self.visual_cursor.y:
                return column < self.cursor.x
            elif self.cursor.y < self.visual_cursor.y:
                return column > self.cursor.x
        return True

    def set_visual(self, per_lines=True):
        if self.visual_cursor is None:
            self.visual_cursor = Cursor(self.cursor)
            if per_lines:
                self.visual_cursor.x = 0
                self.visual_cursor_line = True
            else:
                self.visual_cursor_line = False
        else:
            self.visual_cursor = None

    def set_visual_line(self):
        ''' Set visual in a cursor from the end of the current line'''
        pass

    def get_range(self):
        pass
