#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.

"""Módulo para obtener Carta de Porte Electrónica
para transporte ferroviario y automotor RG 5017/2021
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2021- Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.05e"

LICENCIA = """
wscpe.py: Interfaz para generar Carta de Porte Electrónica AFIP v1.0.0
Resolución General 5017/2021
Copyright (C) 2021 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/CartadePorte

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
  --prueba: genera y autoriza una rec de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)
  --dummy: consulta estado de servidores

  --autorizar: autoriza un cpe

  --ult: consulta ultimo nro cpe emitido
  --consultar: consulta un cpe generado

  --anular: un CPE existente (usa cabecera)
  --informar_contingencia: (usa cabecera y contingencias)
  --cerrar_contingencia: (usa cabecera y contingencias)
  --rechazo: (usa cabecera)
  --confirmar_arribo: (usa cabecera)
  --descargado_destino: (usa cabecera)
  --confirmacion_definitiva: (usa cabecera, datos_carga)
  --nuevo_destino_destinatario: (usa cabecera, destino, transporte)
  --regreso_origen: (usa cabecera, transporte)
  --desvio: (usa cabecera, destino, transporte)

  --provincias: listado de provincias
  --localidades_por_provincia: listado de localidades para la provincia dada
  --localidades_por_productor: listado de localidades para el CUIT
  --tipos_granos': listado de granos
  --plantas: codigos de plantas habilitados para el cuit

Ver wscpe.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time, base64, datetime
from utils import date
import traceback
from pysimplesoap.client import SoapFault
import utils

# importo funciones compartidas:
from utils import json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir, json_serializer
from utils import leer_txt, grabar_txt, leer_dbf, guardar_dbf, N, A, B, I, json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir

from wscpe import WSCPE

# constantes de configuración (producción/homologación):

WSDL = ["https://serviciosjava.afip.gob.ar/cpe-ws/services/wscpe?wsdl",
        "https://fwshomo.afip.gov.ar/wscpe/services/soap?wsdl"]

DEBUG = False
XML = False
CONFIG_FILE = "wscpe.ini"
HOMO = True

ENCABEZADO = [
    ('tipo_reg', 1, A), # 0: encabezado carta de porte

    ('tipo_cpe', 3, N),  # 74: CPE Automotor, 75: CPE Ferroviaria,  99: Flete Corto.
    
    ('sucursal', 5, N),
    ('nro_orden', 8, N),
    ('planta', 6, N),

    # desvio cpe automotor
    ('cuit_solicitante', 11, N),

    # confirmación definitiva
    ('peso_bruto_descarga', 10, N),
    ('peso_tara_descarga', 10, N),

    # resultado:
    ('nro_ctg', 12, N),
    ('fecha_emision', 25, A), # 2021-08-21T23:29:26
    ('fecha_inicio_estado', 25, A),
    ('estado', 15, A),
    ('fecha_vencimiento', 25, A), # 26/02/2013

    ('observaciones', 2000, A),
    ]

ORIGEN = [
    ('tipo_reg', 1, A), # O: Origen
    ('cod_provincia_operador', 2, N),
    ('cod_localidad_operador', 6, N), 
    ('planta', 6, N),
    ('cod_provincia_productor', 2, N),
    ('cod_localidad_productor', 6, N), 
    ]

INTERVINIENTES = [
    ('tipo_reg', 1, A), # I: Intervinientes
    ('cuit_remitente_comercial_venta_primaria', 11, N),
    ('cuit_remitente_comercial_venta_secundaria', 11, N),
    ('cuit_remitente_comercial_venta_secundaria2', 11, N),
    ('cuit_mercado_a_termino', 11, N),
    ('cuit_corredor_venta_primaria', 11, N),
    ('cuit_corredor_venta_secundaria', 11, N),
    ('cuit_representante_entregador', 11, N),
    ('cuit_representante_recibidor', 11, N),
    ]

RETIRO_PRODUCTOR = [
    ('tipo_reg', 1, A), # R: Retiro Productor
    ('corresponde_retiro_productor', 5, B),
    ('es_solicitante_campo', 5, B),
    ('certificado_coe', 12, N),
    ('cuit_remitente_comercial_productor', 11, N),
    ]

DATOS_CARGA = [
    ('tipo_reg', 1, A), # C
    ('cod_grano', 2, N),
    ('cosecha', 4, N),
    ('peso_bruto', 10, N),
    ('peso_tara', 10, N),
    ]

DESTINO = [
    ('tipo_reg', 1, A), # D
    ('cuit_destino', 11, N),
    ('es_destino_campo', 5, B),
    ('cod_provincia', 2, N),
    ('cod_localidad', 6, N),
    ('planta', 6, N),
    ('cuit_destinatario', 11, N),
    ]

TRANSPORTE = [
    ('tipo_reg', 1, A), # D
    ('cuit_transportista', 11, N),
    ('dominio', 10, A),
    ('fecha_hora_partida', 20, A),  # 2016-11-17T12:00:39
    ('km_recorrer', 5, N),
    ('codigo_turno', 30, A),
    ('cuit_chofer', 11, N),
    ('tarifa', 10, I, 2),  # 99999.99
    ('cuit_intermediario_flete', 11, N),
    ('cuit_pagador_flete', 11, N),
    ('mercaderia_fumigada', 5, B),
    ]

CONTINGENCIA = [
    ('tipo_reg', 1, A), # D
    ('concepto', 2, A),
    ('cuit_transportista', 11, N),
    ('nro_operativo', 11, N),
    ('concepto_desactivacion', 2, A),
    ('descripcion', 140, A),
]

EVENTO = [
    ('tipo_reg', 1, A), # E: Evento
    ('codigo', 4, A), 
    ('descripcion', 250, A), 
    ]
    
ERROR = [
    ('tipo_reg', 1, A), # R: Error
    ('codigo', 4, A), 
    ('descripcion', 250, A), 
    ]

FORMATOS = {
    'encabezado': ENCABEZADO,
    'origen': ORIGEN,
    'intervinientes': INTERVINIENTES,
    'retiro_productor': RETIRO_PRODUCTOR,
    'datos_carga': DATOS_CARGA,
    'destino': DESTINO,
    'transporte': TRANSPORTE,
    'contingencia': CONTINGENCIA,
    'errores': ERROR,
    'eventos': EVENTO,
}
TIPO_REGISTROS = {
    "0": 'encabezado',
    "O": 'origen',
    "I": 'intervinientes',
    "R": 'retiro_productor',
    "C": 'datos_carga',
    "D": 'destino',
    "T": 'transporte',
    "N": 'contingencia',
    "E": 'errores',
    "V": 'eventos',
}
TIPO_REGISTROS_REV = dict([(v, k) for (k, v) in TIPO_REGISTROS.items()])

def preparar_registros(dic, header='encabezado'):
    formatos = []
    for key, formato in FORMATOS.items():
        nombre = key
        tipo_reg = TIPO_REGISTROS_REV[key]
        if key != header:
            regs = dic.get(key, [])
        else:
            regs = dic
        if not isinstance(regs, list):
            regs = [regs]
        for reg in regs:
            try:
                reg["tipo_reg"] = tipo_reg
            except Exception as e:
                print(e)

        formatos.append((nombre, formato, regs))
    return formatos


def escribir_archivo(dic, nombre_archivo, agrega=True):
    if '--json' in sys.argv:
        with open(nombre_archivo, agrega and "a" or "w") as archivo:
            json.dump(dic, archivo, sort_keys=True, indent=4)
    elif '--dbf' in sys.argv:
        formatos = preparar_registros(dic)
        guardar_dbf(formatos, agrega, conf_dbf)
    else:
        grabar_txt(FORMATOS, TIPO_REGISTROS, nombre_archivo, [dic], agrega)


def leer_archivo(nombre_archivo):
    if '--json' in sys.argv:
        with open(nombre_archivo, "r") as archivo:
            dic = json.load(archivo)
    elif '--dbf' in sys.argv:
        dic = []
        formatos = preparar_registros(dic)
        leer_dbf(formatos, conf_dbf)
    else:
        dics = leer_txt(FORMATOS, TIPO_REGISTROS, nombre_archivo)
        dic = dics[0]
    if DEBUG:
        import pprint; pprint.pprint(dic)
    return dic


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato in sorted(FORMATOS.items(), key=lambda x: TIPO_REGISTROS_REV[x[0]]):
            tipo_reg = TIPO_REGISTROS_REV[msg]
            comienzo = 1
            print "=== %s ===" % msg
            print "|| Campo %-39s || Posición || Longitud || Tipo %7s || Dec. || Valor ||" % (" ", " ")
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                print "|| %-45s || %8d || %8d || %-12s || %-4s || %-5s ||" % (
                    clave, comienzo, longitud, tipo,
                    ("%s" % dec) if tipo == I else "",
                    ("%s" % tipo_reg) if clave == "tipo_reg" else "",
                )
                comienzo += longitud
        sys.exit(0)

    from ConfigParser import SafeConfigParser

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        for arg in sys.argv[1:]:
            if arg.startswith("--"):
                break
            print "Usando configuración:", arg
            CONFIG_FILE = arg

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSCPE','CUIT')
        ENTRADA = config.get('WSCPE','ENTRADA')
        SALIDA = config.get('WSCPE','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = None
        if config.has_option('WSCPE','URL') and not HOMO:
            wscpe_url = config.get('WSCPE','URL')
        else:
            wscpe_url = WSDL[HOMO]

        if config.has_section('DBF'):
            conf_dbf = dict(config.items('DBF'))
            if DEBUG: print "conf_dbf", conf_dbf
        else:
            conf_dbf = {}

        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "wsaa_url:", wsaa_url
            print "wscpe_url:", wscpe_url

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wscpe", CERT, PRIVATEKEY, wsaa_url, debug=DEBUG)
        ##if not ta:
        ##    sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wscpe = WSCPE()
        wscpe.Conectar(wsdl=wscpe_url)
        ##print(wscpe.client.help("autorizarCPEAutomotor"))
        wscpe.SetTicketAcceso(ta)
        wscpe.Cuit = CUIT
        ok = None
        
        if '--dummy' in sys.argv:
            ret = wscpe.Dummy()
            print "AppServerStatus", wscpe.AppServerStatus
            print "DbServerStatus", wscpe.DbServerStatus
            print "AuthServerStatus", wscpe.AuthServerStatus
            sys.exit(0)

        if '--ult' in sys.argv:
            try:
                sucursal = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError, ValueError:
                sucursal = 1
            try:
                tipo_cpe = int(sys.argv[sys.argv.index("--ult") + 2])
            except IndexError, ValueError:
                tipo_cpe = 74
            rec = {}
            print "Consultando ultimo cpe sucursal=%s tipo_cpe=%s" % (sucursal, tipo_cpe)
            ok = wscpe.ConsultarUltNroOrden(tipo_cpe=tipo_cpe, sucursal=sucursal)
            if wscpe.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wscpe.Excepcion
                if DEBUG: print >> sys.stderr, wscpe.Traceback
            print "Ultimo Nro de CPE", wscpe.NroOrden
            print "Errores:", wscpe.Errores

        if '--consultar' in sys.argv:
            rec = {}
            try:
                nro_orden = sys.argv[sys.argv.index("--consultar") + 1]
                sucursal = sys.argv[sys.argv.index("--consultar") + 2]
                tipo_cpe = sys.argv[sys.argv.index("--consultar") + 3]
                nro_ctg = sys.argv[sys.argv.index("--consultar") + 4]
            except IndexError, ValueError:
                tipo_cpe = raw_input("Tipo de CPE [74]:") or 74
                sucursal = raw_input("Sucursal [1]:") or 1
                nro_orden = raw_input("Nro de orden:") or 1
                nro_ctg = raw_input("Nro de CTG:") or None
            if nro_ctg:
                ok = wscpe.ConsultarCPEAutomotor(cuit_solicitante=wscpe.Cuit, nro_ctg=nro_ctg)
            else:
                ok = wscpe.ConsultarCPEAutomotor(tipo_cpe=tipo_cpe, sucursal=sucursal, nro_orden=nro_orden, cuit_solicitante=wscpe.Cuit)
            if wscpe.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wscpe.Excepcion
                if DEBUG: print >> sys.stderr, wscpe.Traceback
            print "Nro de CTG", wscpe.NroCTG
            print "Errores:", wscpe.Errores
            if DEBUG:
                import pprint
                pprint.pprint(wscpe.cpe)

        ##wscpe.client.help("generarCPE")
        if '--prueba' in sys.argv:
            ok = wscpe.ConsultarUltNroOrden(sucursal=1, tipo_cpe=74)
            nro_orden = wscpe.NroOrden + 1
            dic = dict(
                    tipo_cpe=74,  # 74: CPE Automotor, 75: CPE Ferroviaria,  99: Flete Corto.
                    cuit_solicitante=wscpe.Cuit,
                    sucursal=1,
                    nro_orden=nro_orden,
            )
            dic["origen"] = [dict(
                    #cod_provincia_operador=12,
                    #cod_localidad_operador=6904,
                    #planta=1938,
                    cod_provincia_productor=12,
                    cod_localidad_productor=14310,
            )]
            dic["retiro_productor"] = [dict(
                    corresponde_retiro_productor="false",
                    es_solicitante_campo="true",
                    #certificado_coe=330100025869,
                    #cuit_remitente_comercial_productor=20111111112,
            )]
            dic["intervinientes"] = [dict(
                    cuit_remitente_comercial_venta_primaria=20222222223,
                    cuit_remitente_comercial_venta_secundaria=20222222223,
                    cuit_mercado_a_termino=20222222223,
                    cuit_corredor_venta_primaria=20222222223,
                    cuit_corredor_venta_secundaria=20222222223,
                    cuit_representante_entregador=27000000014,
                    cuit_representante_recibidor=27000000014,
            )]
            dic["datos_carga"] = [dict(
                    cod_grano=23,
                    cosecha=2021,
                    peso_bruto=110,
                    peso_tara=10,
            )]
            dic["destino"] = [dict(
                    cuit_destino=wscpe.Cuit,
                    es_destino_campo="true",
                    cod_provincia=12,
                    cod_localidad=14310,
                    planta=1938,
                    cuit_destinatario=wscpe.Cuit,
            )]
            dic["transporte"] = [dict(
                    cuit_transportista=20120372913,
                    dominio="AA001ST",
                    fecha_hora_partida="2021-08-21T23:29:26",
                    km_recorrer=500,
                    cuit_chofer='20333333334',
                    codigo_turno="00",
                    mercaderia_fumigada="true",
                    cuit_pagador_flete='20333333334',
                    cuit_intermediario_flete='20267565393',
                    tarifa=100,
            ), dict(
                    dominio="AA001ST101",
            )]
            dic["contingencia"] = [dict(
                    concepto="B",
                    cuit_transportista=20333333334,
                    nro_operativo=1111111111,
                    concepto_desactivacion="B",
                    descripcion="Desctrucción carga",
            )]
            escribir_archivo(dic, ENTRADA, False)

        if '--cargar' in sys.argv:
            dic = leer_archivo(ENTRADA)
            if '--autorizar' in sys.argv:
                wscpe.CrearCPE()
            wscpe.AgregarCabecera(**dic)
            if dic.get("origen"):
                wscpe.AgregarOrigen(**dic['origen'][0])
            if dic.get("retiro_productor"):
                wscpe.AgregarRetiroProductor(**dic['retiro_productor'][0])
            if dic.get("intervinientes"):
                wscpe.AgregarIntervinientes(**dic['intervinientes'][0])
            if dic.get("datos_carga"):
                wscpe.AgregarDatosCarga(**dic['datos_carga'][0])
            if dic.get("destino"):
                wscpe.AgregarDestino(**dic['destino'][0])
            if dic.get("transporte"):
                dominios = []
                for transporte in reversed(dic['transporte']):
                    dominios.insert(0, transporte["dominio"])
                transporte["dominio"] = dominios
                wscpe.AgregarTransporte(**transporte)
            if dic.get("contingencia"):
                contingencia = dic['contingencia'][0]
                del contingencia["tipo_reg"]
                if '--informar_contingencia' in sys.argv:
                    for campo in "cuit_transportista", "nro_operativo", "concepto_desactivacion":
                        del contingencia[campo]
                    wscpe.AgregarContingencia(**contingencia)
                elif '--cerrar_contingencia' in sys.argv:
                    wscpe.AgregarCerrarContingencia(**contingencia)
        else:
            dic = {}

        if '--autorizar' in sys.argv:
            if '--testing' in sys.argv:
                wscpe.LoadTestXML("tests/xml/wscpe.xml")  # cargo respuesta

            ok = wscpe.AutorizarCPEAutomotor(archivo="cpe.pdf")

        if '--anular' in sys.argv:
            ok = wscpe.AnularCPE()

        if '--informar_contingencia' in sys.argv:
            ok = wscpe.InformarContingencia()

        if '--cerrar_contingencia' in sys.argv:
            ok = wscpe.CerrarContingenciaCPE()

        if '--rechazo' in sys.argv:
            ok = wscpe.RechazoCPE()

        if '--confirmar_arribo' in sys.argv:
            ok = wscpe.ConfirmarArriboCPE()

        if '--descargado_destino' in sys.argv:
            ok = wscpe.DescargadoDestinoCPE()

        if '--confirmacion_definitiva' in sys.argv:
            if not "--ferroviaria" in sys.argv:
                ok = wscpe.ConfirmacionDefinitivaCPEAutomotor()
            else:
                ok = wscpe.ConfirmacionDefinitivaCPEFerroviaria()

        if '--nuevo_destino_destinatario' in sys.argv:
            if not "--ferroviaria" in sys.argv:
                ok = wscpe.NuevoDestinoDestinatarioCPEAutomotor()
            else:
                ok = wscpe.NuevoDestinoDestinatarioCPEFerroviaria()

        if '--regreso_origen' in sys.argv:
            if not "--ferroviaria" in sys.argv:
                ok = wscpe.RegresoOrigenCPEAutomotor()
            else:
                ok = wscpe.RegresoOrigenCPEFerroviaria()

        if '--desvio' in sys.argv:
            if not "--ferroviaria" in sys.argv:
                ok = wscpe.DesvioCPEAutomotor()
            else:
                ok = wscpe.DesvioCPEFerroviaria()

        if ok is not None:
            print "Resultado: ", wscpe.Resultado
            print "Numero CTG: ", wscpe.NroCTG
            print "Fecha Emision", wscpe.FechaEmision
            print "Fecha Inicio Estado", wscpe.FechaInicioEstado
            print "Fecha Vencimiento", wscpe.FechaVencimiento
            print "Estado: ", wscpe.Estado
            print "Observaciones: ", wscpe.Observaciones
            print "Errores:", wscpe.Errores
            print "Evento:", wscpe.Evento
            dic['nro_ctg'] = wscpe.NroCTG

            dic['resultado'] = wscpe.Resultado
            dic['estado'] = wscpe.Estado
            dic['observaciones'] = wscpe.Observaciones
            dic['fecha_emision'] = wscpe.FechaEmision
            dic['fecha_vencimiento'] = wscpe.FechaVencimiento
            dic['fecha_inicio_estado'] = wscpe.FechaInicioEstado
            dic['errores'] = wscpe.Errores
            dic['evento'] = wscpe.Evento

        if '--grabar' in sys.argv:
            escribir_archivo(dic, SALIDA)

        # Recuperar parámetros:

        if "--provincias" in sys.argv:
            ret = wscpe.ConsultarProvincias()
            print("\n".join(ret))

        if "--localidades_por_provincia" in sys.argv:
            ret = wscpe.ConsultarLocalidadesPorProvincia(sys.argv[2])
            print("\n".join(ret))

        if "--localidades_por_productor" in sys.argv:
            ret = wscpe.ConsultarLocalidadesProductor(wscpe.Cuit)
            print("\n".join(ret))

        if '--tipos_granos' in sys.argv:
            ret = wscpe.ConsultarTiposGrano()
            print("\n".join(ret))

        if "--plantas" in sys.argv:
            ret = wscpe.ConsultarPlantas(cuit=CUIT)
            print("\n".join(ret))

        if wscpe.Errores:
            print "Errores:", wscpe.Errores

        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        ex = utils.exception_info()
        print ex
        if DEBUG:
            raise
        sys.exit(5)

    finally:
        import xml.dom.minidom
        if XML:
            for (xml_data, xml_path) in ((wscpe.XmlRequest, "wscpe_cli_req.xml"), (wscpe.XmlResponse, "wscpe_cli_res.xml")):
                with open(xml_path, "w") as x:
                    if xml_data:
                        dom = xml.dom.minidom.parseString(xml_data)
                        x.write(dom.toprettyxml())
