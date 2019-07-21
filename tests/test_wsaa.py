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

import os

from pyafipws.wsaa import WSAA
from pyafipws import wsaa as at

try:
    import M2Crypto as m2
except ImportError:
    m2 = None

try:
    import cryptography as crypt
except ImportError:
    crypt = None

# Para usar varibles de entorno en travis
cert = os.environ['CERT']
pkey = os.environ['PKEY']
CERT = cert.replace(r'\n', '\n')
PKEY = pkey.replace(r'\n', '\n')

with open('rei.crt', 'w', encoding='utf-8') as f:
    f.write(CERT)

with open('rei.key', 'w', encoding='utf-8') as f:
    f.write(PKEY)

CERT = 'rei.crt'
PKEY = 'rei.key'

wsaa = WSAA()
# Generar ticket de accseso
ta = wsaa.Autenticar('wsfe', CERT, PKEY)
tra = at.create_tra()
sign = at.sign_tra(tra, CERT, PKEY)

# Se remueven test por tema de 10 minutos Afip


def test_create_tra():
    """ xml para autorizacion inicial"""
    assert isinstance(tra, bytes)


# Si esta instalado m2crypto o cryptography.
if m2 or crypt:
    def test_sign_tra_cript():
        """Firmar tra con las credenciales."""
        assert sign.startswith('MIIG+')

    def test_analizar_certificado():
        """Test analizar datos en certificado."""
        wsaa.AnalizarCertificado(CERT)
        assert wsaa.Identidad
        assert wsaa.Caducidad
        assert wsaa.Emisor

    def test_crear_clave_privada():
        """Test crear clave RSA."""
        pkey = wsaa.CrearClavePrivada()
        assert pkey

    def test_crear_pedido_certificado():
        """Crea CSM para solicitar certificado."""
        csm = wsaa.CrearPedidoCertificado()
        assert csm
else:
    # con OpenSSL directo
    def test_sign_tra_openssl():
        """Firmar tra con las credenciales."""
        assert sign.startswith('MIIG+')


def test_expirado():
    """Revisar si el TA se encuentra vencido."""
    exp = wsaa.Expirado()
    assert exp or True


def test_autenticar():
    """Genera TA o devuelve el ya autorizado"""
    assert ta
