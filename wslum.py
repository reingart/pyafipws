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

from __future__ import with_statement

"""Módulo para obtener código de autorización electrónica (CAE) para 
Liquidación Única Mensual (lechería) del web service WSLUM de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2016 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.03a"

LICENCIA = """
wslum.py: Interfaz para generar Código de Autorización Electrónica (CAE) para
          Liquidación Única Mensual de lechería (LumService)
Copyright (C) 2016 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionUnicaMensualLecheria

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
  --json: utilizar formato json para el archivo de intercambio
  --dummy: consulta estado de servidores
  
  --autorizar: Autorizar Liquidación Única Mensual (lechería) (generarLiquidacion)
  --ult: Consulta el último número de orden registrado en AFIP 
         (consultarUltimoComprobanteXPuntoVenta)
  --consultar: Consulta una liquidación registrada en AFIP 
         (consultarLiquidacionXNroComprobante / consultarLiquidacionXCAE)

  --pdf: descarga la liquidación en formato PDF
  --mostrar: muestra el documento PDF generado (usar con --pdf)
  --imprimir: imprime el documento PDF generado (usar con --mostrar y --pdf)

  --provincias: obtiene el listado de provincias (código/descripción)
  --localidades: obtiene el listado de localidades para una provincia 
  --bonificaciones_penalizaciones: obtiene el listado de tributos
  --otros_impuestos: obtiene el listado de las retenciones de tabaco
  --puntosventa: obtiene el listado de puntos de venta habilitados

Ver wslum.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, shelve
import decimal, datetime
import traceback
import pprint
from pysimplesoap.client import SoapFault
from fpdf import Template
import utils

# importo funciones compartidas:
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir


WSDL = "https://fwshomo.afip.gov.ar/wslum/LumService?wsdl"
#WSDL = "https://serviciosjava.afip.gov.ar/wslum/LumService?wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wslum.ini"
HOMO = True


class WSLUM(BaseWS):
    "Interfaz para el WebService de Liquidación Única Mensual (lechería)"    
    _public_methods_ = ['Conectar', 'Dummy', 'SetTicketAcceso', 'DebugLog',
                        'AutorizarLiquidacion', 
                        'CrearLiquidacion',
                        'AgregarTambero', 'AgregarCondicionVenta',
                        'AgregarTambo', 'AgregarUbicacionTambo',
                        'AgregarBalanceLitrosPorcentajesSolidos',
                        'AgregarConceptosBasicosMercadoInterno',
                        'AgregarConceptosBasicosMercadoExterno',
                        'AgregarBonificacionPenalizacion',
                        'AgregarOtroImpuesto',
                        'AgregarRemito',
                        'ConsultarLiquidacion', 'ConsultarUltimoComprobante',
                        'AgregarAjuste',
                        'LeerDatosLiquidacion',
                        'ConsultarBonificacionesPenalizaciones',
                        'ConsultarOtrosImpuestos',
                        'ConsultarPuntosVentas', 
                        'ConsultarProvincias', 'ConsultarLocalidades',
                        'MostrarPDF',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'SetParametros', 'SetParametro', 'GetParametro', 
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'InstallDir',
        'CAE', 'NroComprobante', 'FechaComprobante',
        'AlicuotaIVA', 'TotalNeto', 'ImporteIVA',
        'TotalBonificacionesCalidad', 'TotalPenalizacionesCalidad',
        'TotalBonificacionesComerciales' ,'TotalDebitosComerciales',
        'TotalOtrosImpuestos', 'Total',
        ]
    _reg_progid_ = "WSLUM"
    _reg_clsid_ = "{4CBB2DF8-7AAE-434E-916D-9D663BB1CAFC}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    LanzarExcepciones = False
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.errores = []
        self.CAE = ""
        self.NroComprobante = self.FechaComprobante = ''
        self.AlicuotaIVA = self.TotalNeto = self.ImporteIVA = None
        self.TotalBonificacionesCalidad = None
        self.TotalPenalizacionesCalidad = None
        self.TotalBonificacionesComerciales = None
        self.TotalDebitosComerciales = None
        self.TotalOtrosImpuestos = None
        self.Total = None
        self.datos = {}

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, url="", proxy="", wrapper="", cacert=None, timeout=30):
        "Establecer la conexión a los servidores de la AFIP"
        # llamo al constructor heredado:
        ok = BaseWS.Conectar(self, cache, url, proxy, wrapper, cacert, timeout)
        if False and ok:        
            # corrijo ubicación del servidor (puerto htttp 80 en el WSDL)
            location = self.client.services['LumService']['ports']['LumEndPoint']['location']
            if location.startswith("http://"):
                print "Corrigiendo WSDL ...", location,
                location = location.replace("http://", "https://").replace(":80", ":443")
                self.client.services['LumService']['ports']['LumEndPoint']['location'] = location
                print location
        return ok

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = []
        if 'errores' in ret:
            errores.extend(ret['errores'])
        if errores:
            self.Errores = ["%(codigo)s: %(descripcion)s" % err['error'][0]
                            for err in errores]
            self.errores = [
                {'codigo': err['error'][0]['codigo'],
                 'descripcion': err['error'][0]['descripcion'].replace("\n", "")
                                .replace("\r", "")} 
                             for err in errores]
            self.ErrCode = ' '.join(self.Errores)
            self.ErrMsg = '\n'.join(self.Errores)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['respuesta']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])
        return True

    @inicializar_y_capturar_excepciones
    def CrearLiquidacion(self, tipo_cbte, pto_vta, nro_cbte, fecha, periodo,
                         iibb_adquirente=None, domicilio_sede=None,
                         inscripcion_registro_publico=None, 
                         datos_adicionales=None, alicuota_iva=None, **kwargs):
        "Inicializa internamente los datos de una liquidación para autorizar"
        # creo el diccionario con los campos generales de la liquidación:
        liq = {'tipoComprobante': tipo_cbte, 'puntoVenta': pto_vta,
                'nroComprobante': nro_cbte, 'fechaComprobante': fecha, 
                'periodo': periodo, 'iibbAdquirente': iibb_adquirente, 
                'domicilioSede': domicilio_sede, 
                'inscripcionRegistroPublico': inscripcion_registro_publico, 
                'datosAdicionales': datos_adicionales, 
                'alicuotaIVA': alicuota_iva, 
              }
        liq["condicionVenta"] = []
        self.solicitud = dict(liquidacion=liq,
                              bonificacionPenalizacion=[],
                              otroImpuesto=[],
                              remito=[]
                             )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCondicionVenta(self, codigo, descripcion=None, **kwargs):
        "Agrego una o más condicion de venta a la liq."
        cond = {'codigo': codigo, 'descripcion': descripcion}
        self.solicitud['liquidacion']['condicionVenta'].append(cond)
        return True
    
    @inicializar_y_capturar_excepciones
    def AgregarTambero(self, cuit, iibb=None, **kwargs):
        "Agrego los datos del productor a la liq."
        tambero = {'cuit': cuit, 'iibb': iibb}
        self.solicitud['tambero'] = tambero
        return True

    @inicializar_y_capturar_excepciones
    def AgregarTambo(self, nro_tambo_interno, nro_renspa,
                     fecha_venc_cert_tuberculosis, fecha_venc_cert_brucelosis,
                     nro_tambo_provincial=None, **kwargs):
        "Agrego los datos del productor a la liq."
        tambo = {'nroTamboInterno': nro_tambo_interno,
                 'nroTamboProvincial': nro_tambo_provincial, 
                 'nroRenspa': nro_renspa, 
                 'ubicacionTambo': {},
                 'fechaVencCertTuberculosis': fecha_venc_cert_tuberculosis,
                 'fechaVencCertBrucelosis': fecha_venc_cert_brucelosis}
        self.solicitud['tambo'] = tambo
        return True

    @inicializar_y_capturar_excepciones
    def AgregarUbicacionTambo(self, latitud, longitud, domicilio,
                              cod_localidad, cod_provincia, codigo_postal,
                              nombre_partido_depto, **kwargs):
        "Agrego los datos del productor a la liq."
        ubic_tambo = {'latitud': latitud, 
                      'longitud': longitud,
                      'domicilio': domicilio,
                      'codLocalidad': cod_localidad,
                      'codProvincia': cod_provincia,
                      'nombrePartidoDepto': nombre_partido_depto,
                      'codigoPostal': codigo_postal}
        self.solicitud['tambo']['ubicacionTambo'] = ubic_tambo
        return True

    @inicializar_y_capturar_excepciones
    def AgregarBalanceLitrosPorcentajesSolidos(self, litros_remitidos, litros_decomisados, 
                                               kg_grasa, kg_proteina, **kwargs):
        "Agrega balance litros y porcentajes sólidos a la liq. (obligatorio)"
        d = {'litrosRemitidos': litros_remitidos,
             'litrosDecomisados': litros_decomisados,
             'kgGrasa': kg_grasa,
             'kgProteina': kg_proteina}
        self.solicitud['balanceLitrosPorcentajesSolidos'] = d

    @inicializar_y_capturar_excepciones
    def AgregarConceptosBasicosMercadoInterno(self, kg_produccion_gb, precio_por_kg_produccion_gb, 
                                              kg_produccion_pr, precio_por_kg_produccion_pr,
                                              kg_crecimiento_gb, precio_por_kg_crecimiento_gb,
                                              kg_crecimiento_pr, precio_por_kg_crecimiento_pr,
                                               **kwargs):
        "Agrega balance litros y porcentajes sólidos (mercado interno)"
        d = {'kgProduccionGB': kg_produccion_gb, 
             'precioPorKgProduccionGB': precio_por_kg_produccion_gb, 
             'kgProduccionPR': kg_produccion_pr, 
             'precioPorKgProduccionPR': precio_por_kg_produccion_pr, 
             'kgCrecimientoGB': kg_crecimiento_gb, 
             'precioPorKgCrecimientoGB': precio_por_kg_crecimiento_gb, 
             'kgCrecimientoPR':kg_crecimiento_pr, 
             'precioPorKgCrecimientoPR': precio_por_kg_crecimiento_pr}
        self.solicitud['conceptosBasicosMercadoInterno'] = d
        return True

    @inicializar_y_capturar_excepciones
    def AgregarConceptosBasicosMercadoExterno(self, kg_produccion_gb, precio_por_kg_produccion_gb, 
                                              kg_produccion_pr, precio_por_kg_produccion_pr,
                                              kg_crecimiento_gb, precio_por_kg_crecimiento_gb,
                                              kg_crecimiento_pr, precio_por_kg_crecimiento_pr,
                                               **kwargs):
        "Agrega balance litros y porcentajes sólidos (mercado externo)"
        d = {'kgProduccionGB': kg_produccion_gb, 
             'precioPorKgProduccionGB': precio_por_kg_produccion_gb, 
             'kgProduccionPR': kg_produccion_pr, 
             'precioPorKgProduccionPR': precio_por_kg_produccion_pr, 
             'kgCrecimientoGB': kg_crecimiento_gb, 
             'precioPorKgCrecimientoGB': precio_por_kg_crecimiento_gb, 
             'kgCrecimientoPR':kg_crecimiento_pr, 
             'precioPorKgCrecimientoPR': precio_por_kg_crecimiento_pr}
        self.solicitud['conceptosBasicosMercadoExterno'] = d

    @inicializar_y_capturar_excepciones
    def AgregarBonificacionPenalizacion(self, codigo, detalle, resultado=None, 
                                        porcentaje=None, importe=None, **kwargs):
        "Agrega la información referente a las bonificaciones o penalizaciones"
        ret = dict(codBonificacionPenalizacion=codigo, detalle=detalle,
                   resultado=resultado, porcentajeAAplicar=porcentaje, 
                   importe=importe)
        self.solicitud['bonificacionPenalizacion'].append(ret)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarOtroImpuesto(self, tipo, base_imponible, alicuota, detalle=None):
        "Agrega la información referente a otros tributos de la liquidación"
        trib = dict(tipo=tipo, baseImponible=base_imponible, alicuota=alicuota,
                    detalle=detalle)
        self.solicitud['otroImpuesto'].append(trib)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRemito(self, nro_remito):
        "Agrega la información referente a los remitos (multiples)"
        self.solicitud['remito'].append(nro_remito)
        return True


    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self):
        "Generar o ajustar una liquidación única y obtener del CAE"
        # limpio los elementos que no correspondan por estar vacios:
        for campo in ["bonificacionPenalizacion", "otroImpuesto"]:
            if campo in self.solicitud and not self.solicitud[campo]:
                del self.solicitud[campo]
        # llamo al webservice:
        ret = self.client.generarLiquidacion(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud=self.solicitud,
                        )
        # analizo la respusta
        ret = ret['respuesta']
        self.__analizar_errores(ret)
        liqs = ret.get('liquidacion', [])
        liq = liqs[0] if liqs else None
        self.AnalizarLiquidacion(liq)
        return True


    def AnalizarLiquidacion(self, liq):
        "Método interno para analizar la respuesta de AFIP"
        # proceso los datos básicos de la liquidación (devuelto por consultar):
        if liq:
            cab = liq['encabezado']
            self.CAE = str(cab['cae'])
            self.FechaComprobante = str(cab['fechaComprobante'])
            self.NroComprobante = cab['nroComprobante']
            tot = liq['resumenTotales']
            self.AlicuotaIVA = tot['alicuotaIVA']
            self.TotalNeto = tot['totalNetoLiquidacion']
            self.ImporteIVA = tot['importeIVA']
            self.TotalBonificacionesCalidad = tot['totalBonificacionesCalidad']
            self.TotalPenalizacionesCalidad = tot['totalPenalizacionesCalidad']
            self.TotalBonificacionesComerciales = tot['totalBonificacionesComerciales']
            self.TotalDebitosComerciales = tot['totalDebitosComerciales']
            self.TotalOtrosImpuestos = tot['totalOtrosImpuestos']
            self.Total = tot['totalLiquidacion']

            # parámetros de salida:
            self.params_out = dict(
                tipo_cbte=liq['encabezado']['tipoComprobante'],
                pto_vta=liq['encabezado']['puntoVenta'],
                nro_cbte=liq['encabezado']['nroComprobante'],
                fecha=str(liq['encabezado']['fechaComprobante']),
                cae=str(liq['encabezado']['cae']),
                domicilio_comprador=liq['encabezado']['domicilioComprador'],
                tambero=dict(
                    cuit=liq['tambero']['cuit'],
                    iibb=liq['tambero']['iibb'],
                    razon_social=liq['tambero']['razonSocial'],
                    situacion_iva=liq['tambero']['situacionIVA'],
                    domicilio_fiscal=liq['tambero']['domicilioFiscal'],
                    provincia=liq['tambero']['provincia'],
                    cod_postal=liq['tambero']['codPostal'],
                    ),
                resumen_kg_remitidos=liq['resumenKgRemitidos'],
                alicuota_iva=liq['resumenTotales']['alicuotaIVA'],
                importe_iva=liq['resumenTotales']['importeIVA'],
                total_neto=liq['resumenTotales']['totalNetoLiquidacion'],
                total_bonificaciones_calidad=liq['resumenTotales']['totalBonificacionesCalidad'],
                total_penalizaciones_calidad=liq['resumenTotales']['totalPenalizacionesCalidad'],
                total_bonificaciones_comerciales=liq['resumenTotales']['totalBonificacionesComerciales'],
                total_debitos_comerciales=liq['resumenTotales']['totalDebitosComerciales'],
                total_otros_impuestos=liq['resumenTotales']['totalOtrosImpuestos'],
                total=liq['resumenTotales']['totalLiquidacion'],
                bonificacion_penalizacion=[],
                remitos=[],
                otro_impuesto=[],               
                pdf=liq.get('pdf'),
                )
            for ret in liq.get('bonificacionPenalizacion', []):
                self.params_out['bonificacion_penalizacion'].append(dict(
                    retencion_codigo=ret['codigo'],
                    retencion_importe=ret['importe'],
                    ))
            for trib in liq.get('otroImpuesto',[]):
                self.params_out['otro_impuesto'].append(dict(
                    tributo_descripcion=trib.get('descripcion', ""),
                    tributo_base_imponible=trib['baseImponible'],
                    tributo_alicuota=trib['alicuota'],
                    tributo_codigo=trib['codigo'],
                    tributo_importe=trib['importe'],
                    ))
            if DEBUG:
                import pprint
                pprint.pprint(self.params_out)
        self.params_out['errores'] = self.errores

    @inicializar_y_capturar_excepciones
    def AgregarAjuste(self, cai, tipo_cbte, pto_vta, nro_cbte, cae_a_ajustar):
        "Agrega comprobante a ajustar"
        cbte = dict(cai=cai, caeAAjustar=cae_a_ajustar, 
                    tipoComprobante=tipo_cbte, puntoVenta=pto_vta, 
                    nroComprobante=nro_cbte)
        self.solicitud['liquidacion']['ajuste']['formularioPapel'].append(cbte)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacion(self, tipo_cbte=None, pto_vta=None, nro_cbte=None,
                                   cae=None, cuit_comprador=None, pdf="liq.pdf"):
        "Consulta una liquidación por No de Comprobante o CAE"
        if cae:
            ret = self.client.consultarLiquidacionPorCae(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud={
                            'cae': cae,
                            'pdf': pdf and True or False,
                            },
                        )
        else:
            ret = self.client.consultarLiquidacionPorNroComprobante(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud={
                            'cuitComprador': cuit_comprador,
                            'puntoVenta': pto_vta,
                            'nroComprobante': nro_cbte,
                            'tipoComprobante': tipo_cbte,
                            'pdf': pdf and True or False,
                            },
                        )
        ret = ret['respuesta']
        self.__analizar_errores(ret)
        if 'liquidacion' in ret:
            liqs = ret.get('liquidacion', [])
            liq = liqs[0] if liqs else None
            self.AnalizarLiquidacion(liq)
            # guardo el PDF si se indico archivo y vino en la respuesta:
            if pdf and 'pdf' in liq:
                open(pdf, "wb").write(liq['pdf'])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarUltimoComprobante(self, tipo_cbte=151, pto_vta=1):
        "Consulta el último No de Comprobante registrado"
        ret = self.client.consultarUltimoNroComprobantePorPtoVta(
                    auth={
                        'token': self.Token, 'sign': self.Sign,
                        'cuit': self.Cuit, },
                    solicitud={
                        'puntoVenta': pto_vta,
                        'tipoComprobante': tipo_cbte},
                    )
        ret = ret['respuesta']
        self.__analizar_errores(ret)
        self.NroComprobante = ret['nroComprobante']
        return True


    def ConsultarProvincias(self, sep="||"):
        "Consulta las provincias habilitadas"
        ret = self.client.consultarProvincias(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('provincia', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarLocalidades(self, cod_provincia, sep="||"):
        "Consulta las localidades habilitadas"
        ret = self.client.consultarLocalidadesPorProvincia(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud={'codProvincia': cod_provincia},
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('localidad', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarCondicionesVenta(self, sep="||"):
        "Retorna un listado de códigos y descripciones de las condiciones de ventas"
        ret = self.client.consultarCondicionesVenta(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('condicionVenta', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarOtrosImpuestos(self, sep="||"):
        "Retorna un listado de tributos con código, descripción y signo."
        ret = self.client.consultarOtrosImpuestos(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('otroImpuesto', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarBonificacionesPenalizaciones(self, sep="||"):
        "Retorna un listado de bonificaciones/penalizaciones con código y descripción"
        ret = self.client.consultarBonificacionesPenalizaciones(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        self.XmlResponse = self.client.xml_response
        array = ret.get('tipo', [])
        if sep is None:
            # sin separador, devuelve un diccionario con clave cod_variadedad
            # y valor: {"descripcion": ds_variedad, "clases": lista_clases}
            # siendo lista_clases = [{'codigo': ..., 'descripcion': ...}]
            return dict([(it['codigo'], {'descripcion': it['descripcion'], 
                                         'subtipo': it['subtipo']}) 
                         for it in array])
        else:
            # con separador, devuelve una lista de strings:
            # || cod.variedad || desc.variedad || desc.clase || cod.clase ||
            ret = []
            for it in array:
                for subtipo in it['subtipo']:
                    ret.append(
                        ("%s %%s %s %%s %s %%s %s %%s %s %%s %s %%s %s" % 
                            (sep, sep, sep, sep, sep, sep, sep)) %
                        (it['codigo'], it['descripcion'], 
                         subtipo['descripcion'], subtipo['codigo'],
                         subtipo['valor'], subtipo['signo']) 
                        )
            return ret

    def ConsultarPuntosVentas(self, sep="||"):
        "Retorna los puntos de ventas autorizados para la utilizacion de WS"
        ret = self.client.consultarPuntosVenta(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('puntoVenta', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]


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


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSLUM.InstallDir = get_install_dir()


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)
    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato in []:
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
        win32com.server.register.UseCommandLine(WSLUM)
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
        CUIT = config.get('WSLUM','CUIT')
        ENTRADA = config.get('WSLUM','ENTRADA')
        SALIDA = config.get('WSLUM','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            WSAA_URL = config.get('WSAA','URL')
        else:
            WSAA_URL = None #wsaa.WSAAURL
        if config.has_option('WSLUM','URL') and not HOMO:
            WSLUM_URL = config.get('WSLUM','URL')
        else:
            WSLUM_URL = WSDL

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
            print "WSLUM_URL:", WSLUM_URL
            print "CACERT", CACERT
            print "WRAPPER", WRAPPER
        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wslum", CERT, PRIVATEKEY, wsdl=WSAA_URL, 
                               proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
        if not ta:
            pass#sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wslum = WSLUM()
        wslum.LanzarExcepciones = True
        wslum.Conectar(url=WSLUM_URL, proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
        wslum.SetTicketAcceso(ta)
        wslum.Cuit = CUIT

        if '--dummy' in sys.argv:
            ret = wslum.Dummy()
            print "AppServerStatus", wslum.AppServerStatus
            print "DbServerStatus", wslum.DbServerStatus
            print "AuthServerStatus", wslum.AuthServerStatus
            ##sys.exit(0)

        if '--autorizar' in sys.argv:

            if '--prueba' in sys.argv:

                # Solicitud 1: Alta de liquidación
                wslum.CrearLiquidacion(tipo_cbte=27, pto_vta=1, nro_cbte=1, 
                        fecha="2015-12-31", periodo="2015/12",
                        iibb_adquirente="123456789012345", 
                        domicilio_sede="Domicilio Administrativo",
                        inscripcion_registro_publico="Nro IGJ", 
                        datos_adicionales="Datos Adicionales Varios", 
                        alicuota_iva=21.00)
                wslum.AgregarCondicionVenta(codigo=1, descripcion=None)
                if False:
                    wslum.AgregarAjuste(cai="10000000000000", 
                            tipo_cbte=0, pto_vta=0, nro_cbte=0, cae_a_ajustar=0)
                
                wslum.AgregarTambero(cuit=11111111111, iibb="123456789012345")
                
                wslum.AgregarTambo(nro_tambo_interno=123456789, 
                        nro_renspa="12.345.6.78901/12",
                        fecha_venc_cert_tuberculosis="2015-01-01", 
                        fecha_venc_cert_brucelosis="2015-01-01",
                        nro_tambo_provincial=100000000)
                wslum.AgregarUbicacionTambo(
                        latitud=-34.62987, longitud=-58.65155, 
                        domicilio="Domicilio Tambo",
                        cod_localidad=10109, cod_provincia=1, 
                        codigo_postal=1234, 
                        nombre_partido_depto='Partido Tambo')

                wslum.AgregarBalanceLitrosPorcentajesSolidos(
                        litros_remitidos=11000, litros_decomisados=1000, 
                        kg_grasa=100.00, kg_proteina=100.00)
                
                wslum.AgregarConceptosBasicosMercadoInterno(
                        kg_produccion_gb=100, precio_por_kg_produccion_gb=5.00, 
                        kg_produccion_pr=100, precio_por_kg_produccion_pr=5.00,
                        kg_crecimiento_gb=0, precio_por_kg_crecimiento_gb=0.00,
                        kg_crecimiento_pr=0, precio_por_kg_crecimiento_pr=0.00)
                
                wslum.AgregarConceptosBasicosMercadoExterno(
                        kg_produccion_gb=0, precio_por_kg_produccion_gb=0.00, 
                        kg_produccion_pr=0, precio_por_kg_produccion_pr=0.00,
                        kg_crecimiento_gb=0, precio_por_kg_crecimiento_gb=0.00,
                        kg_crecimiento_pr=0, precio_por_kg_crecimiento_pr=0.00)
                
                wslum.AgregarBonificacionPenalizacion(codigo=1,
                        detalle="opcional", resultado="400", porcentaje=10.00)
                wslum.AgregarBonificacionPenalizacion(codigo=10,
                        detalle="opcional", resultado="2.5", porcentaje=10.00)
                wslum.AgregarBonificacionPenalizacion(codigo=4,
                        detalle="opcional", resultado="400", porcentaje=10.00)
                wslum.AgregarBonificacionPenalizacion(codigo=5,
                        detalle="opcional", resultado="En Saneamiento", 
                        porcentaje=10.00)

                wslum.AgregarOtroImpuesto(tipo=1, base_imponible=100.00, 
                                          alicuota=10.00, detalle="")
                wslum.AgregarOtroImpuesto(tipo=9, base_imponible=100.00, 
                                          alicuota=10.00, 
                                          detalle="Detalle Otras Percepciones")
                wslum.AgregarOtroImpuesto(tipo=8, base_imponible=100.00, 
                                          alicuota=10.00, detalle="")

                wslum.AgregarRemito(nro_remito="123456789012")
                wslum.AgregarRemito(nro_remito="123456789")

            else:
                # cargar un archivo de texto:
                with open("wslum.json", "r") as f:
                    wslum.solicitud = json.load(f, encoding="utf-8")
                
            
            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo, cargo respuesta:
                wslum.LoadTestXML("tests/xml/wslum_liq_test_pdf_response.xml")
                import json
                with open("wslum.json", "w") as f:
                    json.dump(wslum.solicitud, f, sort_keys=True, indent=4, encoding="utf-8",)

            print "Liquidacion: pto_vta=%s nro_cbte=%s tipo_cbte=%s" % (
                    wslum.solicitud['liquidacion']['puntoVenta'],
                    wslum.solicitud['liquidacion']['nroComprobante'], 
                    wslum.solicitud['liquidacion']['tipoComprobante'],
                    )
            
            if not '--dummy' in sys.argv:        
                print "Autorizando..." 
                ret = wslum.AutorizarLiquidacion()
                    
            if wslum.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslum.Excepcion
                if DEBUG: print >> sys.stderr, wslum.Traceback
            print "Errores:", wslum.Errores
            print "CAE", wslum.CAE
            print "FechaComprobante", wslum.FechaComprobante
            print "NroComprobante", wslum.NroComprobante
            print "TotalNeto", wslum.TotalNeto
            print "AlicuotaIVA", wslum.AlicuotaIVA
            print "ImporteIVA", wslum.ImporteIVA
            print "TotalBonificacionesCalidad", wslum.TotalBonificacionesCalidad
            print "TotalPenalizacionesCalidad", wslum.TotalPenalizacionesCalidad
            print "TotalBonificacionesComerciales", wslum.TotalBonificacionesComerciales
            print "TotalDebitosComerciales", wslum.TotalDebitosComerciales
            print "TotalOtrosImpuestos", wslum.TotalOtrosImpuestos
            print "Total", wslum.Total

            pdf = wslum.GetParametro("pdf")
            if pdf:
                open("liq.pdf", "wb").write(pdf)

            if '--testing' in sys.argv:
                assert wslum.CAE == "75521002437246"

            if DEBUG: 
                pprint.pprint(wslum.params_out)

            if "--guardar" in sys.argv:
                # grabar un archivo de texto (intercambio) con el resultado:
                liq = wslum.params_out.copy()
                if "pdf" in liq:
                    del liq["pdf"]                  # eliminador binario
                with open("wslum_salida.json", "w") as f:
                    json.dump(liq, f, default=str,
                              indent=2, sort_keys=True, encoding="utf-8")
            
        if '--consultar' in sys.argv:
            tipo_cbte = 27
            pto_vta = 1
            nro_cbte = 0
            cuit = None
            try:
                tipo_cbte = sys.argv[sys.argv.index("--consultar") + 1]
                pto_vta = sys.argv[sys.argv.index("--consultar") + 2]
                nro_cbte = sys.argv[sys.argv.index("--consultar") + 3]
                cuit = sys.argv[sys.argv.index("--consultar") + 4]
            except IndexError:
                pass
            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo, cargo prueba:
                wslum.LoadTestXML("tests/xml/wslum_cons_test.xml")
            print "Consultando: tipo_cbte=%s pto_vta=%s nro_cbte=%s" % (tipo_cbte, pto_vta, nro_cbte)
            ret = wslum.ConsultarLiquidacion(tipo_cbte, pto_vta, nro_cbte, 
                                             cuit_comprador=cuit)
            print "CAE", wslum.CAE
            print "Errores:", wslum.Errores

            if DEBUG: 
                pprint.pprint(wslum.params_out)

            if '--mostrar' in sys.argv and pdf:
                wslum.MostrarPDF(archivo=pdf,
                                 imprimir='--imprimir' in sys.argv)

        if '--ult' in sys.argv:
            tipo_cbte = 27
            pto_vta = 1
            try:
                tipo_cbte = sys.argv[sys.argv.index("--ult") + 1]
                pto_vta = sys.argv[sys.argv.index("--ult") + 2]
            except IndexError:
                pass

            print "Consultando ultimo nro_cbte para pto_vta=%s" % pto_vta,
            ret = wslum.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
            if wslum.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslum.Excepcion
                if DEBUG: print >> sys.stderr, wslum.Traceback
            print "Ultimo Nro de Comprobante", wslum.NroComprobante
            print "Errores:", wslum.Errores
            sys.exit(0)

        # Recuperar parámetros:
        
        if '--provincias' in sys.argv:
            ret = wslum.ConsultarProvincias()
            print "\n".join(ret)

        if '--localidades' in sys.argv:
            try:
                cod_provincia = sys.argv[sys.argv.index("--localidades") + 1]
            except:
                cod_provincia = raw_input("Codigo Provincia:")
            ret = wslum.ConsultarLocalidades(cod_provincia)
            print "\n".join(ret)

        if '--bonificaciones_penalizaciones' in sys.argv:
            ret = wslum.ConsultarBonificacionesPenalizaciones()
            print "\n".join(ret)

        if '--otros_impuestos' in sys.argv:
            ret = wslum.ConsultarOtrosImpuestos()
            print "\n".join(ret)

        if '--puntosventa' in sys.argv:
            ret = wslum.ConsultarPuntosVentas()
            print "\n".join(ret)

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
            open("wslum_request.xml", "w").write(wslum.client.xml_request)
            open("wslum_response.xml", "w").write(wslum.client.xml_response)


