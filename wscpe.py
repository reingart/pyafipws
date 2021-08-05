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


# constantes de configuración (producción/homologación):

WSDL = ["https://serviciosjava.afip.gob.ar/cpe-ws/services/wscpe?wsdl",
        "https://fwshomo.afip.gov.ar/wscpe/services/soap?wsdl"]

DEBUG = False
XML = False
CONFIG_FILE = "wscpe.ini"
HOMO = True
ENCABEZADO = []


class WSCPE(BaseWS):
    "Interfaz para el WebService de Carta de Porte Electrónica (Version 1)"
    _public_methods_ = ['Conectar', 'Dummy', 'SetTicketAcceso', 'DebugLog',
                        'GenerarCPE', 'EmitirCPE', 'AutorizarCPE', 'AnularCPE', 'ConsultarCPE',
                        'InformarContingencia', 'ModificarViaje', 'RegistrarRecepcion',  'ConsultarUltimoCPEEmitido',
                        'CrearCPE', 'AgregarViaje', 'AgregarVehiculo', 'AgregarMercaderia', 'AgregarReceptor', 
                        'AgregarDatosAutorizacion', 'AgregarContingencia',
                        'ConsultarTiposMercaderia', 'ConsultarTiposEmbalaje', 'ConsultarTiposUnidades', 'ConsultarTiposComprobante',
                        'ConsultarTiposComprobante', 'ConsultarTiposContingencia', 'ConsultarCodigosDomicilio', 'ConsultarPaises',
                        'SetParametros', 'SetParametro', 'GetParametro', 'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        ]
    _public_attrs_ = ['XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'Excepcion', 'LanzarExcepciones',
                      'Token', 'Sign', 'Cuit', 'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
                      'CodCPE', 'TipoComprobante', 'PuntoEmision',
                      'NroCPE', 'CodAutorizacion', 'FechaVencimiento', 'FechaEmision', 'Estado', 'Resultado', 'QR',
                      'ErrCode', 'ErrMsg', 'Errores', 'ErroresFormato', 'Observaciones', 'Obs', 'Evento', 'Eventos',
                     ]
    _reg_progid_ = "WSCPE"
    _reg_clsid_ = "{37F6A7B5-344E-45C5-9198-0CF7B206F409}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL[HOMO]
    LanzarExcepciones = False
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def Conectar(self, *args, **kwargs):
        ret = BaseWS.Conectar(self, *args, **kwargs)
        return ret

    def inicializar(self):
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.CodCPE = self.TipoComprobante = self.PuntoEmision = None
        self.NroCPE = self.CodAutorizacion = self.FechaVencimiento = self.FechaEmision = None
        self.Estado = self.Resultado = self.QR = None
        self.Errores = []
        self.ErroresFormato = []
        self.Observaciones = []
        self.Eventos = []
        self.Evento = self.ErrCode = self.ErrMsg = self.Obs = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.Errores = [err['codigoDescripcion'] for err in ret.get('arrayErrores', [])]
        self.ErroresFormato = [err['codigoDescripcionString'] for err in ret.get('arrayErroresFormato', [])]
        errores = self.Errores + self.ErroresFormato
        self.ErrCode = ' '.join(["%(codigo)s" % err for err in errores])
        self.ErrMsg = '\n'.join(["%(codigo)s: %(descripcion)s" % err for err in errores])

    def __analizar_observaciones(self, ret):
        "Comprueba y extrae observaciones si existen en la respuesta XML"
        self.Observaciones = [obs["codigoDescripcion"] for obs in ret.get('arrayObservaciones', [])]
        self.Obs = '\n'.join(["%(codigo)s: %(descripcion)s" % obs for obs in self.Observaciones])

    def __analizar_evento(self, ret):
        "Comprueba y extrae el wvento informativo si existen en la respuesta XML"
        evt = ret.get('evento')
        if evt:
            self.Eventos = [evt]
            self.Evento = "%(codigo)s: %(descripcion)s" % evt

    @inicializar_y_capturar_excepciones
    def CrearCPE(self, tipo_cp, sucursal,
                 tipo_titular_mercaderia,
                 cuit_solicitante=None, cuit_autorizado_retirar=None,
                 cuit_productor_contrato=None, numero_maquila=None,
                 cod_cpe=None, estado=None, es_entrega_mostrador=None,
                 **kwargs):
        "Inicializa internamente los datos de un cpe para autorizar"
        self.cpe = {'puntoEmision': punto_emision, 'tipoTitularMercaderia': tipo_titular_mercaderia,
                       'cuitTitularMercaderia': cuit_titular_mercaderia,
                       'cuitAutorizadoRetirar': cuit_autorizado_retirar,
                       'cuitProductorContrato': cuit_productor_contrato,
                       'numeroMaquila': numero_maquila,
                       'codCPE': cod_cpe,
                       'esEntregaMostrador': es_entrega_mostrador,
                       'arrayMercaderias': [], 'arrayContingencias': [],
                      }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarReceptor(self, cuit_pais_receptor,
                        cuit_receptor=None, cod_dom_receptor=None,
                        cuit_despachante=None, codigo_aduana=None, 
                        denominacion_receptor=None, domicilio_receptor=None, **kwargs):
        "Agrega la información referente al viaje del cpe electrónico granosero"
        receptor = {'cuitPaisReceptor': cuit_pais_receptor}
        if cuit_receptor:
            receptor['receptorNacional'] = {'codDomReceptor': cod_dom_receptor,
                                            'cuitReceptor':cuit_receptor}
        else:
            receptor['receptorExtranjero'] = {
                                        'codigoAduana': codigo_aduana,
                                        'cuitDespachante': cuit_despachante,
                                        'denominacionReceptor': denominacion_receptor,
                                        'domicilioReceptor': domicilio_receptor}
        self.cpe['receptor'] = receptor

    @inicializar_y_capturar_excepciones
    def AgregarViaje(self, fecha_inicio_viaje, distancia_km, cod_pais_transportista, ducto=None, **kwargs):
        "Agrega la información referente al viaje del cpe electrónico granosero"
        self.cpe.update({
            'viaje': {
                'fechaInicioViaje': fecha_inicio_viaje ,
                'kmDistancia': distancia_km,
                'tramo': [{
                }]
            }})

        if ducto:
            transporte = self.cpe['viaje']['tramo'][0]['ducto'] = ducto
        else:
            self.cpe['viaje']['tramo'][0]['automotor'] = {
                        'codPaisTransportista': cod_pais_transportista,
                    }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarVehiculo(self, dominio_vehiculo, dominio_acoplado=None, 
                        cuit_transportista=None, cuit_conductor=None, 
                        apellido_conductor=None, cedula_conductor=None, denom_transportista=None,
                        id_impositivo=None, nombre_conductor=None,
                        **kwargs):
        "Agrega la información referente al vehiculo usado en el viaje del cpe electrónico granosero"
        transporte = self.cpe['viaje']['tramo'][0]['automotor']
        vehiculo = {
                    'dominioVehiculo': dominio_vehiculo, 
                    'dominioAcoplado': dominio_acoplado,
                   }
        transporte.update(vehiculo)

        if cuit_transportista:
            transporte['transporteNacional'] = {
                'cuitTransportista': cuit_transportista, 
                'cuitConductor': cuit_conductor,
            }
        else:
            transporte['transporteExtranjero'] = {
                'apellidoConductor': apellido_conductor,
                'cedulaConductor': cedula_conductor,
                'denomTransportista': denom_transportista,
                'idImpositivo': id_impositivo,
                'nombreConductor': nombre_conductor,
            }

        return True

    @inicializar_y_capturar_excepciones
    def AgregarMercaderia(self, orden, cod_tipo_prod, cod_tipo_emb, cantidad_emb, cod_tipo_unidad, cant_unidad, 
                          anio_safra, **kwargs):
        "Agrega la información referente a la mercadería del cpe electrónico granosero"
        mercaderia = dict(orden=orden,  
                          tipoProducto=cod_tipo_prod,
                          tipoEmbalaje=cod_tipo_emb,
                          unidadMedida=cod_tipo_unidad,
                          cantidad=cant_unidad,
                          anioZafra=anio_safra,
                         )
        self.cpe['arrayMercaderias'].append(dict(mercaderia=mercaderia))
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDatosAutorizacion(self, nro_cpe=None, cod_autorizacion=None, fecha_emision=None, fecha_vencimiento=None, **kwargs):
        "Agrega la información referente a los datos de autorización del cpe electrónico granosero"
        self.cpe['datosEmision'] = dict(nroCPE=nro_cpe, codAutorizacion=cod_autorizacion,
                                                fechaEmision=fecha_emision, fechaVencimiento=fecha_vencimiento,
                                               )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarContingencias(self, tipo=None, observacion=None, **kwargs):
        "Agrega la información referente a los opcionales de la liq. seq."
        contingencia = dict(tipoContingencia=tipo, observacion=observacion)
        self.cpe['arrayContingencias'].append(dict(contingencia=contingencia))
        return True

    @inicializar_y_capturar_excepciones
    def GenerarCPE(self, id_req, archivo="qr.png"):
        "Informar los datos necesarios para la generación de un cpe nuevo"
        if not self.cpe['arrayContingencias']:
            del self.cpe['arrayContingencias']
        response = self.client.generarCPE(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                idReqCliente=id_req, cpe=self.cpe) 
        ret = response.get("generarCPEReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarCPE(ret, archivo)
        return bool(self.CodCPE)

    def AnalizarCPE(self, ret, archivo=None):
        "Extrae el resultado del cpe, si existen en la respuesta XML"
        if ret:
            datos_aut = ret.get('cpeDatosAutorizacion')
            if datos_aut:
                self.CodCPE = datos_aut.get("codigoCPE")
                self.TipoComprobante = datos_aut.get("idTipoComprobante")
                self.NroCPE = datos_aut.get('nroComprobante')
                self.CodAutorizacion = datos_aut.get('codigoAutorizacion')
                self.FechaEmision = datos_aut.get('fechaEmision')
                self.FechaVencimiento = datos_aut.get('fechaVencimiento')
            self.Estado = ret.get('estado')
            self.Resultado = ret.get('resultado')
            self.QR = ret.get('qr') or ""
            if archivo:
                f = open(archivo, "wb")
                f.write(self.QR)
                f.close()

    @inicializar_y_capturar_excepciones
    def EmitirCPE(self, archivo="qr.png"):
        "Emitir CPEs que se encuentren en estado Pendiente de Emitir."
        response = self.client.emitirCPE(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                emitirCPE=dict(
                                    codigoCPE=self.cpe['codCPE'],
                                    )
                                )
        ret = response.get("emitirCPEReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarCPE(ret, archivo)
        return bool(self.CodCPE)

    @inicializar_y_capturar_excepciones
    def AutorizarCPE(self, archivo="qr.png"):
        "Autorizar o denegar un cpe (cuando corresponde autorizacion) por parte del titular/depositario"
        response = self.client.autorizarCPEAutomotor(
            auth={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            solicitud={
                'cabecera': {'tipoCP': 1, 'cuitSolicitante': 20267565393, 'sucursal': 1, 'nroOrden': 1},
                'origen': {'operador': {'planta': 1, 'codProvincia': 12, 'codLocalidad': 5544}},
                'correspondeRetiroProductor': True,
                'esSolicitanteCampo': "N",
                'retiroProductor': {'certificadoCOE': 330100025869, 'cuitRemitenteComercialProductor': 20111111112},
                'intervinientes': {'cuitMercadoATermino': 20222222223, 'cuitCorredorVentaPrimaria': 20222222223, 'cuitCorredorVentaSecundaria': 20222222223, 'cuitRemitenteComercialVentaSecundaria': 20222222223, 'cuitIntermediario': 20222222223, 'cuitRemitenteComercialVentaPrimaria': 20222222223, 'cuitRepresentanteEntregador': 20222222223},
                'datosCarga': {'pesoTara': 1000, 'codGrano': 31, 'pesoBruto': 1000, 'cosecha': 910},
                'destino': {'planta': 1, 'codProvincia': 12, 'esDestinoCampo': "M", 'codLocalidad': 3058, 'cuit': 20111111112},
                'destinatario': {'cuit': 30000000006},
                'transporte': {'fechaHoraPartida': datetime.datetime.now(), 'codigoTurno': "00", 'cuitTransportista': 20333333334, 'dominio': "ZZZ000", 'kmRecorrer': 500},
                'productor': {'codLocalidad': 3059},
                }
        )
        ret = response.get("respuesta")
        # 'cabecera': {'fechaEmision': datetime.datetime, 'sucursal': int, 'planta': int, 'tipoCartaPorte': int, 'nroCPE': long, 'nroOrden': long, 'fechaInicioEstado': datetime.datetime, 'estado': unicode, 'fechaVencimiento': datetime.datetime},
        # 'origen': {'planta': int, 'codProvincia': int, 'domicilio': unicode, 'codLocalidad': int},
        # 'correspondeRetiroProductor': bool,
        # 'retiroProductor': {
        #     'certificadoCOE': long,
        #     'cuitRemitenteComercialProductor': long},
        # 'intervinientes': {'cuitMercadoATermino': long, 'cuitCorredorVentaPrimaria': long, 'cuitCorredorVentaSecundaria': long, 'cuitRemitenteComercialVentaSecundaria': long, 'cuitIntermediario': long, 'cuitRemitenteComercialVentaPrimaria': long, 'cuitRepresentanteEntregador': long},
        # 'datosCarga': {
        #     'pesoTara': int, 'codGrano': int, 'pesoBruto': int, 'cosecha': int},
        # 'destino': {'planta': int, 'codProvincia': int, 'codLocalidad': int, 'cuit': long},
        # 'destinatario': {'cuit': long},
        # 'transporte': [{'fechaHoraPartida': datetime.datetime, 'codigoTurno': int, 'cuitTransportista': long, 'dominio': unicode, 'kmRecorrer': int}], 
        # 'errores': [{'error': [{'descripcion': unicode, 'codigo': unicode}]}], 
        # 'pdf': b64decode,
        # 'metadata': {'servidor': unicode, 'fechaHora': datetime.datetime}}
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarCPE(ret, archivo)
        return bool(self.CodCPE)

    @inicializar_y_capturar_excepciones
    def AnularCPE(self):
        "Anular un cpe generado que aún no haya sido emitido"
        response = self.client.anularCPE(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                codCPE=self.cpe['codCPE'])
        ret = response.get("anularCPEReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarCPE(ret)
        return bool(self.CodCPE)

    @inicializar_y_capturar_excepciones
    def InformarContingencia(self, archivo="qr.png"):
        "Reportar una contingencia que impide el envío de la mercadería y realiza la anulación del cpe"
        mercaderias = []
        for it in self.cpe['arrayMercaderias']:
            mercaderia = it['mercaderia']
            mercaderias.append({"mercaderia": [mercaderia]})

        response = self.client.informarContingencia(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                informarContingencia={
                                    'codigoCPE': self.cpe["codCPE"],
                                    'tipoContingencia': self.cpe['arrayContingencias'][0]["contingencia"]["tipoContingencia"],
                                    'observaciones': self.cpe['arrayContingencias'][0]["contingencia"]["observacion"],
                                    'arrayMercaderiaPerdida': mercaderias,
                                })
        ret = response.get("informarContingenciaReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarCPE(ret, archivo)
        return ret["resultado"]

    @inicializar_y_capturar_excepciones
    def ConsultarUltimoCPEEmitido(self, tipo_comprobante=995, punto_emision=1):
        "Obtener el último número de cpe que se emitió por tipo de comprobante y punto de emisión"
        response = self.client.consultarUltimoCPEEmitido(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                tipoComprobante=tipo_comprobante,
                                puntoEmision=punto_emision)
        ret = response.get("consultarUltimoCPEReturn", {})
        id_req = ret.get("idReq", 0)
        rec = ret.get("cpe", {})
        self.__analizar_errores(ret)
        self.__analizar_observaciones(ret)
        self.__analizar_evento(ret)
        self.AnalizarCPE(rec)
        return id_req

    @inicializar_y_capturar_excepciones
    def ConsultarCPE(self, cod_cpe=None, id_req=None,
                        tipo_comprobante=None, punto_emision=None, nro_comprobante=None):
        "Obtener los datos de un cpe generado"
        ##print(self.client.help("consultarCPE"))
        response = self.client.consultarCPE(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                codCPE=cod_cpe,
                                cuitEmisor=self.Cuit,
                                idReq=id_req,
                                tipoComprobante=tipo_comprobante,
                                puntoEmision=punto_emision,
                                nroComprobante=nro_comprobante)
        ret = response.get("consultarCPEReturn", {})
        id_req = ret.get("idReq", 0)
        self.cpe = rec = ret.get("cpe", {})
        self.__analizar_errores(ret)
        self.__analizar_observaciones(ret)
        self.__analizar_evento(ret)
        self.AnalizarCPE(rec)
        return id_req

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['dummyReturn']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    @inicializar_y_capturar_excepciones
    def ConsultarTiposComprobante(self, sep="||"):
        "Obtener el código y descripción para tipo de comprobante"
        ret = self.client.consultarTiposComprobante(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['consultarTiposComprobanteReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayTiposComprobante', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarPaises(self, sep="||"):
        "Obtener el código y descripción para los paises"
        ret = self.client.consultarPaises(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['consultarCodigosPaisReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayPaises', [])
        lista = [it['pais'] for it in array]
        return [(u"%s {codigo} %s {cuit} %s {nombre} %s {tipoSujeto} %s" % (sep, sep, sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposContingencia(self, sep="||"):
        "Obtener el código y descripción para cada tipo de contingencia que puede reportar"
        ret = self.client.consultarTiposContingencia(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['codigoDescripcionReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayCodigoDescripcion', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposMercaderia(self, sep="||"):
        "Obtener el código y descripción  códigos y la descripción para cada tipo de mercadería"
        ret = self.client.consultarTiposMercaderia(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['codigoDescripcionReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayCodigoDescripcion', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposEmbalaje(self, sep="||"):
        "Obtener el código y descripción  códigos y la descripción para cada tipo de embalaje"
        ret = self.client.consultarTiposEmbalaje(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['codigoDescripcionReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayCodigoDescripcion', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposUnidades(self, sep="||"):
        "Obtener el código y descripción  códigos y la descripción para cada tipo de unidades de venta"
        ret = self.client.consultarUnidadesMedida(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['codigoDescripcionReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayCodigoDescripcion', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarCodigosDomicilio(self, cuit_titular=1, sep="||"):
        "Obtener el código de depositos que tiene habilitados para operar el cuit informado"
        ret = self.client.consultarCodigosDomicilio(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                            cuitTitularDomicilio=cuit_titular,
                            )['consultarCodigosDomicilioReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayDomicilios', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]



# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = WSCPE.InstallDir = get_install_dir()


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSCPE)
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
