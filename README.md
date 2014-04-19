hellfire
========

A small ncurses based console text editor with vi keybindings written in Python

Caveat emptor: This is the editor I use, it lacks vi POSIX compatibility
and lacks a lot of commands, but it is easier to extend than many others (at
least for me :)

Featuring:
 - Somehow vi-alike keybindings
 - Full UTF-8 support
 - Syntax highlighting using pygments for a whole lot of languages
 - A cool game (2048)
 - Hellfire!!

![2048](http://i.imgur.com/qxjJXSn.png)

![hellfire](http://i.imgur.com/JfvlU7n.png)

Requirements
------------

Requires Python 2.7, setuptools and pygments. To install on Debian Wheezy:

        apt-get install python-pygments python-setuptools

You will need also a terminal emulator and locale that support UTF-8, and a
font that can display Unicode graphic characters. As a reference, i use
'Bitstream Vera Sans Mono' in an xterm (xterm -fs 12 -fa 'Bitstream Vera Sans
Mono')

Installation
------------
Install system-wide, with executable in /usr/bin/hellfire:

        sudo python ./setup.py install

Supported vi commands
---------------------
Command mode:

 - Motion commands:
  - k, j, h, l, +, -, cursor keys
  - Avpag, Repag, Control+f, Control+b
  - Home, End, 0 and $
 - Insertion:
  - a, i
 - Deletion:
  - x, X, Supr, Backspace, J, D, dd
 - Visual line selection:
  - V (start selection/end selection)
 - Copying:
  - (range)y or y over visual selection

Insert mode:

 - Motion commands
  - cursor keys, Home, End, Avpag

Ex (:) mode:
 - Substitution
  - s[ubstitute], using python regular expressions
 - Writing
  - w[rite] [file]

Unsupported vi features
-----------------------

There is no horizontal scroll...

You can not prefix a command with a repetition number (i.e. 10j)

Delete to end of line or to end of world (d$, dw) is not implemented

There is no undo (yet)

Games and other nuisances
-------------------------

 - Type :game2048 (or just :g) to play the popular game

 - Yup, type :hellfire to become the god of hellfire!

