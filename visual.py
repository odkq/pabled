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
#import curses
#import re
#from hellfire import (Ex, StatusLine, Cursor, Viewport, Line, Highlighter,
#                      Char, insert_element, delete_element)

class Visual:
    def __init__(self):
        self.visual_cursor = None

    def in_visual_range(self, line, column):
        ''' Return wether we are in the visual range or not '''
        if self.visual_cursor == None:
            return False
        start_y = min(self.cursor.y, self.visual_cursor.y)
        end_y = max(self.cursor.y, self.visual_cursor.y)
        start_x = min(self.cursor.x, self.visual_cursor.x)
        end_x = min(self.cursor.x, self.visual_cursor.x)
        if line not in range(start_y, end_y + 1):
            return False
        if self.cursor.y == self.visual_cursor.y:
            if self.cursor.x == self.visual_cursor.x:
                return False
            if column not in range(start_x, end_x + 1):
                return False
            return True
        if line == self.visual_cursor.y or line == self.cursor.y:
            if self.cursor.y > self.visual.cursor.y:
                if column > self.visual_cursor.x:
                    return True
            elif self.cursor.y < self.visual.cursor.y:
                if column < self.visual_cursor.x:
                    return True
            return False
        return True

    def set_visual(self):
        if self.visual_cursor == None:
            self.visual_cursor = self.cursor
        else:
            self.visual_cursor = None

    def set_visual_line(self):
        ''' Set visual in a cursor from the end of the current line'''
        pass

    def get_range(self):
        pass

