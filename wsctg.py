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

"""Módulo para obtener código de trazabilidad de granos
del web service WSCTG de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.04"

LICENCIA = """
wsctg.py: Interfaz para generar Código de Trazabilidad de Granos AFIP
Copyright (C) 2010 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA="""
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una CTG de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)

  --dummy: consulta estado de servidores
  --solicitar: obtiene el CTG
  --confirmar: confirma el CTG 

  --provincias: obtiene el listado de provincias
  --localidades: obtiene el listado de localidades por provincia
  --especies: obtiene el listado de especies
  --cosechas: obtiene el listado de cosechas

Ver wsctg.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time
from php import date, SimpleXMLElement, SoapClient, SoapFault

WSCTGURL = "https://fwshomo.afip.gov.ar/wsctg/services/CTGService"
SOAP_ACTION = 'http://impl.service.wsctg.afip.gov.ar/CTGService/'
SOAP_NS = 'http://impl.service.wsctg.afip.gov.ar/CTGService/'

DEBUG = False
XML = False
CONFIG_FILE = "wsctg.ini"
HOMO = True


def dummy(client):
    "Metodo dummy para verificacion de funcionamiento"
    response = client.dummy()
    result = response.dummyResponse
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


def obtener_provincias(client, token, sign, cuit):
    "Obtener el código y descripción de todas las Provincias de la República Argentina"
    response = client.call("obtenerProvincias", 
        ('auth', (("token",token), ("sign",sign), ("cuitRepresentado",cuit))))

    items = [] 
    for ret in response.obtenerProvinciasResponse.__getattr__("return"):
        it = {'codigo': str(ret.codigoProvincia), 
               'descripcion': ret.descripcionProvincia,
               }
        items.append(it)
    return items


def obtener_localidades_por_codigo_provincia(client, token, sign, cuit, codigo):
    "Obtener el código y descripción de las Localidades según el código de Provincia solicitado"
    response = client.call("obtenerLocalidadesPorCodigoProvincia", 
        ("auth", (("token",token), ("sign",sign), ("cuitRepresentado",cuit))), 
        ("obtenerLocalidadesPorCodigoProvinciaRequest", (("codigoProvincia",codigo),)))
    
    items = [] 
    for ret in response.obtenerLocalidadesPorCodigoProvinciaResponse.__getattr__("return"):
        it = {'codigo': str(ret.codigoLocalidad), 
               'descripcion': ret.descripcionLocalidad,
               }
        items.append(it)
    return items


def obtener_especies(client, token, sign, cuit):
    "Obtener el código y descripción de las Especies habilitadas"
    response = client.call("obtenerEspecies", 
        ('auth', (("token",token), ("sign",sign), ("cuitRepresentado",cuit))))
    
    items = [] 
    for ret in response.obtenerEspeciesResponse.__getattr__("return"):
        it = {'codigo': str(ret.codigoEspecie), 
               'descripcion': ret.descripcionEspecie,
               }
        items.append(it)
    return items


def obtener_cosechas(client, token, sign, cuit, **kwargs ):
    "Obtener el código y descripción de las Cosechas habilitadas"

    response = client.call("obtenerCosechas", 
        ('auth', (("token",token), ("sign",sign), ("cuitRepresentado",cuit))))
    
    items = [] 
    for ret in response.obtenerCosechasResponse.__getattr__("return"):
        it = {'codigo': str(ret.codigoCosecha), 
               'descripcion': ret.descripcionCosecha,
               }
        items.append(it)
    return items

ARG_SOLICITAR_CTG = ("numeroCartaDePorte", "codigoEspecie",
        "cuitRemitenteComercial", "cuitDestino", "cuitDestinatario", "codigoLocalidadOrigen", 
        "codigoLocalidadDestino", "codigoCosecha", "pesoNetoCarga", "cantHoras", 
        "patenteVehiculo", "cuitTransportista", )
RET_SOLICITAR_CTG = 'numeroCTG'

def solicitar_ctg(client, token, sign, cuit, **kwargs):
    "Obtener el CTG"
    
    args = [(k, kwargs[k]) for k in ARG_SOLICITAR_CTG]

    response = client.call("solicitarCTG", 
        ("auth", (("token", token), ("sign", sign), ("cuitRepresentado", cuit))),
        ("solicitarCTGRequest", tuple(args)))
    
    result = response.solicitarCTGResponse
    return str(result.numeroCTG)


ARG_CONFIRMAR_CTG = ("numeroCartaDePorte", "numeroCTG",
        "cuitTransportista", "pesoNetoCarga", )
RET_CONFIRMAR_CTG = ("codigoTransaccion", "observaciones")

def confirmar_ctg(client, token, sign, cuit, **kwargs):
    "Confirmar el CTG"

    # ordeno los parámetros
    args = [(k, kwargs[k]) for k in ARG_CONFIRMAR_CTG]

    response = client.call("confirmarCTG", 
        ("auth", (("token", token), ("sign", sign), ("cuitRepresentado", cuit))),
        ("confirmarCTGRequest", tuple(args)))
    
    result = response.confirmarCTGResponse
    return str(result.codigoTransaccion), str(result.observaciones)


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    import csv
    import traceback
    from ConfigParser import SafeConfigParser

    import wsaa

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        for arg in sys.argv[1:]:
            if not arg.startswith("--"):
                print "Usando configuración:", arg
                CONFIG_FILE = arg

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSCTG','CUIT')
        ENTRADA = config.get('WSCTG','ENTRADA')
        SALIDA = config.get('WSCTG','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = wsaa.WSAAURL
        if config.has_option('WSCTG','URL') and not HOMO:
            wsctg_url = config.get('WSCTG','URL')
        else:
            wsctg_url = WSCTGURL

        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "wsaa_url:", wsaa_url
            print "wsctg_url:", wsctg_url
        # obteniendo el TA
        TA = "ctg-ta.xml"
        if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
            tra = wsaa.create_tra(service="wsctg")
            cms = wsaa.sign_tra(tra,CERT,PRIVATEKEY)
            ta_string = wsaa.call_wsaa(cms, wsaa_url)
            open(TA,"w").write(ta_string)
        ta_string=open(TA).read()
        ta = SimpleXMLElement(ta_string)
        token = str(ta.credentials.token)
        sign = str(ta.credentials.sign)
        # fin TA

        # cliente soap del web service
        client = SoapClient(wsctg_url, 
            action = SOAP_ACTION, 
            namespace = SOAP_NS, exceptions = True,
            soap_ns = 'soapenv',
            trace = XML, ns = "ctg")
        
        if '--dummy' in sys.argv:
            ret = dummy(client)
            print '\n'.join(["%s: %s" % it for it in ret.items()])    

        # Recuperar parámetros:
        
        if '--provincias' in sys.argv:
            items = obtener_provincias(client, token, sign, CUIT)
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])
        
        if '--localidades' in sys.argv:    
            provincia = int(raw_input("Código de provincia: "))
            items = obtener_localidades_por_codigo_provincia(client, token, sign, CUIT, provincia)
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])

        if '--especies' in sys.argv:    
            items = obtener_especies(client, token, sign, CUIT)    
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])

        if '--cosechas' in sys.argv:    
            items = obtener_cosechas(client, token, sign, CUIT)    
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])

        if '--prueba' in sys.argv or '--formato' in sys.argv:
            prueba = dict(numeroCartaDePorte=512345679, codigoEspecie=23,
                cuitRemitenteComercial=30640872566, cuitDestino=20061341677, cuitDestinatario=30500959629, 
                codigoLocalidadOrigen=3058, codigoLocalidadDestino=3059, 
                codigoCosecha='0910', pesoNetoCarga=1000, cantHoras=1, 
                patenteVehiculo='CZO985', cuitTransportista=20234455967,
                numeroCTG="43816783", transaccion='10000001681', observaciones='',
            )

            if '--prueba' in sys.argv:
                f = open(ENTRADA,"wb")
                csv_writer = csv.writer(f, dialect='excel', delimiter=";")
                csv_writer.writerows([prueba.keys()])
                csv_writer.writerows([[prueba[k] for k in prueba.keys()]])
                f.close()
            
            if '--formato' in sys.argv:
                print "Formato: archivo csv con las siguientes columnas"
                for k, v in prueba.items():
                    print "%s: " % (k,),
                    if k in ARG_SOLICITAR_CTG:
                        print "entrada solicitar_ctg,",
                    if k in RET_SOLICITAR_CTG:
                        print "salida solicitar_ctg,",
                    if k in ARG_CONFIRMAR_CTG:
                        print "entrada confirmar_ctg,",
                    if k in RET_CONFIRMAR_CTG:
                        print "salida confirmar_ctg,",
                    print "ej. '%s'" % v

        items = []
        csv_reader = csv.reader(open(ENTRADA), dialect='excel', delimiter=";")
        for row in csv_reader:
            items.append(row)
        cols = [str(it).strip() for it in items[0]]
        # armar diccionario por cada linea
        items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

        if '--solicitar' in sys.argv:
            for it in items:
                print "solicitando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                if 'cuitRepresentado' in it:
                    cuit = it['cuitRepresentado']
                else:
                    cuit = CUIT
                ctg = solicitar_ctg(client, token, sign, cuit, **it)
                print "numero CTG: ", ctg
                it['numeroCTG'] = ctg

        if '--confirmar' in sys.argv:
            for it in items:
                print "confirmando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                if 'cuitRepresentado' in it:
                    cuit = it['cuitRepresentado']
                else:
                    cuit = CUIT
                transaccion, observaciones = confirmar_ctg(client, token, sign, cuit, **it)
                print "transaccion: %s, observaciones: %s" % (transaccion, observaciones)
                it['transaccion'], it['observaciones'] = transaccion, observaciones
                
        f = open(SALIDA,"wb")
        csv_writer = csv.writer(f, dialect='excel', delimiter=";")
        csv_writer.writerows([cols])
        csv_writer.writerows([[item[k] for k in cols] for item in items])
        f.close()
        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
