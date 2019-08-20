# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Test para Módulo WS_SR_PADRON
(Módulo para acceder a los datos de un contribuyente registrado en el Padrón
de AFIP).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import pytest

from pyafipws.wsaa import WSAA
from pyafipws.ws_sr_padron import WSSrPadronA4, WSSrPadronA5


WSDL = "https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA5?wsdl"
CUIT = os.environ['CUIT']
CERT = 'rei.crt'
PKEY = 'rei.key'
CACHE = ""

# obteniendo el TA para pruebas
wsaa = WSAA()
wspa5 = WSSrPadronA5()

ta = wsaa.Autenticar("ws_sr_padron_a5", CERT, PKEY)
# ta = wsaa.Autenticar("ws_sr_padron_a4", CERT, PKEY)
wspa5.Cuit = CUIT
wspa5.SetTicketAcceso(ta)
wspa5.Conectar(CACHE, WSDL)


@pytest.mark.skip
def test_server_status():
    """Test de estado de servidores."""
    # Estados de servidores respuesta no funciona afip
    wspa5.Dummy()
    assert wspa5.AppServerStatus == 'OK'
    assert wspa5.DbServerStatus == 'OK'
    assert wspa5.AuthServerStatus == 'OK'


def test_inicializar():
    """Test inicializar variables de BaseWS."""
    wspa5.inicializar()
    assert wspa5.tipo_doc == 0
    assert wspa5.denominacion == ''
    assert wspa5.actividades == []


@pytest.mark.skip
def test_consultar():
    """Test consultar."""
    # Consulta Nivel A4 afip no esta funcionando.
    id_persona = "20002307554"
    consulta = wspa4.Consultar(id_persona)
    assert consulta


def test_consultar_a5():
    """Test consultar padron nivel A5."""
    id_persona = "20201797064"
    consulta = wspa5.Consultar(id_persona)
    assert consulta
    assert wspa5.direccion == 'LARREA 1'
    assert wspa5.provincia == 'CIUDAD AUTONOMA BUENOS AIRES'
    assert wspa5.cod_postal == '1030'

    # metodo analizar datos
    assert wspa5.imp_iva == 'N'
    assert wspa5.cat_iva == 5
