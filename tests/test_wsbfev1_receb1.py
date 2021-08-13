#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Test para receb1"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.38c"

import pytest
import sys
import shutil
from pyafipws import wsbfev1
from pyafipws import receb1
from pyafipws.wsaa import WSAA

HOMO = wsbfev1.HOMO
CONFIG_FILE = "conf/rece.ini"

# entrada.txt required for testing
shutil.copy('tests/txt/entrada_receb1.txt','entrada.txt')

pytestmark =[pytest.mark.vcr, pytest.mark.dontusefix, pytest.mark.freeze_time('2021-08-02')]

def test_main_ayuda():
    sys.argv = []
    sys.argv.append('/debug')
    sys.argv.append('/ayuda')
    receb1.main()


def test_main_formato():
    sys.argv = []
    sys.argv.append('/formato')
    receb1.main()

def test_main_prueba():
    sys.argv = []
    sys.argv.append('/prueba')
    sys.argv.append('/debug')
    receb1.main()

def test_main_dummy():
    sys.argv = []
    sys.argv.append('/dummy')
    receb1.main()

def test_main_ult():
    sys.argv = []
    sys.argv.append('/ult')
    sys.argv.append('1')
    sys.argv.append('2')
    receb1.main()

def test_main_id():
    sys.argv = []
    sys.argv.append('/id')
    receb1.main()

def test_main_get():
    sys.argv = []
    sys.argv.append('/get')
    sys.argv.append('1')
    sys.argv.append('2')
    sys.argv.append('133833')
    receb1.main()