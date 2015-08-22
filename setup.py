#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="ugly",
    version="0.0.1",
    author='Adam Victor Brandizzi',
    author_email='adam@brandizzi.com.br',
    description='Ugly things we want to do with tests all the time.',
    license='LGPLv3',
    url='http://bitbucket.com/brandizzi/ugly',

    packages=find_packages(),

    test_suite='ugly.test'
)
