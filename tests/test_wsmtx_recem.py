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

"""Test para recem"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.38c"

import pytest
import os
import sys
import time

from pyafipws import wsmtx
from pyafipws import recem
from pyafipws.wsaa import WSAA

HOMO = wsmtx.HOMO
CONFIG_FILE = "conf/rece.ini"

pytestmark =[pytest.mark.vcr, pytest.mark.dontusefix]


def test_main_prueba():
    sys.argv = []
    sys.argv.append("/debug")
    sys.argv.append("/prueba")
    recem.main()

def test_main_prueba_fce():
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("--fce")
    recem.main()

def test_main_ayuda():
    sys.argv = []
    sys.argv.append("/debug")
    sys.argv.append("/ayuda")
    recem.main()

def test_main_dummy():
    sys.argv = []
    sys.argv.append("/debug")
    sys.argv.append("/dummy")
    recem.main()

def test_main_formato():
    sys.argv = []
    sys.argv.append("/formato")
    recem.main()

def test_main_puntosventa():
    sys.argv = []
    sys.argv.append("/puntosventa")
    recem.main()

def test_main_ult():
    sys.argv = []
    sys.argv.append("/ult")
    sys.argv.append("1")
    sys.argv.append("4000")
    recem.main()

def test_main_get():
    sys.argv = []
    sys.argv.append("/get")
    sys.argv.append("1")
    sys.argv.append("4000")
    sys.argv.append("1845")
    recem.main()

def test_main_solicitarcaea():
    sys.argv = []
    sys.argv.append("/solicitarcaea")
    sys.argv.append("202108")
    sys.argv.append("1")
    recem.main()

def test_main_consultarcaea():
    sys.argv = []
    sys.argv.append("/consultarcaea")
    sys.argv.append("202108")
    sys.argv.append("1")
    recem.main()

def test_main_ptosventa():
    sys.argv = []
    sys.argv.append("/ptosventa")
    recem.main()


def test_main_informarcaeanoutilizado():
    sys.argv = []
    sys.argv.append("/informarcaeanoutilizado")
    sys.argv.append("21353598240916")
    recem.main()

def test_main_informarcaeanoutilizadoptovta():
    sys.argv = []
    sys.argv.append("/informarcaeanoutilizadoptovta")
    sys.argv.append("21353598240916")
    sys.argv.append("4000")
    recem.main()

