#!/usr/bin/env python
#
# Copyright 2015 Adam Victor Brandizzi
#
# This file is part of Inelegant.
#
# Inelegant is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Inelegant is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Inelegant.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

setup(
    name='inelegant',
    version="0.2.0",
    author='Adam Victor Brandizzi',
    author_email='adam@brandizzi.com.br',
    description='Inelegant, a directory of weird helpers for tests.',
    long_description="""
    "Inelegant" is a set of not very elegant tools to help testing. So far
    there are eight packages:

    inelegant.net: the most important tools are the waiter functions.
    inelegant.net.wait_server_down() will block until a port in a host is not
    accepting connections anymore, and inelegant.net.wait_server_up() will
    block until a port in the host will be ready for receiving data. There is
    also inelegant.net.Server, that sets up a very dumb SocketServer.TCPServer
    subclass for testing.

    inelegant.finder: contains the inelegant.finder.TestFinder class. It is a
    unittest.TestSuite subclass that makes the task of finding test cases and
    doctests way less annoying.

    inelegant.module: with inelegant.module.create_module(), one can create
    fully importable Python modules. inelegant.module.installed_module() will
    create and remove the importable module. There are other related functions.

    inelegant.process: home of inelegant.process.Process, a nice
    multiprocessing.Process subclass that makes the process of starting,
    stopping and communicating with a function in another process easier
    enough.

    inelegant.fs: tools for file system operations. Most notably, context
    managers to make such operations reverted. So, now once can "cd" into a
    directory and be back to the original one, create a temporary file and have
    it automatically deleted after the context, and the same with temporary
    directories.

    inelegant.dict: it provides the temp_key() context manager. It adds a key
    to a dictionary and, once its context is done, removes the key.

    inelegant.toggle: it provides the Toggle class. It is used to create
    flags to enable global behaviors. A toggle is, indeed, something you would
    rather avoid but may need.

    inelegant.io: tools to process standard input/output/error. Right now it
    has four context managers: redirect_stdout() and redirect_stderr(), that
    redirect the standard output and the standard error, respectively, to a
    file, and suppress_stdout() and suppress_stderr(), that only discard
    content written to these files.

    For more info, check the project page.
    """,
    keywords=['test', 'testing'],
    license='LGPLv3',
    url='https://bitbucket.com/brandizzi/inelegant',

    packages=find_packages(),

    test_suite='inelegant.test',
    test_loader='unittest:TestLoader'
)
