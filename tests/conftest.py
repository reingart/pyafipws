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

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2021- Mariano Reingart"
__license__ = "GPL 3.0"


WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
CUIT = 20267565393
# CERT = "/home/reingart/pyafipws/reingart.crt"
# PRIVATEKEY = "/home/reingart/pyafipws/reingart.key"
# CACERT = "/home/reingart/pyafipws/afip_root_desa_ca.crt"
# CACHE = "/home/reingart/pyafipws/cache"

os.environ["CUIT"] = str(CUIT)