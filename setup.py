#!/usr/bin/env python
#
# Copyright 2015 Adam Victor Brandizzi
#
# This file is part of Ugly.
#
# Ugly is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ugly is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Ugly.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

setup(
    name='ugly',
    version="0.0.1",
    author='Adam Victor Brandizzi',
    author_email='adam@brandizzi.com.br',
    description='Ugly, a directory of weird helpers for tests.',
    long_description="""
    "Ugly" is a set of not very elegant tools to help testing. So far there are
    four packages:

    ugly.net: the most important tools are the waiter functions:
    ugly.net.wait_server_down() will block until a port in a host is not
    accepting connections anymore, and ugly.net.wait_server_up() will block
    until a port in the host will be ready for receiving data. There is also
    ugly.net.Server, that sets up a very dumb SocketServer.TCPServer subclass
    for testing.

    ugly.finder: contains the ugly.finder.TestFinder class. It is a
    unittest.TestSuite subclass that makes the task of finding test cases and
    doctests way less annoying.

    ugly.module: with ugly.module.create_module(), one can create fully
    importable Python modules. ugly.module.installed_module() will create and
    remove the importable module.

    ugly.process: home of ugly.process.Process, a nice multiprocessing.Process
    subclass that makes the process of starting, stopping and communicating
    with a function in another process easier enough.

    For more info, check the project page.
    """,
    license='LGPLv3',
    url='https://bitbucket.com/brandizzi/ugly',

    packages=find_packages(),

    test_suite='ugly.test'
)
