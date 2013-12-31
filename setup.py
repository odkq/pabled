#!/usr/bin/env python
from setuptools import setup

classifiers = [
   "Development Status :: 2 - Alpha",
   "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
   "Programming Language :: Python :: 2.7",
   "Topic :: Text Editors",
   "Environment :: Console",
   "Environment :: Console :: Curses",
]

setup(
    name='vy',
    version='0.0.1',
    description="A small vi clone with fancy features",
    author="Pablo Martin Medrano",
    author_email="pablo@odkq.com",
    package_dir = {'vy': '.'},
    packages=['vy'],
    entry_points = {
        'console_scripts' : {
            'vy = vy.main:main_curses'
        }
    },
    url="https://github.com/odkq/vy",
    license="GPL v3",
    long_description=open('README.rst').read(),
    data_files=[("/usr/share/doc/vy", ["README.rst"])],
    classifiers=classifiers)
