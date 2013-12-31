#!/usr/bin/env python
import curses
from vy import Char

class StatusLine:
    ''' Status Line handler. Extracted from
        Buffer for convenience '''

    def status_first(self):
        return self.display.status[0].ch

    def status(self, key):
        self.mode = self.STATUS
        self.display.clear_statusline()
        self.display.print_in_statusline(0, key, 1)
        self.sx = 1

    def status_up(self, key):
        # TODO Filtered history up
        pass

    def status_down(self, key):
        # TODO Filtered history down
        pass

    def status_left(self, key):
        if self.sx > 1:
            self.sx -= 1
        pass

    def status_right(self, key):
        if self.sx < self.display.mx - 2:
            self.sx +=1
        pass

    def status_enter(self, key):
        # Extract status string
        refs = {}
        s, i = self.display.status.get_string_and_refs(refs, 1)
        s = s[1:].rstrip()
        #raise Exception('status_first: [' +  str(self.status_first()) +
        #                '] string: [' + string + ']')
        first = self.status_first()
        if first == u'/':
            self.search(s)
        elif first == u'?':
            self.search(s, True)
        elif first == u':':
            self.ex(s)
        self.mode = self.COMMAND
        #self.status_cancel(key)

    def status_cancel(self, key):
        self.mode = self.COMMAND
        self.display.clear_statusline()

    def status_tab(self, key):
        # TODO autocompletion
        pass

    def status_insert(self, key):
        self.insert_element(self.display.status, self.sx,
                            Char(key, curses.A_NORMAL))
        self.status_right('@')

    def status_backspace(self, key):
        if self.sx == 1:
            self.status_cancel(key)
        self.sx -= 1
        self.status_delete(key)

    def status_delete(self, key):
        l = len(self.display.status)
        if l == 1:
            return
        if self.sx  == l - 1:
            self.status_backspace(key)
        else:
            self.delete_element(self.display.status, self.sx)
