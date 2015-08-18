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

"Módulo para Consulta de Operaciones Cambiarias"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.09a"

import os
import socket
import sys
import traceback
import pysimplesoap.client
from pysimplesoap.client import SoapClient, SoapFault, parse_proxy, \
                                set_http_wrapper
from pysimplesoap.simplexml import SimpleXMLElement
from cStringIO import StringIO

HOMO = True

if HOMO:
    WSDL = "https://fwshomo.afip.gov.ar/wscoc/COCService"
    LOCATION = "https://fwshomo.afip.gob.ar:443/wscoc2/COCService"
else:
    WSDL = "https://serviciosjava.afip.gob.ar/wscoc2/COCService"
    LOCATION = "https://serviciosjava.afip.gob.ar:443/wscoc2/COCService"
    
def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Errores = []
            self.ErroresFormato = []
            self.Traceback = self.Excepcion = ""
            self.ErrCode = ""
            self.ErrMsg = ""
            self.CodigoSolicitud = self.FechaSolicitud = None
            self.COC = self.FechaEmisionCOC = self.CodigoDestino = None
            self.EstadoSolicitud = self.FechaEstado = None
            self.CUITComprador = self.DenominacionComprador = None
            self.CodigoMoneda = self.CotizacionMoneda = self.MontoPesos = None
            self.CUITRepresentante = self.DenominacionRepresentante = None
            self.DJAI = self.CodigoExcepcionDJAI = self.EstadoDJAI = None
            self.DJAS = self.CodigoExcepcionDJAS = self.EstadoDJAS = None
            self.MontoFOB = self.CodigoMoneda = None
            # iniciaalizo estructuras internas persistentes
            self.__detalles_solicitudes = []
            self.__detalles_cuit = []

            # llamo a la función (sin reintentos)
            return func(self, *args, **kwargs)

        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            if self.LanzarExcepciones:
                raise
        except Exception, e:
            ex = traceback.format_exception(sys.exc_type, sys.exc_value,
                                            sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = u"%s" % (e)
            if self.LanzarExcepciones:
                raise
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class WSCOC:
    "Interfaz para el WebService de Consulta de Operaciones Cambiarias"
    _public_methods_ = ['GenerarSolicitudCompraDivisa',
                        'GenerarSolicitudCompraDivisaTurExt',
                        'InformarSolicitudCompraDivisa',
                        'ConsultarCUIT',
                        'ConsultarCOC',
                        'AnularCOC',
                        'ConsultarSolicitudCompraDivisa',
                        'ConsultarSolicitudesCompraDivisas',
                        'ConsultarDestinosCompra',
                        'ConsultarTiposReferencia',
                        'ConsultarMonedas',
                        'ConsultarTiposDocumento',
                        'ConsultarTiposEstadoSolicitud',
                        'ConsultarMotivosExcepcionDJAI',
                        'ConsultarDestinosCompraDJAI',
                        'ConsultarMotivosExcepcionDJAS',
                        'ConsultarDestinosCompraDJAS',
                        'ConsultarDestinosCompraTipoReferencia',
                        'LeerSolicitudConsultada', 'LeerCUITConsultado',
                        'ConsultarDJAI', 'ConsultarDJAS', 'ConsultarReferencia',
                        'LeerError', 'LeerErrorFormato', 'LeerInconsistencia',
                        'LoadTestXML',
                        'AnalizarXml', 'ObtenerTagXml',
                        'Dummy', 'Conectar', 'DebugLog']
    _public_attrs_ = ['Token', 'Sign', 'Cuit',
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
        'XmlRequest', 'XmlResponse', 'Version', 'InstallDir', 
        'Resultado', 'Inconsistencias', 'ErrCode', 'ErrMsg',
        'CodigoSolicitud', 'FechaSolicitud', 'EstadoSolicitud', 'FechaEstado',
        'COC', 'FechaEmisionCOC', 'CodigoDestino',
        'CUITComprador', 'DenominacionComprador',
        'CodigoMoneda', 'CotizacionMoneda', 'MontoPesos',
        'CUITRepresentante', 'DenominacionRepresentante',
        'TipoDoc', 'NumeroDoc', 'CUITConsultada', 'DenominacionConsultada',
		'DJAI', 'CodigoExcepcionDJAI', 'DJAS', 'CodigoExcepcionDJAS',
        'MontoFOB', 'EstadoDJAI', 'EstadoDJAS', 'Estado', 'Tipo', 'Codigo',
        'ErroresFormato', 'Errores', 'Traceback', 'Excepcion', 'LanzarExcepciones',
        ]

    _reg_progid_ = "WSCOC"
    _reg_clsid_ = "{B30406CE-326A-46D9-B807-B7916E3F1B96}"

    Version = "%s %s %s" % (__version__, HOMO and 'Homologación' or '', pysimplesoap.client.__file__)
    LanzarExcepciones = False

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = None
        self.DbServerStatus = None
        self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.__analizar_solicitud({})
        self.__analizar_inconsistencias({})
        self.__analizar_errores({})
        self.__detalles_solicitudes = None
        self.__detalles_cuit = None
        self.client = None
        self.ErrCode = self.ErrMsg = self.Traceback = self.Excepcion = ""
        self.EmisionTipo = ''
        self.Reprocesar = self.Reproceso = ''  # no implementado
        self.Log = None
        self.InstallDir = INSTALL_DIR

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.Errores = []
        self.ErroresFormato = []
        if 'arrayErrores' in ret:
            errores = ret['arrayErrores']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['codigoDescripcion']['codigo'],
                    error['codigoDescripcion']['descripcion'],
                    ))
        if 'arrayErroresFormato' in ret:
            errores = ret['arrayErroresFormato']
            for error in errores:
                self.ErroresFormato.append("%s: %s" % (
                    error['codigoDescripcionString']['codigo'],
                    error['codigoDescripcionString']['descripcion'],
                    ))

    def __analizar_solicitud(self, det):
        "Analiza y extrae los datos de una solicitud"
        self.CodigoSolicitud = det.get("codigoSolicitud")
        self.FechaSolicitud = det.get("fechaSolicitud")
        self.COC = str(det.get("coc"))
        self.FechaEmisionCOC = det.get("fechaEmisionCOC")
        self.EstadoSolicitud = det.get("estadoSolicitud")
        self.FechaEstado = det.get("fechaEstado")
        self.CUITComprador = str(det.get("detalleCUITComprador", 
                                     {}).get("cuit", ""))
        self.DenominacionComprador = det.get("detalleCUITComprador", 
                                             {}).get("denominacion")
        self.CodigoMoneda = det.get("codigoMoneda")
        self.CotizacionMoneda = det.get("cotizacionMoneda")
        self.MontoPesos = det.get("montoPesos")
        self.CUITRepresentante = str(det.get("DetalleCUITRepresentante", 
                                         {}).get("cuit", ""))
        self.DenominacionRepresentante = det.get("DetalleCUITRepresentante", 
                                                 {}).get("denominacion")
        self.CodigoDestino = det.get("codigoDestino")
        self.DJAI = det.get("djai")
        self.CodigoExcepcionDJAI = det.get("codigoExcepcionDJAI")
        self.DJAS = det.get("djas")
        self.CodigoExcepcionDJAS = det.get("codigoExcepcionDJAS")
        ref = det.get("referencia")
        if ref:
            self.Tipo = ref['tipo']
            self.Codigo = ref['codigo']

    def __analizar_inconsistencias(self, ret):
        "Comprueba y extrae (formatea) las inconsistencias"
        self.Inconsistencias = []
        if 'arrayInconsistencias' in ret:
            inconsistencias = ret['arrayInconsistencias']
            for inconsistencia in inconsistencias:
                self.Inconsistencias.append("%s: %s" % (
                    inconsistencia['codigoDescripcion']['codigo'],
                    inconsistencia['codigoDescripcion']['descripcion'],
                    ))

    def __log(self, msg):
        if not isinstance(msg, unicode):
            msg = unicode(msg, 'utf8', 'ignore')
        if not self.Log:
            self.Log = StringIO()
        self.Log.write(msg)
        self.Log.write('\n\r')
    
    def DebugLog(self):
        "Devolver y limpiar la bitácora de depuración"
        if self.Log:
            msg = self.Log.getvalue()
            # limpiar log
            self.Log.close()
            self.Log = None
        else:
            msg = u''
        return msg    

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30):
        # cliente soap del web service
        if timeout:
            self.__log("Estableciendo timeout=%s" % (timeout, ))
            socket.setdefaulttimeout(timeout)
        if wrapper:
            Http = set_http_wrapper(wrapper)
            self.Version = WSCOC.Version + " " + Http._wrapper_version
        proxy_dict = parse_proxy(proxy)
        location = LOCATION
        if HOMO or not wsdl:
            wsdl = WSDL
        elif not wsdl.endswith("?wsdl") and wsdl.startswith("http"):
            location = wsdl
            wsdl += "?wsdl"
        elif wsdl.endswith("?wsdl"):
            location = wsdl[:-5]
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        self.__log("Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict))
        self.client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            ns="coc",
            cacert=cacert,
            soap_ns="soapenv",
            soap_server="jbossas6",
            trace = "--trace" in sys.argv)
        # corrijo ubicación del servidor (http en el WSDL)
        self.client.services['COCService']['ports']['COCServiceHttpSoap11Endpoint']['location'] = location
        self.__log("Corrigiendo location=%s" % (location, ))
        return True

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.dummy()
        ret = result['dummyReturn']
        self.AppServerStatus = ret['appserver']
        self.DbServerStatus = ret['dbserver']
        self.AuthServerStatus = ret['authserver']
        return True
    
    @inicializar_y_capturar_excepciones
    def GenerarSolicitudCompraDivisa(self, cuit_comprador, codigo_moneda,
                                     cotizacion_moneda, monto_pesos,
                                    cuit_representante, codigo_destino,
									djai=None, codigo_excepcion_djai=None,
                                    djas=None, codigo_excepcion_djas=None,
                                    tipo=None, codigo=None,
                                    ):
        "Generar una Solicitud de operación cambiaria"
        if tipo and codigo:
            referencia = {'tipo': tipo, 'codigo': codigo}
        else:
            referencia = None
        res = self.client.generarSolicitudCompraDivisa(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            cuitComprador=cuit_comprador,
            codigoMoneda=codigo_moneda,
            cotizacionMoneda=cotizacion_moneda,
            montoPesos=monto_pesos,
            cuitRepresentante=cuit_representante,
            codigoDestino=codigo_destino,
			djai=djai, codigoExcepcionDJAI=codigo_excepcion_djai,
            djas=djas, codigoExcepcionDJAS=codigo_excepcion_djas,
            referencia=referencia,
            )

        self.Resultado = ""
        ret = res.get('generarSolicitudCompraDivisaReturn', {})
        self.Resultado = ret.get('resultado')
        det = ret.get('detalleSolicitud', {})
        self.__analizar_solicitud(det)
        self.__analizar_inconsistencias(det)
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def GenerarSolicitudCompraDivisaTurExt(self, tipo_doc, numero_doc, apellido_nombre,
                                    codigo_moneda, cotizacion_moneda, monto_pesos,
                                    cuit_representante, codigo_destino,
                                    ):
        "Generar una Solicitud de operación cambiaria"
        res = self.client.generarSolicitudCompraDivisaTurExt(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            detalleTurExtComprador={
                'tipoNumeroDoc': {'tipoDoc': tipo_doc, 'numeroDoc': numero_doc},
                'apellidoNombre': apellido_nombre},
            codigoMoneda=codigo_moneda,
            cotizacionMoneda=cotizacion_moneda,
            montoPesos=monto_pesos,
            cuitRepresentante=cuit_representante,
            codigoDestino=codigo_destino,
            )

        self.Resultado = ""
        ret = res.get('generarSolicitudCompraDivisaTurExtReturn', {})
        self.Resultado = ret.get('resultado')
        det = ret.get('detalleSolicitud', {})
        self.__analizar_solicitud(det)
        self.__analizar_inconsistencias(det)
        self.__analizar_errores(ret)
        
        return True

    @inicializar_y_capturar_excepciones
    def InformarSolicitudCompraDivisa(self, codigo_solicitud, nuevo_estado):
        "Informar la aceptación o desistir una solicitud generada con anterioridad"

        res = self.client.informarSolicitudCompraDivisa(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            codigoSolicitud=codigo_solicitud,
            nuevoEstado=nuevo_estado,
        )

        self.Resultado = ""
        ret = res.get('informarSolicitudCompraDivisaReturn', {})
        self.Resultado = ret.get('resultado')
        self.__analizar_solicitud(ret)
        self.__analizar_errores(ret)
        return True


    @inicializar_y_capturar_excepciones
    def ConsultarCUIT(self, numero_doc, tipo_doc=80, sep="|"):
        "Consultar la CUIT, CDI ó CUIL, según corresponda, para un determinado tipo y número de documento."
        
        res = self.client.consultarCUIT(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            tipoNumeroDoc={'tipoDoc': tipo_doc, 'numeroDoc': numero_doc}
        )

        self.__detalles_cuit = []
        
        if 'consultarCUITReturn' in res:
            ret = res['consultarCUITReturn']
            self.__analizar_errores(ret)
            if 'tipoNumeroDoc' in ret:
                self.TipoDoc = ret['tipoNumeroDoc']['tipoDoc']
                self.NumeroDoc = ret['tipoNumeroDoc']['numeroDoc']
                for detalle in ret.get('arrayDetallesCUIT', []):
                    # agrego el detalle para consultarlo luego (LeerCUITConsultado)
                    det = detalle['detalleCUIT']
                    self.__detalles_cuit.append(det)
                # devuelvo una lista de cuit/denominación
                return [(u"%(cuit)s\t%(denominacion)s" % 
                            d['detalleCUIT']).replace("\t", sep)
                        for d in ret.get('arrayDetallesCUIT', [])]
            else:
                return []
        else:
            self.TipoDoc = None
            self.NumeroDoc = None
            return [""]

    def LeerCUITConsultado(self):
        "Recorro los CUIT devueltos por ConsultarCUIT"
        
        if self.__detalles_cuit:
            # extraigo el primer item
            det = self.__detalles_cuit.pop(0)
            self.CUITConsultada = str(det['cuit'])
            self.DenominacionConsultada = str(det['denominacion'])
            return True
        else:
            return False

    @inicializar_y_capturar_excepciones
    def ConsultarCOC(self, coc):
        "Obtener los datos de un COC existente"

        res = self.client.consultarCOC(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            coc=coc,
        )
        ret = res.get('consultarCOCReturn', {})
        det = ret.get('detalleSolicitud', {})
        self.__analizar_solicitud(det)
        self.__analizar_inconsistencias(det)
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def AnularCOC(self, coc, cuit_comprador):
        "Anular COC existente (estado CO 24hs)"
        res = self.client.anularCOC(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            coc=coc,
            cuitComprador=cuit_comprador,
            )
        
        ret = res.get('anularCOCReturn', {})
        self.__analizar_solicitud(ret)
        self.__analizar_inconsistencias(ret)
        self.__analizar_errores(ret)
        
        return True


    @inicializar_y_capturar_excepciones
    def ConsultarSolicitudCompraDivisa(self, codigo_solicitud):
        "Consultar una Solicitud de Operación Cambiaria"
        res = self.client.consultarSolicitudCompraDivisa(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            codigoSolicitud=codigo_solicitud,
            )

        ret = res.get('consultarSolicitudCompraDivisaReturn', {})
        det = ret.get('detalleSolicitud', {})
        self.__analizar_solicitud(det)
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def ConsultarSolicitudesCompraDivisas(self, cuit_comprador, 
                                          estado_solicitud,
                                          fecha_emision_desde,
                                          fecha_emision_hasta,
                                        ):
        "Consultar Solicitudes de operaciones cambiarias"
        res = self.client.consultarSolicitudesCompraDivisas(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            cuitComprador=cuit_comprador,
            estadoSolicitud=estado_solicitud,
            fechaEmisionDesde=fecha_emision_desde,
            fechaEmisionHasta=fecha_emision_hasta,
            )

        self.__analizar_errores(res)
        
        ret = res.get('consultarSolicitudesCompraDivisasReturn', {})
        solicitudes = []                    # códigos a devolver
        self.__detalles_solicitudes = []    # diccionario para recorrerlo luego
        for array in ret.get('arrayDetallesSolicitudes', []):
            det = array['detalleSolicitudes']
            # guardo el detalle para procesarlo luego (LeerSolicitudConsultada)
            self.__detalles_solicitudes.append(det) 
            # devuelvo solo el código de solicitud
            solicitudes.append(det.get("codigoSolicitud"))            
        return solicitudes


    def LeerSolicitudConsultada(self):
        "Proceso de a una solicitud los detalles devueltos por ConsultarSolicitudesCompraDivisas"
        if self.__detalles_solicitudes:
            # extraigo el primer item
            det = self.__detalles_solicitudes.pop(0)
            self.__analizar_solicitud(det)
            self.__analizar_errores(det)
            self.__analizar_inconsistencias(det)
            return True
        else:
            return False

    @inicializar_y_capturar_excepciones
    def ConsultarDJAI(self, djai, cuit):
        "Consultar Declaración Jurada Anticipada de Importación"
        res = self.client.consultarDJAI(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            djai=djai, cuit=cuit,
            )

        ret = res.get('consultarDJAIReturn', {})
        self.__analizar_errores(ret)
        self.DJAI = ret.get('djai')
        self.MontoFOB = ret.get('montoFOB')
        self.CodigoMoneda = ret.get('codigoMoneda')
        self.EstadoDJAI = ret.get('estadoDJAI')
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarDJAS(self, djas, cuit):
        "Consultar Declaración Jurada Anticipada de Servicios"
        res = self.client.consultarDJAS(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            djas=djas, cuit=cuit,
            )

        ret = res.get('consultarDJASReturn', {})
        self.__analizar_errores(ret)
        self.DJAS = ret.get('djas')
        self.MontoFOB = ret.get('montoFOB')
        self.CodigoMoneda = ret.get('codigoMoneda')
        self.EstadoDJAS = ret.get('estadoDJAS')
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarReferencia(self, tipo, codigo):
        "Consultar una determinada referencia según su tipo (1: DJAI, 2: DJAS, 3: DJAT)"
        res = self.client.consultarReferencia(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            referencia={'tipo': tipo, 'codigo': codigo},
            )

        ret = res.get('consultarReferenciaReturn', {})
        self.__analizar_errores(ret)
        #self.Codigo = ret.get('codigo')
        self.MontoFOB = ret.get('monto')
        self.CodigoMoneda = ret.get('codigoMoneda')
        self.Estado = ret.get('estado')
        return True
        
    @inicializar_y_capturar_excepciones
    def ConsultarMonedas(self, sep="|"):
        "Este método retorna el universo de Monedas disponibles en el presente WS, indicando código y descripción de cada una"
        res = self.client.consultarMonedas(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarMonedasReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayMonedas']]

    @inicializar_y_capturar_excepciones
    def ConsultarDestinosCompra(self, sep="|"):
        "Consultar Tipos de Destinos de compra de divisas"
        res = self.client.consultarDestinosCompra(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        #<consultarDestinosCompraReturn>22.02 m
        #<arrayDestinos>
        #<destinos>
        #<tipoDestino>TipoDestinoSimpleType</tipoDestino>
        #<arrayCodigosDescripciones>
        #<codigoDescripcion>
        #<codigo>short</codigo>
        #<descripcion>string</descripcion>
        #</codigoDescripcion>
        #</arrayCodigosDescripciones>
        #</destinos>
        #</arrayDestinos>
        ret = res['consultarDestinosCompraReturn']
        dest = []
        for array in ret['arrayDestinos']:
            destino = array['destinos']
            codigos = [("%s\t%s\t%s" 
                    % (destino['tipoDestino'], 
                       p['codigoDescripcion']['codigo'],
                       p['codigoDescripcion']['descripcion'],
                    )).replace("\t", sep)
                 for p in destino['arrayCodigosDescripciones']]
            dest.extend(codigos)
        return dest

    @inicializar_y_capturar_excepciones
    def ConsultarTiposDocumento(self, sep="|"):
        "Consultar Tipos de Documentos"
        res = self.client.consultarTiposDocumento(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposDocumentoReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayTiposDocumento']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposEstadoSolicitud(self, sep="|"):
        "Este método devuelve los diferentes tipos de estado que puede tener una solicitud."
        res = self.client.consultarTiposEstadoSolicitud(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposEstadoSolicitudReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcionString']).replace("\t", sep)
                 for p in ret['arrayTiposEstadoSolicitud']]

    @inicializar_y_capturar_excepciones
    def ConsultarMotivosExcepcionDJAI(self, sep='|'):
        "Este método retorna el universo de motivos de excepciones a la Declaración Jurada Anticipada de Importación"
        res = self.client.consultarMotivosExcepcionDJAI(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarMotivosExcepcionDJAIReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayMotivosExcepcion']]

    @inicializar_y_capturar_excepciones
    def ConsultarDestinosCompraDJAI(self, sep='|'):
        "Este método retorna el subconjunto de los destinos de compra de divisas alcanzados por las normativas de la Declaración Jurada Anticipada de Importación."
        res = self.client.consultarDestinosCompraDJAI(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarDestinosCompraDJAIReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayCodigosDescripciones']]

    @inicializar_y_capturar_excepciones
    def ConsultarMotivosExcepcionDJAS(self, sep='|'):
        "Este método retorna el universo de motivos de excepciones a la Declaración Jurada Anticipada de Servicios"
        res = self.client.consultarMotivosExcepcionDJAS(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarMotivosExcepcionDJASReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayMotivosExcepcion']]

    @inicializar_y_capturar_excepciones
    def ConsultarDestinosCompraDJAS(self, sep='|'):
        "Este método retorna el subconjunto de los destinos de compra de divisas alcanzados por las normativas de la Declaración Jurada Anticipada de Servicios"
        res = self.client.consultarDestinosCompraDJAS(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarDestinosCompraDJASReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayCodigosDescripciones']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposReferencia(self, sep='|'):
        "Este método retorna el conjunto de los tipos de referencia que pueden ser utilizados en la generación de una solicitud de compra de divisas según corresponda."
        res = self.client.consultarTiposReferencia(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposReferenciaReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayCodigosDescripciones']]
                 
    @inicializar_y_capturar_excepciones
    def ConsultarDestinosCompraTipoReferencia(self, tipo, sep='|'):
        "Este método retorna el subconjunto de los destinos de compra de divisas alcanzados por algunas de las normativas vigentes según el tipo de referencia requerido"
        res = self.client.consultarDestinosCompraTipoReferencia(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            tipo=tipo,
            )
        ret = res['consultarDestinosCompraTipoReferenciaReturn']
        return [("%(codigo)s\t%(descripcion)s" 
                    % p['codigoDescripcion']).replace("\t", sep)
                 for p in ret['arrayCodigosDescripciones']]

    def LeerError(self):
        "Recorro los errores devueltos y devuelvo el primero si existe"
        
        if self.Errores:
            # extraigo el primer item
            er = self.Errores.pop(0)
            return er
        else:
            return ""

    def LeerErrorFormato(self):
        "Recorro los errores de formatos devueltos y devuelvo el primero si existe"
        
        if self.ErroresFormato:
            # extraigo el primer item
            er = self.ErroresFormato.pop(0)
            return er
        else:
            return ""

    def LeerInconsistencia(self):
        "Recorro las inconsistencias devueltas y devuelvo la primera si existe"
        
        if self.Inconsistencias:
            # extraigo el primer item
            er = self.Inconsistencias.pop(0)
            return er
        else:
            return ""

    def LoadTestXML(self, xml_file):
        class DummyHTTP:
            def __init__(self, xml_response):
                self.xml_response = xml_response
            def request(self, location, method, body, headers):
                return {}, self.xml_response
        self.client.http = DummyHTTP(open(xml_file).read())

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


def p_assert_eq(a,b):
    print a, a==b and '==' or '!=', b


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = '--debug' in sys.argv

    # obteniendo el TA
    TA = "TA-wscoc.xml"
    if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wscoc")
        cms = wsaa.sign_tra(tra,"olano.crt", "olanoycia.key")
        ta_string = wsaa.call_wsaa(cms, trace='--trace' in sys.argv)
        open(TA,"w").write(ta_string)
    
    # fin TA

    ws = WSCOC()
    ws.Cuit = "20267565393"

    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    ws.Token = str(ta.credentials.token)
    ws.Sign = str(ta.credentials.sign)

    ws.LanzarExcepciones = True
    ws.Conectar(wsdl=WSDL)
    
    if "--dummy" in sys.argv:
        ##print ws.client.help("dummy")
        try:
            ws.Dummy()
            print "AppServerStatus", ws.AppServerStatus
            print "DbServerStatus", ws.DbServerStatus
            print "AuthServerStatus", ws.AuthServerStatus
        except Exception, e:
            raise
            print "Exception", e
            print ws.XmlRequest
            print ws.XmlResponse

    if "--monedas" in sys.argv:
        print ws.client.help("consultarMonedas")
        try:
            for moneda in ws.ConsultarMonedas():
                print moneda
        except Exception, e:
            raise
            print "Exception", e
            print ws.XmlRequest
            print ws.XmlResponse

    if "--motivos_ex_djai" in sys.argv:
        print ws.ConsultarMotivosExcepcionDJAI()
    if "--destinos_djai" in sys.argv:
        print ws.ConsultarDestinosCompraDJAI()
        
    if "--consultar_cuit" in sys.argv:
        print ws.client.help("consultarCUIT")
        try:
            print "Consultado CUITs...."
            nro_doc = 26756539
            tipo_doc = 96
            print ws.ConsultarCUIT(nro_doc, tipo_doc)
            # recorro el detalle de los cuit devueltos:
            while ws.LeerCUITConsultado():
                print "CUIT", ws.CUITConsultada
                print "Denominación", ws.DenominacionConsultada
        except Exception, e:
            raise
            print "Exception", e
            print ws.XmlRequest
            print ws.XmlResponse
    
    if "--prueba" in sys.argv:
        print ws.client.help("generarSolicitudCompraDivisa").encode("latin1")
        try:
            cuit_comprador = 20267565393
            codigo_moneda = 1
            cotizacion_moneda = 4.26
            monto_pesos = 100
            cuit_representante = None
            codigo_destino = 625

            if "--loadxml" in sys.argv:
                ws.LoadTestXML("wscoc_response.xml")

            if not "--tur" in sys.argv:   
                djai = "--djai" in sys.argv and "12345DJAI000001N" or None
                djas = "--djas" in sys.argv and "12001DJAS000901N" or None
                cod_ex_djai = "--no-djai" and 3 or None
                cod_ex_djas = "--no-djas" and 1 or None
                if '--ref' in sys.argv:
                    tipo, codigo = 1, '12345DJAI000067C'
                else:
                    tipo, codigo = None, None
                print "djai", djai
                ok = ws.GenerarSolicitudCompraDivisa(cuit_comprador, codigo_moneda,
                                    cotizacion_moneda, monto_pesos,
                                    cuit_representante, codigo_destino,
                                    djai=djai, codigo_excepcion_djai=cod_ex_djai, 
                                    djas=djas, codigo_excepcion_djas=cod_ex_djas, 
                                    tipo=tipo, codigo=codigo,)
            else:
                print "Turista!"
                tipo_doc=91
                numero_doc=1234567
                apellido_nombre="Nombre y Apellido del turista extranjero"
                codigo_destino = 985
                ok = ws.GenerarSolicitudCompraDivisaTurExt(
                        tipo_doc, numero_doc, apellido_nombre,
                        codigo_moneda, cotizacion_moneda, monto_pesos,
                        cuit_representante, codigo_destino,
                        )
            while True:
                i = ws.LeerInconsistencia()
                if not i:
                    break
                print "Inconsistencia...", i
                
            assert ok
            print 'Resultado', ws.Resultado
            assert ws.Resultado == 'A'
            print 'COC', ws.COC
            assert len(str(ws.COC)) == 12
            print "FechaEmisionCOC", ws.FechaEmisionCOC
            print 'CodigoSolicitud', ws.CodigoSolicitud
            assert ws.CodigoSolicitud is not None
            print "EstadoSolicitud", ws.EstadoSolicitud
            assert ws.EstadoSolicitud == 'OT'
            print "FechaEstado", ws.FechaEstado
            print "DetalleCUITComprador", ws.CUITComprador, ws.DenominacionComprador
            print "CodigoMoneda", ws.CodigoMoneda
            assert ws.CodigoMoneda == 1
            print "CotizacionMoneda", ws.CotizacionMoneda
            assert round(ws.CotizacionMoneda, 2) == 4.26
            print "MontoPesos", ws.MontoPesos
            assert ws.MontoPesos - monto_pesos <= 0.01
            print "CodigoDestino", ws.CodigoDestino
            assert ws.CodigoDestino == codigo_destino

            coc = ws.COC
            codigo_solicitud = ws.CodigoSolicitud
            # CO: confirmar, o 'DC' (desistio cliente) 'DB' (desistio banco)
            nuevo_estado =  'CO'
            ok = ws.InformarSolicitudCompraDivisa(codigo_solicitud, nuevo_estado)
            assert ok
            print 'Resultado', ws.Resultado
            assert ws.Resultado == 'A'
            print 'COC', ws.COC
            assert ws.COC == coc
            print "EstadoSolicitud", ws.EstadoSolicitud
            assert ws.EstadoSolicitud == nuevo_estado

            ok = ws.AnularCOC(coc, cuit_comprador)
            assert ok
            print 'Resultado', ws.Resultado
            assert ws.Resultado == 'A'
            print 'COC', ws.COC
            assert ws.COC == coc
            print "EstadoSolicitud", ws.EstadoSolicitud
            assert ws.EstadoSolicitud == 'AN'

            ok = ws.ConsultarSolicitudCompraDivisa(codigo_solicitud)
            assert ok
            print 'CodigoSolicitud', ws.CodigoSolicitud
            assert ws.CodigoSolicitud == codigo_solicitud
            print "EstadoSolicitud", ws.EstadoSolicitud
            assert ws.EstadoSolicitud == 'AN'
            
        except:
            print ws.XmlRequest
            print ws.XmlResponse
            print ws.ErrCode
            print ws.ErrMsg
            raise

    if "--consultar_solicitudes" in sys.argv:
        cuit_comprador = None
        estado_solicitud = None
        fecha_emision_desde = '2011-11-01'
        fecha_emision_hasta = '2011-11-30'
        sols = ws.ConsultarSolicitudesCompraDivisas(cuit_comprador, 
                                             estado_solicitud,
                                             fecha_emision_desde,
                                             fecha_emision_hasta,)
        # muestro los resultados de la búsqueda
        print "Solicitudes consultadas:"
        for sol in sols:
            print "Código de Solicitud:", sol
            # podría llamar a ws.ConsultarSolicitudCompraDivisa
        print "hecho."

        ws.AnalizarXml("XmlResponse")
               
        # recorro las solicitudes devueltas
        i = 0
        while ws.LeerSolicitudConsultada():
            print "-" * 80
            coc = ws.ObtenerTagXml('arrayDetallesSolicitudes', 'detalleSolicitudes', i, 'coc')
            cuit = ws.ObtenerTagXml('arrayDetallesSolicitudes', 'detalleSolicitudes', i, 'cuit')
            p_assert_eq(coc, ws.COC)
            print 'CUIT', cuit
            print "FechaEmisionCOC", ws.FechaEmisionCOC
            print 'CodigoSolicitud', ws.CodigoSolicitud
            print "EstadoSolicitud", ws.EstadoSolicitud
            print "FechaEstado", ws.FechaEstado
            print "DetalleCUITComprador", ws.CUITComprador, ws.DenominacionComprador
            print "CodigoMoneda", ws.CodigoMoneda
            print "CotizacionMoneda", ws.CotizacionMoneda
            print "MontoPesos", ws.MontoPesos
            print "CodigoDestino", ws.CodigoDestino
            print "=" * 80
            i = i + 1



    if "--parametros" in sys.argv:
        print "=== Tipos de Estado Solicitud ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarTiposEstadoSolicitud(sep="||")])
        print "=== Monedas ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarMonedas(sep="||")])
        print "=== Destinos de Compra ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarDestinosCompra(sep="||")])
        print "=== Tipos de Documento ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarTiposDocumento(sep="||")])
        print "=== Tipos Estado Solicitud ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarTiposEstadoSolicitud(sep="||")])
        print "=== Motivos Excepcion DJAI ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarMotivosExcepcionDJAI(sep="||")])
        print "=== Destinos Compra DJAI ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarDestinosCompraDJAI(sep="||")])
        print "=== Motivos Excepcion DJAS ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarMotivosExcepcionDJAS(sep="||")])
        print "=== Destinos Compra DJAS ==="
        print u'\n'.join(["||%s||" % s for s in ws.ConsultarDestinosCompraDJAS(sep="||")])
    
    if "--consultar_djai" in sys.argv:
        djai = "12345DJAI000001N"
        cuit = 20267565393
        ws.ConsultarDJAI(djai, cuit)
        print "DJAI", ws.DJAI
        print "Monto FOB", ws.MontoFOB
        print "Codigo Moneda", ws.CodigoMoneda
        print "Estado DJAI", ws.EstadoDJAI
        print "Errores", ws.Errores
        print "ErroresFormato", ws.ErroresFormato

    if "--consultar_djas" in sys.argv:
        djas = "12001DJAS000901N"
        cuit = 20267565393
        ws.ConsultarDJAS(djas, cuit)
        print "DJAS", ws.DJAS
        print "Monto FOB", ws.MontoFOB
        print "Codigo Moneda", ws.CodigoMoneda
        print "Estado DJAI", ws.EstadoDJAI
        print "Errores", ws.Errores
        print "ErroresFormato", ws.ErroresFormato
        
    if "--consultar_ref" in sys.argv:
        codigo = "12345DJAI000067C"
        cuit = 20267565393
        ws.ConsultarReferencia(1, codigo)
        print "Monto FOB", ws.MontoFOB
        print "Codigo Moneda", ws.CodigoMoneda
        print "Estado", ws.Estado
        print "Errores", ws.Errores
        print "ErroresFormato", ws.ErroresFormato
      
    if "--consultar_dest_ref" in sys.argv:
        print ws.ConsultarDestinosCompraTipoReferencia(1)

    if "--consultar_tipos_ref" in sys.argv:
        print ws.ConsultarTiposReferencia()
        
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

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSCOC)
    else:
        main()
