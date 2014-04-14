hellfire
========

A small ncurses based console text editor with vi keybindings written in Python

Featuring:
 - Full UTF-8 support
 - Syntax highlighting using pygments
 - A cool game (2048)


![screenshot](http://i.imgur.com/pN5hnAO.png)

Requirements
------------

Requires Python 2.7, setuptools and pygments. To install on Debian Wheezy:

        apt-get install python-pygments python-setuptools

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
  - x, X, Supr, Backspace, J
 - Visual line selection:
  - V (start selection/end selection)

Insert mode:

 - Motion commands
  - cursor keys, Home, End, Avpag

Ex (:) mode:
 - Substitution
  - s[ubstitute], using python regular expressions
 - Writing
  - w[rite] [file]

Games:
 - Type :game2048 (or just :g) to play the popular game

