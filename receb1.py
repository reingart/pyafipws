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

"Módulo de Intefase para archivos de texto (bono fiscal version 1)"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2009 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.18b"

import datetime
import os
import sys
import time
import traceback

# revisar la instalación de pyafip.ws:
import wsaa, wsbfev1
from utils import abrir_conf

HOMO = False
DEBUG = False
XML = False
CONFIG_FILE = "rece.ini"

LICENCIA = """
receb.py: Interfaz de texto para generar Facturas Electrónicas Bienes de Capital
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
ENCABEZADO = [
    ('tipo_reg', 1, N), # 0: encabezado
    ('fecha_cbte', 8, A),
    ('tipo_cbte', 2, N), ('punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ('tipo_doc', 2, N), ('nro_doc', 11, N),
    ('imp_total', 15, I), ('imp_tot_conc', 15, I),
    ('imp_neto', 15, I), ('impto_liq', 15, I),
    ('impto_liq_rni', 15, I), ('imp_op_ex', 15, I),
    ('impto_perc', 15, I), ('imp_iibb', 15, I),
    ('impto_perc_mun', 15, I), ('imp_internos', 15, I),
    ('imp_moneda_id', 3, A),
    ('imp_moneda_ctz', 10, I),
    ('zona', 5, A),
    ('cae', 14, N), ('fecha_vto', 8, A), 
    ('resultado', 1, A), ('obs', 2, A), ('reproceso', 1, A),
    ('id', 15, N),
    ]

DETALLE = [
    ('tipo_reg', 1, N), # 1: detalle item
    ('ncm', 15, A),
    ('sec', 15, A),
    ('qty', 15, I),
    ('umed', 5, N),
    ('precio', 15, I),
    ('bonif', 15, I),
    ('imp_total', 15, I),
    ('iva_id', 5, N),
    ('ds', 200, A),
    ]

def leer(linea, formato):
    dic = {}
    comienzo = 1
    for (clave, longitud, tipo) in formato:    
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        if tipo == N and valor:
            valor = str(int(valor))
        if tipo == I:
            if valor:
                valor = float("%s.%02d" % (int(valor[:-2]), int(valor[-2:])))
            else:
                valor = 0.00
        dic[clave] = valor

        comienzo += longitud
    return dic

translate_keys = {'ncm':'Pro_codigo_ncm', 'bonif':'Imp_bonif', 'precio':'Pro_precio_uni', 'sec':'Pro_codigo_sec', 
                'ds':'Pro_ds', 'umed':'Pro_umed', 'qty':'Pro_qty', 'imp_moneda_id':'Imp_moneda_Id'}
def escribir(dic, formato):
    linea = " " * 335
    comienzo = 1
    for (clave, longitud, tipo) in formato:
        if clave.capitalize() in dic:
            clave = clave.capitalize()
        valor = str(dic.get(clave,""))
        if valor=="" and clave in translate_keys:
            valor = str(dic.get(translate_keys[clave],""))
        if tipo == N and valor and valor!="NULL":
            valor = ("%%0%dd" % longitud) % int(valor)
        elif tipo == I and valor:
            valor = ("%%0%dd" % longitud) % (float(valor)*100)
        else:
            valor = ("%%0%ds" % longitud) % valor
        linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
        comienzo += longitud
    return linea + "\n"


def autorizar(ws, entrada, salida):
    # recupero el último número de transacción
    ##id = wsbfe.ultnro(client, token, sign, cuit)

   
    detalles = []
    encabezado = {}
    for linea in entrada:
        if str(linea[0])=='0':
            encabezado = leer(linea, ENCABEZADO)
        elif str(linea[0])=='1':
            detalle = leer(linea, DETALLE)
            detalles.append(detalle)
        else:
            print "Tipo de registro incorrecto:", linea[0]

    if not encabezado['id'].strip():
        # TODO: habria que leer y/o grabar el id en el archivo
        ##id += 1 # incremento el nº de transacción 
        # Por el momento, el id se calcula con el tipo, pv y nº de comprobant
        i = long(encabezado['cbte_nro'])
        i += (int(encabezado['cbte_nro'])*10**4 + int(encabezado['punto_vta']))*10**8
        encabezado['id'] = i

    if not encabezado['zona'].strip():
        encabezado['zona'] = 0

    if 'testing' in sys.argv:
        ult_cbte = ws.GetLastCMP(punto_vta, tipo_cbte)
        encabezado['cbte_nro'] = ult_cbte + 1
        ult_id = ws.GetLastID()
        encabezado['id'] = ult_id + 1    
   
    ##encabezado['imp_moneda_ctz'] = 1.00
    ws.CrearFactura(**encabezado)
    for detalle in detalles:
        ws.AgregarItem(**detalle)
            
    if DEBUG:
        print '\n'.join(["%s='%s'" % (k,v) for k,v in ws.factura.items()])
        print 'id:', encabezado['id']
    if not DEBUG or raw_input("Facturar?")=="S":
        cae = ws.Authorize(encabezado['id'])
        dic = ws.factura
        dic.update({'id':  encabezado['id'],
                    'fecha_cbte': ws.FechaCbte, 
                    'imp_total': ws.ImpTotal or 0,
                    'imp_neto': ws.ImpNeto or 0, 
                    'impto_liq': ws.ImptoLiq or 0, 
                    'cae': str(ws.CAE), 
                    'obs': str(ws.Obs), 'reproceso': str(ws.Reproceso),
                    'fch_venc_cae': ws.Vencimiento,  
                    'err_msg': ws.ErrMsg,
                   })
        escribir_factura(dic, salida)
        print "ID:", dic['id'], "CAE:",dic['cae'],"Obs:",dic['obs'],"Reproceso:",dic['reproceso']

def escribir_factura(dic, archivo):
    dic['tipo_reg'] = 0
    archivo.write(escribir(dic, ENCABEZADO))
    for it in dic['detalles']:
        it['tipo_reg'] = 1
        archivo.write(escribir(it, DETALLE))

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
        print " /id: consulta último ID"
        print " /debug: modo depuración (detalla y confirma las operaciones)"
        print " /formato: muestra el formato de los archivos de entrada/salida"
        print " /get: recupera datos de un comprobante autorizado previamente (verificación)"
        print " /xml: almacena los requerimientos y respuestas XML (depuración)"
        print
        print "Ver rece.ini para parámetros de configuración (URL, certificados, etc.)"
        sys.exit(0)

    if '/debug'in sys.argv:
        DEBUG = True
        print "VERSION", __version__, "HOMO", HOMO

    config = abrir_conf(CONFIG_FILE, DEBUG)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSBFE','CUIT')
    entrada = config.get('WSBFE','ENTRADA')
    salida = config.get('WSBFE','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = wsaa.WSAAURL
    if config.has_option('WSBFE','URL') and not HOMO:
        wsbfe_url = config.get('WSBFE','URL')
    else:
        wsbfe_url = None

    if '/debug'in sys.argv:
        DEBUG = True

    if '/xml'in sys.argv:
        XML = True

    if DEBUG:
        print "wsaa_url %s\nwsbfe_url %s" % (wsaa_url, wsbfe_url)
    
    try:
        ws = wsbfev1.WSBFEv1()
        ws.Conectar("", wsbfe_url)
        ws.Cuit = cuit
         
        if '/dummy' in sys.argv:
            print "Consultando estado de servidores..."
            print ws.Dummy()
            sys.exit(0)

        if '/formato' in sys.argv:
            print "Formato:"
            for msg, formato in [('Encabezado', ENCABEZADO), ('Detalle', DETALLE)]:
                comienzo = 1
                print "== %s ==" % msg
                for (clave, longitud, tipo) in formato:
                    print " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s" % (
                        clave, comienzo, longitud, tipo)
                    comienzo += longitud
            sys.exit(0)

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsbfe", cert, privatekey, wsaa_url)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)
        ws.SetTicketAcceso(ta)


        if '/prueba' in sys.argv or False:
            # generar el archivo de prueba para la próxima factura
            fecha = datetime.datetime.now().strftime("%Y%m%d")
            tipo_cbte = 1
            punto_vta = 2
            ult_cbte = int(ws.GetLastCMP(tipo_cbte, punto_vta)) + 1
            ult_id = ws.GetLastID() + 1

            f_entrada = open(entrada,"w")

            f = ws.CrearFactura(
                punto_vta=punto_vta, cbte_nro=ult_cbte,
                imp_moneda_id='PES', imp_moneda_ctz=1, 
                fecha_cbte=fecha,
                imp_neto="390.00", impto_liq="81.90"
                )            
            ws.AgregarItem(umed=7, ncm='7308.10.00', sec='', ds='prueba', qty=2.0, precio=100.0, bonif=0.0, iva_id=5, imp_total="242.00")
            ws.AgregarItem(umed=7, ncm='7308.20.00', sec='', ds='prueba 2', qty=4.0, precio=50.0, bonif=10.0, iva_id=5, imp_total="229.90")

            dic = ws.factura
            dic['id'] = ult_id
            escribir_factura(dic, f_entrada)            
            f_entrada.close()
        
        if '/ult' in sys.argv:
            print "Consultar ultimo numero:"
            tipo_cbte = int(raw_input("Tipo de comprobante: "))
            punto_vta = int(raw_input("Punto de venta: "))
            ult_cbte = ws.GetLastCMP(tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            print "Fecha: ", ws.FechaCbte
            depurar_xml(ws.client)
            sys.exit(0)
            
        if '/id' in sys.argv:
            ult_id = ws.GetLastID()
            print "ID: ", ult_id
            depurar_xml(ws.client)
            sys.exit(0)
            
        if '/get' in sys.argv:
            print "Recuperar comprobante:"
            tipo_cbte = int(raw_input("Tipo de comprobante: "))
            punto_vta = int(raw_input("Punto de venta: "))
            cbte_nro = int(raw_input("Numero de comprobante: "))
            cae = ws.GetCMP(tipo_cbte, punto_vta, cbte_nro)
            cbt = { 'fecha_cbte': ws.FechaCbte, 
                    'imp_total': ws.ImpTotal or 0,
                    'imp_neto': ws.ImpNeto or 0, 
                    'impto_liq': ws.ImptoLiq or 0, 
                    'cae': str(ws.CAE), 
                    'obs': str(ws.Obs), 'reproceso': str(ws.Reproceso),
                    'fch_venc_cae': ws.Vencimiento,  
                    'err_msg': ws.ErrMsg,
                    }
            for k,v in cbt.items():
                print "%s = %s" % (k, v)
            depurar_xml(ws.client)
            sys.exit(0)

        f_entrada = f_salida = None
        try:
            f_entrada = open(entrada,"r")
            f_salida = open(salida,"w")
            try:
                autorizar(ws, f_entrada, f_salida)
            except:
                XML = True
                raise
        finally:
            if f_entrada is not None: f_entrada.close()
            if f_salida is not None: f_salida.close()
            if XML:
                depurar_xml(ws.client)
        sys.exit(0)
    
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
