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
        # if os.path.exists('web/mxcjobman.js'):
        #    os.remove('web/mxcjobman.js')
        for d in ['vy.egg-info', 'build', 'dist', 'deb_dist']:
            subprocess.call(['sudo', 'rm', '-fR', d])
    else:
        setup(
            name='vy',
            version='0.0.1',
            description="A small vi clone with fancy features",
            author="Pablo Martin Medrano",
            author_email="pablo@odkq.com",
            package_dir={'vy': '.'},
            packages=['vy'],
            entry_points={
                'console_scripts': {
                    'vy = vy.main:main_curses'
                }
            },
            url="https://github.com/odkq/vy",
            license="GPL v3",
            long_description=open('README.rst').read(),
            data_files=[("/usr/share/doc/vy", ["README.rst"])],
            classifiers=classifiers)
