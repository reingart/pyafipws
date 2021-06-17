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

from pyafipws.wsaa import WSAA
from pyafipws.wscdc import WSCDC
from pyafipws import wscdc


WSDL = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL"
CUIT = os.environ["CUIT"]
CERT = "rei.crt"
PKEY = "rei.key"
CACHE = ""

wsc = wscdc
wsaa = WSAA()
wscdc = WSCDC()
# obteniendo el TA para pruebas
ta = wsaa.Autenticar("wscdc", CERT, PKEY)
wscdc.Cuit = CUIT
wscdc.SetTicketAcceso(ta)
wscdc.Conectar(CACHE, WSDL)


@pytest.mark.skip
def test_server_status():
    """Test de estado de servidores."""
    wscdc.Dummy()
    assert wscdc.AppServerStatus == "OK"
    assert wscdc.DbServerStatus == "OK"
    assert wscdc.AuthServerStatus == "OK"


def test_inicializar():
    """Test inicializar variables de BaseWS."""
    wscdc.inicializar()
    assert wscdc.ImpTotal is None
    assert wscdc.Resultado == ""


def test_analizar_errores():
    """Test analizar si se encuentran errores."""
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


def test_constatar_comprobante():
    """Test constatar comprobante."""
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


def test_consultar_modalidad_comprobantes():
    """Test consultar modalidad comprobantes."""
    consulta = wscdc.ConsultarModalidadComprobantes()
    assert consulta


def test_consultar_tipo_comprobantes():
    """Test consultar tipo comprobantes."""
    consulta = wscdc.ConsultarTipoComprobantes()
    assert consulta


def test_consultar_tipo_documentos():
    """Test consultar tipo documentos."""
    consulta = wscdc.ConsultarTipoDocumentos()
    assert consulta


def test_consultar_tipo_opcionales():
    """Test consultar tipo opcionales."""
    # Error 503: No existen datos en nuestros registros.
    # Error afip: No esta funcionado esta consulta en el WS
    consulta = wscdc.ConsultarTipoOpcionales()
    assert consulta == []
