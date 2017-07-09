#!/usr/bin/env python
"""
 keys - keys to commands array handler

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

from pabled.buffer import Buffer


class Keys:
    """ Map c keys or key arrays to functions """
    def __init__(self):
        self.methods = {}
        self.default = {}
        self.count = 0
        self.multi = None  # When in a multikey command, the string so far
        self.methods[Buffer.COMMAND] = {}
        self.methods[Buffer.INSERT] = {}
        self.methods[Buffer.STATUS] = {}

        # Digits in command mode are for count
        for n in range(10):
            self.bind(Buffer.COMMAND, str(n), self.set_count)

    def bind(self, mode, key, method):
        ''' Bind a key or a list of keys to a certain method, referenced
            by name '''
        if type(key) in (tuple, list):
            for i in key:
                self.bind(mode, i, method)
            return
        if type(mode) in (tuple, list):
            for m in mode:
                self.bind(m, key, method)
            return
        if type(key) is str:
            if len(key) > 1:
                if mode != Buffer.COMMAND:
                    raise Exception('Multikeys are only allowed on COMMAND')
                self.methods[mode][key[0]] = self.process_multi
        if key is None:
            self.default[mode] = method
        else:
            self.methods[mode][key] = method

    def process(self, key, mode):
        ''' Process key '''
        try:
            method = self.methods[mode][key]
        except KeyError:
            method = self.default[mode]
        if method != self.set_count:
            if self.count != 0:
                for i in range(self.count):
                    method(key)
                self.count = 0
                return
        method(key)

    def process_multi(self, key):
        ''' Multikey continuation '''
        if self.multi is None:
            self.multi = key
        else:
            self.multi += key
            # Check wether the whole string forms a command
            # or not
            try:
                method = self.methods[Buffer.COMMAND][self.multi]
            except KeyError:
                # Send an escape to reset whatever needs to be reset
                method = self.methods[Buffer.COMMAND][27]
            self.multi = None
            method(key)

    def setmode(self, mode):
        ''' Change from command to edition mode and versavice '''
        self.mode = mode

    def set_count(self, key):
        if self.count == 0 and key == '0':
            self.methods[Buffer.COMMAND]['0']
        else:
            self.count = int(str(self.count) + key)
