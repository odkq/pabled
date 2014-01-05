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

from vy.buffer import Buffer


class Keys:
    """ Map c keys or key arrays to functions """
    def __init__(self):
        self.methods = {}
        self.default = {}
        self.multi = None  # When in a multikey command, the string so far
        self.methods[Buffer.COMMAND] = {}
        self.methods[Buffer.INSERT] = {}
        self.methods[Buffer.STATUS] = {}

    def bind(self, mode, key, method):
        if type(key) in (tuple, list):
            for i in key:
                self.bind(mode, i, method)
            return
        if type(mode) in (tuple, list):
            for m in mode:
                self.bind(m, key, method)
            return
        if type(key) in (str, unicode):
            if len(key) > 1:
                if mode != Buffer.COMMAND:
                    raise Exception('Multikeys are only allowed on COMMAND')
                self.methods[mode][key[0]] = self.process_multi
        if key is None:
            self.default[mode] = method
        else:
            self.methods[mode][key] = method

    def process(self, key, mode):
        try:
            method = self.methods[mode][key]
        except KeyError:
            method = self.default[mode]
        method(key)

    def process_multi(self, key):
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
        self.mode = mode
