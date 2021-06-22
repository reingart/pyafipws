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

import os
import pytest
from pyafipws.wsaa import WSAA

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2021- Mariano Reingart"
__license__ = "GPL 3.0"


WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
CUIT = 20267565393
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE=""
# CERT = "/home/reingart/pyafipws/reingart.crt"
# PRIVATEKEY = "/home/reingart/pyafipws/reingart.key"
# CACERT = "/home/reingart/pyafipws/afip_root_desa_ca.crt"
# CACHE = "/home/reingart/pyafipws/cache"

os.environ["CUIT"] = str(CUIT)

#fixture for setting directory
@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)

#WSAA authentication fixture, used by all tests
@pytest.fixture(autouse=True)
def auth(request):
    if 'dontusefix' in request.keywords:
        return
    z=request.module.__obj__
    z.Cuit = CUIT
    wsaa=WSAA()
    ta = wsaa.Autenticar(request.module.__service__, CERT, PKEY)
    z.SetTicketAcceso(ta)
    z.Conectar(CACHE, request.module.__WSDL__)
    return z