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

"""Test para Módulo WSCDC(Constatación de Comprobantes)."""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import sys
import pytest
import unittest
from pyafipws.wsaa import WSAA
from pyafipws.wscdc import WSCDC
from pyafipws import wscdc as ws


WSDL = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""

pytestmark =pytest.mark.vcr


@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)



wscdc = WSCDC()
@pytest.fixture(autouse=True)
def auth():
    wsc = ws
    ta = WSAA().Autenticar("wscdc", CERT, PKEY)
    wscdc.Cuit = CUIT
    wscdc.SetTicketAcceso(ta)
    wscdc.Conectar(CACHE, WSDL)
    return [wscdc,wsc]


@pytest.mark.skip
def test_server_status(auth):
    """Test de estado de servidores."""
    wscdc=auth[0]
    wscdc.Dummy()
    assert wscdc.AppServerStatus == "OK"
    assert wscdc.DbServerStatus == "OK"
    assert wscdc.AuthServerStatus == "OK"


def test_inicializar(auth):
    """Test inicializar variables de BaseWS."""
    wscdc=auth[0]
    wscdc.inicializar()
    assert wscdc.ImpTotal is None
    assert wscdc.Resultado == ""


def test_analizar_errores(auth):
    """Test analizar si se encuentran errores."""
    wscdc=auth[0]
    ret = {
        "Errors": [
            {
                "Err": {
                    "Code": 100,
                    "Msg": "El N° de CAI/CAE/CAEA consultado no existe"
                    "en las bases del organismo.",
                }
            }
        ]
    }
    wscdc._WSCDC__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wscdc.ErrMsg


def test_constatar_comprobante(auth):
    """Test constatar comprobante."""
    wscdc=auth[0]
    wsc=auth[1]
    datos_consulta = dict(
        cbte_modo="CAE",
        cuit_emisor="20267565393",
        pto_vta=5,
        cbte_tipo=1,
        cbte_nro=2424,
        cbte_fch="20190813",
        imp_total=1754.5,
        cod_autorizacion="69333775104382",
        doc_tipo_receptor=80,
        doc_nro_receptor=20888888883,
    )

    constatar = wscdc.ConstatarComprobante(**datos_consulta)

    assert constatar
    assert wscdc.Resultado == "A"

    nombre_archivo = "datos_consulta.json"
    # Indico comando interno para lectura y escritura
    sys.argv.append("--json")

    if not os.path.exists(nombre_archivo):
        archivo = wsc.escribir_archivo(datos_consulta, nombre_archivo)
        assert os.path.isfile(nombre_archivo)

    archivo = wsc.leer_archivo(nombre_archivo)
    assert archivo
    assert isinstance(archivo, dict)


def test_consultar_modalidad_comprobantes(auth):
    """Test consultar modalidad comprobantes."""
    wscdc=auth[0]
    consulta = wscdc.ConsultarModalidadComprobantes()
    assert consulta


def test_consultar_tipo_comprobantes(auth):
    """Test consultar tipo comprobantes."""
    wscdc=auth[0]
    consulta = wscdc.ConsultarTipoComprobantes()
    assert consulta


def test_consultar_tipo_documentos(auth):
    """Test consultar tipo documentos."""
    wscdc=auth[0]
    consulta = wscdc.ConsultarTipoDocumentos()
    assert consulta


def test_consultar_tipo_opcionales(auth):
    """Test consultar tipo opcionales."""
    # Error 503: No existen datos en nuestros registros.
    # Error afip: No esta funcionado esta consulta en el WS
    wscdc=auth[0]
    consulta = wscdc.ConsultarTipoOpcionales()
    assert consulta == []


