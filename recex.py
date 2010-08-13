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

"Módulo de Intefase para archivos de texto (exportación)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.24a"

import os
import sys
import time
import traceback
from ConfigParser import SafeConfigParser

# revisar la instalación de pyafip.ws:
import wsaa, wsfex
from php import SimpleXMLElement, SoapClient, SoapFault, date


HOMO = True
DEBUG = False
XML = False
CONFIG_FILE = "rece.ini"

LICENCIA = """
recex.py: Interfaz de texto para generar Facturas Electrónica Exportación
Copyright (C) 2010 Mariano Reingart reingart@gmail.com

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
ENCABEZADO = [
    ('tipo_reg', 1, N), # 0: encabezado
    ('fecha_cbte', 8, A),
    ('tipo_cbte', 2, N), ('punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ('tipo_expo', 1, N), # 1:bienes, 2:servicios,... 
    ('permiso_existente', 1, A), # S/N/
    ('dst_cmp', 3, N), # 203
    ('cliente', 200, A), # 'Joao Da Silva'
    ('cuit_pais_cliente', 11, N), # 50000000016
    ('domicilio_cliente', 300, A), # 'Rua 76 km 34.5 Alagoas'
    ('id_impositivo', 50, A), # 'PJ54482221-l'    
    ('imp_total', 15, I, 3), 
    ('moneda_id', 3, A),
    ('moneda_ctz', 10, I, 6), #10,6
    ('obs_comerciales', 1000, A),
    ('obs', 1000, A),
    ('forma_pago', 50, A),
    ('incoterms', 3, A),
    ('incoterms_ds', 20, A),
    ('idioma_cbte', 1, A),
    ('cae', 14, N), ('fecha_vto', 8, A),
    ('resultado', 1, A), 
    ('reproceso', 1, A),
    ('motivos_obs', 40, A),
    ('id', 15, N),
    ('fch_venc_cae', 8, A),
    ]

DETALLE = [
    ('tipo_reg', 1, N), # 1: detalle item
    ('codigo', 30, A),
    ('qty', 12, I),
    ('umed', 2, N),
    ('precio', 12, I, 3),
    ('imp_total', 14, I, 3),
    ('ds', 4000, A),
    ]

PERMISO = [
    ('tipo_reg', 1, N), # 2: permiso
    ('id_permiso', 16, A),
    ('dst_merc', 3, N),
    ]

CMP_ASOC = [
    ('tipo_reg', 1, N), # 3: comprobante asociado
    ('cbte_tipo', 3, N), ('cbte_punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ]


def leer(linea, formato):
    dic = {}
    comienzo = 1
    for fmt in formato:    
        clave, longitud, tipo = fmt[0:3]
        dec = len(fmt)>3 and fmt[3] or 2
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        try:
            if tipo == N:
                if valor:
                    valor = str(int(valor))
                else:
                    valor = '0'
            elif tipo == I:
                if valor:
                    try:
                        valor = valor.strip(" ")
                        valor = float(("%%s.%%0%sd" % dec) % (int(valor[:-dec] or '0'), int(valor[-dec:] or '0')))
                    except ValueError:
                        raise ValueError("Campo invalido: %s = '%s'" % (clave, valor))
                else:
                    valor = 0.00
            else:
                valor = valor.decode("ascii","ignore")
            dic[clave] = valor

            comienzo += longitud
        except Exception, e:
            raise ValueError("Error al leer campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return dic

translate_keys = {'moneda_id':'Moneda_Id', 
                'codigo':'Pro_codigo', 'precio':'Pro_precio_uni','imp_total':'Pro_total_item',  
                'ds':'Pro_ds', 'umed':'Pro_umed', 'qty':'Pro_qty', }
def escribir(dic, formato):
    linea = " " * 335
    comienzo = 1
    for fmt in formato:
        clave, longitud, tipo = fmt[0:3]
        dec = len(fmt)>3 and fmt[3] or 2
        if clave.capitalize() in dic:
            clave = clave.capitalize()
        valor = str(dic.get(clave,""))
        if valor=="" and clave in translate_keys:
            valor = str(dic.get(translate_keys[clave],""))
        if tipo == N and valor and valor!="NULL":
            valor = ("%%0%dd" % longitud) % int(valor)
        elif tipo == I and valor:
            valor = ("%%0%dd" % longitud) % (float(valor)*(10**dec))
        else:
            valor = ("%%0%ds" % longitud) % valor
        linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
        comienzo += longitud
    return linea + "\n"

def autenticar(cert, privatekey, url):
    "Obtener el TA"
    TA = "TA.xml"
    ttl = 60*60*5
    if not os.path.exists(TA) or os.path.getmtime(TA)+(ttl)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsfex",ttl=ttl)
        cms = wsaa.sign_tra(str(tra),str(cert),str(privatekey))
        ta_string = wsaa.call_wsaa(cms,wsaa_url,trace=DEBUG)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    return token, sign

def autorizar(client, token, sign, cuit, entrada, salida):
    # recupero el último número de transacción
    ##id = wsfex.ultnro(client, token, sign, cuit)

    detalles = []
    permisos = []
    cbtasocs = []
    encabezado = {}
    for linea in entrada:
        if str(linea[0])=='0':
            encabezado = leer(linea, ENCABEZADO)
        elif str(linea[0])=='1':
            detalle = leer(linea, DETALLE)
            detalles.append(detalle)
        elif str(linea[0])=='2':
            permiso = leer(linea, PERMISO)
            permisos.append(permiso)
        elif str(linea[0])=='3':
            cbtasoc = leer(linea, CMP_ASOC)
            cbtasocs.append(cbtasoc)
        else:
            print "Tipo de registro incorrecto:", linea[0]

    if not encabezado['id'].strip() or int(encabezado['id'])==0:
        # TODO: habria que leer y/o grabar el id en el archivo
        ##id += 1 # incremento el nº de transacción 
        # Por el momento, el id se calcula con el tipo, pv y nº de comprobant
        i = long(encabezado['cbte_nro'])
        i += (int(encabezado['cbte_nro'])*10**4 + int(encabezado['punto_vta']))*10**8
        encabezado['id'] = wsfex.get_last_id(client, token, sign, cuit)[0] + 1
    
    factura = wsfex.FacturaEX(**encabezado)
    for detalle in detalles:
        it = wsfex.ItemFEX(**detalle)
        factura.add_item(it, calcular=False)
    for permiso in permisos:
        p = wsfex.PermisoFEX(**permiso)
        factura.add_permiso(p)
    for cbtasoc in cbtasocs:
        c = wsfex.CmpAsocFEX(**cbtasoc)
        factura.add_cmp_asoc(c)

    if DEBUG:
        #print f.to_dict()
        print '\n'.join(["%s='%s'" % (k,str(v)) for k,v in factura.to_dict().items()])
        print 'id:', encabezado['id']
    if not DEBUG or raw_input("Facturar?")=="S":
        dic = factura.to_dict()
        auth, events = wsfex.authorize(client, token, sign, cuit,
                                       id=encabezado['id'],
                                       factura=dic)
        dic.update(auth)
        escribir_factura(dic, salida)
        print "ID:", dic['id'], "CAE:",dic['cae'],"Obs:",dic['obs'],"Reproceso:",dic['reproceso']

def escribir_factura(dic, archivo):
    dic['tipo_reg'] = 0
    archivo.write(escribir(dic, ENCABEZADO))
    for it in dic['Items']:
        it['Item']['tipo_reg'] = 1
        archivo.write(escribir(it['Item'], DETALLE))
    if 'Permisos' in dic:    
        for it in dic['Permisos']:
            it['Permiso']['tipo_reg'] = 2
            archivo.write(escribir(it['Permiso'], PERMISO))
            
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
        print " /formato: muestra el formato de los archivos de entrada/salida"
        print " /get: recupera datos de un comprobante autorizado previamente (verificación)"
        print " /xml: almacena los requerimientos y respuestas XML (depuración)"
        print
        print "Ver rece.ini para parámetros de configuración (URL, certificados, etc.)"
        sys.exit(0)

    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSFEX','CUIT')
    entrada = config.get('WSFEX','ENTRADA')
    salida = config.get('WSFEX','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = wsaa.WSAAURL
    if config.has_option('WSFEX','URL') and not HOMO:
        wsfex_url = config.get('WSFEX','URL')
    else:
        wsfex_url = wsfex.WSFEXURL

    if '/debug'in sys.argv:
        DEBUG = True

    if '/xml'in sys.argv:
        XML = True

    if DEBUG:
        print "wsaa_url %s\nwsfex_url %s" % (wsaa_url, wsfex_url)
    
    try:
        client = SoapClient(wsfex_url, action=wsfex.SOAP_ACTION, namespace=wsfex.SOAP_NS,
                            trace=False, exceptions=True)

        if '/dummy' in sys.argv:
            print "Consultando estado de servidores..."
            print wsfex.dummy(client)
            sys.exit(0)

        if '/formato' in sys.argv:
            print "Formato:"
            for msg, formato in [('Encabezado', ENCABEZADO), ('Detalle', DETALLE), ('Permiso', PERMISO), ('Comprobante Asociado', CMP_ASOC)]:
                comienzo = 1
                print "== %s ==" % msg
                for fmt in formato:
                    clave, longitud, tipo = fmt[0:3]
                    dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                    print " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                        clave, comienzo, longitud, tipo, dec)
                    comienzo += longitud
            sys.exit(0)

        # TODO: esto habría que guardarlo en un archivo y no tener que autenticar cada vez
        token, sign = autenticar(cert, privatekey, wsaa_url)

        if '/prueba' in sys.argv:
            # generar el archivo de prueba para la próxima factura
            fecha = date('Ymd')
            tipo_cbte = 19
            punto_vta = 3
            ult_cbte, fecha, events = wsfex.get_last_cmp(client, token, sign, cuit, tipo_cbte, punto_vta)

            ult_id, events = wsfex.get_last_id(client, token, sign, cuit)

            f_entrada = open(entrada,"w")

            f = wsfex.FacturaEX()
            f.punto_vta = punto_vta
            f.cbte_nro = ult_cbte+1
            f.imp_moneda_id = 'PES'
            f.fecha_cbte = date('Ymd')
            f.tipo_expo = 1
            f.permiso_existente = 'S'
            f.dst_cmp = 203
            f.cliente = 'Joao Da Silva'
            f.cuit_pais_cliente = 50000000016
            f.domicilio_cliente = 'Rua 76 km 34.5 Alagoas'
            f.id_impositivo = 'PJ54482221-l'
            f.moneda_id = 'DOL'
            f.moneda_ctz = 3.875
            f.obs_comerciales = 'Observaciones comerciales'
            f.obs = 'Sin observaciones'
            f.forma_pago = '30 dias'
            f.incoterms = 'FOB'
            f.idioma_cbte = 1
            # agrego los items
            it = wsfex.ItemFEX(codigo='PRO1', ds=u'Producto Tipo 1 Exportacion MERCOSUR ISO 9001', 
                         qty=1, precio=125)
            f.add_item(it)
            it = wsfex.ItemFEX(codigo='PRO2', ds=u'Producto Tipo 2 Exportacion MERCOSUR ISO 9001', 
                         qty=1, precio=125)
            f.add_item(it)
            permiso = wsfex.PermisoFEX(id_permiso="99999AAXX999999A",dst_merc=225)
            f.add_permiso(permiso)
                
            if DEBUG:
                print f.to_dict()

            dic = f.to_dict()
            dic['id'] = ult_id+1
            escribir_factura(dic, f_entrada)            
            f_entrada.close()
        
        if '/ult' in sys.argv:
            print "Consultar ultimo numero:"
            tipo_cbte = int(raw_input("Tipo de comprobante: "))
            punto_vta = int(raw_input("Punto de venta: "))
            ult_cbte, fecha, events = wsfex.get_last_cmp(client, token, sign, cuit, tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            print "Fecha: ", fecha
            depurar_xml(client)
            sys.exit(0)

        if '/get' in sys.argv:
            print "Recuperar comprobante:"
            tipo_cbte = int(raw_input("Tipo de comprobante: "))
            punto_vta = int(raw_input("Punto de venta: "))
            cbte_nro = int(raw_input("Numero de comprobante: "))
            cbt, events = wsfex.get_cmp(client, token, sign, cuit, tipo_cbte, punto_vta, cbte_nro)
            for k,v in cbt.items():
                print "%s = %s" % (k, v)
            depurar_xml(client)
            sys.exit(0)

        f_entrada = f_salida = None
        try:
            f_entrada = open(entrada,"r")
            f_salida = open(salida,"w")
            try:
                autorizar(client, token, sign, cuit, f_entrada, f_salida)
            except SoapFault, wsfex.FEXError:
                XML = True
                raise
        finally:
            if f_entrada is not None: f_entrada.close()
            if f_salida is not None: f_salida.close()
            if XML:
                depurar_xml(client)
        sys.exit(0)
    
    except SoapFault,e:
        print e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except wsfex.FEXError,e:
        print e.code, e.msg.encode("ascii","ignore")
        sys.exit(4)
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
