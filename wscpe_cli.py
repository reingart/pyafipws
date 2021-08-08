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
__version__ = "1.00a"

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

  --generar: generar un cpe
  --emitir: emite un cpe
  --anular: anula un cpe
  --autorizar: autoriza un cpe

  --ult: consulta ultimo nro cpe emitido
  --consultar: consulta un cpe generado

  --tipos_comprobante: tabla de parametros para tipo de comprobante
  --tipos_contingencia: tipo de contingencia que puede reportar
  --tipos_categoria_emisor: tipos de categorías de emisor
  --tipos_categoria_receptor: tipos de categorías de receptor
  --tipos_estados: estados posibles en los que puede estar un cpe granosero
  --grupos_granos' grupos de los distintos tipos de cortes de granos
  --tipos_granos': tipos de corte de granos
  --codigos_domicilio: codigos de depositos habilitados para el cuit

Ver wscpe.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time, base64, datetime
from utils import date
import traceback
from pysimplesoap.client import SoapFault
import utils

# importo funciones compartidas:
from utils import json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir, json_serializer
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir


# constantes de configuración (producción/homologación):

WSDL = ["https://serviciosjava.afip.gob.ar/cpe-ws/services/wscpe?wsdl",
        "https://fwshomo.afip.gov.ar/wscpe/services/soap?wsdl"]

DEBUG = False
XML = False
CONFIG_FILE = "wscpe.ini"
HOMO = True

B = I

ENCABEZADO = [
    ('tipo_reg', 1, A), # 0: encabezado carta de porte

    ('tipo_cpe', 2, N),  # 74: CPE Automotor, 75: CPE Ferroviaria,  99: Flete Corto.
    
    ('sucursal', 5, N),
    ('nro_orden', 18, N),
    ('planta', 5, N),

    ('planta', 5, N),

    # desvio cpe automotor
    ('cuit_solicitante', 11, N),
    ('razon_social_titular_planta', 11, A),

    # confirmación definitiva
    ('peso_bruto_descarga', 10, I , 2),
    ('peso_tara_descarga', 10, I , 2),

    # resultado:
    ('nro_cpe', 12, N),
    ('fecha_emision', 10, A), # 26/02/2013
    ('fecha_inicio_estado', 10, N),
    ('estado', 15, N),
    ('fecha_vencimiento', 10, A), # 26/02/2013
    ]

ORIGEN = [
    ('tipo_reg', 1, A), # O: Origen
    ('cod_provincia_operador', 2, N),
    ('cod_localidad_operador', 6, N), 
    ('planta', 5, N),
    ('cod_provincia_productor', 2, N),
    ('cod_localidad_productor', 6, N), 
    ]

INTERVINIENTES = [
    ('tipo_reg', 1, A), # I: Intervinientes
    ('cuit_intermediario', 11, N),
    ('cuit_remitente_comercial_venta_primaria', 11, N),
    ('cuit_remitente_comercial_venta_secundaria', 11, N),
    ('cuit_mercado_a_termino', 11, N),
    ('cuit_corredor_venta_primaria', 11, N),
    ('cuit_corredor_venta_secundaria', 11, N),
    ('cuit_representante_entregador', 11, N),
    ]

RETIRO_PRODUCTOR = [
    ('tipo_reg', 1, A), # R: Retiro Productor
    ('corresponde_retiro_productor', 1, B),
    ('es_solicitante_campo', 1, B),
    ('certificado_coe', 12, N),
    ('cuit_remitente_comercial_productor', 11, N),
    ]

DATOS_CARGA = [
    ('tipo_reg', 1, A), # C
    ('cod_grano', 2, N),
    ('cosecha', 4, N),
    ('peso_bruto', 10, I , 2),
    ('peso_tara', 10, I , 2),
    ]

DESTINO = [
    ('tipo_reg', 1, A), # D
    ('cuit_destino', 11, N),
    ('es_destino_campo', 4, N),
    ('cod_provincia', 2, I , 2),
    ('cod_localidad', 6, I , 2),
    ('planta', 5, N),
    ('cuit_destinatario', 11, N),
    ]

TRANSPORTE = [
    ('tipo_reg', 1, A), # D
    ('cuit_transportista', 11, N),
    ('dominio', 10, A),
    ('fecha_hora_partida', 20, A),  # 2016-11-17T12:00:39
    ('km_recorrer', 5, I),
    ('codigo_turno', 30, N),
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

FORMATOS = [('Encabezado', ENCABEZADO, 'encabezado', "0"), 
            ('Origen', ORIGEN, 'origen', "O"),
            ('Intervinientes', INTERVINIENTES, 'intervinientes', "I"), 
            ('Retiro Productor', RETIRO_PRODUCTOR, 'retiro_productor', "R"),
            ('Datos Carga', DATOS_CARGA, 'datos_carga', "C"),
            ('Destino', DESTINO, 'destino', "D"),
            ('Transporte', TRANSPORTE, 'transporte', "T"),
            ('Error', ERROR, 'errores', "E"),
            ('Eventos', ERROR, 'eventos', "V"),
            ]


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato, key, tipo_reg in FORMATOS:
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
        print(wscpe.client.help("autorizarCPEAutomotor"))
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
                pto_emision = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError, ValueError:
                pto_emision = 1
            try:
                tipo_cbte = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError, ValueError:
                tipo_comprobante = 995
            rec = {}
            print "Consultando ultimo cpe pto_emision=%s tipo_comprobante=%s" % (pto_emision, tipo_comprobante)
            ok = wscpe.ConsultarUltimoCPEEmitido(tipo_comprobante, pto_emision)
            if wscpe.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wscpe.Excepcion
                if DEBUG: print >> sys.stderr, wscpe.Traceback
            print "Ultimo Nro de CPE", wscpe.NroCPE
            print "Errores:", wscpe.Errores

        if '--consultar' in sys.argv:
            rec = {}
            try:
                cod_cpe = sys.argv[sys.argv.index("--consultar") + 1]
                print "Consultando cpe cod_cpe=%s" % (cod_cpe, )
                ok = wscpe.ConsultarCPE(cod_cpe=cod_cpe)
            except IndexError, ValueError:
                pto_emision = raw_input("Punto de emision [1]:") or 1
                tipo_cbte = raw_input("Tipo de comprobante [995]:") or 995
                nro_comprobante = raw_input("Nro de comprobante:") or 1
                ok = wscpe.ConsultarCPE(tipo_comprobante=tipo_cbte,
                                                 punto_emision=pto_emision,
                                                 nro_comprobante=nro_comprobante)
            if wscpe.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wscpe.Excepcion
                if DEBUG: print >> sys.stderr, wscpe.Traceback
            print "Ultimo Nro de CPE", wscpe.NroCPE
            print "Errores:", wscpe.Errores
            if DEBUG:
                import pprint
                pprint.pprint(wscpe.cpe)

        ##wscpe.client.help("generarCPE")
        if '--prueba' in sys.argv:
            rec = dict(
                    tipo_comprobante=997, punto_emision=1,
                    tipo_titular_mercaderia=1,
                    cuit_titular_mercaderia='20222222223',
                    cuit_autorizado_retirar='20111111112',
                    cuit_productor_contrato=None, 
                    numero_maquila=9999,
                    cod_cpe=1234 if '--informar-contingencia' in sys.argv else None,
                    estado=None,
                    id_req=int(time.time()),
                    es_entrega_mostrador='S',
                )
            if "--autorizar" in sys.argv:
                rec["estado"] = 'A'  # 'A': Autorizar, 'D': Denegar
            rec['receptor'] = dict(
                    cuit_pais_receptor='50000000016',
                    cuit_receptor='20111111112', cod_dom_receptor=1,
                    cuit_despachante=None, codigo_aduana=None, 
                    denominacion_receptor=None, domicilio_receptor=None)
            rec['viaje'] = dict(fecha_inicio_viaje='2020-04-01', distancia_km=999, cod_pais_transportista=200, ducto="S")
            rec['viaje']['vehiculo'] = dict(
                    dominio_vehiculo='AAA000', dominio_acoplado='ZZZ000', 
                    cuit_transportista='20333333334', cuit_conductor='20333333334',  
                    apellido_conductor=None, cedula_conductor=None, denom_transportista=None,
                    id_impositivo=None, nombre_conductor=None)
            rec['mercaderias'] = [dict(orden=1, cod_tipo_prod=1, cod_tipo_emb=1, cantidad_emb=1, cod_tipo_unidad=1, cant_unidad=1,
                                       anio_safra=2019 )]
            rec['datos_autorizacion'] = None # dict(nro_cpe=None, cod_autorizacion=None, fecha_emision=None, fecha_vencimiento=None)
            rec['contingencias'] = [dict(tipo=1, observacion="anulacion")]
            with open(ENTRADA, "w") as archivo:
                json.dump(rec, archivo, sort_keys=True, indent=4)

        if '--cargar' in sys.argv:
            with open(ENTRADA, "r") as archivo:
                rec = json.load(archivo)
            wscpe.CrearCPE(**rec)
            if 'receptor' in rec:
                wscpe.AgregarReceptor(**rec['receptor'])
            if 'viaje' in rec:
                wscpe.AgregarViaje(**rec['viaje'])
                if not rec["viaje"].get("ducto"):
                    wscpe.AgregarVehiculo(**rec['viaje']['vehiculo'])
            for mercaderia in rec.get('mercaderias', []):
                wscpe.AgregarMercaderia(**mercaderia)
            datos_aut = rec.get('datos_autorizacion')
            if datos_aut:
                wscpe.AgregarDatosAutorizacion(**datos_aut)
            for contingencia in rec.get('contingencias', []):
                wscpe.AgregarContingencias(**contingencia)

        if '--generar' in sys.argv:
            if '--testing' in sys.argv:
                wscpe.LoadTestXML("tests/xml/wscpe.xml")  # cargo respuesta

            ok = wscpe.GenerarCPE(id_req=rec['id_req'], archivo="qr.jpg")

        if '--emitir' in sys.argv:
            ok = wscpe.EmitirCPE()

        if '--autorizar' in sys.argv:
            ok = wscpe.AutorizarCPE()

        if '--anular' in sys.argv:
            ok = wscpe.AnularCPE()

        if '--informar-contingencia' in sys.argv:
            ok = wscpe.InformarContingencia()

        if ok is not None:
            print "Resultado: ", wscpe.Resultado
            print "Cod CPE: ", wscpe.CodCPE
            if wscpe.CodAutorizacion:
                print "Numero CPE: ", wscpe.NroCPE
                print "Cod Autorizacion: ", wscpe.CodAutorizacion
                print "Fecha Emision", wscpe.FechaEmision
                print "Fecha Vencimiento", wscpe.FechaVencimiento
            print "Estado: ", wscpe.Estado
            print "Observaciones: ", wscpe.Observaciones
            print "Errores:", wscpe.Errores
            print "Errores Formato:", wscpe.ErroresFormato
            print "Evento:", wscpe.Evento
            rec['cod_cpe'] = wscpe.CodCPE
            rec['resultado'] = wscpe.Resultado
            rec['observaciones'] = wscpe.Observaciones
            rec['fecha_emision'] = wscpe.FechaEmision
            rec['fecha_vencimiento'] = wscpe.FechaVencimiento
            rec['errores'] = wscpe.Errores
            rec['errores_formato'] = wscpe.ErroresFormato
            rec['evento'] = wscpe.Evento

        if '--grabar' in sys.argv:
            with open(SALIDA, "w") as archivo:
                json.dump(rec, archivo, sort_keys=True, indent=4, default=json_serializer)

        # Recuperar parámetros:

        if '--tipos_comprobante' in sys.argv:
            ret = wscpe.ConsultarTiposComprobante()
            print "\n".join(ret)

        if '--tipos_contingencia' in sys.argv:
            ret = wscpe.ConsultarTiposContingencia()
            print "\n".join(ret)

        if '--tipos_mercaderia' in sys.argv:
            ret = wscpe.ConsultarTiposMercaderia()
            print "\n".join(ret)

        if '--tipos_embalaje' in sys.argv:
            ret = wscpe.ConsultarTiposEmbalaje()
            print "\n".join(ret)

        if '--tipos_unidades' in sys.argv:
            ret = wscpe.ConsultarTiposUnidades()
            print "\n".join(ret)

        if '--tipos_categoria_emisor' in sys.argv:
            ret = wscpe.ConsultarTiposCategoriaEmisor()
            print "\n".join(ret)

        if '--tipos_categoria_receptor' in sys.argv:
            ret = wscpe.ConsultarTiposCategoriaReceptor()
            print "\n".join(ret)

        if '--tipos_estados' in sys.argv:
            ret = wscpe.ConsultarTiposEstado()
            print "\n".join(ret)

        if '--paises' in sys.argv:
            ret = wscpe.ConsultarPaises()
            print "\n".join(ret)

        if '--grupos_granos' in sys.argv:
            ret = wscpe.ConsultarGruposAzucar()
            print "\n".join(ret)

        if '--tipos_granos' in sys.argv:
            for grupo_granos in wscpe.ConsultarGruposAzucar(sep=None):
                ret = wscpe.ConsultarTiposAzucar(grupo_granos['codigo'])
                print "\n".join(ret)

        if '--codigos_domicilio' in sys.argv:
            cuit = raw_input("Cuit Titular Domicilio: ")
            ret = wscpe.ConsultarCodigosDomicilio(cuit)
            print "\n".join(utils.norm(ret))

        if wscpe.Errores or wscpe.ErroresFormato:
            print "Errores:", wscpe.Errores, wscpe.ErroresFormato

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
