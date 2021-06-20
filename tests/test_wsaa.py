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
from pyafipws.wsaa import WSAA
from pyafipws.utils import *
from pysimplesoap import *
DEFAULT_TTL = 60 * 60 * 5  # five hours

WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
CACERT = "conf/afip_ca_info.crt"


@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)


#fixture for key and certificate
@pytest.fixture
def key_and_cert():
    KEY='reingart.key'
    CERT='reingart.crt'
    return [KEY,CERT]


def test_analizar_certificado(key_and_cert):
    """Test analizar datos en certificado."""
    wsaa=WSAA()
    wsaa.AnalizarCertificado(key_and_cert[1])
    assert wsaa.Identidad
    assert wsaa.Caducidad
    assert wsaa.Emisor

def test_crear_clave_privada():
    """Test crear clave RSA."""
    wsaa=WSAA()
    chk = wsaa.CrearClavePrivada()
    assert chk==True

def test_crear_pedido_certificado():
    """Crea CSM para solicitar certificado."""
    wsaa=WSAA()
    chk1 = wsaa.CrearClavePrivada()
    chk2 = wsaa.CrearPedidoCertificado()
    assert chk1==True
    assert chk2==True

@pytest.mark.xfail
def test_expirado():
    """Revisar si el TA se encuentra vencido."""
    wsaa=WSAA()
    #checking for expired certificate
    chk=wsaa.AnalizarXml(xml=open(r"tests\xml\expired_ta.xml", "r").read())
    chk2=wsaa.Expirado()

    #checking for a valid certificate,i.e. which will 
    #have expiration time 12 hrs(43200 secs) from generation
    fec=str(date("c", date("U") + 43200))
    chk3=wsaa.Expirado(fecha=fec)

    assert chk==True
    assert chk2==True
    assert chk3==False


@pytest.mark.vcr
def test_login_cms(key_and_cert):
    """comprobando si LoginCMS está funcionando correctamente"""
    wsaa = WSAA()

    tra=wsaa.CreateTRA(service="wsfe",ttl=DEFAULT_TTL)
    cms=wsaa.SignTRA(tra,key_and_cert[1],key_and_cert[0])
    chk=wsaa.Conectar(cache=None, wsdl=WSAAURL,cacert=CACERT,proxy=None)
    ta_xml = wsaa.LoginCMS(cms)

    ta = SimpleXMLElement(ta_xml)

    assert isinstance(cms,str)
    assert cms.startswith('MIIG+')

    assert chk==True
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




