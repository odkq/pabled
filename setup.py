#!/usr/bin/env python3
from setuptools import setup
import os
import sys
import subprocess

classifiers = [
    "Development Status :: 2 - Alpha",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Programming Language :: Python :: 3.5",
    "Topic :: Text Editors",
    "Environment :: Console",
    "Environment :: Console :: Curses",
]

if __name__ == '__main__':
    # Do a proper clean as root
    if len(sys.argv) >= 2 and sys.argv[1] == "mrproper":
        for (dirpath, dirnames, filenames) in os.walk("."):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                for end in ['_pb2.py', '.pyc', '.so', '.o']:
                    if filepath.endswith(end):
                        os.remove(filepath)
        for d in ['pabled.egg-info', 'build', 'dist', 'deb_dist']:
            subprocess.call(['sudo', 'rm', '-fR', d])
    else:
        setup(
            name='pabled',
            version='0.2.0',
            description="A small text editor with fancy features",
            author="Pablo Martin Medrano",
            author_email="pablo@odkq.com",
            packages=['pabled'],
	    entry_points = {
		'console_scripts': ['pabled=pabled.main:main_curses'],
	    },
            url="https://github.com/odkq/pabled",
            license="GPL v3",
            long_description=open('README.md').read(),
            classifiers=classifiers)
