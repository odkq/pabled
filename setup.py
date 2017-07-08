#!/usr/bin/env python
from setuptools import setup
import os
import sys
import subprocess

classifiers = [
    "Development Status :: 2 - Alpha",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Programming Language :: Python :: 2.7",
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
        for d in ['hellfire.egg-info', 'build', 'dist', 'deb_dist']:
            subprocess.call(['sudo', 'rm', '-fR', d])
    else:
        setup(
            name='hellfire',
            version='0.0.1',
            description="A small text editor with fancy features",
            author="Pablo Martin Medrano",
            author_email="pablo@odkq.com",
            package_dir={'hellfire': '.'},
            packages=['hellfire'],
            entry_points={
                'console_scripts': {
                    'hellfire = hellfire.main:main_curses'
                }
            },
            url="https://github.com/odkq/hellfire",
            license="GPL v3",
            long_description=open('README.md').read(),
            data_files=[("/usr/share/doc/hellfire", ["README.md"])],
            classifiers=classifiers)
