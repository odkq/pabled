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
Highlight white
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

''' Original '''
schema256_2 = """Text 7 16
Highlight 235
Whitespace 0 7
Error 200 1
Keyword.Namespace 171 16
Keyword 186 16
Name.Class 205 16
Name.Function 104 16
Name.Exception 212 16
Name.Builtin.Pseudo 210 16
Name.Builtin 222 16
Name 7 16
Literal.String.Escape 3 16
Literal 3 16
String 38 16
Number 41 16
Punctuation 8 16
Operator 8 16
Comment 36 16
Other red black"""


schema256 = """Text 231 16
Highlight 235
Whitespace 0 7
Error 200 1
Keyword.Namespace 171 16
Keyword 186 16
Name.Class 205 16
Name.Function 104 16
Name.Exception 212 16
Name.Builtin.Pseudo 210 16
Name.Builtin 222 16
Name 7 16
Literal.String.Escape 3 16
Literal 3 16
String 143 16
Number 41 16
Punctuation 8 16
Operator 8 16
Comment 243 16
Other red black"""

class Highlighter:
    """ Fill the attributes of the text using Pygments """
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
        # Set default color schema when only 8 colors are available
        if curses.COLORS != 256:
            open('/tmp/perico.txt', 'w').write('16*\n')
            self.setcolorschema(defcolschema)
        # Set default schema for 256 colors
        else:
            open('/tmp/perico.txt', 'w').write('256*\n')
            self.setcolorschema(schema256)
        # self.setcolorschema(defcolschema)

    def default_attribute(self):
        c = pygments.token.string_to_tokentype('Token.Text')
        return self.token_colors[c]['color']

    def highlight_background(self):
        pass

    def setcolorschema(self, text):
        i = 1   # First color pair settable is 1, 0 is fixed to white on black
        self.highlight_background = None
        for npass in range(1, 3):
            for token in text.split('\n'):
                tk = token.split()
                if tk[0] == 'Highlight':
                    # Highlight background
                    try:
                        self.highlight_background = int(self.__colors[tk[1]])
                    except KeyError:
                        self.highlight_background = int(tk[1])
                    continue
                else:
                    try:
                        foreground = self.__colors[tk[1]]
                        if npass == 1:
                            background = self.__colors[tk[2]]
                        else:
                            background = self.highlight_background
                    except KeyError:
                        foreground = int(tk[1])
                        if npass == 1:
                            background = int(tk[2])
                        else:
                            background = self.highlight_background

                c = pygments.token.string_to_tokentype('Token.' + tk[0])
                try:
                    curses.init_pair(i, foreground, background)
                except:
                    s = 'int(tk[1]) {} int(tk[2]) {}'
                    raise Exception(s.format(int(tk[1]), int(tk[2])))
                if npass == 1:
                    self.token_colors[c] = {'color': curses.color_pair(i)}
                else:
                    self.token_colors[c]['highlight'] = curses.color_pair(i)
                i += 1

    def get_attrs_for_token(self, tokentype):
        ''' 'split' the token into it's hierarchy and search for
             it in order in the loaded dictionary '''
        types = tokentype.split()
        if types is None:
            return curses.color_pair(0)
        types.reverse()
        for tt in types:
            try:
                attribute = self.token_colors[tt]['color']
                highlight = self.token_colors[tt]['highlight']
                return attribute, highlight
            except KeyError:
                pass
        return curses.A_NORMAL, curses.A_REVERSE
        # curses.color_pair(0)

    def scan(self, since, to):
        t = self.b.extract_text(since, to)
        index = 0
        for tokentype, value in self.lexer.get_tokens(t['text']):
            attribute, highlight = self.get_attrs_for_token(tokentype)
            for i in range(len(value)):
                (t['refs'][i + index]).attr = attribute
                (t['refs'][i + index]).high = highlight
                # if (i + index) < len(t['attributes']):
            index += len(value)
