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

"Módulo de Intefase para archivos de texto (mercado interno versión 1)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010-2015 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.36d"

import datetime
import os
import sys
import time
import traceback
import warnings

# revisar la instalación de pyafip.ws:
import wsfev1
from utils import SimpleXMLElement, SoapClient, SoapFault, date
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, abrir_conf


HOMO = wsfev1.HOMO
DEBUG = False
XML = False
TIMEOUT = 30
CONFIG_FILE = "rece.ini"

LICENCIA = """
rece1.py: Interfaz de texto para generar Facturas Electrónica Mercado Interno V1
Copyright (C) 2010 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

# definición del formato del archivo de intercambio:

ENCABEZADO = [
    ('tipo_reg', 1, N), # 0: encabezado
    ('fecha_cbte', 8, A),
    ('tipo_cbte', 2, N), ('punto_vta', 4, N),
    ('cbt_desde', 8, N), 
    ('cbt_hasta', 8, N), 
    ('concepto', 1, N), # 1:bienes, 2:servicios,... 
    ('tipo_doc', 2, N), # 80
    ('nro_doc', 11, N), # 50000000016    
    ('imp_total', 15, I, 2), 
    ('no_usar', 15, I, 2), 
    ('imp_tot_conc', 15, I, 2), 
    ('imp_neto', 15, I, 2), 
    ('imp_iva', 15, I, 2), 
    ('imp_trib', 15, I, 2), 
    ('imp_op_ex', 15, I, 2), 
    ('moneda_id', 3, A),
    ('moneda_ctz', 10, I, 6), #10,6
    ('fecha_venc_pago', 8, A),   # opcional solo conceptos 2 y 3
    ('cae', 14, A), ('fch_venc_cae', 8, A),
    ('resultado', 1, A), 
    ('motivos_obs', 1000, A),
    ('err_code', 6, A),
    ('err_msg', 1000, A),
    ('reproceso', 1, A),
    ('emision_tipo', 4, A),
    ('fecha_serv_desde', 8, A), # opcional solo conceptos 2 y 3
    ('fecha_serv_hasta', 8, A), # opcional solo conceptos 2 y 3
    ]
                   
#DETALLE = [
#    ('tipo_reg', 1, N), # 1: detalle item
#    ('codigo', 30, A),
#    ('qty', 12, I),
#    ('umed', 2, N),
#    ('precio', 12, I, 3),
#    ('imp_total', 14, I, 3),
#    ('ds', 4000, A),
#    ]

TRIBUTO = [
    ('tipo_reg', 1, N), # 1: tributo
    ('tributo_id', 16, N),
    ('desc', 100, A),
    ('base_imp', 15, I, 2), 
    ('alic', 15, I, 2), 
    ('importe', 15, I, 2), 
    ]

IVA = [
    ('tipo_reg', 1, N), # 2: alicuota de IVA
    ('iva_id', 16, N),
    ('base_imp', 15, I, 2), 
    ('importe', 15, I, 2), 
    ]

CMP_ASOC = [
    ('tipo_reg', 1, N), # 3: comprobante asociado
    ('tipo', 3, N), ('pto_vta', 4, N),
    ('nro', 8, N), 
    ]

OPCIONAL = [
    ('tipo_reg', 1, N), # 6: datos opcionales
    ('opcional_id', 4, A),
    ('valor', 250, A), 
    ]

# Constantes (tablas de parámetros):

TIPO_CBTE = {1: "FAC A", 2: "N/D A", 3: "N/C A", 6: "FAC B", 7: "N/D B",
             8: "N/C B", 4: "REC A", 5: "NV A", 9: "REC B",             
             10: "NV B", 11: "FAC C", 12: "N/D C", 13: "N/C C", 15: "REC C",
             49: "BIENES USADOS",
             60: "LIQ PROD A", 61: "LIQ PROD B", 63: "LIQ A", 64: "LIQ B", 
            }

TIPO_DOC = {80: 'CUIT', 86: 'CUIL', 96: 'DNI', 99: '', 87: u"CDI"} 


def autorizar(ws, entrada, salida, informar_caea=False):
    encabezados = []
    if '/dbf' in sys.argv:
        tributos = []
        ivas = []
        cbtasocs = []
        encabezados = []
        opcionales = []
        if DEBUG: print "Leyendo DBF..."

        formatos = [('Encabezado', ENCABEZADO, encabezados), 
                    ('Tributo', TRIBUTO, tributos), 
                    ('Iva', IVA, ivas), 
                    ('Comprobante Asociado', CMP_ASOC, cbtasocs),
                    ('Datos Opcionales', OPCIONAL, opcionales),
                    ]
        dic = leer_dbf(formatos, conf_dbf)
        
        # rearmar estructura asociando id (comparando, si se útiliza)
        for encabezado in encabezados:
            for tributo in tributos:
                if tributo.get("id") == encabezado.get("id"):
                    encabezado.setdefault("tributos", []).append(tributo)
            for iva in ivas:
                if iva.get("id") == encabezado.get("id"):
                    encabezado.setdefault("ivas", []).append(iva)
            for cbtasoc in cbtasocs:
                if cbtasoc.get("id") == encabezado.get("id"):
                    encabezado.setdefault("cbtasocs", []).append(cbtasoc)
            for opcional in opcionales:
                if opcional.get("id") == encabezado.get("id"):
                    encabezado.setdefault("opcionales", []).append(opcional)
            if encabezado.get("id") is None and len(encabezados) > 1:
                # compatibilidad hacia atrás, descartar si hay más de 1 factura
                warnings.warn("Para múltiples registros debe usar campo id!")
                break
    elif '/json' in sys.argv:
        # ya viene estructurado
        import json
        encabezados = json.load(entrada)
    else:
        # la estructura está implícita en el órden de los registros (líneas)
        for linea in entrada:
            if str(linea[0])=='0':
                encabezado = leer(linea, ENCABEZADO)
                encabezados.append(encabezado)
                if DEBUG: print len(encabezados), "Leida factura %(cbt_desde)s" % encabezado 
            elif str(linea[0])=='1':
                tributo = leer(linea, TRIBUTO)
                encabezado.setdefault("tributos", []).append(tributo)
            elif str(linea[0])=='2':
                iva = leer(linea, IVA)
                encabezado.setdefault("ivas", []).append(iva)
            elif str(linea[0])=='3':
                cbtasoc = leer(linea, CMP_ASOC)
                encabezado.setdefault("cbtasocs", []).append(cbtasoc)
            elif str(linea[0])=='6':
                opcional = leer(linea, OPCIONAL)
                encabezado.setdefault("opcionales", []).append(opcional)
            else:
                print "Tipo de registro incorrecto:", linea[0]

    if not encabezados:
        raise RuntimeError("No se pudieron leer los registros de la entrada")

    # ajusto datos para pruebas en depuración (nro de cbte. / fecha)
    if '--testing' in sys.argv and DEBUG:
        encabezado['punto_vta'] = 9998
        cbte_nro = int(ws.CompUltimoAutorizado(encabezado['tipo_cbte'], 
                                               encabezado['punto_vta'])) + 1
        encabezado['cbt_desde'] = cbte_nro
        encabezado['cbt_hasta'] = cbte_nro
        encabezado['fecha_cbte'] = datetime.datetime.now().strftime("%Y%m%d")

    # recorrer los registros para obtener CAE (dicts tendrá los procesados)
    dicts = []
    for encabezado in encabezados:
        if informar_caea:
            if '/testing' in sys.argv:
                encabezado['cae'] = '21073372218437'
            encabezado['caea'] = encabezado['cae']
        # extraer sub-registros:
        ivas = encabezado.get('ivas', encabezado.get('iva', []))
        tributos = encabezado.get('tributos', [])
        cbtasocs = encabezado.get('cbtasocs', [])
        opcionales = encabezado.get('opcionales', [])

        ws.CrearFactura(**encabezado)
        for tributo in tributos:
            ws.AgregarTributo(**tributo)
        for iva in ivas:
            ws.AgregarIva(**iva)
        for cbtasoc in cbtasocs:
            ws.AgregarCmpAsoc(**cbtasoc)
        for opcional in opcionales:
            ws.AgregarOpcional(**opcional)

        if DEBUG:
            print '\n'.join(["%s='%s'" % (k,str(v)) for k,v in ws.factura.items()])
        if not DEBUG or raw_input("Facturar (S/n)?")=="S":
            if not informar_caea:
                cae = ws.CAESolicitar()
                dic = ws.factura
            else:
                cae = ws.CAEARegInformativo()
                dic = ws.factura
            print "Procesando %s %04d %08d %08d %s %s $ %0.2f IVA: $ %0.2f" % (
                TIPO_CBTE.get(dic['tipo_cbte'], dic['tipo_cbte']), 
                dic['punto_vta'], dic['cbt_desde'], dic['cbt_hasta'], 
                TIPO_DOC.get(dic['tipo_doc'], dic['tipo_doc']), dic['nro_doc'], 
                float(dic['imp_total']), 
                float(dic['imp_iva'] if dic['imp_iva'] is not None else 'NaN')) 
            dic.update(encabezado)         # preservar la estructura leida
            dic.update({
                'cae': cae and str(cae) or '',
                'fch_venc_cae': ws.Vencimiento and str(ws.Vencimiento) or '',
                'resultado': ws.Resultado,
                'motivos_obs': ws.Obs,
                'err_code': str(ws.ErrCode),
                'err_msg': ws.ErrMsg,
                'reproceso': ws.Reproceso,
                'emision_tipo': ws.EmisionTipo,
                })
            dicts.append(dic)
            print "NRO:", dic['cbt_desde'], "Resultado:", dic['resultado'], "%s:" % ws.EmisionTipo,dic['cae'],"Obs:",dic['motivos_obs'].encode("ascii", "ignore"), "Err:", dic['err_msg'].encode("ascii", "ignore"), "Reproceso:", dic['reproceso']
    if dicts:
        escribir_facturas(dicts, salida)

def escribir_facturas(encabezados, archivo, agrega=False):
    if '/json' in sys.argv:
        import json
        facturas = []
        for dic in encabezados:
            factura = dic.copy()
            facturas.append(factura)
            # ajsutes por compatibilidad hacia atras y con pyfepdf
            factura['fecha_vto'] = factura.get('fch_venc_cae')
            if 'iva' in factura:
                factura['ivas'] = factura.get('iva', [])
                del factura['iva']
        json.dump(facturas, archivo, sort_keys=True, indent=4)
    else:
        for dic in encabezados:
            dic['tipo_reg'] = 0
            archivo.write(escribir(dic, ENCABEZADO))
            if 'tributos' in dic:
                for it in dic['tributos']:
                    it['tipo_reg'] = 1
                    archivo.write(escribir(it, TRIBUTO))
            if 'iva' in dic or 'ivas' in dic:
                for it in dic.get('iva', dic.get('ivas')):
                    it['tipo_reg'] = 2
                    archivo.write(escribir(it, IVA))
            if 'cbtes_asoc' in dic:
                for it in dic['cbtes_asoc']:
                    it['tipo_reg'] = 3
                    archivo.write(escribir(it, CMP_ASOC))
            if 'opcionales' in dic:
                for it in dic['opcionales']:
                    it['tipo_reg'] = 6
                    archivo.write(escribir(it, OPCIONAL))

    if '/dbf' in sys.argv:
        formatos = [('Encabezado', ENCABEZADO, encabezados), 
                    ('Tributo', TRIBUTO, dic.get('tributos', [])), 
                    ('Iva', IVA, dic.get('iva', [])), 
                    ('Comprobante Asociado', CMP_ASOC, dic.get('cbtes_asoc', [])),
                    ('Datos Opcionales', OPCIONAL, dic.get("opcionales", [])),
                    ]
        guardar_dbf(formatos, agrega, conf_dbf)


def depurar_xml(client, ruta="."):
    fecha = time.strftime("%Y%m%d%H%M%S")
    f=open(os.path.join(ruta, "request-%s.xml" % fecha),"w")
    f.write(client.xml_request)
    f.close()
    f=open(os.path.join(ruta, "response-%s.xml" % fecha),"w")
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

    if '/debug'in sys.argv:
        DEBUG = True
        print "VERSION", __version__, "HOMO", HOMO

    config = abrir_conf(CONFIG_FILE, DEBUG)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSFEv1','CUIT')
    if '/entrada' in sys.argv:
        entrada = sys.argv[sys.argv.index("/entrada")+1]
    else:
        entrada = config.get('WSFEv1','ENTRADA')
    salida = config.get('WSFEv1','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = None
    if config.has_option('WSFEv1','URL') and not HOMO:
        wsfev1_url = config.get('WSFEv1','URL')
    else:
        wsfev1_url = None

    if config.has_option('WSFEv1','REPROCESAR'):
        wsfev1_reprocesar = config.get('WSFEv1','REPROCESAR') == 'S'
    else:
        wsfev1_reprocesar = None

    if config.has_option('WSFEv1', 'XML_DIR'):
        wsfev1_xml_dir = config.get('WSFEv1', 'XML_DIR')
    else:
        wsfev1_xml_dir = "."

    if config.has_section('DBF'):
        conf_dbf = dict(config.items('DBF'))
        if DEBUG: print "conf_dbf", conf_dbf
    else:
        conf_dbf = {}

    if config.has_section('PROXY') and not HOMO:
        proxy_dict = dict(("proxy_%s" % k,v) for k,v in config.items('PROXY'))
        proxy_dict['proxy_port'] = int(proxy_dict['proxy_port'])
    else:
        proxy_dict = {}
    CACERT = config.has_option('WSFEv1', 'CACERT') and config.get('WSFEv1', 'CACERT') or None
    WRAPPER = config.has_option('WSFEv1', 'WRAPPER') and config.get('WSFEv1', 'WRAPPER') or None

    if config.has_option('WSFEv1', 'TIMEOUT'):
        TIMEOUT = int(config.get('WSFEv1', 'TIMEOUT'))

    if '/xml'in sys.argv:
        XML = True

    RUTA_XML = config.has_option('WSFEv1', 'XML') and config.get('WSFEv1', 'XML') or "."

    if DEBUG:
        print "wsaa_url %s\nwsfev1_url %s\ncuit %s" % (wsaa_url, wsfev1_url, cuit)
        if proxy_dict: print "proxy_dict=",proxy_dict
        print "timeout:", TIMEOUT

    if '/x' in sys.argv:
        escribir_facturas([{'err_msg': "Prueba",
                     }], open("x.txt","w"))

    try:
        ws = wsfev1.WSFEv1()
        ws.LanzarExcepciones = True
        ws.Conectar("", wsfev1_url, proxy=proxy_dict, cacert=CACERT, wrapper=WRAPPER, timeout=TIMEOUT)
        ws.Cuit = cuit
        if wsfev1_reprocesar is not None:
            ws.Reprocesar = wsfev1_reprocesar

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
                                 ('Tributo', TRIBUTO), ('Iva', IVA), 
                                 ('Comprobante Asociado', CMP_ASOC),
                                 ('Opcionales', OPCIONAL)]:
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
                    from formatos.formato_dbf import definir_campos
                    filename =  "%s.dbf" % msg.lower()[:8]
                    print "==== %s (%s) ====" % (msg, filename)
                    claves, campos = definir_campos(formato)
                    for campo in campos:
                        print " * Campo: %s" % (campo,)
            sys.exit(0)

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsfe", cert, privatekey, wsaa_url, proxy=proxy_dict, cacert=CACERT, wrapper=WRAPPER)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)
        ws.SetTicketAcceso(ta)
                    
        if '/prueba' in sys.argv:
            # generar el archivo de prueba para la próxima factura
            tipo_cbte = 1
            punto_vta = 4002
            cbte_nro = ws.CompUltimoAutorizado(tipo_cbte, punto_vta)
            if not cbte_nro: cbte_nro=0
            cbte_nro=int(cbte_nro)
            fecha = datetime.datetime.now().strftime("%Y%m%d")
            concepto = 1
            tipo_doc = 80; nro_doc = "30628789661"
            cbt_desde = cbte_nro + 1; cbt_hasta = cbte_nro + 1
            imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
            imp_iva = "21.00"; imp_trib = "1.00"; imp_op_ex = "0.00"
            fecha_cbte = fecha; fecha_venc_pago = None # fecha
            # Fechas del período del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = ""; fecha_serv_hasta = ""
            moneda_id = 'PES'; moneda_ctz = '1.000'

            ws.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
                fecha_serv_desde, fecha_serv_hasta, #--
                moneda_id, moneda_ctz)
            
            if tipo_cbte not in (1, 2, 6, 7):
                tipo = 1
                pto_vta = 2
                nro = 1234
                ws.AgregarCmpAsoc(tipo, pto_vta, nro)
            
            if '--proyectos' in sys.argv:
                ws.AgregarOpcional(2, "1234")  # identificador del proyecto
            
            # datos opcionales para RG 3668 Impuesto al Valor Agregado - Art.12:
            if '--rg3668' in sys.argv:
                ws.AgregarOpcional(5, "02")             # IVA Excepciones
                ws.AgregarOpcional(61, "80")            # Firmante Doc Tipo
                ws.AgregarOpcional(62, "20267565393")   # Firmante Doc Nro
                ws.AgregarOpcional(7, "01")             # Carácter del Firmante

            # RG 3.368 Establecimientos de educación pública de gestión privada
            if '--rg3749' in sys.argv:
                ws.AgregarOpcional(10, "1")             # Actividad Comprendida
                ws.AgregarOpcional(1011, "80")            # Tipo de Documento
                ws.AgregarOpcional(1012, "20267565393")   # Número de Documento
                
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = 100
            alic = 1
            importe = 1
            ws.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_imp = 100
            importe = 21
            ws.AgregarIva(iva_id, base_imp, importe) 
                        
            f_entrada = open(entrada,"w")
                
            if DEBUG:
                print ws.factura

            dic = ws.factura
            escribir_facturas([dic], f_entrada, agrega=True)
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
            ult_cbte = ws.CompUltimoAutorizado(tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            print ws.ErrMsg
            depurar_xml(ws.client, RUTA_XML)
            escribir_facturas([{'tipo_cbte': tipo_cbte, 
                              'punto_vta': punto_vta, 
                              'cbt_desde': ult_cbte, 
                              'fecha_cbte': ws.FechaCbte, 
                              'err_msg': ws.ErrMsg,
                              }], open(salida,"w"))
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
            ws.CompConsultar(tipo_cbte, punto_vta, cbte_nro)

            ws.AnalizarXml("XmlResponse")
            print "FechaCbte = ", ws.FechaCbte
            print "CbteNro = ", ws.CbteNro
            print "PuntoVenta = ", ws.PuntoVenta
            print "TipoDoc = ", ws.ObtenerTagXml('DocTipo')
            print "NroDoc = ", ws.ObtenerTagXml('DocNro')
            print "ImpTotal =", ws.ImpTotal
            print "CAE = ", ws.CAE
            print "Vencimiento = ", ws.Vencimiento
            print "EmisionTipo = ", ws.EmisionTipo
            print ws.ErrMsg 

            depurar_xml(ws.client, RUTA_XML)
            # grabar todos los datos devueltos por AFIP:
            factura = ws.factura.copy()
            # actulizar los campos básicos:
            factura.update({'tipo_cbte': tipo_cbte, 
                              'punto_vta': ws.PuntoVenta, 
                              'cbt_desde': ws.CbtDesde, 
                              'cbt_hasta': ws.CbtHasta, 
                              'fecha_cbte': ws.FechaCbte, 
                              'tipo_doc': ws.ObtenerCampoFactura('tipo_doc'),
                              'nro_doc': ws.ObtenerCampoFactura('nro_doc'),
                              'imp_total': ws.ImpTotal, 
                              'imp_neto': ws.ImpNeto,
                              'imp_iva': ws.ImpOpEx,
                              'imp_trib': ws.ImpTrib,
                              'imp_op_ex': ws.ImpTrib,
                              'cae': str(ws.CAE), 
                              'fch_venc_cae': ws.Vencimiento,  
                              'emision_tipo': ws.EmisionTipo, 
                              'resultado': ws.Resultado,
                              'err_msg': ws.ErrMsg,
                              'motivos_obs': ws.Obs,
                            })
            escribir_facturas([factura], open(salida,"w"))

            sys.exit(0)

        if '/solicitarcaea' in sys.argv:
            i = sys.argv.index("/solicitarcaea")
            if i+2<len(sys.argv):
                periodo = sys.argv[sys.argv.index("/solicitarcaea")+1]
                orden = sys.argv[sys.argv.index("/solicitarcaea")+2]
            else:
                periodo = raw_input("Periodo: ")
                orden = raw_input("Orden: ")
                
            if DEBUG: 
                print "Solicitando CAEA para periodo %s orden %s" % (periodo, orden)
            
            caea = ws.CAEASolicitar(periodo, orden)
            print "CAEA:", caea

            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error

            depurar_xml(ws.client, RUTA_XML)

            if not caea:
                if DEBUG: 
                    print "Consultando CAEA para periodo %s orden %s" % (periodo, orden)
                caea = ws.CAEAConsultar(periodo, orden)
                print "CAEA:", caea
                
            if DEBUG:
                print "Periodo:", ws.Periodo 
                print "Orden:", ws.Orden 
                print "FchVigDesde:", ws.FchVigDesde 
                print "FchVigHasta:", ws.FchVigHasta 
                print "FchTopeInf:", ws.FchTopeInf 
                print "FchProceso:", ws.FchProceso

            escribir_facturas([{'cae': str(caea), 
                              'emision_tipo': "CAEA", 
                             }], open(salida,"w"))
                              
            sys.exit(0)

        if '/consultarcaea' in sys.argv:
            i = sys.argv.index("/consultarcaea")
            if i+2<len(sys.argv):
                periodo = sys.argv[sys.argv.index("/consultarcaea")+1]
                orden = sys.argv[sys.argv.index("/consultarcaea")+2]
            else:
                periodo = raw_input("Periodo: ")
                orden = raw_input("Orden: ")

            if DEBUG: 
                print "Consultando CAEA para periodo %s orden %s" % (periodo, orden)
            
            caea = ws.CAEAConsultar(periodo, orden)
            print "CAEA:", caea

            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error
                
            if DEBUG:
                print "Periodo:", ws.Periodo 
                print "Orden:", ws.Orden 
                print "FchVigDesde:", ws.FchVigDesde 
                print "FchVigHasta:", ws.FchVigHasta 
                print "FchTopeInf:", ws.FchTopeInf
                print "FchProceso:", ws.FchProceso
            sys.exit(0)

        if '/ptosventa' in sys.argv:

            print "=== Puntos de Venta ==="
            print u'\n'.join(ws.ParamGetPtosVenta())
            sys.exit(0)

        if '/informarcaeanoutilizadoptovta' in sys.argv:
            i = sys.argv.index('/informarcaeanoutilizadoptovta') 
            if i+2 < len(sys.argv):
                caea = sys.argv[i+1]
                pto_vta = sys.argv[i+2]
            else:
                caea = raw_input("CAEA: ")
                pto_vta = raw_input("Punto de Venta: ")
            if DEBUG: 
                print "Informando CAEA no utilizado: %s pto_vta %s" % (caea, pto_vta)
            ok = ws.CAEASinMovimientoInformar(pto_vta, caea)
            print "Resultado:", ok
            print "FchProceso:", ws.FchProceso            
            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error
            sys.exit(0)

        ws.LanzarExcepciones = False
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
                depurar_xml(ws.client, RUTA_XML)
        sys.exit(0)
    
    except SoapFault, e:
        print "SoapFault:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        e_str = unicode(e).encode("ascii","ignore")
        if not e_str:
            e_str = repr(e)
        print "Excepcion:", e_str
        escribir_facturas([{'err_msg': e_str,
                         }], open(salida,"w"))
        ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
        open("traceback.txt", "wb").write('\n'.join(ex))

        if DEBUG:
            raise
        sys.exit(5)
