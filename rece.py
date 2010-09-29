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

"Módulo de Intefase para archivos de texto"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2009 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.24e"

import os
import sys
import time
import traceback
from ConfigParser import SafeConfigParser

# revisar la instalación de pyafip.ws:
import wsaa,wsfe
from php import SimpleXMLElement, SoapClient, SoapFault, date


HOMO = True
DEBUG = False
CONFIG_FILE = "rece.ini"

LICENCIA = """
rece.py: Interfaz de texto para generar Facturas Electrónicas
Copyright (C) 2008/2009 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

# definición del formato del archivo de intercambio:
N = 'Numerico'
A = 'Alfanumerico'
I = 'Importe'
FORMATO = { 'tipo_doc': (36,2,N), 'nro_doc':  (38,11,N),
            'tipo_cbte': (10,2,N), 'punto_vta': (13,4,N),
            'cbt_desde': (17,8,N), 'cbt_hasta': (25,8,N),
            'imp_total': (79,15,I), 'imp_tot_conc': (94,15,I),
            'imp_neto': (109,15,I), 'impto_liq': (124,15,I),
            'impto_liq_rni': (139,15,I), 'imp_op_ex': (154,15,I),
            'fecha_cbte': (2,8,A),
            'cae': (261,14,N), 'fecha_vto': (275,8,A), 
            'resultado': (291,1,A), 'motivo': (292,2,A), 'reproceso': (294,1,A),
            'fecha_venc_pago': (295,8,A),
            'presta_serv': (303,1,N),
            'fecha_serv_desde': (304,8,A),
            'fecha_serv_hasta': (312,8,A),
            'id': (320,15,N)
            }

def leer(linea, formato):
    dic = {}
    for clave, (comienzo, longitud, tipo) in formato.items():
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        try:
            if tipo == N and valor:
                valor = str(int(valor))
            if tipo == I and valor:
                valor = "%s.%02d" % (int(valor[:-2]), int(valor[-2:]))
            dic[clave] = valor
        except Exception, e:
            raise ValueError("Error al leer campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return dic

def escribir(dic, formato):
    linea = " " * 335
    for clave, (comienzo, longitud, tipo) in formato.items():
        valor = dic.get(clave,"")
        if tipo == N and valor and valor!="NULL":
            valor = ("%%0%dd" % longitud) % int(valor)
        elif tipo == I and valor:
            valor = ("%%0%dd" % longitud) % int(valor.replace(".",""))
        else:
            valor = ("%%0%ds" % longitud) % valor
        linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
    return linea + "\n"

def autenticar(cert, privatekey, url):
    "Obtener el TA"
    TA = "TA-wsfe.xml"
    ttl = 60*60*5
    if not os.path.exists(TA) or os.path.getmtime(TA)+(ttl)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsfe",ttl=ttl)
        cms = wsaa.sign_tra(str(tra),str(cert),str(privatekey))
        ta_string = wsaa.call_wsaa(cms,wsaa_url,trace=DEBUG)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    return token, sign

def autorizar(client, token, sign, cuit, entrada, salida, formato):
    # recupero el último número de transacción
    ##id = wsfe.ultnro(client, token, sign, cuit)
    for linea in entrada:
        kargs = leer(linea, FORMATO)
        if not kargs['id'].strip():
            # TODO: habria que leer y/o grabar el id en el archivo
            ##id += 1 # incremento el nº de transacción 
            # Por el momento, el id se calcula con el tipo, pv y nº de comprobant
            id = long(kargs['cbt_desde'])
            id += (int(kargs['tipo_cbte'])*10**4 + int(kargs['punto_vta']))*10**8
            kargs['id'] = id
        if DEBUG:
            print '\n'.join(["%s='%s'" % (k,v) for k,v in kargs.items()])
        if not DEBUG or raw_input("Facturar?")=="S":
            ret = wsfe.aut(client, token, sign, cuit, 
                **kargs)
            kargs.update(ret)
            salida.write(escribir(kargs, FORMATO))
            print "ID:", kargs['id'], "CAE:",kargs['cae'],"Motivo:",kargs['motivo'],"Reproceso:",kargs['reproceso']


def depurar_xml(client):
    fecha = time.strftime("%Y%m%d%H%M%S")
    f=open("request-%s.xml" % fecha,"w")
    f.write(client.xml_request)
    f.close()
    f=open("response-%s.xml" % fecha,"w")
    f.write(client.xml_response)
    f.close()


if __name__ == "__main__":
    if '/ayuda' in sys.argv:
        print LICENCIA
        print
        print "Opciones: "
        print " /ayuda: este mensaje"
        print " /dummy: consulta estado de servidores"
        print " /prueba: genera y autoriza una factura de prueba (no usar en producción!)"
        print " /ult: consulta último número de comprobante"
        print " /debug: modo depuración (detalla y confirma las operaciones)"
        print
        print "Ver rece.ini para parámetros de configuración (URL, certificados, etc.)"
        sys.exit(0)

    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSFE','CUIT')
    entrada = config.get('WSFE','ENTRADA')
    salida = config.get('WSFE','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = wsaa.WSAAURL
    if config.has_option('WSFE','URL') and not HOMO:
        wsfe_url = config.get('WSFE','URL')
    else:
        wsfe_url = wsfe.WSFEURL

    if '/debug'in sys.argv:
        DEBUG = True

    XML = '/xml' in sys.argv

    if DEBUG:
        print "wsaa_url %s\nwsfe_url %s" % (wsaa_url, wsfe_url)
    
    try:
        client = SoapClient(wsfe_url, action=wsfe.SOAP_ACTION, namespace=wsfe.SOAP_NS,
                            trace=DEBUG, exceptions=True)

        if '/dummy' in sys.argv:
            print "Consultando estado de servidores..."
            wsfe.dummy(client)
            sys.exit(0)

        # TODO: esto habría que guardarlo en un archivo y no tener que autenticar cada vez
        token, sign = autenticar(cert, privatekey, wsaa_url)

        if '/prueba' in sys.argv or False:
            # generar el archivo de prueba para la próxima factura
            fecha = date('Ymd')
            tipo_cbte = 1
            punto_vta = 2
            ult_cbte = wsfe.recuperar_last_cmp(client, token, sign, cuit, punto_vta, tipo_cbte)
            f_entrada = open(entrada,"w")
            for cbte in range(ult_cbte+1,ult_cbte+4):
                dic = dict(
                    fecha=fecha,
                    presta_serv = 1,
                    tipo_doc = 80, nro_doc = "23111111114",
                    tipo_cbte=tipo_cbte, punto_vta=punto_vta,
                    cbt_desde=cbte, cbt_hasta=cbte,
                    imp_total="121.00", imp_tot_conc="0.00", imp_neto="100.00",
                    impto_liq="21.00", impto_liq_rni="0.00", imp_op_ex="0.00",
                    fecha_cbte=fecha, fecha_venc_pago=fecha,
                    fecha_serv_desde=fecha, fecha_serv_hasta=fecha)
                f_entrada.write(escribir(dic, FORMATO))
            f_entrada.close()
        
        if '/ult' in sys.argv:
            print "Consultar ultimo numero:"
            tipo_cbte = int(raw_input("Tipo de comprobante: "))
            punto_vta = int(raw_input("Punto de venta: "))
            ult_cbte = wsfe.recuperar_last_cmp(client, token, sign, cuit, punto_vta, tipo_cbte)
            print "Ultimo numero: ", ult_cbte
            sys.exit(0)

        f_entrada = f_salida = None
        try:
            f_entrada = open(entrada,"r")
            f_salida = open(salida,"w")
            autorizar(client, token, sign, cuit, f_entrada, f_salida, FORMATO)
        finally:
            if f_entrada is not None: f_entrada.close()
            if f_salida is not None: f_salida.close()
            if XML:
                depurar_xml(client)

        sys.exit(0)
    
    except SoapFault,e:
        print e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except wsfe.WSFEError,e:
        print e.code, e.msg.encode("ascii","ignore")
        sys.exit(4)
    except Exception, e:
        print e
        sys.exit(5)
