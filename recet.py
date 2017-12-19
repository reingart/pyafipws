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

"Módulo de Intefase para archivos de intercambio(Comprobantes Turismo)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2017 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01d"

import datetime
import json
import os
import sys
import time
import traceback

# revisar la instalación de pyafip.ws:
import wsct
from utils import SimpleXMLElement, SoapClient, SoapFault, date
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, abrir_conf


HOMO = wsct.HOMO
DEBUG = False
PDB = False
XML = False
CONFIG_FILE = "rece.ini"

LICENCIA = """
recet.py: Interfaz de texto para generar Facturas Electrónica Turismo
Copyright (C) 2017 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

# definición del formato del archivo de intercambio:

TIPOS_REG = '0', '1', '2', '3', '4', '5', '6'
ENCABEZADO = [
    ('tipo_reg', 1, N), # 0: encabezado
    ('fecha_cbte', 10, A),
    ('tipo_cbte', 3, N),
    ('punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ('tipo_doc', 2, N), # 80
    ('nro_doc', 11, A), # 50000000016    
    ('imp_total', 15, I, 2), 
    ('imp_tot_conc', 15, I, 2), 
    ('imp_neto', 15, I, 2), 
    ('imp_subtotal', 15, I, 2), 
    ('imp_trib', 15, I, 2), 
    ('imp_op_ex', 15, I, 2), 
    ('imp_reintegro', 15, I, 2), 
    ('moneda_id', 3, A),
    ('moneda_ctz', 10, I, 6), #10,6
    ('fecha_venc_pago', 10, A),   # opcional solo conceptos 2 y 3
    ('id_impositivo', 2, N),
    ('cod_relacion', 2, N),
    ('cod_pais', 3, N), # 203
    ('domicilio', 300, A), # 'Rua 76 km 34.5 Alagoas'
    ('cae', 14, A),
    ('fch_venc_cae', 10, A),
    ('resultado', 1, A), 
    ('motivos_obs', 1000, A),
    ('err_code', 6, A),
    ('err_msg', 1000, A),
    ('reproceso', 1, A),
    ('emision_tipo', 4, A),
    ('observaciones', 1000, A),  # observaciones (opcional)
    ]

DETALLE = [
    ('tipo_reg', 1, N),     # 4: detalle item
    ('tipo', 3, N),
    ('cod_tur', 30, A),
    ('codigo', 30, A),
    ('iva_id', 3, N),
    ('imp_iva', 15, I, 2),
    ('imp_subtotal', 15, I, 2),
    ('ds', 4000, A),
    ]

TRIBUTO = [
    ('tipo_reg', 1, N),     # 1: tributo
    ('tributo_id', 3, A),   # código de otro tributo
    ('desc', 100, A),       # descripción
    ('base_imp', 15, I, 2), 
    ('alic', 15, I, 2),     # no se usa...
    ('importe', 15, I, 2),  
    ]

IVA = [
    ('tipo_reg', 1, N),     # 2: IVA
    ('iva_id', 3, A),       # código de alícuota
    ('base_imp', 15, I, 2), # no se usa... 
    ('importe', 15, I, 2),  
    ]

CMP_ASOC = [
    ('tipo_reg', 1, N),     # 3: comprobante asociado
    ('tipo', 3, N),         
    ('pto_vta', 4, N),
    ('nro', 8, N), 
    ('cuit', 11, N),
    ('cuit', 11, N),
    ]

FORMA_PAGO = [
    ('tipo_reg', 1, N),     # 6: formas de pago
    ('codigo', 3, N),
    ('tipo_tarjeta', 2, N),
    ('numero_tarjeta', 6, N),
    ('swift_code', 11, A),
    ('tipo_cuenta', 2, N),
    ('numero_cuenta', 20, N),
    ]


def autorizar(ws, entrada, salida, informar_caea=False):
    tributos = []
    ivas = []
    cbtasocs = []
    encabezado = []
    detalles = []
    formas_pago = []
    if '/dbf' in sys.argv:
        formatos = [('Encabezado', ENCABEZADO, encabezado), 
                    ('Tributo', TRIBUTO, tributos), 
                    ('Iva', IVA, ivas), 
                    ('Comprobante Asociado', CMP_ASOC, cbtasocs), 
                    ('Detalles', DETALLE, detalles)]
        dic = leer_dbf(formatos, conf_dbf)
        encabezado = encabezado[0]
    elif '/json' in sys.argv:
        encabezado = json.load(entrada)
        for lista, clave in ((detalles, "detalles"), (ivas, "iva"),
                             (tributos, "tributos"), (cbtasocs, "cbtes_asoc"),
                             (formas_pago, "formas_pago")):
            if clave in encabezado:
                lista.extend(encabezado.pop(clave))
    else:
        for linea in entrada:
            if str(linea[0])==TIPOS_REG[0]:
                encabezado = leer(linea, ENCABEZADO, expandir_fechas=True)
            elif str(linea[0])==TIPOS_REG[1]:
                tributo = leer(linea, TRIBUTO)
                tributos.append(tributo)
            elif str(linea[0])==TIPOS_REG[2]:
                iva = leer(linea, IVA)
                ivas.append(iva)
            elif str(linea[0])==TIPOS_REG[3]:
                cbtasoc = leer(linea, CMP_ASOC)
                cbtasocs.append(cbtasoc)
            elif str(linea[0])==TIPOS_REG[4]:
                detalle = leer(linea, DETALLE)
                detalles.append(detalle)
            elif str(linea[0])==TIPOS_REG[5]:
                fp = leer(linea, FORMA_PAGO)
                formas_pago.append(fp)
                for campo in fp.keys():
                    if not fp[campo]:
                        fp[campo] = None
            else:
                print "Tipo de registro incorrecto:", linea[0]
       
    if informar_caea:
        if '/testing' in sys.argv:
            encabezado['cae'] = '21353598240916'
            encabezado['fch_venc_cae'] = '2011-09-15'
        encabezado['caea'] = encabezado['cae']

    if 'imp_subtotal' not in encabezado:
        encabezado['imp_subtotal'] = encabezado['imp_neto'] + encabezado['imp_tot_conc']

    ws.CrearFactura(**encabezado)
    for detalle in detalles:
        if 'imp_subtotal' not in detalle:
            detalle['imp_subtotal'] = detalle['importe']
        ws.AgregarItem(**detalle)
    for tributo in tributos:
        if 'alic' not in tributo:
            tributo['alic'] = None
        ws.AgregarTributo(**tributo)
    for iva in ivas:
        if 'base_imp' not in iva:
            iva['base_imp'] = None
        ws.AgregarIva(**iva)
    for cbtasoc in cbtasocs:
        if 'cbte_punto_vta' in cbtasoc:
            cbtasoc['tipo'] = cbtasoc.pop('cbte_tipo')
            cbtasoc['pto_vta'] = cbtasoc.pop('cbte_punto_vta')
            cbtasoc['nro'] = cbtasoc.pop('cbte_nro')
        ws.AgregarCmpAsoc(**cbtasoc)
    for fp in formas_pago:
        ws.AgregarFormaPago(**fp)

    if DEBUG:
        print '\n'.join(["%s='%s'" % (k,str(v)) for k,v in ws.factura.items()])
    if not DEBUG or raw_input("Facturar?")=="S":
        if not informar_caea:
            cae = ws.AutorizarComprobante()
            dic = ws.factura
        else:
            cae = ws.InformarComprobanteCAEA()
            dic = ws.factura
        dic.update({
            'cae':cae,
            'fch_venc_cae': ws.Vencimiento,
            'resultado': ws.Resultado,
            'motivos_obs': ws.Obs,
            'err_code': ws.ErrCode,
            'err_msg': ws.ErrMsg,
            'reproceso': ws.Reproceso,
            'emision_tipo': ws.EmisionTipo,
            })
        escribir_factura(dic, salida)
        print "NRO:", dic['cbte_nro'], "Resultado:", dic['resultado'], "%s:" % ws.EmisionTipo,dic['cae'],"Obs:",dic['motivos_obs'].encode("ascii", "ignore"), "Err:", dic['err_msg'].encode("ascii", "ignore"), "Reproceso:", dic['reproceso']

def escribir_factura(dic, archivo, agrega=False):
    if '/dbf' in sys.argv:
        formatos = [('Encabezado', ENCABEZADO, [dic]), 
                    ('Tributo', TRIBUTO, dic.get('tributos', [])), 
                    ('Iva', IVA, dic.get('iva', [])), 
                    ('Comprobante Asociado', CMP_ASOC, dic.get('cbtes_asoc', [])),
                    ('Detalles', DETALLE, dic.get('detalles', [])),
                    ('Forma Pago', FORMA_PAGO, dic.get('formas_pago', [])),
                   ]
        guardar_dbf(formatos, agrega, conf_dbf)
    elif '/json' in sys.argv:
        json.dump(dic, archivo, sort_keys=True, indent=4)
    else:
        dic['tipo_reg'] = TIPOS_REG[0]
        archivo.write(escribir(dic, ENCABEZADO, contraer_fechas=True))
        if 'tributos' in dic:
            for it in dic['tributos']:
                it['tipo_reg'] = TIPOS_REG[1]
                archivo.write(escribir(it, TRIBUTO))
        if 'iva' in dic:
            for it in dic['iva']:
                it['tipo_reg'] = TIPOS_REG[2]
                archivo.write(escribir(it, IVA))
        if 'cbtes_asoc' in dic:
            for it in dic['cbtes_asoc']:
                it['tipo_reg'] = TIPOS_REG[3]
                archivo.write(escribir(it, CMP_ASOC))
        if 'detalles' in dic:
            for it in dic['detalles']:
                it['tipo_reg'] = TIPOS_REG[4]
                it['importe'] = it['imp_subtotal']
                archivo.write(escribir(it, DETALLE))
        if 'forma_pago' in dic:
            for it in dic['fp']:
                it['tipo_reg'] = TIPOS_REG[5]
                archivo.write(escribir(it, FORMA_PAGO))


def depurar_xml(client):
    global wsct_xml_dir
    fecha = time.strftime("%Y%m%d%H%M%S")
    f=open(os.path.join(wsct_xml_dir, "request-%s.xml" % fecha),"w")
    f.write(client.xml_request)
    f.close()
    f=open(os.path.join(wsct_xml_dir, "response-%s.xml" % fecha),"w")
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
        print " /dbf: lee y almacena la información en tablas DBF"
        print " /json: utiliza el formato JSON para el archivo de entrada"
        print
        print "Ver rece.ini para parámetros de configuración (URL, certificados, etc.)"
        sys.exit(0)

    if '/debug'in sys.argv:
        DEBUG = True
        print "VERSION", __version__, "HOMO", HOMO

    config = abrir_conf(CONFIG_FILE, DEBUG)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSCT','CUIT')
    if '/entrada' in sys.argv:
        entrada = sys.argv[sys.argv.index("/entrada")+1]
    else:
        entrada = config.get('WSCT','ENTRADA')
    salida = config.get('WSCT','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = None
    if config.has_option('WSCT','URL') and not HOMO:
        wsct_url = config.get('WSCT','URL')
    else:
        wsct_url = None

    if config.has_option('WSCT','REPROCESAR'):
        wsct_reprocesar = config.get('WSCT','REPROCESAR') == 'S'
    else:
        wsct_reprocesar = None

    if config.has_option('WSCT', 'XML_DIR'):
        wsct_xml_dir = config.get('WSCT', 'XML_DIR')
    else:
        wsct_xml_dir = "."

    if config.has_section('DBF'):
        conf_dbf = dict(config.items('DBF'))
        if DEBUG: print "conf_dbf", conf_dbf
    else:
        conf_dbf = {}

    if '/xml'in sys.argv:
        XML = True

    if DEBUG:
        print "wsaa_url %s\nwsct_url %s\ncuit %s" % (wsaa_url, wsct_url, cuit)
    
    try:
        ws = wsct.WSCT()
        ws.Conectar("", wsct_url)
        ws.Cuit = cuit
        if wsct_reprocesar is not None:
            ws.Reprocesar = wsct_reprocesar

        if '/dummy' in sys.argv:
            print "Consultando estado de servidores..."
            ws.Dummy()
            print "AppServerStatus", ws.AppServerStatus
            print "DbServerStatus", ws.DbServerStatus
            print "AuthServerStatus", ws.AuthServerStatus
            sys.exit(0)

        if '/formato' in sys.argv:
            print "Formato:"
            for msg, formato in [('Encabezado', ENCABEZADO), 
                                 ('Tributo', TRIBUTO), 
                                 ('Iva', IVA), 
                                 ('Comprobante Asociado', CMP_ASOC), 
                                 ('Detalle', DETALLE), 
                                 ('Forma Pago', FORMA_PAGO)]:
                comienzo = 1
                print "=== %s ===" % msg
                print "|| %-20s || %-4s || %-4s|| %-15s || %s || ||" % (
                      "Campo", "Pos.", "Long.", "Tipo", "Decimales")
                for fmt in formato:
                    clave, longitud, tipo = fmt[0:3]
                    if isinstance(longitud, tuple):
                        longitud, dec = longitud
                    else:
                        dec = len(fmt)>3 and fmt[3] or 2
                    print "|| %-20s || %4d || %4d || %-15s || %s || ||" % (
                        clave, comienzo, longitud, tipo, dec)
                    comienzo += longitud
            sys.exit(0)

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsct", cert, privatekey, wsaa_url)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)
        ws.SetTicketAcceso(ta)
                
        if '/puntosventa' in sys.argv:
            print "Consultando puntos de venta ..."
            print '\n'.join(ws.ConsultarPuntosVenta())
            sys.exit(0)
            
        if '/prueba' in sys.argv:
            # generar el archivo de prueba para la próxima factura
            tipo_cbte = 195
            punto_vta = 4000
            cbte_nro = ws.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            concepto = 3
            tipo_doc = 80; nro_doc = "50000000059"
            cbte_nro = long(cbte_nro) + 1
            id_impositivo = 9     # "Cliente del Exterior"
            cod_relacion = 3      # Alojamiento Directo a Turista No Residente
            imp_total = "101.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
            imp_trib = "1.00"; imp_op_ex = "0.00"; imp_subtotal = "100.00"
            imp_reintegro = -21.00      # validación AFIP 346
            cod_pais = 203
            domicilio = "Rua N.76 km 34.5 Alagoas"
            fecha_cbte = fecha
            moneda_id = 'PES'; moneda_ctz = '1.000'
            obs = "Observaciones Comerciales, libre"

            ws.CrearFactura(tipo_doc, nro_doc, tipo_cbte, punto_vta,
                              cbte_nro, imp_total, imp_tot_conc, imp_neto,
                              imp_subtotal, imp_trib, imp_op_ex, imp_reintegro,
                              fecha_cbte, id_impositivo, cod_pais, domicilio,
                              cod_relacion, moneda_id, moneda_ctz, obs)            
            
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            ws.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_imp = 100
            importe = 21
            ws.AgregarIva(iva_id, base_imp, importe)
            
            tipo = 0    # Item General
            cod_tur = 1 # Servicio de hotelería - alojamiento sin desayuno
            codigo = "T0001"
            ds = "Descripcion del producto P0001"
            iva_id = 5
            imp_iva = 21.00
            imp_subtotal = 121.00
            ws.AgregarItem(tipo, cod_tur, codigo, ds, 
                             iva_id, imp_iva, imp_subtotal)
            
            codigo = 68             # tarjeta de crédito
            tipo_tarjeta = 99       # otra (ver tabla de parámetros)
            numero_tarjeta = "999999"
            swift_code = None
            tipo_cuenta = None
            numero_cuenta = None
            ws.AgregarFormaPago(codigo, tipo_tarjeta, numero_tarjeta, 
                                  swift_code, tipo_cuenta, numero_cuenta)

            f_entrada = open(entrada,"w")
            dic = ws.factura
            escribir_factura(dic, f_entrada, agrega=True)            
            f_entrada.close()
    
        if '/ult' in sys.argv:
            print "Consultar ultimo numero:"
            i = sys.argv.index("/ult")
            if i+2<len(sys.argv):
               tipo_cbte = int(sys.argv[i+1])
               punto_vta = int(sys.argv[i+2])
            else:
               tipo_cbte = int(raw_input("Tipo de comprobante: "))
               punto_vta = int(raw_input("Punto de venta: "))
            ult_cbte = ws.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': punto_vta, 
                              'cbte_nro': ult_cbte, 
                              'fecha_cbte': ws.FechaCbte, 
                              }, open(salida,"w"))
            sys.exit(0)

        if '/get' in sys.argv:
            print "Recuperar comprobante:"
            i = sys.argv.index("/get")
            if i+3<len(sys.argv):
               tipo_cbte = int(sys.argv[i+1])
               punto_vta = int(sys.argv[i+2])
               cbte_nro = int(sys.argv[i+3])
            else:
               tipo_cbte = int(raw_input("Tipo de comprobante: "))
               punto_vta = int(raw_input("Punto de venta: "))
               cbte_nro = int(raw_input("Numero de comprobante: "))
            ws.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)

            print "FechaCbte = ", ws.FechaCbte
            print "CbteNro = ", ws.CbteNro
            print "PuntoVenta = ", ws.PuntoVenta
            print "ImpTotal =", ws.ImpTotal
            print "CAE = ", ws.CAE
            print "Vencimiento = ", ws.Vencimiento
            print "EmisionTipo = ", ws.EmisionTipo

            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': ws.PuntoVenta, 
                              'cbte_nro': ws.CbteNro, 
                              'fecha_cbte': ws.FechaCbte, 
                              'imp_total': ws.ImpTotal, 
                              'cae': ws.CAE, 
                              'fch_venc_cae': ws.Vencimiento,  
                              'emision_tipo': ws.EmisionTipo, 
                              }, open(salida,"w"))

            sys.exit(0)

        f_entrada = f_salida = None
        try:
            f_entrada = open(entrada,"r")
            f_salida = open(salida,"w")
            try:
                if DEBUG: print "Autorizando usando entrada:", entrada
                autorizar(ws, f_entrada, f_salida, '/informarcaea' in sys.argv)
            except SoapFault:
                XML = True
                raise
        finally:
            if f_entrada is not None: f_entrada.close()
            if f_salida is not None: f_salida.close()
            if XML:
                depurar_xml(ws.client)
        sys.exit(0)
    
    except SoapFault, e:
        print e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        e_str = unicode(e).encode("ascii","ignore")
        if not e_str:
            e_str = repr(e)
        print e_str
        escribir_factura({'err_msg': e_str,
                         }, open(salida,"w"))
        ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
        open("traceback.txt", "wb").write('\n'.join(ex))

        if DEBUG:
            raise
        sys.exit(5)
