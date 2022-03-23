'''
Author: Lingchu Xi <xilingchu@163.com>

This package is distributed under MIT license.
'''
from setuptools import setup, find_packages
from pathlib import Path

long_description='''
File Extraordinary Manager(FileEM) is a Python package help you manage all your files in your computer.
That will help you if you always ask yourself,
    1. Why I should use my mouse click here and there if I just want to open a file?
    2. How to sort my files in a smart way?
    3. How to dig all the potential of my computer?
This software can help you open your file in terminal and with just a simple TUI(in the future).
'''

classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
        'Operation System :: Unix',
        'Operation System :: MacOS'
        ]
        

setup(
        name='fileEM',
        version='0.1.0',      # The initial and first test version.
        description='File Exordinary Manager',
        long_description=long_description,
        author='Lingchu Xi',
        author_email='xilingchu@163.com',
        license='MIT',
        classifiers=classifiers,
        packages=find_packages(exclude=['scripts', 'config']),
        url="https://github.com/xilingchu/fileEM",
        requires=['PyYAML', 'suds'],
        scripts=['scripts/fileEm']
        )
