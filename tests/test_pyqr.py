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

"""Test para pyqr"""


__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

from pyafipws.pyqr import PyQR, main
from PIL import Image, ImageChops
import base64
import json
import os
import sys
import tempfile
import traceback
import pytest
import qrcode

pytestmark = [pytest.mark.dontusefix]

pyqr = PyQR()

def test_GenerarImagen():
    "Prueba de generación de una imagen"
    ver = 1
    fecha = "2020-10-13"
    cuit = 30000000007
    pto_vta = 10
    tipo_cmp = 1
    nro_cmp = 94
    importe = 12100
    moneda = "DOL"
    ctz = 65.000
    tipo_doc_rec = 80
    nro_doc_rec = 20000000001
    tipo_cod_aut = "E"
    cod_aut = 70417054367476

    url = pyqr.GenerarImagen(
        ver,
        fecha,
        cuit,
        pto_vta,
        tipo_cmp,
        nro_cmp,
        importe,
        moneda,
        ctz,
        tipo_doc_rec,
        nro_doc_rec,
        tipo_cod_aut,
        cod_aut,
    )

    assert url.startswith("https://www.afip.gob.ar/fe/qr/?p=")

def test_CrearArchivo():
    "Prueba de creación de un archivo"
    ok = pyqr.CrearArchivo()
    assert ok 

def test_main():
    sys.argv = []
    url = main()
    assert url.startswith("https://www.afip.gob.ar/fe/qr/?p=")

def test_main_prueba():
    sys.argv = []
    sys.argv.append("--prueba")
    main()

def test_main_mostrar(mocker):
    mocker.patch("os.system")
    sys.argv = []
    archivo = "qr.png"
    sys.argv.append("--archivo")
    sys.argv.append(archivo)
    sys.argv.append("--mostrar")
    main()
    if(sys.platform == 'linux2' or sys.platform == 'linux'):
        os.system.assert_called_with("eog " "%s" "" % archivo)

@pytest.mark.xfail
def test_main_archivo():
    archivo = "prueba_qr.png"
    sys.argv = []
    sys.argv.append("--archivo")
    sys.argv.append(archivo)
    main()

    assert os.path.exists(archivo)
    #compare the image with a reference one
    ref = Image.open("tests/images/qr.png")
    test = Image.open(archivo)
    diff = ImageChops.difference(ref, test)
    assert diff.getbbox() is None