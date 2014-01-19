hellfire
========

A small text editor written in Python

Featuring:
 - Full UTF-8 support
 - Syntax highlighting using pygments
 - Multiple files are opened contiguously

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

