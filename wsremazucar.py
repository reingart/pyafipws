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

"""Módulo para obtener Remito Electronico Azucar:
del servicio web RemAzucarService versión 2.0.3 de AFIP (RG4519/19)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2018-2019 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.02a"

LICENCIA = """
wsremhairna.py: Interfaz para generar Remito Electrónico Azúcar AFIP v2.0.3
remisiones de los productos obtenidos de la industrialización de la
caña de azúcar (azúcar, alcohol, bagazo y melaza)
Resolución General Conjunta 4519/2019
Copyright (C) 2019 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoAzucar

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

  --generar: generar un remito
  --emitir: emite un remito
  --anular: anula un remito
  --autorizar: autoriza un remito

  --ult: consulta ultimo nro remito emitido
  --consultar: consulta un remito generado

  --tipos_comprobante: tabla de parametros para tipo de comprobante
  --tipos_contingencia: tipo de contingencia que puede reportar
  --tipos_categoria_emisor: tipos de categorías de emisor
  --tipos_categoria_receptor: tipos de categorías de receptor
  --tipos_estados: estados posibles en los que puede estar un remito azucarero
  --grupos_azucar' grupos de los distintos tipos de cortes de azucar
  --tipos_azucar': tipos de corte de azucar
  --codigos_domicilio: codigos de depositos habilitados para el cuit

Ver wsremazucar.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time, base64
from utils import date
import traceback
from pysimplesoap.client import SoapFault
import utils

# importo funciones compartidas:
from utils import json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir, json_serializer


# constantes de configuración (producción/homologación):

WSDL = ["https://serviciosjava.afip.gob.ar/wsremazucar/RemAzucarService?wsdl",
        "https://fwshomo.afip.gov.ar/wsremazucar/RemAzucarService?wsdl"]

DEBUG = False
XML = False
CONFIG_FILE = "wsremazucar.ini"
HOMO = True
ENCABEZADO = []


class WSRemAzucar(BaseWS):
    "Interfaz para el WebService de Remito Electronico Carnico (Version 3)"
    _public_methods_ = ['Conectar', 'Dummy', 'SetTicketAcceso', 'DebugLog',
                        'GenerarRemito', 'EmitirRemito', 'AutorizarRemito', 'AnularRemito', 'ConsultarRemito',
                        'InformarContingencia', 'ModificarViaje', 'RegistrarRecepcion',  'ConsultarUltimoRemitoEmitido',
                        'CrearRemito', 'AgregarViaje', 'AgregarVehiculo', 'AgregarMercaderia', 'AgregarReceptor', 
                        'AgregarDatosAutorizacion', 'AgregarContingencia',
                        'ConsultarTiposMercaderia', 'ConsultarTiposEmbalaje', 'ConsultarTiposUnidades', 'ConsultarTiposComprobante',
                        'ConsultarTiposComprobante', 'ConsultarTiposContingencia', 'ConsultarCodigosDomicilio', 'ConsultarPaises',
                        'SetParametros', 'SetParametro', 'GetParametro', 'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        ]
    _public_attrs_ = ['XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'Excepcion', 'LanzarExcepciones',
                      'Token', 'Sign', 'Cuit', 'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
                      'CodRemito', 'TipoComprobante', 'PuntoEmision',
                      'NroRemito', 'CodAutorizacion', 'FechaVencimiento', 'FechaEmision', 'Estado', 'Resultado', 'QR',
                      'ErrCode', 'ErrMsg', 'Errores', 'ErroresFormato', 'Observaciones', 'Obs', 'Evento', 'Eventos',
                     ]
    _reg_progid_ = "WSRemAzucar"
    _reg_clsid_ = "{448F912A-C013-4E19-8D52-7FC88305590A}"

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
        self.CodRemito = self.TipoComprobante = self.PuntoEmision = None
        self.NroRemito = self.CodAutorizacion = self.FechaVencimiento = self.FechaEmision = None
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
    def CrearRemito(self, tipo_comprobante, punto_emision,
                    tipo_titular_mercaderia,
                    cuit_titular_mercaderia=None, cuit_autorizado_retirar=None,
                    cuit_productor_contrato=None, numero_maquila=None,
                    cod_remito=None, estado=None,
                    **kwargs):
        "Inicializa internamente los datos de un remito para autorizar"
        self.remito = {'puntoEmision': punto_emision, 'tipoTitularMercaderia': tipo_titular_mercaderia,
                       'cuitTitularMercaderia': cuit_titular_mercaderia,
                       'cuitAutorizadoRetirar': cuit_autorizado_retirar,
                       'cuitProductorContrato': cuit_productor_contrato,
                       'numeroMaquila': numero_maquila,
                       'arrayMercaderias': [], 'arrayContingencias': [],
                      }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarReceptor(self, cuit_pais_receptor,
                        cuit_receptor=None, cod_dom_receptor=None,
                        cuit_despachante=None, codigo_aduana=None, 
                        denominacion_receptor=None, domicilio_receptor=None, **kwargs):
        "Agrega la información referente al viaje del remito electrónico azucarero"
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
        self.remito['receptor'] = receptor

    @inicializar_y_capturar_excepciones
    def AgregarViaje(self, fecha_inicio_viaje, distancia_km, cod_pais_transportista, **kwargs):
        "Agrega la información referente al viaje del remito electrónico azucarero"
        self.remito.update({'fechaInicioViaje': fecha_inicio_viaje ,
                            'kmDistancia': distancia_km,
                            'transporte': {'codPaisTransportista': cod_pais_transportista, },
                           })
        return True

    @inicializar_y_capturar_excepciones
    def AgregarVehiculo(self, dominio_vehiculo, dominio_acoplado=None, 
                        cuit_transportista=None, cuit_conductor=None, 
                        apellido_conductor=None, cedula_conductor=None, denom_transportista=None,
                        id_impositivo=None, nombre_conductor=None,
                        **kwargs):
        "Agrega la información referente al vehiculo usado en el viaje del remito electrónico azucarero"
        transporte = self.remito['transporte']
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
        "Agrega la información referente a la mercadería del remito electrónico azucarero"
        mercaderia = dict(orden=orden,  
                          tipoProducto=cod_tipo_prod,
                          tipoEmbalaje=cod_tipo_emb,
                          unidadMedida=cod_tipo_unidad,
                          cantidad=cant_unidad,
                          anioZafra=anio_safra,
                         )
        self.remito['arrayMercaderias'].append(dict(mercaderia=mercaderia))
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDatosAutorizacion(self, nro_remito=None, cod_autorizacion=None, fecha_emision=None, fecha_vencimiento=None, **kwargs):
        "Agrega la información referente a los datos de autorización del remito electrónico azucarero"
        self.remito['datosEmision'] = dict(nroRemito=nro_remito, codAutorizacion=cod_autorizacion,
                                                fechaEmision=fecha_emision, fechaVencimiento=fecha_vencimiento,
                                               )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarContingencias(self, tipo=None, observacion=None, **kwargs):
        "Agrega la información referente a los opcionales de la liq. seq."
        contingencia = dict(tipoContingencia=tipo, observacion=observacion)
        self.remito['arrayContingencias'].append(dict(contingencia=contingencia))
        return True

    @inicializar_y_capturar_excepciones
    def GenerarRemito(self, id_req, archivo="qr.png"):
        "Informar los datos necesarios para la generación de un remito nuevo"
        if not self.remito['arrayContingencias']:
            del self.remito['arrayContingencias']
        response = self.client.generarRemito(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                idReqCliente=id_req, remito=self.remito) 
        ret = response.get("generarRemitoReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarRemito(ret, archivo)
        return bool(self.CodRemito)

    def AnalizarRemito(self, ret, archivo=None):
        "Extrae el resultado del remito, si existen en la respuesta XML"
        if ret:
            datos_aut = ret.get('remitoDatosAutorizacion')
            if datos_aut:
                self.CodRemito = datos_aut.get("codigoRemito")
                self.TipoComprobante = datos_aut.get("idTipoComprobante")
                self.NroRemito = datos_aut.get('nroComprobante')
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
    def EmitirRemito(self, archivo="qr.png"):
        "Emitir Remitos que se encuentren en estado Pendiente de Emitir."
        response = self.client.emitirRemito(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                codRemito=self.remito['codRemito'],
                                viaje=self.remito.get('viaje'))
        ret = response.get("emitirRemitoReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarRemito(ret, archivo)
        return bool(self.CodRemito)

    @inicializar_y_capturar_excepciones
    def AutorizarRemito(self, archivo="qr.png"):
        "Autorizar o denegar un remito (cuando corresponde autorizacion) por parte del titular/depositario"
        response = self.client.autorizarRemito(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                codRemito=self.remito['codRemito'],
                                estado=self.remito['estado'])
        ret = response.get("autorizarRemitoReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarRemito(ret, archivo)
        return bool(self.CodRemito)

    @inicializar_y_capturar_excepciones
    def AnularRemito(self):
        "Anular un remito generado que aún no haya sido emitido"
        response = self.client.anularRemito(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                codRemito=self.remito['codRemito'])
        ret = response.get("anularRemitoReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarRemito(ret)
        return bool(self.CodRemito)

    @inicializar_y_capturar_excepciones
    def ConsultarUltimoRemitoEmitido(self, tipo_comprobante=995, punto_emision=1):
        "Obtener el último número de remito que se emitió por tipo de comprobante y punto de emisión"
        response = self.client.consultarUltimoRemitoEmitido(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                tipoComprobante=tipo_comprobante,
                                puntoEmision=punto_emision)
        ret = response.get("consultarUltimoRemitoReturn", {})
        id_req = ret.get("idReq", 0)
        rec = ret.get("remito", {})
        self.__analizar_errores(ret)
        self.__analizar_observaciones(ret)
        self.__analizar_evento(ret)
        self.AnalizarRemito(rec)
        return id_req

    @inicializar_y_capturar_excepciones
    def ConsultarRemito(self, cod_remito=None, id_req=None,
                        tipo_comprobante=None, punto_emision=None, nro_comprobante=None):
        "Obtener los datos de un remito generado"
        print(self.client.help("consultarRemito"))
        response = self.client.consultarRemito(
                                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                                codRemito=cod_remito,
                                idReq=id_req,
                                tipoComprobante=tipo_comprobante,
                                puntoEmision=punto_emision,
                                nroComprobante=nro_comprobante)
        ret = response.get("consultarRemitoReturn", {})
        id_req = ret.get("idReq", 0)
        self.remito = rec = ret.get("remito", {})
        self.__analizar_errores(ret)
        self.__analizar_observaciones(ret)
        self.__analizar_evento(ret)
        self.AnalizarRemito(rec)
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
INSTALL_DIR = WSRemAzucar.InstallDir = get_install_dir()


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSRemAzucar)
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
        CUIT = config.get('WSRemAzucar','CUIT')
        ENTRADA = config.get('WSRemAzucar','ENTRADA')
        SALIDA = config.get('WSRemAzucar','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = None
        if config.has_option('WSRemAzucar','URL') and not HOMO:
            wsremazucar_url = config.get('WSRemAzucar','URL')
        else:
            wsremazucar_url = WSDL[HOMO]

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
            print "wsremazucar_url:", wsremazucar_url

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsremazucar", CERT, PRIVATEKEY, wsaa_url, debug=DEBUG)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wsremazucar = WSRemAzucar()
        wsremazucar.Conectar(wsdl=wsremazucar_url)
        wsremazucar.SetTicketAcceso(ta)
        wsremazucar.Cuit = CUIT
        ok = None
        
        if '--dummy' in sys.argv:
            ret = wsremazucar.Dummy()
            print "AppServerStatus", wsremazucar.AppServerStatus
            print "DbServerStatus", wsremazucar.DbServerStatus
            print "AuthServerStatus", wsremazucar.AuthServerStatus
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
            print "Consultando ultimo remito pto_emision=%s tipo_comprobante=%s" % (pto_emision, tipo_comprobante)
            ok = wsremazucar.ConsultarUltimoRemitoEmitido(tipo_comprobante, pto_emision)
            if wsremazucar.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wsremazucar.Excepcion
                if DEBUG: print >> sys.stderr, wsremazucar.Traceback
            print "Ultimo Nro de Remito", wsremazucar.NroRemito
            print "Errores:", wsremazucar.Errores

        if '--consultar' in sys.argv:
            try:
                cod_remito = sys.argv[sys.argv.index("--consultar") + 1]
            except IndexError, ValueError:
                cod_remito = None
            rec = {}
            print "Consultando remito cod_remito=%s" % (cod_remito, )
            ok = wsremazucar.ConsultarRemito(cod_remito)
            if wsremazucar.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wsremazucar.Excepcion
                if DEBUG: print >> sys.stderr, wsremazucar.Traceback
            print "Ultimo Nro de Remito", wsremazucar.NroRemito
            print "Errores:", wsremazucar.Errores
            if DEBUG:
                import pprint
                pprint.pprint(wsremazucar.remito)

        ##wsremazucar.client.help("generarRemito")
        if '--prueba' in sys.argv:
            rec = dict(
                    tipo_comprobante=997, punto_emision=1,
                    tipo_titular_mercaderia=1,
                    cuit_titular_mercaderia='20222222223',
                    cuit_autorizado_retirar='20111111112',
                    cuit_productor_contrato=None, 
                    numero_maquila=9999,
                    cod_remito=None, estado=None,
                    id_req=int(time.time()),
                )
            if "--autorizar" in sys.argv:
                rec["estado"] = 'A'  # 'A': Autorizar, 'D': Denegar
            rec['receptor'] = dict(
                    cuit_pais_receptor='50000000016',
                    cuit_receptor='20111111112', cod_dom_receptor=1,
                    cuit_despachante=None, codigo_aduana=None, 
                    denominacion_receptor=None, domicilio_receptor=None)
            rec['viaje'] = dict(fecha_inicio_viaje='2018-10-01', distancia_km=999, cod_pais_transportista=200)
            rec['viaje']['vehiculo'] = dict(
                    dominio_vehiculo='AAA000', dominio_acoplado='ZZZ000', 
                    cuit_transportista='20333333334', cuit_conductor='20333333334',  
                    apellido_conductor=None, cedula_conductor=None, denom_transportista=None,
                    id_impositivo=None, nombre_conductor=None)
            rec['mercaderias'] = [dict(orden=1, cod_tipo_prod=0, cod_tipo_emb=0, cantidad_emb=0, cod_tipo_unidad=0, cant_unidad=1, 
                                       anio_safra=2019 )]
            rec['datos_autorizacion'] = None # dict(nro_remito=None, cod_autorizacion=None, fecha_emision=None, fecha_vencimiento=None)
            rec['contingencias'] = [dict(tipo=1, observacion="anulacion")]
            with open(ENTRADA, "w") as archivo:
                json.dump(rec, archivo, sort_keys=True, indent=4)

        if '--cargar' in sys.argv:
            with open(ENTRADA, "r") as archivo:
                rec = json.load(archivo)
            wsremazucar.CrearRemito(**rec)
            wsremazucar.AgregarReceptor(**rec['receptor'])
            wsremazucar.AgregarViaje(**rec['viaje'])
            wsremazucar.AgregarVehiculo(**rec['viaje']['vehiculo'])
            for mercaderia in rec['mercaderias']:
                wsremazucar.AgregarMercaderia(**mercaderia)
            datos_aut = rec['datos_autorizacion']
            if datos_aut:
                wsremazucar.AgregarDatosAutorizacion(**datos_aut)
            for contingencia in rec['contingencias']:
                wsremazucar.AgregarContingencias(**contingencia)

        if '--generar' in sys.argv:
            if '--testing' in sys.argv:
                wsremazucar.LoadTestXML("tests/xml/wsremazucar.xml")  # cargo respuesta

            ok = wsremazucar.GenerarRemito(id_req=rec['id_req'], archivo="qr.jpg")

        if '--emitir' in sys.argv:
            ok = wsremazucar.EmitirRemito()

        if '--autorizar' in sys.argv:
            ok = wsremazucar.AutorizarRemito()

        if '--anular' in sys.argv:
            ok = wsremazucar.AnularRemito()

        if ok is not None:
            print "Resultado: ", wsremazucar.Resultado
            print "Cod Remito: ", wsremazucar.CodRemito
            if wsremazucar.CodAutorizacion:
                print "Numero Remito: ", wsremazucar.NroRemito
                print "Cod Autorizacion: ", wsremazucar.CodAutorizacion
                print "Fecha Emision", wsremazucar.FechaEmision
                print "Fecha Vencimiento", wsremazucar.FechaVencimiento
            print "Estado: ", wsremazucar.Estado
            print "Observaciones: ", wsremazucar.Observaciones
            print "Errores:", wsremazucar.Errores
            print "Errores Formato:", wsremazucar.ErroresFormato
            print "Evento:", wsremazucar.Evento
            rec['cod_remito'] = wsremazucar.CodRemito
            rec['resultado'] = wsremazucar.Resultado
            rec['observaciones'] = wsremazucar.Observaciones
            rec['fecha_emision'] = wsremazucar.FechaEmision
            rec['fecha_vencimiento'] = wsremazucar.FechaVencimiento
            rec['errores'] = wsremazucar.Errores
            rec['errores_formato'] = wsremazucar.ErroresFormato
            rec['evento'] = wsremazucar.Evento

        if '--grabar' in sys.argv:
            with open(SALIDA, "w") as archivo:
                json.dump(rec, archivo, sort_keys=True, indent=4, default=json_serializer)

        # Recuperar parámetros:

        if '--tipos_comprobante' in sys.argv:
            ret = wsremazucar.ConsultarTiposComprobante()
            print "\n".join(ret)

        if '--tipos_contingencia' in sys.argv:
            ret = wsremazucar.ConsultarTiposContingencia()
            print "\n".join(ret)

        if '--tipos_mercaderia' in sys.argv:
            ret = wsremazucar.ConsultarTiposMercaderia()
            print "\n".join(ret)

        if '--tipos_embalaje' in sys.argv:
            ret = wsremazucar.ConsultarTiposEmbalaje()
            print "\n".join(ret)

        if '--tipos_unidades' in sys.argv:
            ret = wsremazucar.ConsultarTiposUnidades()
            print "\n".join(ret)

        if '--tipos_categoria_emisor' in sys.argv:
            ret = wsremazucar.ConsultarTiposCategoriaEmisor()
            print "\n".join(ret)

        if '--tipos_categoria_receptor' in sys.argv:
            ret = wsremazucar.ConsultarTiposCategoriaReceptor()
            print "\n".join(ret)

        if '--tipos_estados' in sys.argv:
            ret = wsremazucar.ConsultarTiposEstado()
            print "\n".join(ret)

        if '--paises' in sys.argv:
            ret = wsremazucar.ConsultarPaises()
            print "\n".join(ret)

        if '--grupos_azucar' in sys.argv:
            ret = wsremazucar.ConsultarGruposAzucar()
            print "\n".join(ret)

        if '--tipos_azucar' in sys.argv:
            for grupo_azucar in wsremazucar.ConsultarGruposAzucar(sep=None):
                ret = wsremazucar.ConsultarTiposAzucar(grupo_azucar['codigo'])
                print "\n".join(ret)

        if '--codigos_domicilio' in sys.argv:
            cuit = raw_input("Cuit Titular Domicilio: ")
            ret = wsremazucar.ConsultarCodigosDomicilio(cuit)
            print "\n".join(ret)

        if wsremazucar.Errores or wsremazucar.ErroresFormato:
            print "Errores:", wsremazucar.Errores, wsremazucar.ErroresFormato

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
