#!/usr/bin/python3
from setuptools import setup, find_packages
import shutil

with open('README.md') as f:
    long_description = f.read()
shutil.copyfile('gm_termcontrol/termcontrol.py', 'gm_termcontrol/__init__.py')

setup(
    name='gm_termcontrol',
    version='0.0.3',
    license='GPL3',
    url='https://github.com/gretchycat/termcontrol',
    author='Gretchen Maculo',
    author_email='gretchen.maculo@gmail.com',
    description='python terminal control and basïc gui',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'pyte',
    ],
    tests_require=[
    ],
    #scripts=['termcontrol/termcontrol']
)
