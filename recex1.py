#!/usr/bin/python
# -*- coding: utf_8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Módulo de Intefase para archivos de texto (exportación version 1)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.27d"

import datetime
import os
import sys
import time
import traceback

# revisar la instalación de pyafip.ws:
import wsfexv1
from utils import SimpleXMLElement, SoapClient, SoapFault, date
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, abrir_conf


HOMO = wsfexv1.HOMO
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

if not '--pyfepdf' in sys.argv:
    TIPOS_REG = '0', '1', '2', '3'
    ENCABEZADO = [
        ('tipo_reg', 1, N), # 0: encabezado
        ('fecha_cbte', 8, A),
        ('tipo_cbte', 2, N), ('punto_vta', 4, N),
        ('cbte_nro', 8, N), 
        ('tipo_expo', 1, N), # 1:bienes, 2:servicios,... 
        ('permiso_existente', 1, A), # S/N/
        ('pais_dst_cmp', 3, N), # 203
        ('nombre_cliente', 200, A), # 'Joao Da Silva'
        ('cuit_pais_cliente', 11, N), # 50000000016
        ('domicilio_cliente', 300, A), # 'Rua 76 km 34.5 Alagoas'
        ('id_impositivo', 50, A), # 'PJ54482221-l'    
        ('imp_total', 15, I, 2), 
        ('moneda_id', 3, A),
        ('moneda_ctz', 10, I, 6), #10,6
        ('obs_comerciales', 4000, A),
        ('obs_generales', 1000, A),
        ('forma_pago', 50, A),
        ('incoterms', 3, A),
        ('incoterms_ds', 20, A),
        ('idioma_cbte', 1, A),
        ('cae', 14, N), ('fecha_vto', 8, A),
        ('resultado', 1, A), 
        ('reproceso', 1, A),
        ('motivos_obs', 1000, A),
        ('id', 15, N),
        ('fch_venc_cae', 8, A),
        ('excepcion', 100, A),
        ('err_code', 100, A),
        ('err_msg', 1000, A),
        ]

    DETALLE = [
        ('tipo_reg', 1, N), # 1: detalle item
        ('codigo', 50, A),
        ('qty', 12, I, 6),
        ('umed', 2, N),
        ('precio', 12, I, 6),
        ('importe', 13, I, 2),
        ('bonif', 12, I, 6),
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
        ('cbte_nro', 8, N), ('cbte_cuit', 11, N), 
        ]
else:
    print "!" * 78
    print "importando formato segun pyfepdf"
    from formato_txt import ENCABEZADO, DETALLE, PERMISO, CMP_ASOC, IVA, TRIBUTO
    TIPOS_REG = '0', '1', '2', '3'

if '/recex' in sys.argv:
    from recex import ENCABEZADO, DETALLE, PERMISO, CMP_ASOC
    ENCABEZADO[8] = ('nombre_cliente', 200, A) # 'Joao Da Silva'
    ENCABEZADO[7] = ('pais_dst_cmp', 3, N)
    ENCABEZADO[16] = ('obs_generales', 1000, A)
    DETALLE[5] = ('importe', 13, I, 2)
    DETALLE.append(('bonif', 12, I, 6))


def autorizar(ws, entrada, salida):
    # recupero el último número de transacción
    ##id = wsfex.ultnro(client, token, sign, cuit)

    detalles = []
    permisos = []
    cbtasocs = []
    encabezado = []
    if '/dbf' in sys.argv:
        formatos = [('Encabezado', ENCABEZADO, encabezado), ('Permisos', PERMISO, permisos), ('Comprobante Asociado', CMP_ASOC, cbtasocs), ('Detalles', DETALLE, detalles)]
        dic = leer_dbf(formatos, conf_dbf)
        encabezado = encabezado[0]
    else:
        encabezado = {}
        for linea in entrada:
            if str(linea[0])==TIPOS_REG[0]:
                encabezado = leer(linea, ENCABEZADO)
                if 'nro_doc' in encabezado:
                    encabezado['cuit_pais_cliente'] = encabezado['nro_doc']
            elif str(linea[0])==TIPOS_REG[1]:
                detalle = leer(linea, DETALLE)
                detalles.append(detalle)
            elif str(linea[0])==TIPOS_REG[2]:
                permiso = leer(linea, PERMISO)
                permisos.append(permiso)
            elif str(linea[0])==TIPOS_REG[3]:
                cbtasoc = leer(linea, CMP_ASOC)
                cbtasocs.append(cbtasoc)
            else:
                print "Tipo de registro incorrecto:", linea[0]

    if not encabezado['id']:
        # TODO: habria que leer y/o grabar el id en el archivo
        ##id += 1 # incremento el nº de transacción 
        # Por el momento, el id se calcula con el tipo, pv y nº de comprobant
        i = long(encabezado['cbte_nro'])
        i += (int(encabezado['cbte_nro'])*10**4 + int(encabezado['punto_vta']))*10**8
        encabezado['id'] = ws.GetLastID() + 1
    
    if '/testing' in sys.argv:
        encabezado['id'] = long(ws.GetLastID()) + 1
        encabezado['cbte_nro'] = int(ws.GetLastCMP(encabezado['tipo_cbte'], encabezado['punto_vta'])) + 1
        encabezado['fecha_cbte'] = datetime.datetime.now().strftime("%Y%m%d")

    ws.CrearFactura(**encabezado)
    for detalle in detalles:
        ws.AgregarItem(**detalle)
    for permiso in permisos:
        ws.AgregarPermiso(**permiso)
    for cbtasoc in cbtasocs:
        ws.AgregarCmpAsoc(**cbtasoc)

    if DEBUG:
        #print f.to_dict()
        print '\n'.join(["%s='%s'" % (k,str(v)) for k,v in encabezado.items()])
        for detalle in detalles:
            print ', '.join(["%s='%s'" % (k,str(v)) for k,v in detalle.items()])
            print "DIF:", detalle['qty'] * detalle['precio'] - detalle['importe']
            
        print 'id:', encabezado['id']
    if not DEBUG or not sys.stdout.isatty() or raw_input("Facturar?")=="S":
        ws.LanzarExcepcion = False
        cae = ws.Authorize(id=encabezado['id'])
        dic = ws.factura
        dic.update({
            'cae': cae and str(cae) or '',
            'fch_venc_cae': ws.FchVencCAE and str(ws.FchVencCAE) or '',
            'resultado': ws.Resultado or '',
            'motivos_obs': ws.Obs or '',
            'err_code': str(ws.ErrCode),
            'err_msg': ws.ErrMsg or '',
            'reproceso': ws.Reproceso or '',
            })
        escribir_factura(dic, salida)
        print "ID:", encabezado['id'], "NRO:", dic['cbte_nro'], "Resultado:", dic['resultado'],
        print "CAE:", dic['cae'], "Obs:", dic['motivos_obs'].encode("ascii", "ignore"),
        print "Err:", dic['err_msg'].encode("ascii", "ignore"), "Reproceso:", dic['reproceso']
        if ws.Excepcion:
            print "Excepcion:", ws.Excepcion.encode("ascii", "ignore")
            print "Traceback:", ws.Traceback.encode("ascii", "ignore")

def escribir_factura(dic, archivo, agrega=False):
    dic['tipo_reg'] = TIPOS_REG[0]
    archivo.write(escribir(dic, ENCABEZADO))
    for it in dic.get('detalles', []):
        it['tipo_reg'] = TIPOS_REG[1]
        archivo.write(escribir(it, DETALLE))
    if 'permisos' in dic:    
        for it in dic['permisos']:
            it['tipo_reg'] = TIPOS_REG[2]
            archivo.write(escribir(it, PERMISO))

    if '/dbf' in sys.argv:
        formatos = [('Encabezado', ENCABEZADO, [dic]), ('Permisos', PERMISO, dic.get('permisos', [])), ('Comprobante Asociado', CMP_ASOC, dic.get('cbtes_asoc', [])), ('Detalles', DETALLE, dic.get('detalles', []))]
        guardar_dbf(formatos, agrega, conf_dbf)

            
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
        print " /dbf: lee y almacena la información en tablas DBF"
        print
        print "Ver rece.ini para parámetros de configuración (URL, certificados, etc.)"
        sys.exit(0)

    config = abrir_conf(CONFIG_FILE, DEBUG)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSFEXv1','CUIT')
    entrada = config.get('WSFEXv1','ENTRADA')
    salida = config.get('WSFEXv1','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = None
    if config.has_option('WSFEXv1','URL') and not HOMO:
        wsfexv1_url = config.get('WSFEXv1','URL')
    else:
        wsfexv1_url = ""

    CACERT = config.has_option('WSFEXv1', 'CACERT') and config.get('WSFEXv1', 'CACERT') or None
    WRAPPER = config.has_option('WSFEXv1', 'WRAPPER') and config.get('WSFEXv1', 'WRAPPER') or None

    if config.has_section('PROXY') and not HOMO:
        proxy_dict = dict(("proxy_%s" % k,v) for k,v in config.items('PROXY'))
        proxy_dict['proxy_port'] = int(proxy_dict['proxy_port'])
    else:
        proxy_dict = {}

    if config.has_section('DBF'):
        conf_dbf = dict(config.items('DBF'))
        if DEBUG: print "conf_dbf", conf_dbf
    else:
        conf_dbf = {}
        
    if '/debug'in sys.argv:
        DEBUG = True

    if '/xml'in sys.argv:
        XML = True

    if DEBUG:
        print "wsaa_url %s\nwsfexv1_url %s" % (wsaa_url, wsfexv1_url)
        print "Config_file:", CONFIG_FILE
        print "Entrada: ", entrada
        print "Salida:", salida
    
    try:
        ws = wsfexv1.WSFEXv1()
        ws.Conectar("", wsfexv1_url, cacert=CACERT, wrapper=WRAPPER)
        ws.Cuit = cuit

        if '/dummy' in sys.argv:
            print "Consultando estado de servidores..."
            ws.Dummy()
            print "AppServerStatus", ws.AppServerStatus
            print "DbServerStatus", ws.DbServerStatus
            print "AuthServerStatus", ws.AuthServerStatus
            sys.exit(0)


        if '/formato' in sys.argv:
            from formatos.formato_dbf import definir_campos
            print "Formato:"
            for msg, formato in [('Encabezado', ENCABEZADO), ('Detalle', DETALLE), ('Permiso', PERMISO), ('Comprobante Asociado', CMP_ASOC)]:
                if not '/dbf' in sys.argv:
                    comienzo = 1
                    print "== %s ==" % msg
                    for fmt in formato:
                        clave, longitud, tipo = fmt[0:3]
                        dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                        print " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                            clave, comienzo, longitud, tipo, dec)
                        comienzo += longitud
                else:
                    filename =  "%s.dbf" % msg.lower()[:8]
                    print "==== %s (%s) ====" % (msg, filename)
                    claves, campos = definir_campos(formato)
                    for campo in campos:
                        print " * Campo: %s" % (campo,)
            sys.exit(0)

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsfex", cert, privatekey, wsaa_url, proxy=proxy_dict, cacert=CACERT, wrapper=WRAPPER)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)
        ws.SetTicketAcceso(ta)
        
        if '/prueba' in sys.argv:
            # generar el archivo de prueba para la próxima factura
            f_entrada = open(entrada,"w")

            tipo_cbte = 19 # FC Expo (ver tabla de parámetros)
            punto_vta = 7
            # Obtengo el último número de comprobante y le agrego 1
            cbte_nro = int(ws.GetLastCMP(tipo_cbte, punto_vta)) + 1
            fecha_cbte = datetime.datetime.now().strftime("%Y%m%d")
            tipo_expo = 1 # tipo de exportación (ver tabla de parámetros)
            permiso_existente = "S"
            dst_cmp = 203 # país destino
            cliente = "Joao Da Silva"
            cuit_pais_cliente = "50000000016"
            domicilio_cliente = "Rua 76 km 34.5 Alagoas"
            id_impositivo = "PJ54482221-l"
            moneda_id = "DOL" # para reales, "DOL" o "PES" (ver tabla de parámetros)
            moneda_ctz = 8.02
            obs_comerciales = "Observaciones comerciales"
            obs = "Sin observaciones"
            forma_pago = "30 dias"
            incoterms = "FOB" # (ver tabla de parámetros)
            incoterms_ds = "Flete a Bordo" 
            idioma_cbte = 1 # (ver tabla de parámetros)
            imp_total = "250.00"
            
            # Creo una factura (internamente, no se llama al WebService):
            ok = ws.CrearFactura(tipo_cbte, punto_vta, cbte_nro, fecha_cbte, 
                    imp_total, tipo_expo, permiso_existente, dst_cmp, 
                    cliente, cuit_pais_cliente, domicilio_cliente, 
                    id_impositivo, moneda_id, moneda_ctz, 
                    obs_comerciales, obs, forma_pago, incoterms, 
                    idioma_cbte, incoterms_ds)
            
            # Agrego un item:
            codigo = "PRO1"
            ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
            qty = 2
            precio = "150.00"
            umed = 1 # Ver tabla de parámetros (unidades de medida)
            bonif = "50.00"
            imp_total = "250.00" # importe total final del artículo
            # lo agrego a la factura (internamente, no se llama al WebService):
            ok = ws.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)

            # Agrego un permiso (ver manual para el desarrollador)
            id = "99999AAXX999999A"
            dst = 225 # país destino de la mercaderia
            ok = ws.AgregarPermiso(id, dst)

            # Agrego un comprobante asociado (solo para N/C o N/D)
            if tipo_cbte in (20,21): 
                cbteasoc_tipo = 19
                cbteasoc_pto_vta = 2
                cbteasoc_nro = 1234
                cbteasoc_cuit = 20111111111
                ws.AgregarCmpAsoc(cbteasoc_tipo, cbteasoc_pto_vta, cbteasoc_nro, cbteasoc_cuit)
                
            dic = ws.factura
            dic['id'] = ws.GetLastID() + 1
            escribir_factura(dic, f_entrada, agrega=True)
            f_entrada.close()
        
        if '/ult' in sys.argv:
            i = sys.argv.index("/ult")
            if i+2<len(sys.argv):
               tipo_cbte = int(sys.argv[i+1])
               punto_vta = int(sys.argv[i+2])
            else:
               tipo_cbte = int(raw_input("Tipo de comprobante: "))
               punto_vta = int(raw_input("Punto de venta: "))
            ult_cbte = ws.GetLastCMP(tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            print ws.ErrMsg
            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': punto_vta, 
                              'cbte_nro': ult_cbte,
                              'fecha_cbte': ws.FechaCbte, 
                              'err_msg': ws.ErrMsg,
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
            ws.GetCMP(tipo_cbte, punto_vta, cbte_nro)

            print "FechaCbte = ", ws.FechaCbte
            print "CbteNro = ", ws.CbteNro
            print "PuntoVenta = ", ws.PuntoVenta
            print "ImpTotal =", ws.ImpTotal
            print "CAE = ", ws.CAE
            print "Vencimiento = ", ws.Vencimiento
            print ws.ErrMsg 

            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': ws.PuntoVenta, 
                              'cbte_nro': ws.CbteNro, 
                              'fecha_cbte': ws.FechaCbte, 
                              'imp_total': ws.ImpTotal, 
                              'cae': str(ws.CAE), 
                              'fch_venc_cae': ws.Vencimiento,  
                              'err_msg': ws.ErrMsg,
                            }, open(salida,"w"))
            sys.exit(0)

        if '/ctz' in sys.argv:
            i = sys.argv.index("/ctz")
            if i+1<len(sys.argv):
               moneda_id = sys.argv[i+1]
            else:
               moneda_id = raw_input("Id de moneda (DOL): ") or 'DOL'
            ctz = ws.GetParamCtz(moneda_id)
            print "Cotizacion: ", ctz
            print ws.ErrMsg
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
        if DEBUG or True:
            raise
        sys.exit(5)
