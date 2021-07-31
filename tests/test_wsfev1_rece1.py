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

"""Test para rece1"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.38c"

import pytest
import os
import sys
import time

from pyafipws import wsfev1
from pyafipws import rece1
from pyafipws.wsaa import WSAA

HOMO = wsfev1.HOMO
CONFIG_FILE = "conf/rece.ini"

pytestmark =[pytest.mark.vcr, pytest.mark.dontusefix, pytest.mark.freeze_time('2021-07-30')]

def test_main_prueba():
    sys.argv = []
    sys.argv.append("/debug")
    sys.argv.append("/prueba")
    rece1.main()

def test_main_ayuda():
    sys.argv = []
    sys.argv.append("/ayuda")
    sys.argv.append("debug")
    rece1.main()

def test_main_dummy():
    sys.argv = []
    sys.argv.append("/dummy")
    rece1.main()

def test_main_formato():
    sys.argv = []
    sys.argv.append("/formato")
    rece1.main()



def test_prueba_proyectus():
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("--proyectus")
    rece1.main()

def test_prueba_rg3668():
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("--rg3668")
    rece1.main()

def test_prueba_rg3749():
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("--rg3749")
    rece1.main()

def test_prueba_rg4109():
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("--rg4109")
    rece1.main()

def test_prueba_fce():
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("--fce")
    rece1.main()


def test_main_ult():
    sys.argv = []
    sys.argv.append("/ult")
    sys.argv.append("1")
    sys.argv.append("4002")
    rece1.main()

def test_main_get():
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("/get")
    sys.argv.append("1")
    sys.argv.append("4002")
    sys.argv.append("9070")
    rece1.main()

def test_main_solicitar_caea():
    sys.argv = []
    sys.argv.append("/solicitarcaea")
    sys.argv.append("202107")
    sys.argv.append("2")
    rece1.main()

def test_main_consultar_caea():
    sys.argv = []
    sys.argv.append("/consultarcaea")
    sys.argv.append("202107")
    sys.argv.append("2")
    rece1.main()

def test_main_informarcaeanoutilizadoptovta():
    sys.argv = []
    sys.argv.append("/informarcaeanoutilizadoptovta")
    sys.argv.append("21073372218437")
    sys.argv.append("4002")
    rece1.main()

def test_main_ptosventa():
    sys.argv = []
    sys.argv.append("/ptosventa")
    rece1.main()

def test_main_testing():
    sys.argv = []
    sys.argv.append("--testing")
    rece1.main()
