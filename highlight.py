#!/usr/bin/env python
"""
 highlight - define HightLighter class using pygments/curses

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
