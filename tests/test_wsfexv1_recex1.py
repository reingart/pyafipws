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

"""Test para recex1"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.38c"

import pytest
import shutil
import sys
import time

from pyafipws import wsfexv1
from pyafipws import recex1
from pyafipws.wsaa import WSAA

HOMO = wsfexv1.HOMO
CONFIG_FILE = "conf/rece.ini"

# entrada.txt required for testing
shutil.copy('tests/txt/entrada_recex1.txt','entrada.txt')

pytestmark =[pytest.mark.vcr, pytest.mark.dontusefix, pytest.mark.freeze_time('2021-08-02')]


def test_main_ayuda():
    sys.argv = []
    sys.argv.append('/ayuda')
    sys.argv.append('/debug')
    recex1.main()


def test_main_prueba():
    sys.argv = []
    sys.argv.append('/prueba')
    recex1.main()

def test_main_dummy():
    sys.argv = []
    sys.argv.append('/dummy')
    recex1.main()

def test_main_formato():
    sys.argv = []
    sys.argv.append('/formato')
    recex1.main()

def test_main_ult():
    sys.argv = []
    sys.argv.append('/ult')
    sys.argv.append('21')
    sys.argv.append('7')
    recex1.main()

def test_main_get():
    sys.argv = []
    sys.argv.append('/get')
    sys.argv.append('21')
    sys.argv.append('7')
    sys.argv.append('28')
    recex1.main()

def test_main_ctz():
    sys.argv = []
    sys.argv.append('/ctz')
    sys.argv.append('DOL')
    recex1.main()

def test_main_monctz():
    sys.argv = []
    sys.argv.append('/monctz')
    sys.argv.append('')
    recex1.main()