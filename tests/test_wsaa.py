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

"""Test para WSAA"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import pytest
import os
import sys
import base64
from pyafipws.wsaa import WSAA, call_wsaa, sign_tra_openssl
from pyafipws.wsaa import main
from past.builtins import basestring
from builtins import str
from pyafipws.utils import *
from pysimplesoap import *
DEFAULT_TTL = 60 * 60 * 5  # five hours

WSDL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
CACERT = "conf/afip_ca_info.crt"

pytestmark = [pytest.mark.dontusefix]


#fixture for key and certificate
@pytest.fixture
def key_and_cert():
    KEY = 'reingart.key'
    CERT = 'reingart.crt'
    return [KEY, CERT]


def test_analizar_certificado(key_and_cert):
    """Test analizar datos en certificado."""
    wsaa = WSAA()
    wsaa.AnalizarCertificado(key_and_cert[1])
    assert wsaa.Identidad
    assert wsaa.Caducidad
    assert wsaa.Emisor


def test_crear_clave_privada():
    """Test crear clave RSA."""
    wsaa = WSAA()
    chk = wsaa.CrearClavePrivada()
    assert chk == True


def test_crear_pedido_certificado():
    """Crea CSM para solicitar certificado."""
    wsaa = WSAA()
    chk1 = wsaa.CrearClavePrivada()
    chk2 = wsaa.CrearPedidoCertificado()
    assert chk1 == True
    assert chk2 == True


def test_expirado():
    """Revisar si el TA se encuentra vencido."""
    wsaa = WSAA()
    # checking for expired certificate
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, 'xml/expired_ta.xml')
    chk = wsaa.AnalizarXml(xml=open(file_path, "r").read())
    chk2 = wsaa.Expirado()

    # checking for a valid certificate,i.e. which will 
    # have expiration time 12 hrs(43200 secs) from generation
    fec = str(date("c", date("U") + 43200))
    chk3 = wsaa.Expirado(fecha=fec)

    assert chk == True
    assert chk2 == True
    assert chk3 == False


@pytest.mark.vcr
def test_login_cms(key_and_cert):
    """comprobando si LoginCMS está funcionando correctamente"""
    wsaa = WSAA()

    tra = wsaa.CreateTRA(service="wsfe", ttl=DEFAULT_TTL)
    cms = wsaa.SignTRA(tra, key_and_cert[1], key_and_cert[0])
    chk = wsaa.Conectar(cache=None, wsdl=WSDL, cacert=CACERT, proxy=None)
    ta_xml = wsaa.LoginCMS(cms)

    ta = SimpleXMLElement(ta_xml)

    if not isinstance(cms, str):
        cms = cms.decode('utf-8')

    assert isinstance(cms, str)
   
    assert cms.startswith('MII')

    assert chk == True
    assert ta_xml.startswith('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    assert ta.credentials.token
    assert ta.credentials.sign

    assert "<source>" in ta_xml
    assert "<destination>" in ta_xml
    assert "<uniqueId>" in ta_xml
    assert "<expirationTime>" in ta_xml
    assert "<generationTime>" in ta_xml
    assert "<credentials>" in ta_xml
    assert "<token>" in ta_xml
    assert "<sign>" in ta_xml
    assert ta_xml.endswith("</loginTicketResponse>\n")


def test_wsaa_create_tra():
    wsaa = WSAA()
    tra = wsaa.CreateTRA(service="wsfe")

    # sanity checks:
    assert isinstance(tra, basestring)
    assert tra.startswith(
        '<?xml version="1.0" encoding="UTF-8"?>' '<loginTicketRequest version="1.0">'
    )
    assert "<uniqueId>" in tra
    assert "<expirationTime>" in tra
    assert "<generationTime>" in tra
    assert tra.endswith("<service>wsfe</service></loginTicketRequest>")


def test_wsaa_sign():
    wsaa = WSAA()
    tra = '<?xml version="1.0" encoding="UTF-8"?><loginTicketRequest version="1.0"/>'
    # TODO: use certificate and private key as fixture / PEM text (not files)
    cms = wsaa.SignTRA(tra, "reingart.crt", "reingart.key")
    # TODO: return string
    if not isinstance(cms, str):
        cms = cms.decode("utf8")
    # sanity checks:
    assert isinstance(cms, str)
    out = base64.b64decode(cms)
    assert tra.encode("utf8") in out


def test_wsaa_sign_tra(key_and_cert):
    wsaa = WSAA()

    tra = wsaa.CreateTRA("wsfe")
    sign = wsaa.SignTRA(tra, key_and_cert[1], key_and_cert[0])

    if not isinstance(sign, str):
        sign = sign.decode('utf-8')

    assert isinstance(sign, str)
    assert sign.startswith("MII")

def test_wsaa_sign_openssl(key_and_cert):
    wsaa = WSAA()

    tra = wsaa.CreateTRA("wsfe").encode()
    sign = sign_tra_openssl(tra, key_and_cert[1], key_and_cert[0])

    # check if the commanmd line input is a byte data
    assert isinstance(sign, bytes)

    if isinstance(sign, bytes):
        sign = sign.decode("utf8")
        
    assert sign.startswith("MII")



def test_wsaa_sign_tra_inline(key_and_cert):
    wsaa = WSAA()

    tra = wsaa.CreateTRA("wsfe")
    sign = wsaa.SignTRA(tra, key_and_cert[1], key_and_cert[0])

    sign_2 = wsaa.SignTRA(
        tra, open(key_and_cert[1]).read(), open(key_and_cert[0]).read()
    )

    if not isinstance(sign, str):
        sign = sign.decode('utf-8')

    if not isinstance(sign_2, str):
        sign_2 = sign_2.decode('utf-8')

    assert isinstance(sign, str)
    assert sign.startswith("MII")

    assert isinstance(sign_2, str)
    assert sign_2.startswith("MII")


@pytest.mark.vcr
def test_main():
    sys.argv = []
    sys.argv.append("--debug")
    main()


@pytest.mark.vcr
def test_main_crear_pedido_cert():
    sys.argv = []
    sys.argv.append("--crear_pedido_cert")
    sys.argv.append("20267565393")
    sys.argv.append("PyAfipWs")
    sys.argv.append("54654654")
    sys.argv.append(" ")
    main()


@pytest.mark.vcr
def test_main_analizar():
    sys.argv = []
    sys.argv.append("--analizar")
    main()


@pytest.mark.vcr
def test_CallWSAA(key_and_cert):
    wsaa = WSAA()
    tra = wsaa.CreateTRA(service="wsfe", ttl=DEFAULT_TTL)
    cms = wsaa.SignTRA(tra, key_and_cert[1], key_and_cert[0])
    assert wsaa.CallWSAA(cms, WSDL)


@pytest.mark.vcr
def test_call_wsaa(key_and_cert):
    wsaa = WSAA()
    tra = wsaa.CreateTRA(service="wsfe", ttl=DEFAULT_TTL)
    cms = wsaa.SignTRA(tra, key_and_cert[1], key_and_cert[0])
    assert call_wsaa(cms, WSDL)
