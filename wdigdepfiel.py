#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para interfaz Depositario Fiel web service wDigDepFiel de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.01"

LICENCIA = """
wdigdepfiel.py: Interfaz para Digitalizacion Depositario Fiel AFIP
Copyright (C) 2010 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

import os, sys, time
from utils import date, SimpleXMLElement, SoapClient, SoapFault

WSDDFURL = "https://testdia.afip.gov.ar/Dia/Ws/wDigDepFiel/wDigDepFiel.asmx"
SOAP_ACTION = 'ar.gov.afip.dia.serviciosWeb.wDigDepFiel/'
SOAP_NS = 'ar.gov.afip.dia.serviciosWeb.wDigDepFiel'

DEBUG = True
XML = False
HOMO = True


def dummy(client):
    "Metodo dummy para verificacion de funcionamiento"
    response = client.Dummy()
    result = response.DummyResult
    appserver = dbserver = authserver = None
    try:
        appserver = str(result.appserver)
        dbserver = str(result.dbserver)
        authserver = str(result.authserver)
    except (RuntimeError, IndexError, AttributeError), e:
        pass
    return {'appserver': appserver,
            'dbserver': dbserver,
            'authserver': authserver}

def aviso_recep_acept(client, token, sign, cuit, tipo_agente, rol, 
                      nro_legajo, cuit_declarante, cuit_psad, cuit_ie,
                          codigo, fecha_hora_acept, ticket):
    "Aviso de recepcion y aceptacion."
    response = client.AvisoRecepAcept(
                autentica=dict(Cuit=cuit, Token=token, Sign=sign, TipoAgente=tipo_agente, Rol=rol),
                nroLegajo=nro_legajo,
                cuitDeclarante=cuit_declarante,
                cuitPSAD=cuit_psad,
                cuitIE=cuit_ie,
                codigo=codigo,
                fechaHoraAcept=fecha_hora_acept,
                ticket=ticket,
                )
    result = response.AvisoRecepAceptResult
    return str(result.codError), str(result.descError) 


def aviso_digit(client, token, sign, cuit, tipo_agente, rol, 
                nro_legajo, cuit_declarante, cuit_psad, cuit_ie, cuit_ata,
                codigo, url, familias, ticket, hashing, cantidad_total):
    "Aviso de digitalizacion."
    response = client.AvisoDigit(
                autentica=dict(Cuit=cuit, Token=token, Sign=sign, TipoAgente=tipo_agente, Rol=rol),
                nroLegajo=nro_legajo,
                cuitDeclarante=cuit_declarante,
                cuitPSAD=cuit_psad,
                cuitIE=cuit_ie,
                cuitATA=cuit_ata,
                codigo=codigo,
                url=url,
                familias=familias,
                ticket=ticket,
                hashing=hashing,
                cantidadTotal=cantidad_total,
                )
    result = response.AvisoDigitResult
    return str(result.codError), str(result.descError) 


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    import csv
    import traceback
    import datetime

    import wsaa

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        CERT='reingart.crt'
        PRIVATEKEY='reingart.key'
        # obteniendo el TA
        TA = "wsddf-ta.xml"
        if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
            tra = wsaa.create_tra(service="wDigDepFiel")
            cms = wsaa.sign_tra(tra,CERT,PRIVATEKEY)
            ta_string = wsaa.call_wsaa(cms)
            open(TA,"w").write(ta_string)
        ta_string=open(TA).read()
        ta = SimpleXMLElement(ta_string)
        token = str(ta.credentials.token)
        sign = str(ta.credentials.sign)
        # fin TA
    
        # cliente soap del web service
        client = SoapClient(WSDDFURL, 
            action = SOAP_ACTION, 
            namespace = SOAP_NS, exceptions = True,
            trace = True, ns = 'ar', soap_ns='soap')
        
        if '--dummy' in sys.argv:
            ret = dummy(client)
            print '\n'.join(["%s: %s" % it for it in ret.items()])    

        # ejemplos aviso recep acept (prueba):
            
        cuit = 20267565393
        tipo_agente = 'DESP' # 'DESP'
        rol = 'EXTE'
        nro_legajo = '0'*16 # '1234567890123456'
        cuit_declarante = cuit_psad = cuit_ie = cuit
        codigo = '000' # carpeta completa, '0001' carpeta adicional
        fecha_hora_acept = datetime.datetime.now().isoformat()
        ticket = '1234'
        r = aviso_recep_acept(client, token, sign, cuit, tipo_agente, rol,
                              nro_legajo, cuit_declarante, cuit_psad, cuit_ie,
                              codigo, fecha_hora_acept, ticket)
        print r


        # ejemplos aviso digit (prueba):

        cuit = 20267565393
        tipo_agente = 'DESP' # 'DESP'
        rol = 'EXTE'
        nro_legajo = '0'*16 # '1234567890123456'
        cuit_declarante = cuit_psad = cuit_ie = cuit_ata = cuit
        codigo = '000' # carpeta completa, '0001' carpeta adicional
        ticket = '1234'
        url = 'http://www.example.com'
        hashing = 'db1491eda47d78532cdfca19c62875aade941dc2'
        familias = [ {'Familia': {'codigo': '02', 'cantidad': 1}}, {'Familia': {'codigo': '03', 'cantidad': 3}}, ] 
        cantidad_total = 4
        r = aviso_digit(client, token, sign, cuit, tipo_agente, rol,
                        nro_legajo, cuit_declarante, cuit_psad, cuit_ie, cuit_ata,
                        codigo, url, familias, ticket, hashing, cantidad_total)
        print r
        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
