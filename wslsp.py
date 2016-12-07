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
Liquidación Sector Pecuario (hacienda/carne) del web service WSLSP de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2016 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

LICENCIA = """
wslsp.py: Interfaz para generar Código de Autorización Electrónica (CAE) para
          Liquidación Sector Pecuario (LspService)
Copyright (C) 2016 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionSectorPecuario

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
  
  --autorizar: Autorizar Liquidación Única (generarLiquidacion)
  --ult: Consulta el último número de orden registrado en AFIP 
         (consultarUltimoComprobanteXPuntoVenta)
  --consultar: Consulta una liquidación registrada en AFIP 
         (consultarLiquidacionXNroComprobante / consultarLiquidacionXCAE)

  --provincias: obtiene el listado de provincias (código/descripción)
  --localidades: obtiene el listado de localidades para una provincia 
  --tributos: obtiene el listado de los tipos de tributos
  --gastos: obtiene el listado de los tipos de gastos
  --puntosventa: obtiene el listado de puntos de venta habilitados

Ver wslsp.ini para parámetros de configuración (URL, certificados, etc.)"
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


WSDL = "https://fwshomo.afip.gov.ar/wslsp/LspService?wsdl"
#WSDL = "https://serviciosjava.afip.gov.ar/wslsp/LspService?wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wslsp.ini"
HOMO = True


class WSLSP(BaseWS):
    "Interfaz para el WebService de Liquidación Única Mensual (lechería)"    
    _public_methods_ = ['Conectar', 'Dummy', 'SetTicketAcceso', 'DebugLog',
                        'AutorizarLiquidacion', 
                        'CrearLiquidacion', 'AgregarFrigorifico',
                        'AgregarEmisor', 'AgregarReceptor', 'AgregarOperador',
                        'AgregarDTE',
                        'AgregarItemDetalle', 'AgregarCompraAsociada',
                        'AgregarGasto', 'AgregarTributo', 'AgregarGuia',
                        'ConsultarLiquidacion', 'ConsultarUltimoComprobante',
                        'LeerDatosLiquidacion',
                        'ConsultarOperaciones',
                        'ConsultarTiposComprobante', 
                        'ConsultarTiposLiquidacion',
                        'ConsultarCategorias', 'ConsultarMotivos',
                        'ConsultarRazas', 'ConsultarCortes',
                        'ConsultarCaracteresParticipante',
                        'ConsultarGastos', 'ConsultarTributos',
                        'ConsultarPuntosVentas', 
                        'ConsultarProvincias', 'ConsultarLocalidades',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'SetParametros', 'SetParametro', 'GetParametro', 
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'InstallDir',
        'CAE', 'NroComprobante', 'FechaComprobante',
        'NroCodigoBarras', 'NroCodigoBarras', 'FechaProcesoAFIP',
        'ImporteBruto', 'ImporteIVASobreBruto', '',
        'ImporteTotalGastos', 'ImporteIVASobreGastos'
        'ImporteTotalTributos' ,'ImporteTotalNeto',
        ]
    _reg_progid_ = "WSLSP"
    _reg_clsid_ = "{9750BBD4-FBC3-4FE7-8DE5-E193667D6813}"

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
        # todo inicializar "propiedades"
        self.datos = {}

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, url="", proxy="", wrapper="", cacert=None, timeout=30):
        "Establecer la conexión a los servidores de la AFIP"
        # llamo al constructor heredado:
        ok = BaseWS.Conectar(self, cache, url, proxy, wrapper, cacert, timeout)
        if False and ok:        
            # corrijo ubicación del servidor (puerto htttp 80 en el WSDL)
            location = self.client.services['LspService']['ports']['LumEndPoint']['location']
            if location.startswith("http://"):
                print "Corrigiendo WSDL ...", location,
                location = location.replace("http://", "https://").replace(":80", ":443")
                self.client.services['LspService']['ports']['LspEndPoint']['location'] = location
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
    def CrearLiquidacion(self, cod_operacion, fecha_cbte, fecha_op, cod_motivo,
                         cod_localidad_procedencia, cod_provincia_procedencia, 
                         cod_localidad_destino, cod_provincia_destino,
                         lugar_realizacion=None,
                         fecha_recepcion=None, fecha_faena=None, 
                         datos_adicionales=None, **kwargs):
        "Inicializa internamente los datos de una liquidación para autorizar"
        # creo el diccionario con los campos generales de la liquidación:
        liq = { 'fechaComprobante': fecha_cbte, 'fechaOperacion': fecha_op, 
                'lugarRealizacion': unicode, 
                'codMotivo': int, 
                'codLocalidadProcedencia': int, 
                'codProvinciaProcedencia': int, 
                'codLocalidadDestino': int, 
                'codProvinciaDestino': int, 
                'fechaRecepcion': datetime.date, 
                'fechaFaena': datetime.date, 
                'frigorifico': {'cuit': long, 'nroPlanta': int}

              }
        self.solicitud = dict(codOperacion=cod_operacion,
                              emisor={}, receptor={},
                              datosLiquidacio=liq,
                              itemDetalleLiquidacion=[],
                              guia=[], dte=[],
                              tributo=[], gasto=[],
                              datosAdicionales=datos_adicionales, 
                             )
        return True
    
    @inicializar_y_capturar_excepciones
    def AgregarFrigorifico(self, cuit, nro_planta):
        "Agrego el frigorifico a la liquidacíon (opcional)."
        frig = {'cuit': cuit, 'descripcion': descripcion}
        self.solicitud['datosLiquidacio']['frigorifico']  = frig
        return True

    @inicializar_y_capturar_excepciones
    def AgregarEmisor(self, tipo_cbte, pto_vta, nro_cbte, cod_caracter,
                      fecha_inicio_act,
                      iibb=None, nro_ruca=None, nro_renspa=None, **kwargs):
        "Agrego los datos del emisor a la liq."
        d = {'tipoComprobante': tipo_cbte, 'puntoVenta': pto_vta,
             'nroComprobante': nro_cbte, 
             'codCaracter': cod_caracter,
             'fechaInicioActividades': fecha_inicio_act,
             'iibb': iibb,
             'nroRUCA': nro_ruca,
             'nroRenspa': nro_renspa,}
        self.solicitud['emisor'].update(d)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarReceptor(self, cod_caracter, **kwargs):
        "Agrego los datos del receptor a la liq."
        d = {'codCaracter': cod_caracter}
        self.solicitud['receptor'].update(d)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarOperador(self, cuit, iibb=None, nro_ruca=None, nro_renspa=None, 
                        cuit_autorizado=None, **kwargs):
        "Agrego los datos del operador a la liq."
        d = {'cuit': cuit, 
             'iibb': iibb,
             'nroRUCA': nro_ruca,
             'nroRenspa': nro_renspa,
             'cuitAutorizado': cuit_autorizado}
        self.solicitud['receptor']['operador'] = d
        return True

    @inicializar_y_capturar_excepciones
    def AgregarItemDetalle(self, cuit_cliente, cod_categoria, tipo_liquidacion,
                           cantidad, precio_unitario, alicuota_iva, cod_raza,
                           cantidad_cabezas=None, nro_tropa=None, 
                           cod_corte=None, cantidad_kg_vivo=None,
                           precio_recupero=None,
                           **kwargs):
        "Agrega el detalle de item de la liquidación"
        d = {'cuitCliente': cuit_cliente,
             'codCategoria': cod_categoria,
             'tipoLiquidacion': tipo_liquidacion, 
             'cantidad': cantidad,
             'precioUnitario': precio_unitario, 
             'alicuotaIVA': alicuota_iva, 
             'cantidadCabezas': cantidad_cabezas, 
             'codRaza': cod_raza, 
             'nroTropa': nro_tropa, 
             'codCorte': cod_corte, 
             'cantidadKgVivo': cantidad_kg_vivo, 
             'precioRecupero': precio_recupero,
             'liquidacionCompraAsociada': [],
            }
        self.solicitud['itemDetalleLiquidacion'].append(d)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCompraAsociada(self, tipo_cbte, pto_vta, nro_cbte, cant_asoc):
        "Agrega la información referente a la liquidación compra asociada"
        d = {'tipoComprobante': tipo_cbte, 
             'puntoVenta': pto_vta,
             'nroComprobante': nro_cbte, 
             'cantidadAsociada': cant_asoc}
        item_liq = self.solicitud['itemDetalleLiquidacion'][-1]
        item_liq['liquidacionCompraAsociada'].append(item_liq)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarGasto(self, cod_gasto, descripcion=None, base_imponible=None,
                     alicuota=None, importe=None, alicuota_iva=None):
        "Agrega la información referente a los gastos de la liquidación"
        gasto = {'codGasto': cod_gasto, 'descripcion': descripcion, 
                 'baseImponible': base_imponible, 'alicuota': alicuota, 
                 'importe': importe, 'alicuotaIVA': alicuota_iva}
        self.solicitud['gasto'].append(gasto)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarTributo(self, cod_tributo, descripcion=None,     
                       base_imponible=None, alicuota=None, importe=None):
        "Agrega la información referente a los tributos de la liquidación"
        trib = {'codTributo': cod_tributo, 'descripcion': descripcion, 
                'baseImponible': base_imponible, 'alicuota': alicuota, 
                'importe': importe}
        self.solicitud['tributo'].append(trib)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDTE(self, nro_dte, nro_renspa):
        "Agrega la información referente a DTE (multiples)"
        d = {"nroDTE": nro_dte, "nroRenspa": nro_renspa}
        self.solicitud['guia'].append(d)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarGuia(self, nro_guia):
        "Agrega la información referente a las guías (multiples)"
        self.solicitud['guia'].append({"nroGuia": nro_guia})
        return True


    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self):
        "Generar o ajustar una liquidación única y obtener del CAE"
        # limpio los elementos que no correspondan por estar vacios:
        for campo in ["guia", "dte", "gasto", "tributo"]:
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
            cab = liq['cabecera']
            self.CAE = str(cab['cae'])
            self.FechaComprobante = liq['fechaComprobante']
            self.NroComprobante = liq['emisor']['nroComprobante']
            tot = liq['resumenTotales']
            self.ImporteTotalNeto = tot['importeTotalNeto']
            self.ImporteIVASobreBruto = tot['importeIVASobreBruto']
            self.ImporteIVASobreGasto = tot['importeIVASobreGastos']

            # parámetros de salida:
            self.params_out = dict(
                tipo_cbte=liq['emisor']['tipoComprobante'],
                pto_vta=liq['emisor']['puntoVenta'],
                nro_cbte=liq['emisor']['nroComprobante'],
                fecha=liq['fechaComprobante'],
                cae=str(liq['cabecera']['cae']),
                emisor=dict(
                    ),
                importe_iva=liq['resumenTotales']['importeIVASobreBruto'],
                total_neto=liq['resumenTotales']['importeTotalNeto'],
                total_tributos=liq['resumenTotales']['importeTotalTributos'],
                gasto=[],
                guia=[],
                tributo=[],
                )
            for ret in liq.get('gasto', []):
                self.params_out['gasto'].append(dict(
                    cod_gasto=ret['codGasto'],
                    importe=ret['importe'],
                    ))
            for trib in liq.get('tributo',[]):
                self.params_out['otro_impuesto'].append(dict(
                    descripcion=trib.get('descripcion', ""),
                    base_imponible=trib['baseImponible'],
                    alicuota=trib['alicuota'],
                    codigo=trib['codTributo'],
                    importe=trib['importe'],
                    ))
            if DEBUG:
                import pprint
                pprint.pprint(self.params_out)
        self.params_out['errores'] = self.errores


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

    def ConsultarOperaciones(self, sep="||"):
        "Retorna un listado de código y descripción de operaciones permitidas"
        ret = self.client.consultarOperaciones(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('operacion', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarTributos(self, sep="||"):
        "Retorna un listado de tributos con código, descripción y signo."
        ret = self.client.consultarTributos(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('tributo', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarGastos(self, sep="||"):
        "Retorna un listado de gastos con código y descripción"
        ret = self.client.consultarGastos(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        self.XmlResponse = self.client.xml_response
        array = ret.get('gasto', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

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
            return dict([(it['codigo'], it.get('descripcion', '')) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it.get('descripcion', '')) for it in array]


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
INSTALL_DIR = WSLSP.InstallDir = get_install_dir()


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
        win32com.server.register.UseCommandLine(WSLSP)
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
        CUIT = config.get('WSLSP','CUIT')
        ENTRADA = config.get('WSLSP','ENTRADA')
        SALIDA = config.get('WSLSP','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            WSAA_URL = config.get('WSAA','URL')
        else:
            WSAA_URL = None #wsaa.WSAAURL
        if config.has_option('WSLSP','URL') and not HOMO:
            WSLSP_URL = config.get('WSLSP','URL')
        else:
            WSLSP_URL = WSDL

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
            print "WSLSP_URL:", WSLSP_URL
            print "CACERT", CACERT
            print "WRAPPER", WRAPPER
        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wslsp", CERT, PRIVATEKEY, wsdl=WSAA_URL, 
                               proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
        if not ta:
            pass#sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wslsp = WSLSP()
        wslsp.LanzarExcepciones = True
        wslsp.Conectar(url=WSLSP_URL, proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
        wslsp.SetTicketAcceso(ta)
        wslsp.Cuit = CUIT

        if '--dummy' in sys.argv:
            ret = wslsp.Dummy()
            print "AppServerStatus", wslsp.AppServerStatus
            print "DbServerStatus", wslsp.DbServerStatus
            print "AuthServerStatus", wslsp.AuthServerStatus
            ##sys.exit(0)

        if '--autorizar' in sys.argv:

            if '--prueba' in sys.argv:
                print wslsp.client.help("generarLiquidacion")

                # Solicitud 1: Cuenta de Venta y Líquido Producto - Hacienda
                wslsp.CrearLiquidacion(
                        cod_operacion=1, 
                        fecha_cbte='2016-11-12', 
                        fecha_op='2016-11-11', 
                        cod_motivo=6, 
                        cod_localidad_procedencia=1, 
                        cod_provincia_procedencia=8274, 
                        cod_localidad_destino=8274, 
                        cod_provincia_destino=1,
                        lugar_realizacion='CORONEL SUAREZ',
                        fecha_recepcion=None, fecha_faena=None, 
                        datos_adicionales=None)
                if False:
                    wslsp.AgregarFrigorifico(cuit, nro_planta)
                wslsp.AgregarEmisor(
                        tipo_cbte=180, pto_vta=3000, nro_cbte=52, 
                        cod_caracter=5, fecha_inicio_act='2016-01-01',
                        iibb='123456789', nro_ruca=305, nro_renspa=None)
                wslsp.AgregarReceptor(cod_caracter=3)
                wslsp.AgregarOperador(cuit=12222222222, iibb=3456, 
                                      nro_renspa='22.123.1.12345/A4')
                wslsp.AgregarItemDetalle(
                        cuit_cliente="12345688888",
                        cod_categoria=51020102,
                        tipo_liquidacion=1,
                        cantidad=2,
                        precio_unitario=10.0,
                        alicuota_iva=10.5,
                        cod_raza=1,
                        )
                wslsp.AgregarCompraAsociada(tipo_cbte=185, pto_vta=3000,
                                            nro_cbte=33, cant_asoc=2)
                wslsp.AgregarGuia(nro_guia=1)
                wslsp.AgregarDTE(nro_dte="418-1",
                                 nro_renspa='22.123.1.12345/4500')
                wslsp.AgregarGasto(cod_gasto=16, base_imponible=230520.60,
                                   alicuota=3, alicuota_iva=10.5)
                wslsp.AgregarTributo(cod_tributo=5, base_imponible=230520.60,
                                     alicuota=2.5)
                wslsp.AgregarTributo(cod_tributo=3, importe=397)
            else:
                # cargar un archivo de texto:
                with open("wslsp.json", "r") as f:
                    wslsp.solicitud = json.load(f, encoding="utf-8")
                
            
            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo, cargo respuesta:
                wslsp.LoadTestXML("tests/xml/wslsp_liq_test_response.xml")
                import json
                with open("wslsp.json", "w") as f:
                    json.dump(wslsp.solicitud, f, sort_keys=True, indent=4, encoding="utf-8",)

            print "Liquidacion: pto_vta=%s nro_cbte=%s tipo_cbte=%s" % (
                    wslsp.solicitud['emisor']['puntoVenta'],
                    wslsp.solicitud['emisor']['nroComprobante'], 
                    wslsp.solicitud['emisor']['tipoComprobante'],
                    )
            
            if not '--dummy' in sys.argv:        
                print "Autorizando..." 
                ret = wslsp.AutorizarLiquidacion()
                    
            if wslsp.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslsp.Excepcion
                if DEBUG: print >> sys.stderr, wslsp.Traceback
            print "Errores:", wslsp.Errores
            print "CAE", wslsp.CAE
            print "FechaComprobante", wslsp.FechaComprobante
            print "NroComprobante", wslsp.NroComprobante
            print "ImporteTotalNeto", wslsp.ImporteTotalNeto

            pdf = wslsp.GetParametro("pdf")
            if pdf:
                open("liq.pdf", "wb").write(pdf)

            if '--testing' in sys.argv:
                assert wslsp.CAE == "96465021584954"

            if DEBUG: 
                pprint.pprint(wslsp.params_out)

            if "--guardar" in sys.argv:
                # cargar un archivo de texto:
                with open("wslsp_salida.json", "w") as f:
                    json.dump(wslsp.solicitud, f, 
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
                wslsp.LoadTestXML("tests/xml/wslsp_cons_test.xml")
            print "Consultando: tipo_cbte=%s pto_vta=%s nro_cbte=%s" % (tipo_cbte, pto_vta, nro_cbte)
            ret = wslsp.ConsultarLiquidacion(tipo_cbte, pto_vta, nro_cbte, 
                                             cuit_comprador=cuit)
            print "CAE", wslsp.CAE
            print "Errores:", wslsp.Errores

            if DEBUG: 
                pprint.pprint(wslsp.params_out)

            if '--mostrar' in sys.argv and pdf:
                wslsp.MostrarPDF(archivo=pdf,
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
            ret = wslsp.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
            if wslsp.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wslsp.Excepcion
                if DEBUG: print >> sys.stderr, wslsp.Traceback
            print "Ultimo Nro de Comprobante", wslsp.NroComprobante
            print "Errores:", wslsp.Errores
            sys.exit(0)

        # Recuperar parámetros:
        
        if '--provincias' in sys.argv:
            ret = wslsp.ConsultarProvincias()
            print "\n".join(ret)

        if '--localidades' in sys.argv:
            try:
                cod_provincia = sys.argv[sys.argv.index("--localidades") + 1]
            except:
                cod_provincia = raw_input("Codigo Provincia:")
            ret = wslsp.ConsultarLocalidades(cod_provincia)
            print "\n".join(ret)

        if '--operaciones' in sys.argv:
            ret = wslsp.ConsultarOperaciones()
            print "\n".join(ret)

        if '--tributos' in sys.argv:
            ret = wslsp.ConsultarTributos()
            print "\n".join(ret)

        if '--puntosventa' in sys.argv:
            ret = wslsp.ConsultarPuntosVentas()
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
            open("wslsp_request.xml", "w").write(wslsp.client.xml_request)
            open("wslsp_response.xml", "w").write(wslsp.client.xml_response)


