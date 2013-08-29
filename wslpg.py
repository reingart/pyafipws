#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para obtener código de operación electrónico (COE) para 
Liquidación Primaria Electrónica de Granos del web service WSLPG de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.12e"

LICENCIA = """
wslpg.py: Interfaz para generar Código de Operación Electrónica para
Liquidación Primaria de Granos (LpgService)
Copyright (C) 2013 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo respetando la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA="""
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una liquidación de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)
  --dbf: utilizar tablas DBF (xBase) para los archivos de intercambio
  --json: utilizar formato json para el archivo de intercambio
  --dummy: consulta estado de servidores
  
  --autorizar: Autorizar Liquidación Primaria de Granos (liquidacionAutorizar)
  --ajustar: Ajustar Liquidación Primaria de Granos (liquidacionAjustar)
  --anular: Anular una Liquidación Primaria de Granos (liquidacionAnular)
  --consultar: Consulta una liquidación (parámetros: nro de orden y COE)
  --ult: Consulta el último número de orden registrado en AFIP 
         (liquidacionUltimoNroOrdenConsultar)

  --pdf: genera el formulario C 1116 B en formato PDF
  --mostrar: muestra el documento PDF generado (usar con --pdf)
  --imprimir: imprime el documento PDF generado (usar con --mostrar y --pdf)

  --provincias: obtiene el listado de provincias
  --localidades: obtiene el listado de localidades por provincia
  --tipograno: obtiene el listado de los tipos de granos disponibles
  --campanias: obtiene el listado de las campañas 
  --gradoref: obtiene el listado de los grados de referencias
  --gradoent: obtiene el listado de los grados y valores entregados
  --certdeposito: obtiene el listado de los tipos de certificados de depósito
  --deducciones: obtiene el listado de los tipos de deducciones
  --retenciones: obtiene el listado de los tipos de retenciones
  --puertos: obtiene el listado de los puertos habilitados
  --actividades: obtiene el listado de las actividades habilitados
  --actividadesrep: devuelve las actividades en las que emisor/representado 
                    se encuentra inscripto en RUOCA
  --operaciones: obtiene el listado de las operaciones para el representado


Ver wslpg.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time, shelve
import decimal, datetime
from php import date
import traceback
import pprint
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper
from pyfpdf_hg import Template
import utils

# importo funciones compartidas:
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json


WSDL = "https://fwshomo.afip.gov.ar/wslpg/LpgService?wsdl"
#WSDL = "https://serviciosjava.afip.gob.ar/wslpg/LpgService?wsdl"
#WSDL = "file:wslpg.wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wslpg.ini"
HOMO = True

# definición del formato del archivo de intercambio:

ENCABEZADO = [
    ('tipo_reg', 1, A), # 0: encabezado
    ('nro_orden', 18, N), 
    ('cuit_comprador', 11, N),
    ('nro_act_comprador', 5, N),
    ('nro_ing_bruto_comprador', 15, N), 
    ('cod_tipo_operacion', 2, N), 
    ('es_liquidacion_propia', 1, A),  # S o N
    ('es_canje', 1, A),  # S o N
    ('cod_puerto', 4, N), 
    ('des_puerto_localidad', 240, A), 
    ('cod_grano', 3, N), 
    ('cuit_vendedor', 11, N), 
    ('nro_ing_bruto_vendedor', 15, N), 
    ('actua_corredor', 1, A),  # S o N
    ('liquida_corredor', 1, A),  # S o N
    ('cuit_corredor', 11, N), 
    ('nro_ing_bruto_corredor', 15, N), 
    ('comision_corredor', 5, I, 2), # 3.2
    ('fecha_precio_operacion', 10, A), # 26/02/2013
    ('precio_ref_tn', 8, I, 3), # 4.3
    ('cod_grado_ref', 2, A),
    ('cod_grado_ent', 2, A),
    ('factor_ent', 6, I, 3), # 3.3
    ('precio_flete_tn', 7, I, 2), # 5.2
    ('cont_proteico', 6, I, 3), # 3.3
    ('alic_iva_operacion', 5, I, 2), # 3.2
    ('campania_ppal', 4, N),
    ('cod_localidad_procedencia', 6, N), 
    ('reservado1', 200, A),   # datos_adicionales (compatibilidad hacia atras)
    
    ('coe', 12, N),
    ('coe_ajustado', 12, N),
    ('estado', 2, A),
    
    ('total_deduccion', 17, I, 2), # 17.2
    ('total_retencion', 17, I, 2), # 17.2
    ('total_retencion_afip', 17, I, 2), # 17.2
    ('total_otras_retenciones', 17, I, 2), # 17.2
    ('total_neto_a_pagar', 17, I, 2), # 17.2
    ('total_iva_rg_2300_07', 17, I, 2), # 17.2
    ('total_pago_segun_condicion', 17, I, 2), # 17.2
    
    ('fecha_liquidacion', 10, A), 
    ('nro_op_comercial', 10, N), 
    ('precio_operacion', 17, I, 3), # 17.3
    ('subtotal', 17, I, 2), # 17.2
    ('importe_iva', 17, I, 2), # 17.2
    ('operacion_con_iva', 17, I, 2), # 17.2
    ('total_peso_neto', 8, N), # 17.2

    # Campos WSLPGv1.1:
    ('pto_emision', 4, N), 
    ('cod_prov_procedencia', 2, N),
    ('peso_neto_sin_certificado', 8, N),
    
    ('cod_tipo_ajuste', 2, N),
    ('val_grado_ent', 4, I, 3), # 1.3

    # Campos WSLPGv1.3:
    ('cod_prov_procedencia_sin_certificado', 2, N),
    ('cod_localidad_procedencia_sin_certificado', 6, N), 

    # Campos WSLPGv1.4 (ajustes):
    ('nro_contrato', 15, N),
    ('tipo_formulario', 2, N), 
    ('nro_formulario', 12, N), 
    # datos devuetos:
    ('total_iva_10_5', 17, I, 2), # 17.2
    ('total_iva_21', 17, I, 2), # 17.2
    ('total_retenciones_ganancias', 17, I, 2), # 17.2
    ('total_retenciones_iva', 17, I, 2), # 17.2
    
    ('datos_adicionales', 400, A), # max 400 desde WSLPGv1.2

    ]

CERTIFICADO = [
    ('tipo_reg', 1, A), # 1: Certificado
    ('tipo_certificado_deposito', 2, N), 
    ('nro_certificado_deposito', 12, N), 
    ('peso_neto', 8, N), 
    ('cod_localidad_procedencia', 6, N), 
    ('cod_prov_procedencia', 2, N),
    ('reservado', 2, N),
    ('campania', 4, N),
    ('fecha_cierre', 10, A),
    ('peso_neto_total_certificado', 8, N), # para ajuste unificado (WSLPGv1.4)
    ]
    
RETENCION = [
    ('tipo_reg', 1, A), # 2: Retencion
    ('codigo_concepto', 2, A), 
    ('detalle_aclaratorio', 30, A),
    ('base_calculo', 10, I, 2),  # 8.2
    ('alicuota', 6, I, 2),  # 3.2
    ('nro_certificado_retencion', 14, N), 
    ('fecha_certificado_retencion', 10, A),
    ('importe_certificado_retencion', 17, I, 2), # 17.2
    ('importe_retencion', 17, I, 2), # 17.2
    ]

DEDUCCION = [
    ('tipo_reg', 1, A), # 3: Deducción
    ('codigo_concepto', 2, A), 
    ('detalle_aclaratorio', 30, A), # max 50 por WSLPGv1.2
    ('dias_almacenaje', 4, N),
    ('reservado1', 6, I, 3),
    ('comision_gastos_adm', 5, I, 2), # 3.2
    ('base_calculo', 10, I, 2),  # 8.2
    ('alicuota', 6, I, 2),  # 3.2
    ('importe_iva', 17, I, 2), # 17.2
    ('importe_deduccion', 17, I, 2), # 17.2
    ('precio_pkg_diario', 11, I, 8), # 3.8, ajustado WSLPGv1.2
    ]

AJUSTE = [
    ('tipo_reg', 1, A), # 4: ajuste débito / 5: crédito (WSLPGv1.4)
    ('concepto_importe_iva_0', 20, A),
    ('importe_ajustar_iva_0', 15, I, 2), # 11.2
    ('concepto_importe_iva_105', 20, A),
    ('importe_ajustar_iva_105', 15, I, 2), # 11.2
    ('concepto_importe_iva_21', 20, A),
    ('importe_ajustar_iva_21', 15, I, 2), # 11.2
    ('diferencia_peso_neto', 8, N),
    ('diferencia_precio_operacion', 17, I, 3), # 17.3
    ('cod_grado', 2, A),
    ('val_grado', 4, I, 3), # 1.3
    ('factor', 6, I, 3), # 3.3
    ('diferencia_precio_flete_tn', 7, I, 2), # 5.2
    ('datos_adicionales', 400, A),
    # datos devueltos:
    ('fecha_liquidacion', 10, A), 
    ('nro_op_comercial', 10, N), 
    ('precio_operacion', 17, I, 3), # 17.3
    ('subtotal', 17, I, 2), # 17.2
    ('importe_iva', 17, I, 2), # 17.2
    ('operacion_con_iva', 17, I, 2), # 17.2
    ('total_peso_neto', 8, N), # 17.2
    ('total_deduccion', 17, I, 2), # 17.2
    ('total_retencion', 17, I, 2), # 17.2
    ('total_retencion_afip', 17, I, 2), # 17.2
    ('total_otras_retenciones', 17, I, 2), # 17.2
    ('total_neto_a_pagar', 17, I, 2), # 17.2
    ('total_iva_rg_2300_07', 17, I, 2), # 17.2
    ('total_pago_segun_condicion', 17, I, 2), # 17.2
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

DATO = [
    ('tipo_reg', 1, A), # 9: Dato adicional
    ('campo', 25, A), 
    ('valor', 250, A), 
    ]


def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.COE = self.COEAjustado = NroContrato = ""
            self.Excepcion = self.Traceback = ""
            self.ErrMsg = self.ErrCode = ""
            self.Errores = []
            self.Estado = self.Resultado = self.NroOrden = self.NroContrato = ''
            self.TotalDeduccion = ""
            self.TotalRetencion = ""
            self.TotalRetencionAfip = ""
            self.TotalOtrasRetenciones = ""
            self.TotalNetoAPagar = ""
            self.TotalIvaRg2300_07 = ""
            self.TotalPagoSegunCondicion = ""
            self.Subtotal = self.TotalIva105 = self.TotalIva21 = ""
            self.TotalRetencionesGanancias = self.TotalRetencionesIVA = ""
            # actualizo los parámetros
            kwargs.update(self.params_in)
            # limpio los parámetros
            self.params_in = {}
            self.params_out = {}
            # llamo a la función
            func(self, *args, **kwargs)
            return True
        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            if self.LanzarExcepciones:
                raise
            else:
                return False
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            if self.LanzarExcepciones:
                raise
            else:
                return False
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class WSLPG:
    "Interfaz para el WebService de Liquidación Primaria de Granos"    
    _public_methods_ = ['Conectar', 'Dummy', 'LoadTestXML',
                        'AutorizarLiquidacion', 
                        'AnularLiquidacion',
                        'CrearLiquidacion',  
                        'AgregarCertificado', 'AgregarRetencion', 
                        'AgregarDeduccion',
                        'ConsultarLiquidacion', 'ConsultarUltNroOrden',
                        'CrearAjusteBase', 
                        'CrearAjusteDebito', 'CrearAjusteCredito',
                        'AjustarLiquidacionUnificado',
                        'AjustarLiquidacionUnificadoPapel',
                        'AjustarLiquidacionContrato',
                        'AnalizarAjusteDebito', 'AnalizarAjusteCredito',
                        'ConsultarCampanias',
                        'ConsultarTipoGrano',
                        'ConsultarGradoEntregadoXTipoGrano',
                        'ConsultarCodigoGradoReferencia',
                        'ConsultarTipoCertificadoDeposito',
                        'ConsultarTipoDeduccion',
                        'ConsultarTipoRetencion',
                        'ConsultarPuerto',
                        'ConsultarTipoActividad', 
                        'ConsultarTipoActividadRepresentado',
                        'ConsultarProvincias',
                        'ConsultarLocalidadesPorProvincia',
                        'ConsultarTiposOperacion',
                        'BuscarLocalidades',
                        'AnalizarXml', 'ObtenerTagXml',
                        'SetParametro', 'GetParametro',
                        'CargarFormatoPDF', 'AgregarCampoPDF', 'AgregarDatoPDF',
                        'CrearPlantillaPDF', 'ProcesarPlantillaPDF', 
                        'GenerarPDF', 'MostrarPDF',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'InstallDir',
        'COE', 'COEAjustado', 'Estado', 'Resultado', 'NroOrden',
        'TotalDeduccion', 'TotalRetencion', 'TotalRetencionAfip', 
        'TotalOtrasRetenciones', 'TotalNetoAPagar', 'TotalPagoSegunCondicion',
        'TotalIvaRg2300_07', 'Subtotal', 'TotalIva105', 'TotalIva21',
        'TotalRetencionesGanancias', 'TotalRetencionesIVA', 'NroContrato',
        ]
    _reg_progid_ = "WSLPG"
    _reg_clsid_ = "{9D21C513-21A6-413C-8592-047357692608}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.LanzarExcepciones = False
        self.InstallDir = INSTALL_DIR
        self.ErrCode = self.ErrMsg = ''
        self.Errores = self.errores = []
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.COE = ''
        self.Estado = self.Resultado = self.NroOrden = ''
        self.params_in = {}
        self.params_out = {}
        self.datos = {}

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, url="", proxy="", wrapper="", cacert=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = WSDL
        if wrapper:
            Http = set_http_wrapper(wrapper)
            self.Version = self.Version + " " + Http._wrapper_version
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        proxy_dict = parse_proxy(proxy)
        self.client = SoapClient(url,
            wsdl=url, cache=cache,
            trace='--trace' in sys.argv, 
            ns='wslpg', #soap_ns='soapenv',
            cacert = cacert, #server="",
            exceptions=True, proxy=proxy_dict)
       
        # corrijo ubicación del servidor (puerto htttp 80 en el WSDL)
        location = self.client.services['LpgService']['ports']['LpgEndPoint']['location']
        if location.startswith("http://"):
            print "Corrigiendo WSDL ...", location,
            location = location.replace("http://", "https://").replace(":80", ":443")
            self.client.services['LpgService']['ports']['LpgEndPoint']['location'] = location
            print location
        
        try:
            # intento abrir el diccionario persistente de localidades
            import wslpg_datos
            localidades_db = os.path.join(cache, "localidades.dat")
            # verificar que puede escribir en el dir, sino abrir solo lectura
            flag = os.access(cache, os.W_OK) and 'c' or 'r'
            wslpg_datos.LOCALIDADES = shelve.open(localidades_db, flag=flag)
            if DEBUG: print "Localidades en BD:", len(wslpg_datos.LOCALIDADES)
            self.Traceback = "Localidades en BD: %s" % len(wslpg_datos.LOCALIDADES)
        except Exception, e:
            print "ADVERTENCIA: No se pudo abrir la bbdd de localidades:", e
            self.Excepcion = str(e)
            
        return True

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = []
        if 'errores' in ret:
            errores.extend(ret['errores'])
        if 'erroresFormato' in ret:
            errores.extend(ret['erroresFormato'])
        if errores:
            self.Errores = ["%(codigo)s: %(descripcion)s" % err['error'] 
                            for err in errores]
            self.errores = [
                {'codigo': err['error']['codigo'],
                 'descripcion': err['error']['descripcion'].replace("\n", "")
                                .replace("\r", "")} 
                             for err in errores]
            self.ErrCode = ' '.join(self.Errores)
            self.ErrMsg = '\n'.join(self.Errores)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['return']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    @inicializar_y_capturar_excepciones
    def CrearLiquidacion(self, nro_orden=None, cuit_comprador=None, 
               nro_act_comprador=None, nro_ing_bruto_comprador=None,
               cod_tipo_operacion=None,
               es_liquidacion_propia=None, es_canje=None,
               cod_puerto=None, des_puerto_localidad=None, cod_grano=None,
               cuit_vendedor=None, nro_ing_bruto_vendedor=None,
               actua_corredor=None, liquida_corredor=None, cuit_corredor=None,
               comision_corredor=None, nro_ing_bruto_corredor=None,
               fecha_precio_operacion=None,
               precio_ref_tn=None, cod_grado_ref=None, cod_grado_ent=None,
               factor_ent=None, precio_flete_tn=None, cont_proteico=None,
               alic_iva_operacion=None, campania_ppal=None,
               cod_localidad_procedencia=None,
               datos_adicionales=None, pto_emision=1, cod_prov_procedencia=None, 
               peso_neto_sin_certificado=None, val_grado_ent=None,
               cod_localidad_procedencia_sin_certificado=None,
               cod_prov_procedencia_sin_certificado=None,
               nro_contrato=None,
               **kwargs
               ):
        "Inicializa internamente los datos de una liquidación para autorizar"

        # limpio los campos especiales (segun validaciones de AFIP)
        if alic_iva_operacion == 0:
            alic_iva_operacion = None   # no informar alicuota p/ monotributo
        if val_grado_ent == 0:
            val_grado_ent = None
        # borrando datos corredor si no corresponden
        if actua_corredor == "N":
            cuit_corredor = None
            comision_corredor = None
            nro_ing_bruto_corredor = None
        elif es_liquidacion_propia == "N" and liquida_corredor == "N":
            nro_ing_bruto_corredor = None           # validación 1623
        
        # si no corresponde elimino el peso neto certificado campo opcional
        if not peso_neto_sin_certificado or not int(peso_neto_sin_certificado):
            peso_neto_sin_certificado = None
        
        if cod_puerto and int(cod_puerto) != 14:
            des_puerto_localidad = None             # validacion 1630

        # limpio los campos opcionales para no enviarlos si no corresponde:
        if cod_grado_ref == "":
            cod_grado_ref = None
        if cod_grado_ent == "":
            cod_grado_ent = None
        if val_grado_ent == 0:
            val_grado_ent = None

        # creo el diccionario con los campos generales de la liquidación:
        self.liquidacion = dict(
                            ptoEmision=pto_emision,
                            nroOrden=nro_orden,
                            cuitComprador=cuit_comprador,
                            nroActComprador=nro_act_comprador,
                            nroIngBrutoComprador=nro_ing_bruto_comprador,
                            codTipoOperacion=cod_tipo_operacion,
                            esLiquidacionPropia=es_liquidacion_propia,
                            esCanje=es_canje,
                            codPuerto=cod_puerto,
                            desPuertoLocalidad=des_puerto_localidad,
                            codGrano=cod_grano,
                            cuitVendedor=cuit_vendedor,
                            nroIngBrutoVendedor=nro_ing_bruto_vendedor,
                            actuaCorredor=actua_corredor,
                            liquidaCorredor=liquida_corredor,
                            cuitCorredor=cuit_corredor,
                            comisionCorredor=comision_corredor,
                            nroIngBrutoCorredor=nro_ing_bruto_corredor,
                            fechaPrecioOperacion=fecha_precio_operacion,
                            precioRefTn=precio_ref_tn,
                            codGradoRef=cod_grado_ref,
                            codGradoEnt=cod_grado_ent,
                            valGradoEnt=val_grado_ent,
                            factorEnt=factor_ent,
                            precioFleteTn=precio_flete_tn,
                            contProteico=cont_proteico,
                            alicIvaOperacion=alic_iva_operacion,
                            campaniaPPal=campania_ppal,
                            codLocalidadProcedencia=cod_localidad_procedencia,
                            codProvProcedencia=cod_prov_procedencia,
                            datosAdicionales=datos_adicionales,
                            pesoNetoSinCertificado=peso_neto_sin_certificado,
                            numeroContrato=nro_contrato,
                            certificados=[],
            )
        # para compatibilidad hacia atras, "copiar" los campos si no hay cert:
        if peso_neto_sin_certificado:
            if cod_localidad_procedencia_sin_certificado is None:
                cod_localidad_procedencia_sin_certificado = cod_localidad_procedencia
            if cod_prov_procedencia_sin_certificado is None:
                cod_prov_procedencia_sin_certificado = cod_prov_procedencia
            self.liquidacion.update(dict(
                codLocalidadProcedenciaSinCertificado=cod_localidad_procedencia_sin_certificado,
                codProvProcedenciaSinCertificado=cod_prov_procedencia_sin_certificado,
                ))

        # inicializo las listas que contentran las retenciones y deducciones:
        self.retenciones = []
        self.deducciones = []

    @inicializar_y_capturar_excepciones
    def AgregarCertificado(self, tipo_certificado_deposito=None,
                           nro_certificado_deposito=None,
                           peso_neto=None,
                           cod_localidad_procedencia=None,
                           cod_prov_procedencia=None,
                           campania=None, fecha_cierre=None, 
                           peso_neto_total_certificado=None, **kwargs):
        "Agrego el certificado a la liquidación"
        
        self.liquidacion['certificados'].append(
                    dict(certificado=dict(
                        tipoCertificadoDeposito=tipo_certificado_deposito,
                        nroCertificadoDeposito=nro_certificado_deposito,
                        pesoNeto=peso_neto,
                        codLocalidadProcedencia=cod_localidad_procedencia,
                        codProvProcedencia=cod_prov_procedencia,
                        campania=campania,
                        fechaCierre=fecha_cierre,
                        pesoNetoTotalCertificado=peso_neto_total_certificado,
                      )))

    @inicializar_y_capturar_excepciones
    def AgregarRetencion(self, codigo_concepto, detalle_aclaratorio, 
                               base_calculo, alicuota, 
                               nro_certificado_retencion=None, 
                               fecha_certificado_retencion=None,
                               importe_certificado_retencion=None,
                               **kwargs):
        "Agrega la información referente a las retenciones de la liquidación"
        # limpio los campos opcionales:
        if fecha_certificado_retencion is not None and not fecha_certificado_retencion.strip():
            fecha_certificado_retencion = None
        if importe_certificado_retencion is not None and not float(importe_certificado_retencion):
            importe_certificado_retencion = None
        if nro_certificado_retencion is not None and not int(nro_certificado_retencion):
            nro_certificado_retencion = None
        self.retenciones.append(dict(
                                    retencion=dict(
                                        codigoConcepto=codigo_concepto,
                                        detalleAclaratorio=detalle_aclaratorio,
                                        baseCalculo=base_calculo,
                                        alicuota=alicuota,
                                        nroCertificadoRetencion=nro_certificado_retencion,
                                        fechaCertificadoRetencion=fecha_certificado_retencion,
                                        importeCertificadoRetencion=importe_certificado_retencion,
                                    ))
                            )

    @inicializar_y_capturar_excepciones
    def AgregarDeduccion(self, codigo_concepto=None, detalle_aclaratorio=None,
                               dias_almacenaje=None, precio_pkg_diario=None,
                               comision_gastos_adm=None, base_calculo=None,
                               alicuota=None, **kwargs):
        "Agrega la información referente a las deducciones de la liquidación."
        # limpiar campo según validación (comision_gastos_adm puede ser 0.00!)
        if codigo_concepto != "CO" and comision_gastos_adm is not None \
            and float(comision_gastos_adm) == 0:
            comision_gastos_adm = None
        # no enviar campos para prevenir errores AFIP 1705, 1707, 1708
        if base_calculo is not None:
            if codigo_concepto == "AL":
                base_calculo = None
            if codigo_concepto == "CO" and float(base_calculo) == 0:
                base_calculo = None         # no enviar, por retrocompatibilidad
        if codigo_concepto != "AL":
            dias_almacenaje = None
            precio_pkg_diario = None
        self.deducciones.append(dict(
                                    deduccion=dict(
                                        codigoConcepto=codigo_concepto,
                                        detalleAclaratorio=detalle_aclaratorio,
                                        diasAlmacenaje=dias_almacenaje,
                                        precioPKGdiario=precio_pkg_diario,
                                        comisionGastosAdm=comision_gastos_adm,
                                        baseCalculo=base_calculo,
                                        alicuotaIva=alicuota
                                    ))
                            )

    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self):
        "Autorizar Liquidación Primaria Electrónica de Granos"
        
        # limpio los elementos que no correspondan por estar vacios:
        if not self.liquidacion['certificados']:
            del self.liquidacion['certificados']
        if not self.retenciones:
            self.retenciones = None
        if not self.deducciones:
            self.deducciones = None
        
        # llamo al webservice:
        ret = self.client.liquidacionAutorizar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        liquidacion=self.liquidacion,
                        retenciones=self.retenciones,
                        deducciones=self.deducciones,
                        )

        # analizo la respusta
        ret = ret['liqReturn']
        self.__analizar_errores(ret)
        self.AnalizarLiquidacion(ret.get('autorizacion'), self.liquidacion)

    def AnalizarLiquidacion(self, aut, liq=None):
        "Método interno para analizar la respuesta de AFIP"
        # proceso los datos básicos de la liquidación (devuelto por consultar):
        if liq:
            self.params_out = dict(
                        pto_emision=liq.get('ptoEmision'),
                        nro_orden=liq.get('nroOrden'),
                        cuit_comprador=liq.get('cuitComprador'),
                        nro_act_comprador=liq.get('nroActComprador'),
                        nro_ing_bruto_comprador=liq.get('nroIngBrutoComprador'),
                        cod_tipo_operacion=liq.get('codTipoOperacion'),
                        es_liquidacion_propia=liq.get('esLiquidacionPropia'),
                        es_canje=liq.get('esCanje'),
                        cod_puerto=liq.get('codPuerto'),
                        des_puerto_localidad=liq.get('desPuertoLocalidad'),
                        cod_grano=liq.get('codGrano'),
                        cuit_vendedor=liq.get('cuitVendedor'),
                        nro_ing_bruto_vendedor=liq.get('nroIngBrutoVendedor'),
                        actua_corredor=liq.get('actuaCorredor'),
                        liquida_corredor=liq.get('liquidaCorredor'),
                        cuit_corredor=liq.get('cuitCorredor'),
                        comision_corredor=liq.get('comisionCorredor'),
                        nro_ing_bruto_corredor=liq.get('nroIngBrutoCorredor'),
                        fecha_precio_operacion=liq.get('fechaPrecioOperacion'),
                        precio_ref_tn=liq.get('precioRefTn'),
                        cod_grado_ref=liq.get('codGradoRef'),
                        cod_grado_ent=liq.get('codGradoEnt'),
                        factor_ent=liq.get('factorEnt'),
                        precio_flete_tn=liq.get('precioFleteTn'),
                        cont_proteico=liq.get('contProteico'),
                        alic_iva_operacion=liq.get('alicIvaOperacion'),
                        campania_ppal=liq.get('campaniaPPal'),
                        cod_localidad_procedencia=liq.get('codLocalidadProcedencia'),
                        cod_prov_procedencia=liq.get('codProvProcedencia'),
                        datos_adicionales=liq.get('datosAdicionales'),
                        peso_neto_sin_certificado=liq.get('pesoNetoSinCertificado'),
                        cod_localidad_procedencia_sin_certificado=liq.get('codLocalidadProcedenciaSinCertificado'),
                        cod_prov_procedencia_sin_certificado=liq.get('codProvProcedenciaSinCertificado'),
                        certificados=[],
                    )
            if 'certificados' in liq:
                for c in liq['certificados']:
                    cert = c['certificado']
                    self.params_out['certificados'].append(dict(
                        tipo_certificado_deposito=cert['tipoCertificadoDeposito'],
                        nro_certificado_deposito=cert['nroCertificadoDeposito'],
                        peso_neto=cert['pesoNeto'],
                        cod_localidad_procedencia=cert['codLocalidadProcedencia'],
                        cod_prov_procedencia=cert['codProvProcedencia'],
                        campania=cert['campania'],
                        fecha_cierre=cert['fechaCierre'],
                    ))

        self.params_out['errores'] = self.errores
            
        # proceso la respuesta de autorizar, ajustar (y consultar):
        if aut:
            self.TotalDeduccion = aut['totalDeduccion']
            self.TotalRetencion = aut['totalRetencion']
            self.TotalRetencionAfip = aut['totalRetencionAfip']
            self.TotalOtrasRetenciones = aut['totalOtrasRetenciones']
            self.TotalNetoAPagar = aut['totalNetoAPagar']
            self.TotalIvaRg2300_07 = aut['totalIvaRg2300_07']
            self.TotalPagoSegunCondicion = aut['totalPagoSegunCondicion']
            self.COE = str(aut.get('coe', ''))
            self.COEAjustado = aut.get('coeAjustado')
            self.Estado = aut.get('estado', '')
            self.NroContrato = aut.get('numeroContrato', '')

            # actualizo parámetros de salida:
            self.params_out['coe'] = self.COE
            self.params_out['coe_ajustado'] = self.COE
            self.params_out['estado'] = self.Estado
            self.params_out['total_deduccion'] = self.TotalDeduccion
            self.params_out['total_retencion'] = self.TotalRetencion
            self.params_out['total_retencion_afip'] = self.TotalRetencionAfip
            self.params_out['total_otras_retenciones'] = self.TotalOtrasRetenciones
            self.params_out['total_neto_a_pagar'] = self.TotalNetoAPagar
            self.params_out['total_iva_rg_2300_07'] = self.TotalIvaRg2300_07
            self.params_out['total_pago_segun_condicion'] = self.TotalPagoSegunCondicion

            # datos adicionales:
            self.params_out['nro_orden'] = aut.get('nroOrden')
            self.params_out['cod_tipo_ajuste'] = aut.get('codTipoAjuste')
            fecha = aut.get('fechaLiquidacion')
            if fecha:
                fecha = str(fecha)
            self.params_out['fecha_liquidacion'] = fecha
            self.params_out['importe_iva'] = aut.get('importeIva')
            self.params_out['nro_op_comercial'] = aut.get('nroOpComercial')
            self.params_out['operacion_con_iva'] = aut.get('operacionConIva')
            self.params_out['precio_operacion'] = aut.get('precioOperacion')
            self.params_out['total_peso_neto'] = aut.get('totalPesoNeto')
            self.params_out['subtotal'] = aut.get('subTotal')
            self.params_out['retenciones'] = []
            self.params_out['deducciones'] = []
            for retret in aut.get("retenciones", []):
                retret = retret['retencionReturn']
                self.params_out['retenciones'].append({
                    'importe_retencion': retret['importeRetencion'],
                    'alicuota': retret['retencion'].get('alicuota'),
                    'base_calculo': retret['retencion'].get('baseCalculo'),
                    'codigo_concepto': retret['retencion'].get('codigoConcepto'),
                    'detalle_aclaratorio': retret['retencion'].get('detalleAclaratorio', "").replace("\n", ""),
                    'importe_certificado_retencion': retret['retencion'].get('importeCertificadoRetencion'),
                    'nro_certificado_retencion': retret['retencion'].get('nroCertificadoRetencion'),
                    'fecha_certificado_retencion': retret['retencion'].get('fechaCertificadoRetencion'),
                    })
            for dedret in aut.get("deducciones", []):
                dedret = dedret['deduccionReturn']
                self.params_out['deducciones'].append({
                    'importe_deduccion': dedret['importeDeduccion'],
                    'importe_iva': dedret.get('importeIva'),
                     'alicuota': dedret['deduccion'].get('alicuotaIva'),
                     'base_calculo': dedret['deduccion'].get('baseCalculo'),
                     'codigo_concepto': dedret['deduccion'].get('codigoConcepto'),
                     'detalle_aclaratorio': dedret['deduccion'].get('detalleAclaratorio', "").replace("\n", ""),
                     'dias_almacenaje': dedret['deduccion'].get('diasAlmacenaje'),
                     'precio_pkg_diario': dedret['deduccion'].get('precioPKGdiario'),
                     'comision_gastos_adm': dedret['deduccion'].get('comisionGastosAdm'),
                    })
        

    @inicializar_y_capturar_excepciones
    def CrearAjusteBase(self, 
               pto_emision=1, nro_orden=None,       # unificado, contrato, papel
               coe_ajustado=None,                   # unificado
               nro_contrato=None,                   # contrato
               tipo_formulario=None,                # papel
               nro_formulario=None,                 # papel
               actividad=None,                      # contrato / papel
               cod_grano=None,                      # contrato / papel
               cuit_vendedor=None,                  # contrato / papel
               cuit_comprador=None,                 # contrato / papel
               cuit_corredor=None,                  # contrato / papel
               nro_ing_bruto_vendedor=None,         # papel
               nro_ing_bruto_comprador=None,        # papel
               nro_ing_bruto_corredor=None,         # papel
               tipo_operacion=None,                 # papel
               precio_ref_tn=None,                  # contrato
               cod_grado_ent=None,                  # contrato
               val_grado_ent=None,                  # contrato
               precio_flete_tn=None,                # contrato
               cod_puerto=None,                     # contrato
               des_puerto_localidad=None,           # contrato
               cod_provincia=None,                  # papel
               cod_localidad=None,                  # papel
               comision_corredor=None,              # papel
               **kwargs
               ):
        "Inicializa internamente los datos de una liquidación para ajustar"

        # ajusto nombre de campos para compatibilidad hacia atrás (encabezado):
        if 'cod_localidad_procedencia' in kwargs:
            cod_localidad = kwargs['cod_localidad_procedencia']
        if 'cod_provincia_procedencia' in kwargs:
            cod_provincia = kwargs['cod_provincia_procedencia']
        if 'nro_act_comprador' in kwargs:
            actividad = kwargs['nro_act_comprador']
        if 'cod_tipo_operacion' in kwargs:
            tipo_operacion = kwargs['cod_tipo_operacion']
            
        # limpio los campos especiales (segun validaciones de AFIP)
        if val_grado_ent == 0:
            val_grado_ent = None
        # borrando datos si no corresponden
        if cuit_corredor and int(cuit_corredor) == 0:
            cuit_corredor = None
            comision_corredor = None
            nro_ing_bruto_corredor = None
               
        if cod_puerto and int(cod_puerto) != 14:
            des_puerto_localidad = None             # validacion 1630

        # limpio los campos opcionales para no enviarlos si no corresponde:
        if cod_grado_ent == "":
            cod_grado_ent = None
        if val_grado_ent == 0:
            val_grado_ent = None

        # creo el diccionario con los campos generales del ajuste base:
        self.ajuste = { 'ajusteBase': {
                            'ptoEmision': pto_emision,
                            'nroOrden': nro_orden,
                            'coeAjustado': coe_ajustado,
                            'nroContrato': nro_contrato,
                            'tipoFormulario': tipo_formulario,
                            'nroFormulario': nro_formulario,
                            'actividad': actividad,
                            'codGrano': cod_grano,
                            'cuitVendedor': cuit_vendedor,
                            'cuitComprador': cuit_comprador,
                            'cuitCorredor': cuit_corredor,
                            'nroIngBrutoVendedor': nro_ing_bruto_vendedor,
                            'nroIngBrutoComprador': nro_ing_bruto_comprador,
                            'nroIngBrutoCorredor': nro_ing_bruto_corredor,
                            'tipoOperacion': tipo_operacion,
                            'codPuerto': cod_puerto,
                            'desPuertoLocalidad': des_puerto_localidad,
                            'comisionCorredor': comision_corredor,
                            'precioRefTn': precio_ref_tn,
                            'codGradoEnt': cod_grado_ent,
                            'valGradoEnt': val_grado_ent,
                            'precioFleteTn': precio_flete_tn,
                            'codLocalidad': cod_localidad,
                            'codProvincia': cod_provincia,
                            'certificados': [],
                            }
                        }
        # para compatibilidad con AgregarCertificado
        self.liquidacion = self.ajuste['ajusteBase']

    @inicializar_y_capturar_excepciones
    def CrearAjusteCredito(self, 
               datos_adicionales=None,              # unificado, contrato, papel
               concepto_importe_iva_0=None,         # unificado, contrato, papel
               importe_ajustar_iva_0=None,          # unificado, contrato, papel
               concepto_importe_iva_105=None,       # unificado, contrato, papel
               importe_ajustar_iva_105=None,        # unificado, contrato, papel
               concepto_importe_iva_21=None,        # unificado, contrato, papel
               importe_ajustar_iva_21=None,         # unificado, contrato, papel
               diferencia_peso_neto=None,           # unificado
               diferencia_precio_operacion=None,    # unificado
               cod_grado=None,                      # unificado
               val_grado=None,                      # unificado  
               factor=None,                         # unificado
               diferencia_precio_flete_tn=None,     # unificado
               **kwargs
               ):
        "Inicializa internamente los datos del crédito del ajuste"

        self.ajuste['ajusteCredito'] = {
            'diferenciaPesoNeto': diferencia_peso_neto,
            'diferenciaPrecioOperacion': diferencia_precio_operacion,
            'codGrado': cod_grado,
            'valGrado': val_grado,
            'factor': factor,
            'diferenciaPrecioFleteTn': diferencia_precio_flete_tn,
            'datosAdicionales': datos_adicionales,
            'opcionales': None,
            'conceptoImporteIva0': concepto_importe_iva_0,
            'importeAjustarIva0': importe_ajustar_iva_0,
            'conceptoImporteIva105': concepto_importe_iva_105,
            'importeAjustarIva105': importe_ajustar_iva_105,
            'conceptoImporteIva21': concepto_importe_iva_21,
            'deducciones': [],
            'retenciones': [],
            }
        # vinculación con AgregarOpcional:
        self.opcionales = self.ajuste['ajusteCredito']['opcionales']
        # vinculación con AgregarRetencion y AgregarDeduccion
        self.deducciones = self.ajuste['ajusteCredito']['deducciones']
        self.retenciones = self.ajuste['ajusteCredito']['retenciones']

    @inicializar_y_capturar_excepciones
    def CrearAjusteDebito(self, 
               datos_adicionales=None,              # unificado, contrato, papel
               concepto_importe_iva_0=None,         # unificado, contrato, papel
               importe_ajustar_iva_0=None,          # unificado, contrato, papel
               concepto_importe_iva_105=None,       # unificado, contrato, papel
               importe_ajustar_iva_105=None,        # unificado, contrato, papel
               concepto_importe_iva_21=None,        # unificado, contrato, papel
               importe_ajustar_iva_21=None,         # unificado, contrato, papel
               diferencia_peso_neto=None,           # unificado
               diferencia_precio_operacion=None,    # unificado
               cod_grado=None,                      # unificado
               val_grado=None,                      # unificado  
               factor=None,                         # unificado
               diferencia_precio_flete_tn=None,     # unificado
               **kwargs
               ):
        "Inicializa internamente los datos del crédito del ajuste"

        self.ajuste['ajusteDebito'] = {
            'diferenciaPesoNeto': diferencia_peso_neto,
            'diferenciaPrecioOperacion': diferencia_precio_operacion,
            'codGrado': cod_grado,
            'valGrado': val_grado,
            'factor': factor,
            'diferenciaPrecioFleteTn': diferencia_precio_flete_tn,
            'datosAdicionales': datos_adicionales,
            'opcionales': None,
            'conceptoImporteIva0': concepto_importe_iva_0,
            'importeAjustarIva0': importe_ajustar_iva_0,
            'conceptoImporteIva105': concepto_importe_iva_105,
            'importeAjustarIva105': importe_ajustar_iva_105,
            'conceptoImporteIva21': concepto_importe_iva_21,
            'deducciones': [],
            'retenciones': [],
            }
        # vinculación con AgregarOpcional:
        self.opcionales = self.ajuste['ajusteDebito']['opcionales']
        # vinculación con AgregarRetencion y AgregarDeduccion
        self.deducciones = self.ajuste['ajusteDebito']['deducciones']
        self.retenciones = self.ajuste['ajusteDebito']['retenciones']
        
    @inicializar_y_capturar_excepciones
    def AjustarLiquidacionUnificado(self):
        "Ajustar Liquidación Primaria de Granos"
        
        ret = self.client.liquidacionAjustarUnificado(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        **self.ajuste
                        )
        ret = ret['ajusteUnifReturn']
        self.__analizar_errores(ret)
        if 'ajusteUnificado' in ret:
            aut = ret['ajusteUnificado']
            self.AnalizarAjuste(aut)

    @inicializar_y_capturar_excepciones
    def AjustarLiquidacionUnificadoPapel(self):
        "Ajustar Liquidación realizada en un formulario F1116 B / C (papel)"
        
        # limpiar arrays no enviados:
        if not self.ajuste['ajusteBase']['certificados']:
            del self.ajuste['ajusteBase']['certificados']
        for k1 in ('ajusteCredito', 'ajusteDebito'):
            for k2 in ('retenciones', 'deducciones'):
                if not self.ajuste[k1][k2]:
                    del self.ajuste[k1][k2]
        ret = self.client.liquidacionAjustarUnificadoPapel(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        **self.ajuste
                        )
        ret = ret['ajustePapelReturn']
        self.__analizar_errores(ret)
        if 'ajustePapel' in ret:
            aut = ret['ajustePapel']
            self.AnalizarAjuste(aut)

    @inicializar_y_capturar_excepciones
    def AjustarLiquidacionContrato(self):
        "Ajustar Liquidación activas relacionadas a un contrato"
        
        # limpiar arrays no enviados:
        if not self.ajuste['ajusteBase']['certificados']:
            del self.ajuste['ajusteBase']['certificados']
        for k1 in ('ajusteCredito', 'ajusteDebito'):
            for k2 in ('retenciones', 'deducciones'):
                if not self.ajuste[k1][k2]:
                    del self.ajuste[k1][k2]

        ret = self.client.liquidacionAjustarContrato(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        **self.ajuste
                        )
        ret = ret['ajusteContratoReturn']
        self.__analizar_errores(ret)
        if 'ajusteContrato' in ret:
            aut = ret['ajusteContrato']
            self.AnalizarAjuste(aut)
    
    def AnalizarAjuste(self, aut):
        "Método interno para analizar la respuesta de AFIP (ajustes)"
        
        self.params_out['errores'] = self.errores
            
        # proceso la respuesta de autorizar, ajustar (y consultar):
        if aut:
            self.COE = str(aut['coe'])
            self.COEAjustado = aut.get('coeAjustado')
            self.NroContrato = aut.get('nroContrato')
            self.Estado = aut['estado']

            totunif = aut["totalesUnificados"]
            self.Subtotal = totunif['subTotalGeneral']
            self.TotalIva105 = totunif['iva105']
            self.TotalIva21 = totunif['iva21']
            self.TotalRetencionesGanancias = totunif['retencionesGanancias']
            self.TotalRetencionesIVA = totunif['retencionesIVA']
            self.TotalNetoAPagar = totunif['importeNeto']
            self.TotalIvaRg2300_07 = totunif['ivaRG2300_2007']
            self.TotalPagoSegunCondicion = totunif['pagoSCondicion']
            
            # actualizo parámetros de salida:
            self.params_out['coe'] = self.COE
            self.params_out['coe_ajustado'] = self.COE
            self.params_out['estado'] = self.Estado
            self.params_out['nro_orden'] = aut.get('nroOrden')
            self.params_out['cod_tipo_operacion'] = aut.get('codTipoOperacion')
            self.params_out['nro_contrato'] = aut.get('nroContrato')
            self.params_out['subtotal'] = self.Subtotal
            self.params_out['total_iva_10_5'] = self.TotalIva105
            self.params_out['total_iva_21'] = self.TotalIva21
            self.params_out['total_retenciones_ganancias'] = self.TotalRetencionesGanancias
            self.params_out['total_retenciones_iva'] = self.TotalRetencionesIVA
            self.params_out['total_neto_a_pagar'] = self.TotalNetoAPagar
            self.params_out['total_iva_rg_2300_07'] = self.TotalIvaRg2300_07
            self.params_out['total_pago_segun_condicion'] = self.TotalPagoSegunCondicion
            
            # almaceno los datos de ajustes crédito y débito para usarlos luego
            self.__ajuste_debito = aut['ajusteDebito']
            self.__ajuste_credito = aut['ajusteCredito']
        else:
            self.__ajuste_debito = None
            self.__ajuste_credito = None

    @inicializar_y_capturar_excepciones
    def AnalizarAjusteDebito(self):
        "Método para analizar la respuesta de AFIP para Ajuste Debito"
        self.AnalizarLiquidacion(aut=self.__ajuste_debito, liq=self.__ajuste_debito)

    @inicializar_y_capturar_excepciones
    def AnalizarAjusteCredito(self):
        "Método para analizar la respuesta de AFIP para Ajuste Credito"
        self.AnalizarLiquidacion(aut=self.__ajuste_credito, liq=self.__ajuste_credito)

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacion(self, pto_emision=None, nro_orden=None, coe=None):
        "Consulta una liquidación por No de orden"
        if coe:
            ret = self.client.liquidacionXCoeConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        coe=coe,
                        )
        else:
            ret = self.client.liquidacionXNroOrdenConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        ptoEmision=pto_emision,
                        nroOrden=nro_orden,
                        )
        ret = ret['liqConsReturn']
        self.__analizar_errores(ret)
        if 'liquidacion' in ret:
            aut = ret['autorizacion']
            liq = ret['liquidacion']
            self.AnalizarLiquidacion(aut, liq)

    @inicializar_y_capturar_excepciones
    def ConsultarUltNroOrden(self, pto_emision=1):
        "Consulta el último No de orden registrado"
        ret = self.client.liquidacionUltimoNroOrdenConsultar(
                    auth={
                        'token': self.Token, 'sign': self.Sign,
                        'cuit': self.Cuit, },
                    ptoEmision=pto_emision,
                    )
        ret = ret['liqUltNroOrdenReturn']
        self.__analizar_errores(ret)
        self.NroOrden = ret['nroOrden']

    @inicializar_y_capturar_excepciones
    def LeerDatosLiquidacion(self, pop=True):
        "Recorro los datos devueltos y devuelvo el primero si existe"
        
        if self.DatosLiquidacion:
            # extraigo el primer item
            if pop:
                datos = self.DatosLiquidacion.pop(0)
            else:
                datos = self.DatosLiquidacion[0]
            datos_Liquidacion = datos['datosConsultarLiquidacion']
            self.COE = str(datos_Liquidacion['Liquidacion'])
            self.Estado = unicode(datos_Liquidacion['estado'])
            return self.COE
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def AnularLiquidacion(self, coe):
        "Anular liquidación activa"
        ret = self.client.liquidacionAnular(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        coe=coe,
                        )
        ret = ret['anulacionReturn']
        self.__analizar_errores(ret)
        self.Resultado = ret['resultado']
        return self.COE
        
    def ConsultarCampanias(self, sep="||"):
        ret = self.client.campaniasConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['campaniaReturn']
        self.__analizar_errores(ret)
        array = ret.get('campanias', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoGrano(self, sep="||"):
        ret = self.client.tipoGranoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoGranoReturn']
        self.__analizar_errores(ret)
        array = ret.get('granos', [])
        if sep is None:
            return dict([(it['codigoDescripcion']['codigo'], 
                          it['codigoDescripcion']['descripcion']) 
                         for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarCodigoGradoReferencia(self, sep="||"):
        "Consulta de Grados según Grano."
        ret = self.client.codigoGradoReferenciaConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['gradoRefReturn']
        self.__analizar_errores(ret)
        array = ret.get('gradosRef', [])
        if sep is None:
            return dict([(it['codigoDescripcion']['codigo'], 
                          it['codigoDescripcion']['descripcion']) 
                           for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarGradoEntregadoXTipoGrano(self, cod_grano, sep="||"):
        "Consulta de Grado y Valor según Grano Entregado."
        ret = self.client.codigoGradoEntregadoXTipoGranoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        codGrano=cod_grano,
                            )['gradoEntReturn']
        self.__analizar_errores(ret)
        array = ret.get('gradoEnt', [])
        if sep is None:
            return dict([(it['gradoEnt']['codigoDescripcion']['codigo'],
                          it['gradoEnt']['valor'])
                         for it in array])
        else:
            return [("%s %%s %s %%s %s %%s %s" % (sep, sep, sep, sep)) %
                    (it['gradoEnt']['codigoDescripcion']['codigo'], 
                     it['gradoEnt']['codigoDescripcion']['descripcion'],
                     it['gradoEnt']['valor'],
                     ) 
               for it in array]

    def ConsultarTipoCertificadoDeposito(self, sep="||"):
        "Consulta de tipos de Certificados de Depósito"
        ret = self.client.tipoCertificadoDepositoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoCertDepReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposCertDep', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoDeduccion(self, sep="||"):
        "Consulta de tipos de Deducciones"
        ret = self.client.tipoDeduccionConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoDeduccionReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposDeduccion', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoRetencion(self, sep="||"):
        "Consulta de tipos de Retenciones."
        ret = self.client.tipoRetencionConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoRetencionReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposRetencion', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarPuerto(self, sep="||"):
        "Consulta de Puertos habilitados"
        ret = self.client.puertoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['puertoReturn']
        self.__analizar_errores(ret)
        array = ret.get('puertos', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoActividad(self, sep="||"):
        "Consulta de Tipos de Actividad."
        ret = self.client.tipoActividadConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoActividadReturn']
        self.__analizar_errores(ret)
        array = ret.get('tiposActividad', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarTipoActividadRepresentado(self, sep="||"):
        "Consulta de Tipos de Actividad inscripta en el RUOCA."
        try:
            ret = self.client.tipoActividadRepresentadoConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoActividadReturn']
            self.__analizar_errores(ret)
            array = ret.get('tiposActividad', [])
            self.Excepcion = self.Traceback = ""
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]
        except Exception, e:
            ex = utils.exception_info()
            self.Excepcion = ex['msg']
            self.Traceback = ex['tb']
            if sep:
                return ["ERROR"]

            
    def ConsultarProvincias(self, sep="||"):
        "Consulta las provincias habilitadas"
        ret = self.client.provinciasConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['provinciasReturn']
        self.__analizar_errores(ret)
        array = ret.get('provincias', [])
        if sep is None:
            return dict([(int(it['codigoDescripcion']['codigo']), 
                              it['codigoDescripcion']['descripcion']) 
                         for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def ConsultarLocalidadesPorProvincia(self, codigo_provincia, sep="||"):
        ret = self.client.localidadXProvinciaConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        codProvincia=codigo_provincia,
                        )['localidadesReturn']
        self.__analizar_errores(ret)
        array = ret.get('localidades', [])
        if sep is None:
            return dict([(str(it['codigoDescripcion']['codigo']), 
                          it['codigoDescripcion']['descripcion']) 
                         for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
               for it in array]

    def BuscarLocalidades(self, cod_prov, cod_localidad=None, consultar=True):
        "Devuelve la localidad o la consulta en AFIP (uso interno)"
        # si no se especifíca cod_localidad, es util para reconstruir la cache
        import wslpg_datos as datos
        if not str(cod_localidad) in datos.LOCALIDADES and consultar:
            d = self.ConsultarLocalidadesPorProvincia(cod_prov, sep=None)
            try:
                # actualizar el diccionario persistente (shelve)
                datos.LOCALIDADES.update(d)
            except Exception, e:
                print "EXCEPCION CAPTURADA", e
                # capturo errores por permisos (o por concurrencia)
                datos.LOCALIDADES = d
        return datos.LOCALIDADES.get(str(cod_localidad), "")

    def ConsultarTiposOperacion(self, sep="||"):
        "Consulta tipo de Operación por Actividad."
        ops = []
        ret = self.client.tipoActividadConsultar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['tipoActividadReturn']
        self.__analizar_errores(ret)
        for it_act in ret.get('tiposActividad', []):

            ret = self.client.tipoOperacionXActividadConsultar(
                            auth={
                                'token': self.Token, 'sign': self.Sign,
                                'cuit': self.Cuit, },
                            nroActLiquida=it_act['codigoDescripcion']['codigo'],
                            )['tipoOperacionReturn']
            self.__analizar_errores(ret)
            array = ret.get('tiposOperacion', [])
            if sep:
                ops.extend([("%s %%s %s %%s %s %%s %s" % (sep, sep, sep, sep)) % 
                    (it_act['codigoDescripcion']['codigo'],
                     it['codigoDescripcion']['codigo'], 
                     it['codigoDescripcion']['descripcion']) 
                   for it in array])
            else:
                ops.extend([(it_act['codigoDescripcion']['codigo'],
                             it['codigoDescripcion']['codigo'], 
                             it['codigoDescripcion']['descripcion']) 
                           for it in array])
        return ops

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto la respuesta)"
        try:
            if not xml or xml=='XmlResponse':
                xml = self.XmlResponse 
            elif xml=='XmlRequest':
                xml = self.XmlRequest 
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception, e:
            self.Excepcion = u"%s" % (e)
            return False

    def ObtenerTagXml(self, *tags):
        "Busca en el Xml analizado y devuelve el tag solicitado"
        # convierto el xml a un objeto
        try:
            if self.xml:
                xml = self.xml
                # por cada tag, lo busco segun su nombre o posición
                for tag in tags:
                    xml = xml(tag) # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = u"%s" % (e)

    def LoadTestXML(self, xml_file):
        "Cargar una respuesta predeterminada de pruebas (emulación del ws)"
        # cargo el ejemplo de AFIP (emulando respuesta del webservice)
        from pysimplesoap.transport import DummyTransport as DummyHTTP 
        xml = open(os.path.join(INSTALL_DIR, xml_file)).read()
        self.client.http = DummyHTTP(xml)

    def SetParametro(self, clave, valor):
        "Establece un parámetro de entrada (a usarse en llamada posterior)"
        # útil para parámetros de entrada (por ej. VFP9 no soporta más de 27)
        self.params_in[str(clave)] = valor
        return True

    def GetParametro(self, clave, clave1=None, clave2=None):
        "Devuelve un parámetro de salida (establecido por llamada anterior)"
        # útil para parámetros de salida (por ej. campos de TransaccionPlainWS)
        valor = self.params_out.get(clave)
        # busco datos "anidados" (listas / diccionarios)
        if clave1 is not None and valor is not None:
            if isinstance(clave1, basestring) and clave1.isdigit():
                clave1 = int(clave1)
            try:
                valor = valor[clave1]
            except (KeyError, IndexError):
                valor = None
        if clave2 is not None and valor is not None:
            try:
                valor = valor.get(clave2)
            except KeyError:
                valor = None
        if valor is not None:
            return str(valor)
        else:
            return ""


    # Funciones para generar PDF:


    def CargarFormatoPDF(self, archivo=""):
        "Cargo el formato de campos a generar desde una planilla CSV"
        if not archivo:
            archivo = os.path.join(self.InstallDir, 
                                    "liquidacion_form_c1116b_wslpg.csv")
        if DEBUG: print "abriendo archivo ", archivo
        self.elements = []
        for lno, linea in enumerate(open(archivo.encode('latin1')).readlines()):
            if DEBUG: print "procesando linea ", lno, linea
            args = []
            for i,v in enumerate(linea.split(";")):
                if not v.startswith("'"): 
                    v = v.replace(",",".")
                else:
                    v = v#.decode('latin1')
                if v.strip()=='':
                    v = None
                else:
                    v = eval(v.strip())
                args.append(v)

            # corrijo path relativo para las imágenes:
            if args[1] == 'I':
                if not os.path.exists(args[14]):
                    args[14] = os.path.join(self.InstallDir, args[14])
                if DEBUG: print "NUEVO PATH:", args[14]          

            self.AgregarCampoPDF(*args)
        return True        


    def AgregarCampoPDF(self, nombre, tipo, x1, y1, x2, y2, 
                           font="Arial", size=12,
                           bold=False, italic=False, underline=False, 
                           foreground= 0x000000, background=0xFFFFFF,
                           align="L", text="", priority=0, **kwargs):
        "Agrego un campo a la plantilla"
        # convierto colores de string (en hexadecimal)
        if isinstance(foreground, basestring): foreground = int(foreground, 16)
        if isinstance(background, basestring): background = int(background, 16)
        if isinstance(text, unicode): text = text.encode("latin1")
        field = {
                'name': nombre, 
                'type': tipo, 
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 
                'font': font, 'size': size,
                'bold': bold, 'italic': italic, 'underline': underline, 
                'foreground': foreground, 'background': background,
                'align': align, 'text': text, 'priority': priority}
        field.update(kwargs)
        self.elements.append(field)
        return True


    def CrearPlantillaPDF(self, papel="A4", orientacion="portrait"):
        "Iniciar la creación del archivo PDF"
        
        self.AgregarCampoPDF("anulado", 'T', 150, 250, 0, 0, 
              size=70, rotate=45, foreground=0x808080, 
              priority=-1)

        if HOMO:
            self.AgregarCampoPDF("homo", 'T', 100, 250, 0, 0,
                              size=70, rotate=45, foreground=0x808080, 
                              priority=-1)
 
        # genero el renderizador con propiedades del PDF
        t = Template(elements=self.elements,
                 format=papel, orientation=orientacion,
                 title="F 1116 B/C %s" % (self.NroOrden),
                 author="CUIT %s" % self.Cuit,
                 subject="COE %s" % self.params_out.get('coe'),
                 keywords="AFIP Liquidacion Electronica Primaria de Granos", 
                 creator='wslpg.py %s (http://www.PyAfipWs.com.ar)' % __version__,)
        self.template = t
        return True
        

    def AgregarDatoPDF(self, campo, valor, pagina='T'):
        "Agrego un dato a la factura (internamente)"
        self.datos[campo] = valor
        return True

    def ProcesarPlantillaPDF(self, num_copias=1, lineas_max=24, qty_pos='izq'):
        "Generar el PDF según la factura creada y plantilla cargada"
        try:
            f = self.template
            liq = self.params_out

            if HOMO:
                self.AgregarDatoPDF("homo", u"HOMOLOGACIÓN")

            copias = {1: 'Original', 2: 'Duplicado', 3: 'Triplicado', 
                      4: 'Cuadruplicado', 5: 'Quintuplicado'}
                        
            # convierto el formato de intercambio para representar los valores:        
            fmt_encabezado = dict([(v[0], v[1:]) for v in ENCABEZADO])
            fmt_deduccion = dict([(v[0], v[1:]) for v in DEDUCCION])
            fmt_retencion = dict([(v[0], v[1:]) for v in RETENCION])
            
            def formatear(campo, valor, formato):
                "Convertir el valor a una cadena correctamente s/ formato ($ % ...)"
                if campo in formato and v is not None:
                    fmt = formato[campo]
                    if fmt[1] == N:
                        if 'cuit' in campo:
                            c = str(valor)
                            if len(c) == 11:
                                valor = "%s-%s-%s" % (c[0:2], c[2:10], c[10:])
                            else:
                                valor = ""
                        elif 'peso' in campo:
                            valor = "%s Kg" % valor
                        else:
                            valor = "%d" % int(valor)
                    elif fmt[1] == I:
                        valor = ("%%0.%df" % fmt[2]) % valor
                        if 'alic' in campo or 'comision' in campo:
                            valor = valor + " %"
                        elif 'factor' in campo or 'cont' in campo or 'cant' in campo:
                            pass
                        else:
                            valor = "$ " + valor
                    elif 'fecha' in campo:
                        d = valor
                        if isinstance(d, (datetime.date, datetime.datetime)):
                            valor = d.strftime("%d/%m/%Y")
                        else:
                            valor = "%s/%s/%s" % (d[8:10], d[5:7], d[0:4])
                return valor

            def buscar_localidad_provincia(cod_prov, cod_localidad): 
                "obtener la descripción de la provincia/localidad (usar cache)"
                cod_prov = int(cod_prov)
                cod_localidad = str(cod_localidad)
                provincia = datos.PROVINCIAS[cod_prov]
                localidad = self.BuscarLocalidades(cod_prov, cod_localidad)
                return localidad, provincia                

            # divido los datos adicionales (debe haber renglones 1 al 9):
            if liq.get('datos_adicionales') and f.has_key('datos_adicionales1'):
                d = liq.get('datos_adicionales')
                for i, ds in enumerate(f.split_multicell(d, 'datos_adicionales1')):
                    liq['datos_adicionales%s' % (i + 1)] = ds
                
            for copia in range(1, num_copias+1):
                
                # completo campos y hojas
                f.add_page()                   
                f.set('copia', copias.get(copia, "Adicional %s" % copia))
                
                f.set('anulado', {'AC': '', '': 'SIN ESTADO',
                                  'AN': "ANULADO"}.get(liq['estado'], "ERROR"))

                try:
                    cod_tipo_ajuste = int(liq["cod_tipo_ajuste"] or '0')
                except: 
                    cod_tipo_ajuste = None
                f.set('tipo_ajuste', {3: u'Liquidación de Débito', 
                                      4: u'Liquidación de Crédito',
                                      }.get(cod_tipo_ajuste, ''))

                # limpio datos del corredor si no corresponden:
                if liq['actua_corredor'] == 'N':
                    if liq.get('cuit_corredor', None) == 0:
                        del liq['cuit_corredor']
                    
                # establezco campos según tabla encabezado:
                for k,v in liq.items():
                    v = formatear(k, v, fmt_encabezado)
                    if isinstance(v, (basestring, int, long, float)):
                        f.set(k, v)
                    elif isinstance(v, decimal.Decimal):
                        f.set(k, str(v))
                    elif isinstance(v, datetime.datetime):
                        f.set(k, str(v))

                import wslpg_datos as datos
                
                campania = int(liq['campania_ppal'])
                f.set("campania_ppal", datos.CAMPANIAS.get(campania, campania))
                f.set("tipo_operacion", datos.TIPOS_OP[int(liq['cod_tipo_operacion'])])
                f.set("actividad", datos.ACTIVIDADES.get(int(liq['nro_act_comprador']), ""))
                f.set("grano", datos.GRANOS[int(liq['cod_grano'])])
                cod_puerto = int(liq['cod_puerto'])
                if cod_puerto in datos.PUERTOS:
                    f.set("des_puerto_localidad", datos.PUERTOS[cod_puerto])

                cod_grano = int(liq['cod_grano'])
                cod_grado_ref = liq.get('cod_grado_ref', "")
                if cod_grado_ref in datos.GRADOS_REF:
                    f.set("des_grado_ref", datos.GRADOS_REF[cod_grado_ref])
                else:
                    f.set("des_grado_ref", cod_grado_ref)
                cod_grado_ent = liq['cod_grado_ent']
                if 'val_grado_ent' in liq and int(liq.get('val_grado_ent', 0)):
                    val_grado_ent =  liq['val_grado_ent']
                elif cod_grano in datos.GRADO_ENT_VALOR: 
                    valores = datos.GRADO_ENT_VALOR[cod_grano]
                    if cod_grado_ent in valores:
                        val_grado_ent = valores[cod_grado_ent]
                    else:
                        val_grado_ent = ""
                else:
                    val_grado_ent = ""
                f.set("valor_grado_ent", "%s %s" % (cod_grado_ent, val_grado_ent))
                
                if liq.get('certificados'):
                    # uso la procedencia del certificado de depósito 
                    cert = liq['certificados'][0]
                    localidad, provincia = buscar_localidad_provincia(
                        cert['cod_prov_procedencia'],
                        cert['cod_localidad_procedencia'])
                elif liq.get('cod_prov_procedencia_sin_certificado'):
                    localidad, provincia = buscar_localidad_provincia(
                        liq['cod_prov_procedencia_sin_certificado'], 
                        liq['cod_localidad_procedencia_sin_certificado'])
                else:
                    localidad, provincia = "", ""
    
                f.set("procedencia", "%s - %s" % (localidad, provincia))
                
                # si no se especifíca, uso la procedencia para el lugar
                if not self.datos.get('lugar_y_fecha'):
                    localidad, provincia = buscar_localidad_provincia(
                        liq['cod_prov_procedencia'], 
                        liq['cod_localidad_procedencia'])
                    lugar = "%s - %s " % (localidad, provincia)
                    fecha = datetime.datetime.today().strftime("%d/%m/%Y")
                    f.set("lugar_y_fecha", "%s, %s" % (fecha, lugar))
                    if 'lugar_y_fecha' in self.datos:
                        del self.datos['lugar_y_fecha']

                if HOMO:
                    homo = "(pruebas)"
                else:
                    homo = ""
                
                if int(liq['cod_tipo_operacion']) == 1: 
                    f.set("comprador.L", "COMPRADOR:")
                    f.set("vendedor.L", "VENDEDOR:")
                    f.set("formulario", u"Form. Electrónico 1116 B %s" % homo)
                else:
                    f.set("comprador.L", "MANDATARIO/CONSIGNATARIO:")
                    f.set("vendedor.L", "MANDANTE/COMITENTE:")
                    f.set("formulario", u"Form. Electrónico 1116 C %s" % homo)
                    
                certs = []
                for cert in liq['certificados']:
                    certs.append(u"%s Nº %s" % (
                        datos.TIPO_CERT_DEP[int(cert['tipo_certificado_deposito'])],
                        cert['nro_certificado_deposito']))
                f.set("certificados_deposito", ', '.join(certs))

                for i, deduccion in enumerate(liq['deducciones']):
                    for k, v in deduccion.items():
                        v = formatear(k, v, fmt_deduccion)
                        f.set("deducciones_%s_%02d" % (k, i + 1), v)

                for i, retencion in enumerate(liq['retenciones']):
                    for k, v in retencion.items():
                        v = formatear(k, v, fmt_retencion)
                        f.set("retenciones_%s_%02d" % (k, i + 1), v)
                    if retencion['importe_certificado_retencion']:
                        d = retencion['fecha_certificado_retencion']
                        f.set('retenciones_cert_retencion_%02d' % (i + 1),
                            "%s $ %0.2f %s" % (
                                retencion['nro_certificado_retencion'] or '',
                                retencion['importe_certificado_retencion'],
                                "%s/%s/%s" % (d[8:10], d[5:7], d[2:4]), 
                            ))

                # cargo campos adicionales ([PDF] en .ini y AgregarDatoPDF)
                for k,v in self.datos.items():
                    f.set(k, v)
            return True
        except Exception, e:
            ex = utils.exception_info()
            try:
                f.set('anulado', "%(name)s:%(lineno)s" % ex)
            except:
                pass
            self.Excepcion = ex['msg']
            self.Traceback = ex['tb']
            if DEBUG:
                print self.Excepcion
                print self.Traceback
            return False

    def GenerarPDF(self, archivo=""):
        "Generar archivo de salida en formato PDF"
        try:
            self.template.render(archivo)
            return True
        except Exception, e:
            self.Excepcion = str(e)
            return False

    def MostrarPDF(self, archivo, imprimir=False):
        try:
            if sys.platform=="linux2":
                os.system("evince ""%s""" % archivo)
            else:
                operation = imprimir and "print" or ""
                os.startfile(archivo, operation)
            return True
        except Exception, e:
            self.Excepcion = str(e)
            return False

def escribir_archivo(dic, nombre_archivo, agrega=True):
    archivo = open(nombre_archivo, agrega and "a" or "w")
    if '--json' in sys.argv:
        json.dump(dic, archivo, sort_keys=True, indent=4)
    elif '--dbf' in sys.argv:
        formatos = [('Encabezado', ENCABEZADO, [dic]), 
                    ('Certificado', CERTIFICADO, dic.get('certificados', [])), 
                    ('Retencion', RETENCION, dic.get('retenciones', [])), 
                    ('Deduccion', DEDUCCION, dic.get('deducciones', [])),
                    ('AjusteCredito', AJUSTE, dic.get('ajuste_credito', [])),
                    ('AjusteDebito', AJUSTE, dic.get('ajuste_debito', [])),
                    ('Dato', DATO, dic.get('datos', [])),
                    ('Error', ERROR, dic.get('errores', [])),
                    ]
        guardar_dbf(formatos, agrega, conf_dbf)
    else:
        dic['tipo_reg'] = 0
        archivo.write(escribir(dic, ENCABEZADO))
        if 'certificados' in dic:
            for it in dic['certificados']:
                it['tipo_reg'] = 1
                archivo.write(escribir(it, CERTIFICADO))
        if 'retenciones' in dic:
            for it in dic['retenciones']:
                it['tipo_reg'] = 2
                archivo.write(escribir(it, RETENCION))
        if 'deducciones' in dic:
            for it in dic['deducciones']:
                it['tipo_reg'] = 3
                archivo.write(escribir(it, DEDUCCION))
        if 'ajuste_debito' in dic:
            dic['ajuste_debito']['tipo_reg'] = 4
            archivo.write(escribir(dic['ajuste_debito'], AJUSTE))
            for it in dic['ajuste_debito'].get('retenciones', []):
                it['tipo_reg'] = 2
                archivo.write(escribir(it, RETENCION))
            for it in dic['ajuste_debito'].get('deducciones', []):
                it['tipo_reg'] = 3
                archivo.write(escribir(it, DEDUCCION))
        if 'ajuste_credito' in dic:
            dic['ajuste_credito']['tipo_reg'] = 5
            archivo.write(escribir(dic['ajuste_credito'], AJUSTE))
            for it in dic['ajuste_credito'].get('retenciones', []):
                it['tipo_reg'] = 2
                archivo.write(escribir(it, RETENCION))
            for it in dic['ajuste_credito'].get('deducciones', []):
                it['tipo_reg'] = 3
                archivo.write(escribir(it, DEDUCCION))
        if 'datos' in dic:
            for it in dic['datos']:
                it['tipo_reg'] = 9
                archivo.write(escribir(it, DATO))
        if 'errores' in dic:
            for it in dic['errores']:
                it['tipo_reg'] = 'R'
                archivo.write(escribir(it, ERROR))
    archivo.close()

def leer_archivo(nombre_archivo):
    archivo = open(nombre_archivo, "r")
    if '--json' in sys.argv:
        dic = json.load(archivo)
    elif '--dbf' in sys.argv:
        dic = {'retenciones': [], 'deducciones': [], 'certificados': [], 
               'datos': [], 'ajuste_credito': [], 'ajuste_debito': [], }
        formatos = [('Encabezado', ENCABEZADO, dic), 
                    ('Certificado', CERTIFICADO, dic['certificados']), 
                    ('Retencio', RETENCION, dic['retenciones']), 
                    ('Deduccion', DEDUCCION, dic['deducciones']),
                    ('AjusteCredito', AJUSTE, dic['ajuste_credito']),
                    ('AjusteDebito', AJUSTE, dic['ajuste_debito']),
                    ]
        leer_dbf(formatos, conf_dbf)
    else:
        dic = {'retenciones': [], 'deducciones': [], 'certificados': [], 
               'datos': [], 'ajuste_credito': {}, 'ajuste_debito': {}, }
        for linea in archivo:
            if str(linea[0])=='0':
                d = leer(linea, ENCABEZADO)
                if d['reservado1']:
                    print "ADVERTENCIA: USAR datos adicionales (nueva posición)" 
                    d['datos_adicionales'] = d['reservado1'] 
                dic.update(d)
                # referenciar la liquidación para agregar ret. / ded.:
                liq = dic
            elif str(linea[0])=='1':
                liq['certificados'].append(leer(linea, CERTIFICADO))
            elif str(linea[0])=='2':
                liq['retenciones'].append(leer(linea, RETENCION))
            elif str(linea[0])=='3':
                d = leer(linea, DEDUCCION)
                # ajustes por cambios en afip (compatibilidad hacia atras):
                if d['reservado1']:
                    print "ADVERTENCIA: USAR precio_pkg_diario!" 
                    d['precio_pkg_diario'] = d['reservado1'] 
                liq['deducciones'].append(d)
            elif str(linea[0])=='4':
                liq = leer(linea, AJUSTE)
                liq.update({'retenciones': [], 'deducciones': [], 'datos': []})
                dic['ajuste_debito'] = liq
            elif str(linea[0])=='5':
                liq = leer(linea, AJUSTE)
                liq.update({'retenciones': [], 'deducciones': [], 'datos': []})
                dic['ajuste_credito'] = liq
            elif str(linea[0])=='9':
                liq['datos'].append(leer(linea, DATO))
            else:
                print "Tipo de registro incorrecto:", linea[0]
    archivo.close()
    return dic
    

# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)
    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato in [('Encabezado', ENCABEZADO), 
                             ('Certificado', CERTIFICADO), 
                             ('Retencion', RETENCION), 
                             ('Deduccion', DEDUCCION), 
                             ('Ajuste', AJUSTE),
                             ('Evento', EVENTO), ('Error', ERROR), 
                             ('Dato', DATO)]:
            comienzo = 1
            print "=== %s ===" % msg
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                print " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                    clave, comienzo, longitud, tipo, dec)
                comienzo += longitud
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSLPG)
        sys.exit(0)

    import csv
    from ConfigParser import SafeConfigParser

    from wsaa import WSAA

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        if len(sys.argv)>1 and sys.argv[1].endswith(".ini"):
            CONFIG_FILE = sys.argv[1]
            print "Usando configuracion:", CONFIG_FILE
         
        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSLPG','CUIT')
        ENTRADA = config.get('WSLPG','ENTRADA')
        SALIDA = config.get('WSLPG','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            WSAA_URL = config.get('WSAA','URL')
        else:
            WSAA_URL = None #wsaa.WSAAURL
        if config.has_option('WSLPG','URL') and not HOMO:
            WSLPG_URL = config.get('WSLPG','URL')
        else:
            WSLPG_URL = WSDL

        PROXY = config.has_option('WSAA', 'PROXY') and config.get('WSAA', 'PROXY') or None
        CACERT = config.has_option('WSAA', 'CACERT') and config.get('WSAA', 'CACERT') or None
        WRAPPER = config.has_option('WSAA', 'WRAPPER') and config.get('WSAA', 'WRAPPER') or None
        
        if config.has_section('DBF'):
            conf_dbf = dict(config.items('DBF'))
            if DEBUG: print "conf_dbf", conf_dbf
        else:
            conf_dbf = {}
            
        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "WSAA_URL:", WSAA_URL
            print "WSLPG_URL:", WSLPG_URL
            print "CACERT", CACERT
            print "WRAPPER", WRAPPER
        # obteniendo el TA
        TA = "wslpg-ta.xml"
        # verifico que el TA exista, no esté vacio, no haya expirado (5hs)
        # y que no haya sido tramitado antes de la ult. modificación del .ini
        if (not os.path.exists(TA) or os.path.getsize(TA) == 0  
            or os.path.getmtime(TA)+(60*60*5) < time.time() 
            or os.path.getmtime(CONFIG_FILE) > os.path.getmtime(TA)):
            # Tramito un nuevo Ticket de Acceso:
            wsaa = WSAA()
            wsaa.LanzarExcepciones = False
            tra = wsaa.CreateTRA(service="wslpg")
            if DEBUG:
                print tra
            cms = wsaa.SignTRA(tra, CERT, PRIVATEKEY)
            if wsaa.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wsaa.Excepcion
                if DEBUG: print >> sys.stderr, wsaa.Traceback
                sys.exit(6)
            try:
                wsaa.Conectar(wsdl=WSAA_URL, proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
                ta_string = wsaa.LoginCMS(cms)
                if wsaa.Excepcion:
                    print >> sys.stderr, "EXCEPCION:", wsaa.Excepcion
                    if DEBUG: print >> sys.stderr, wsaa.Traceback
                    sys.exit(6)
            except Exception, e:
                print >> sys.stderr, e
                ta_string = ""
                sys.exit(7)
            # guardo el TA en el archivo
            open(TA,"w").write(ta_string)
        # leo el TA del archivo, extraigo token y sign:
        ta_string=open(TA).read()
        if ta_string:
            ta = SimpleXMLElement(ta_string)
            token = str(ta.credentials.token)
            sign = str(ta.credentials.sign)
        else:
            token = ""
            sign = ""
        # fin TA

        # cliente soap del web service
        wslpg = WSLPG()
        wslpg.LanzarExcepciones = True
        wslpg.Conectar(url=WSLPG_URL, proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
        wslpg.Token = token
        wslpg.Sign = sign
        wslpg.Cuit = CUIT

        if '--dummy' in sys.argv:
            ret = wslpg.Dummy()
            print "AppServerStatus", wslpg.AppServerStatus
            print "DbServerStatus", wslpg.DbServerStatus
            print "AuthServerStatus", wslpg.AuthServerStatus
            ##sys.exit(0)

        if '--autorizar' in sys.argv:
        
            if '--prueba' in sys.argv:
                pto_emision = 99
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=pto_emision,
                    nro_orden=0,  # que lo calcule automáticamente
                    cuit_comprador='20400000000',  
                    nro_act_comprador=40, nro_ing_bruto_comprador='20400000000',
                    cod_tipo_operacion=2 if "--consign" in sys.argv else 1,
                    es_liquidacion_propia='N', es_canje='N',
                    cod_puerto=14, des_puerto_localidad="DETALLE PUERTO",
                    cod_grano=31, 
                    cuit_vendedor=23000000019, nro_ing_bruto_vendedor=23000000019,
                    actua_corredor="S", liquida_corredor="S", 
                    cuit_corredor=wslpg.Cuit, # uso Cuit representado
                    comision_corredor=1, nro_ing_bruto_corredor=wslpg.Cuit,
                    fecha_precio_operacion="2013-02-07",
                    precio_ref_tn=2000,
                    cod_grado_ref="G1",
                    cod_grado_ent="FG",
                    factor_ent=98, val_grado_ent=1.02,
                    precio_flete_tn=10,
                    cont_proteico=20,
                    alic_iva_operacion=10.5,
                    campania_ppal=1213,
                    cod_localidad_procedencia=5544,
                    cod_prov_procedencia=12,
                    datos_adicionales=("DATOS ADICIONALES 1234 " * 17) + ".",
                    ##peso_neto_sin_certificado=2000,
                    precio_operacion=None,  # para probar ajustar
                    total_peso_neto=1000,   # para probar ajustar
                    certificados=[dict(   
                        tipo_certificado_deposito=5,
                        nro_certificado_deposito=555501200729,
                        peso_neto=1000,
                        cod_localidad_procedencia=3,
                        cod_prov_procedencia=1,
                        campania=1213,
                        fecha_cierre="2013-01-13",)],
                    retenciones=[dict(
                            codigo_concepto="RI",
                            detalle_aclaratorio="DETALLE DE IVA",
                            base_calculo=1000,
                            alicuota=10.5,
                        ), dict(
                            codigo_concepto="RG",
                            detalle_aclaratorio="DETALLE DE GANANCIAS",
                            base_calculo=100,
                            alicuota=0,
                        ), dict(
                            codigo_concepto="OG",
                            detalle_aclaratorio="OTRO GRAVAMEN",
                            base_calculo=1000,
                            alicuota=0,
                            nro_certificado_retencion=111111111111, 
                            fecha_certificado_retencion="2013-05-01",
                            importe_certificado_retencion=105,
                        )],
                    deducciones=[dict(
                            codigo_concepto="OD",
                            detalle_aclaratorio="FLETE",
                            dias_almacenaje="0",
                            precio_pkg_diario=0.0,
                            comision_gastos_adm=0.0,
                            base_calculo=100.0,
                            alicuota=21.0,
                        ),dict(
                            codigo_concepto="AL",
                            detalle_aclaratorio="ALMACENAJE",
                            dias_almacenaje="30",
                            precio_pkg_diario=0.0001,
                            comision_gastos_adm=0.0,
                            alicuota=21.0,
                        ),],
                    datos=[
                        dict(campo="nombre_comprador", valor="NOMBRE 1"),
                        dict(campo="domicilio1_comprador", valor="DOMICILIO 1"),
                        dict(campo="domicilio2_comprador", valor="DOMICILIO 1"),
                        dict(campo="localidad_comprador", valor="LOCALIDAD 1"),
                        dict(campo="iva_comprador", valor="R.I."),
                        dict(campo="nombre_vendedor", valor="NOMBRE 2"),
                        dict(campo="domicilio1_vendedor", valor="DOMICILIO 2"),
                        dict(campo="domicilio2_vendedor", valor="DOMICILIO 2"),
                        dict(campo="localidad_vendedor", valor="LOCALIDAD 2"),
                        dict(campo="iva_vendedor", valor="R.I."),
                        dict(campo="nombre_corredor", valor="NOMBRE 3"),
                        dict(campo="domicilio_corredor", valor="DOMICILIO 3"),
                        ]
                    )
                if "--sincorr" in sys.argv:
                    # ajusto datos para prueba sin corredor
                    dic.update(dict(
                        cuit_comprador=wslpg.Cuit,  
                        nro_act_comprador=29, nro_ing_bruto_comprador=wslpg.Cuit,
                        actua_corredor="N", liquida_corredor="N", 
                        cuit_corredor=0,
                        comision_corredor=0, nro_ing_bruto_corredor=0,))
                    dic['retenciones'][1]['alicuota'] = 15
                    del dic['datos'][-1]
                    del dic['datos'][-1]
                if "--sincert" in sys.argv:
                    # ajusto datos para prueba sin certificado de deposito
                    dic['peso_neto_sin_certificado'] = 10000
                    dic['cod_prov_procedencia_sin_certificado'] = 1
                    dic['cod_localidad_procedencia_sin_certificado'] = 15124
                    dic['certificados'] = []
                if "--singrado" in sys.argv:
                    # ajusto datos para prueba sin grado ni valor entregado
                    dic['cod_grado_ref'] = ""
                    dic['cod_grado_ent'] = ""
                    dic['val_grado_ent'] = 0
                if "--consign" in sys.argv:
                    # agrego deducción por comisión de gastos administrativos
                    dic['deducciones'].append(dict(
                            codigo_concepto="CO",
                            detalle_aclaratorio="COMISION",
                            dias_almacenaje=None,
                            precio_pkg_diario=None,
                            comision_gastos_adm=1.0,
                            base_calculo=1000.00,
                            alicuota=21.0,
                        ))
                escribir_archivo(dic, ENTRADA)
            else:
                dic = leer_archivo(ENTRADA)

            if not 'nro_orden' in dic:
                raise RuntimeError("Archivo de entrada invalido, revise campos y lineas en blanco")
                
            if int(dic['nro_orden']) == 0 and not '--testing' in sys.argv:
                # consulto el último número de orden emitido:
                ok = wslpg.ConsultarUltNroOrden(dic['pto_emision'])
                if ok:
                    dic['nro_orden'] = wslpg.NroOrden + 1

            # establezco los parametros (se pueden pasar directamente al metodo)
            for k, v in sorted(dic.items()):
                if DEBUG: print "%s = %s" % (k, v)
                wslpg.SetParametro(k, v)
                
            # cargo la liquidación:
            wslpg.CrearLiquidacion()

            for cert in dic.get('certificados', []):
                wslpg.AgregarCertificado(**cert)

            for ded in dic.get('deducciones', []):
                wslpg.AgregarDeduccion(**ded)

            for ret in dic.get('retenciones', []):
                wslpg.AgregarRetencion(**ret)

            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo
                if '--error' in sys.argv:
                    wslpg.LoadTestXML("wslpg_error.xml")     # cargo error
                else:
                    wslpg.LoadTestXML("wslpg_aut_test.xml")  # cargo respuesta

            print "Liquidacion: pto_emision=%s nro_orden=%s nro_act=%s tipo_op=%s" % (
                    wslpg.liquidacion['ptoEmision'], 
                    wslpg.liquidacion['nroOrden'], 
                    wslpg.liquidacion['nroActComprador'],
                    wslpg.liquidacion['codTipoOperacion'], 
                    )
            
            if not '--dummy' in sys.argv:        
                if '--recorrer' in sys.argv:
                    print "Consultando actividades y operaciones habilitadas..."
                    lista_act_op = wslpg.ConsultarTiposOperacion(sep=None)
                    # recorro las actividades habilitadas buscando la 
                    for nro_act, cod_op, det in lista_act_op:
                        print "Probando nro_act=", nro_act, "cod_op=", cod_op, 
                        wslpg.liquidacion['nroActComprador'] = nro_act
                        wslpg.liquidacion['codTipoOperacion'] = cod_op
                        ret = wslpg.AutorizarLiquidacion()
                        if wslpg.COE:
                            print
                            break       # si obtuve COE salgo
                        else:
                            print wslpgPDF.Errores
                else:
                    print "Autorizando..." 
                    ret = wslpg.AutorizarLiquidacion()
                    
            if wslpg.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslpg.Excepcion
                if DEBUG: print >> sys.stderr, wslpg.Traceback
            print "Errores:", wslpg.Errores
            print "COE", wslpg.COE
            print "COEAjustado", wslpg.COEAjustado
            print "TootalDeduccion", wslpg.TotalDeduccion
            print "TotalRetencion", wslpg.TotalRetencion
            print "TotalRetencionAfip", wslpg.TotalRetencionAfip
            print "TotalOtrasRetenciones", wslpg.TotalOtrasRetenciones
            print "TotalNetoAPagar", wslpg.TotalNetoAPagar
            print "TotalIvaRg2300_07", wslpg.TotalIvaRg2300_07
            print "TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion
            if False and '--testing' in sys.argv:
                assert wslpg.COE == "330100000357"
                assert wslpg.COEAjustado == None
                assert wslpg.Estado == "AC"
                assert wslpg.TotalPagoSegunCondicion == 1968.00
                assert wslpg.GetParametro("fecha_liquidacion") == "2013-02-07"
                assert wslpg.GetParametro("retenciones", 1, "importe_retencion") == "157.60"

            if DEBUG: 
                pprint.pprint(wslpg.params_out)

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=('--agrega' in sys.argv))  

        if '--ajustar' in sys.argv:
            print "Ajustando..."
            if '--prueba' in sys.argv:
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=55, nro_orden=0, coe_ajustado='330100013184',
                    certificados=[dict(
                       tipo_certificado_deposito=5,
                       nro_certificado_deposito=555501200729,
                       peso_neto=10000,
                       cod_localidad_procedencia=3,
                       cod_prov_procedencia=1,
                       campania=1213,
                       fecha_cierre='2013-01-13',
                       peso_neto_total_certificado=10000,
                       )],
                    ajuste_credito=dict(
                        diferencia_peso_neto=1000, diferencia_precio_operacion=100,
                        cod_grado="G2", val_grado=1.0, factor=100,
                        diferencia_precio_flete_tn=10,
                        datos_adicionales='AJUSTE CRED UNIF',
                        concepto_importe_iva_0='Alicuota Cero',
                        importe_ajustar_Iva_0=900,
                        concepto_importe_iva_105='Alicuota Diez',
                        importe_ajustar_Iva_105=800,
                        concepto_importe_iva_21='Alicuota Veintiuno',
                        importe_ajustar_Iva_21=700,
                        deducciones=[dict(codigo_concepto="AL",
                               detalle_aclaratorio="Deduc Alm",
                               dias_almacenaje="1",
                               precio_pkg_diario=0.01,
                               comision_gastos_adm=1.0,
                               base_calculo=1000.0,
                               alicuota=10.5, )],
                        retenciones=[dict(codigo_concepto="RI",
                               detalle_aclaratorio="Ret IVA",
                               base_calculo=1000,
                               alicuota=10.5, )], 
                        ),
                    ajuste_debito=dict(
                        diferencia_peso_neto=500, diferencia_precio_operacion=100,
                        cod_grado="G2", val_grado=1.0, factor=100,
                        diferencia_precio_flete_tn=0.01,
                        datos_adicionales='AJUSTE DEB UNIF',
                        concepto_importe_iva_0='Alic 0',
                        importe_ajustar_Iva_0=250,
                        concepto_importe_iva_105='Alic 10.5',
                        importe_ajustar_Iva_105=200,
                        concepto_importe_iva_21='Alicuota 21',
                        importe_ajustar_Iva_21=50,
                        deducciones=[dict(codigo_concepto="AL",
                               detalle_aclaratorio="Deduc Alm",
                               dias_almacenaje="1",
                               precio_pkg_diario=0.01,
                               comision_gastos_adm=1.0,
                               base_calculo=500.0,
                               alicuota=10.5, )],
                        retenciones=[dict(codigo_concepto="RI",
                               detalle_aclaratorio="Ret IVA",
                               base_calculo=100,
                               alicuota=10.5, )],
                        ),
                    )
                if '--contrato' in sys.argv:
                    dic.update(
                        {'nro_act_comprador': 40,
                         'cod_grado_ent': 'G1',
                         'cod_grano': 31,
                         'cod_puerto': 14,
                         'cuit_comprador': 20400000000,
                         'cuit_corredor': 20267565393,
                         'cuit_vendedor': 23000000019,
                         'des_puerto_localidad': 'Desc Puerto',
                         'nro_contrato': 26,
                         'precio_flete_tn': 1000,
                         'precio_ref_tn': 1000,
                         'val_grado_ent': 1.01})
                escribir_archivo(dic, ENTRADA)
            
            dic = leer_archivo(ENTRADA)
            
            if not 'nro_orden' in dic:
                raise RuntimeError("Archivo de entrada invalido, revise campos y lineas en blanco")
                
            if int(dic['nro_orden']) == 0 and not '--testing' in sys.argv:
                # consulto el último número de orden emitido:
                ok = wslpg.ConsultarUltNroOrden(dic['pto_emision'])
                if ok:
                    dic['nro_orden'] = wslpg.NroOrden + 1
            
            if '--contrato' in sys.argv:
                for k in ("nro_contrato", "nro_act_comprador", "cod_grano", 
                          "cuit_vendedor", "cuit_comprador", "cuit_corredor", 
                          "precio_ref_tn", "cod_grado_ent", "val_grado_ent", 
                          "precio_flete_tn", "cod_puerto", 
                          "des_puerto_localidad"):
                    v = dic.get(k)
                    if v:
                        wslpg.SetParametro(k, v)
                        
            wslpg.CrearAjusteBase(pto_emision=dic['pto_emision'], 
                              nro_orden=dic['nro_orden'], 
                              coe_ajustado=dic['coe_ajustado'])
            
            for cert in dic.get('certificados', []):
                if cert:
                    wslpg.AgregarCertificado(**cert)

            liq = dic['ajuste_credito']
            wslpg.CrearAjusteCredito(**liq)
            for ded in liq.get('deducciones', []):
                wslpg.AgregarDeduccion(**ded)
            for ret in liq.get('retenciones', []):
                wslpg.AgregarRetencion(**ret)
            
            liq = dic['ajuste_debito']
            wslpg.CrearAjusteDebito(**liq)
            for ded in liq.get('deducciones', []):
                wslpg.AgregarDeduccion(**ded)
            for ret in liq.get('retenciones', []):
                wslpg.AgregarRetencion(**ret)
            
            if '--testing' in sys.argv:
                wslpg.LoadTestXML("tests/wslpg_ajuste_unificado.xml")

            if '--contrato' in sys.argv:
                ret = wslpg.AjustarLiquidacionContrato()
            else:
                ret = wslpg.AjustarLiquidacionUnificado()
            
            if wslpg.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslpg.Excepcion
                if DEBUG: print >> sys.stderr, wslpg.Traceback
            print "Errores:", wslpg.Errores
            print "COE", wslpg.COE
            print "Subtotal", wslpg.Subtotal
            print "TotalIva105", wslpg.TotalIva105
            print "TotalIva21", wslpg.TotalIva21
            print "TotalRetencionesGanancias", wslpg.TotalRetencionesGanancias
            print "TotalRetencionesIVA", wslpg.TotalRetencionesIVA
            print "TotalNetoAPagar", wslpg.TotalNetoAPagar
            print "TotalIvaRg2300_07", wslpg.TotalIvaRg2300_07
            print "TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion
            
            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)            
            ok = wslpg.AnalizarAjusteCredito()
            dic['ajuste_credito'].update(wslpg.params_out)
            ok = wslpg.AnalizarAjusteDebito()
            dic['ajuste_debito'].update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=('--agrega' in sys.argv))  

            if DEBUG: 
                pprint.pprint(dic)
            
        if '--anular' in sys.argv:
            ##print wslpg.client.help("anularLiquidacion")
            try:
                coe = sys.argv[sys.argv.index("--anular") + 1]
            except IndexError:
                coe = 330100000357

            print "Anulando COE", coe
            ret = wslpg.AnularLiquidacion(coe)
            if wslpg.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslpg.Excepcion
                if DEBUG: print >> sys.stderr, wslpg.Traceback
            print "COE", wslpg.COE
            print "Resultado", wslpg.Resultado
            print "Errores:", wslpg.Errores
            sys.exit(0)

        if '--consultar' in sys.argv:
            pto_emision = None
            nro_orden = 0
            coe = None
            try:
                pto_emision = sys.argv[sys.argv.index("--consultar") + 1]
                nro_orden = sys.argv[sys.argv.index("--consultar") + 2]
                coe = sys.argv[sys.argv.index("--consultar") + 3]
            except IndexError:
                pass
            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo
                wslpg.LoadTestXML("wslpg_cons_test.xml")     # cargo prueba
            print "Consultando: pto_emision=%s nro_orden=%s coe=%s" % (pto_emision, nro_orden, coe)
            ret = wslpg.ConsultarLiquidacion(pto_emision=pto_emision, nro_orden=nro_orden, coe=coe)
            print "COE", wslpg.COE
            print "Estado", wslpg.Estado
            print "Errores:", wslpg.Errores

            # actualizo el archivo de salida con los datos devueltos
            escribir_archivo(wslpg.params_out, SALIDA, agrega=('--agrega' in sys.argv))

            if DEBUG: 
                pprint.pprint(wslpg.params_out)

        if '--ult' in sys.argv:
            try:
                pto_emision = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError, ValueError:
                pto_emision = 1
            print "Consultando ultimo nro_orden para pto_emision=%s" % pto_emision
            ret = wslpg.ConsultarUltNroOrden(pto_emision)
            if wslpg.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslpg.Excepcion
                if DEBUG: print >> sys.stderr, wslpg.Traceback
            print "Ultimo Nro de Orden", wslpg.NroOrden
            print "Errores:", wslpg.Errores
            sys.exit(0)


        # Recuperar parámetros:
        
        if '--campanias' in sys.argv:
            ret = wslpg.ConsultarCampanias()
            print "\n".join(ret)
        
        if '--tipograno' in sys.argv:
            ret = wslpg.ConsultarTipoGrano()
            print "\n".join(ret)

        if '--gradoref' in sys.argv:
            ret = wslpg.ConsultarCodigoGradoReferencia()
            print "\n".join(ret)

        if '--gradoent' in sys.argv:
            ##wslpg.LoadTestXML("wslpg_cod.xml")     # cargo respuesta de ej
            cod_grano = raw_input("Ingrese el código de grano: ")
            ret = wslpg.ConsultarGradoEntregadoXTipoGrano(cod_grano=cod_grano)
            print "\n".join(ret)
        
        if '--datos' in sys.argv:
            print "# Grados"
            print wslpg.ConsultarCodigoGradoReferencia(sep=None)
            
            print "# Datos de grado entregado por tipo de granos:"
            for cod_grano in wslpg.ConsultarTipoGrano(sep=None):
                grad_ent = wslpg.ConsultarGradoEntregadoXTipoGrano(cod_grano, sep=None)
                print cod_grano, ":", grad_ent, ","

        if '--shelve' in sys.argv:
            print "# Construyendo BD de Localidades por Provincias"            
            import wslpg_datos as datos
            for cod_prov, desc_prov in wslpg.ConsultarProvincias(sep=None).items():
                print "Actualizando Provincia", cod_prov, desc_prov
                d = wslpg.BuscarLocalidades(cod_prov)

        if '--certdeposito' in sys.argv:
            ret = wslpg.ConsultarTipoCertificadoDeposito()
            print "\n".join(ret)

        if '--deducciones' in sys.argv:
            ret = wslpg.ConsultarTipoDeduccion()
            print "\n".join(ret)

        if '--retenciones' in sys.argv:
            ret = wslpg.ConsultarTipoRetencion()
            print "\n".join(ret)
            
        if '--puertos' in sys.argv:
            ret = wslpg.ConsultarPuerto()
            print "\n".join(ret)

        if '--actividades' in sys.argv:
            ret = wslpg.ConsultarTipoActividad()
            print "\n".join(ret)

        if '--actividadesrep' in sys.argv:
            ret = wslpg.ConsultarTipoActividadRepresentado()
            print "\n".join(ret)
            print "Errores:", wslpg.Errores
            
        if '--operaciones' in sys.argv:
            ret = wslpg.ConsultarTiposOperacion()
            print "\n".join(ret)

        if '--provincias' in sys.argv:
            ret = wslpg.ConsultarProvincias()
            print "\n".join(ret)
                    
        if '--localidades' in sys.argv:
            cod_prov = raw_input("Ingrese el código de provincia:")
            ret = wslpg.ConsultarLocalidadesPorProvincia(cod_prov)
            print "\n".join(ret)

        # Generación del PDF:

        if '--pdf' in sys.argv:
        
            # cargo los datos del archivo de salida:
            liq = wslpg.params_out = leer_archivo(SALIDA)
        
            conf_liq = dict(config.items('LIQUIDACION'))
            conf_pdf = dict(config.items('PDF'))
        
            # cargo el formato CSV por defecto (liquidacion....csv)
            wslpg.CargarFormatoPDF(conf_liq.get("formato"))
            
            # establezco formatos (cantidad de decimales) según configuración:
            wslpg.FmtCantidad = conf_liq.get("fmt_cantidad", "0.2")
            wslpg.FmtPrecio = conf_liq.get("fmt_precio", "0.2")

            # datos fijos (configuracion):
            for k, v in conf_pdf.items():
                wslpg.AgregarDatoPDF(k, v)

            # datos adicionales (tipo de registro 9):
            for dato in liq.get('datos', []):
                wslpg.AgregarDatoPDF(dato['campo'], dato['valor'])
                if DEBUG: print "DATO", dato['campo'], dato['valor']


            wslpg.CrearPlantillaPDF(papel=conf_liq.get("papel", "legal"), 
                                 orientacion=conf_liq.get("orientacion", "portrait"))
            wslpg.ProcesarPlantillaPDF(num_copias=int(conf_liq.get("copias", 3)),
                                    lineas_max=int(conf_liq.get("lineas_max", 24)),
                                    qty_pos=conf_liq.get("cant_pos") or 'izq')
            if wslpg.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslpg.Excepcion
                if DEBUG: print >> sys.stderr, wslpg.Traceback

            salida = conf_liq.get("salida", "")

            # genero el nombre de archivo según datos de factura
            d = os.path.join(conf_liq.get('directorio', "."), 
                             liq['fecha_liquidacion'].replace("-", "_"))
            if not os.path.isdir(d):
                if DEBUG: print "Creando directorio!", d 
                os.makedirs(d)
            fs = conf_liq.get('archivo','pto_emision,nro_orden').split(",")
            fn = u'_'.join([unicode(liq.get(ff,ff)) for ff in fs])
            fn = fn.encode('ascii', 'replace').replace('?','_')
            salida = os.path.join(d, "%s.pdf" % fn)
            wslpg.GenerarPDF(archivo=salida)
            print "Generando PDF", salida
            if '--mostrar' in sys.argv:
                wslpg.MostrarPDF(archivo=salida,
                                 imprimir='--imprimir' in sys.argv)

        print "hecho."
        
    except SoapFault,e:
        print >> sys.stderr, "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        try:
            print >> sys.stderr, traceback.format_exception_only(sys.exc_type, sys.exc_value)[0]
        except:
            print >> sys.stderr, "Excepción no disponible:", type(e)
        if DEBUG:
            raise
        sys.exit(5)
    finally:
        if XML:
            open("wslpg_request.xml", "w").write(wslpg.client.xml_request)
            open("wslpg_response.xml", "w").write(wslpg.client.xml_response)

