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

"""Módulo para obtener Remito Electronico Carnico:
del web service WSRemCarne versión 3.0 de AFIP (RG4256/18 y RG4303/18)
"""
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from builtins import input
from builtins import str

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2018-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.03a"

LICENCIA = """
wsremcarne.py: Interfaz para generar Remito Electrónico Cárnico AFIP v3.0
Remito de Carnes y subproductos derivados de la faena de bovinos y porcinos
Resolución General 4256/18 y Resolución General 4303/18.
Copyright (C) 2018-2019 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCarnico

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA = """
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
  --tipos_estados: estados posibles en los que puede estar un remito cárnico
  --grupos_carne' grupos de los distintos tipos de cortes de carne
  --tipos_carne': tipos de corte de carne
  --codigos_domicilio: codigos de depositos habilitados para el cuit

Ver wsremcarne.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time, base64
from pyafipws.utils import date
import traceback
from pysimplesoap.client import SoapFault
from pyafipws import utils

# importo funciones compartidas:
from pyafipws.utils import (
    json,
    BaseWS,
    inicializar_y_capturar_excepciones,
    get_install_dir,
    json_serializer,
)


# constantes de configuración (producción/homologación):

WSDL = [
    "https://fwshomo.afip.gov.ar/wsremcarne/RemCarneService?wsdl",
    "https://serviciosjava.afip.gob.ar/wsremcarne/RemCarneService?wsdl",
    
]

DEBUG = False
XML = False
CONFIG_FILE = "wsremcarne.ini"
HOMO = False
ENCABEZADO = []


class WSRemCarne(BaseWS):
    "Interfaz para el WebService de Remito Electronico Carnico (Version 3)"
    _public_methods_ = ['Conectar', 'Dummy', 'SetTicketAcceso', 'DebugLog',
                        'GenerarRemito', 'EmitirRemito', 'AutorizarRemito', 'AnularRemito', 'ConsultarRemito',
                        'InformarContingencia', 'ModificarViaje', 'RegistrarRecepcion',  'ConsultarUltimoRemitoEmitido',
                        'CrearRemito', 'AgregarViaje', 'AgregarVehiculo', 'AgregarMercaderia',
                        'AgregarDatosAutorizacion', 'AgregarContingencia',
                        'ConsultarTiposCarne', 'ConsultarTiposCategoriaEmisor', 'ConsultarTiposCategoriaReceptor',
                        'ConsultarTiposComprobante', 'ConsultarTiposContingencia', 'ConsultarTiposEstado',
                        'ConsultarCodigosDomicilio', 'ConsultarGruposCarne', 'ConsultarPuntosEmision',
                        'ConsultarReceptoresValidos',
                        'SetParametros', 'SetParametro', 'GetParametro', 'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        ]
    _public_attrs_ = ['XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'Excepcion', 'LanzarExcepciones',
                      'Token', 'Sign', 'Cuit', 'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
                      'CodRemito', 'TipoComprobante', 'PuntoEmision',
                      'NroRemito', 'CodAutorizacion', 'FechaVencimiento', 'FechaEmision', 'Estado', 'Resultado', 'QR',
                      'ErrCode', 'ErrMsg', 'Errores', 'ErroresFormato', 'Observaciones', 'Obs', 'Evento', 'Eventos',
                     ]
    _reg_progid_ = "WSRemCarne"
    _reg_clsid_ = "{71DB0CB9-2ED7-4226-A1E6-C3FA7FB18F41}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL[HOMO]
    LanzarExcepciones = False
    Version = "%s %s" % (__version__, HOMO and "Homologación" or "")

    def Conectar(self, *args, **kwargs):
        ret = BaseWS.Conectar(self, *args, **kwargs)
        return ret

    def inicializar(self):
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.CodRemito = self.TipoComprobante = self.PuntoEmision = None
        self.NroRemito = (
            self.CodAutorizacion
        ) = self.FechaVencimiento = self.FechaEmision = None
        self.Estado = self.Resultado = self.QR = None
        self.Errores = []
        self.ErroresFormato = []
        self.Observaciones = []
        self.Eventos = []
        self.Evento = self.ErrCode = self.ErrMsg = self.Obs = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.Errores = [err["codigoDescripcion"] for err in ret.get("arrayErrores", [])]
        self.ErroresFormato = [
            err["codigoDescripcionString"] for err in ret.get("arrayErroresFormato", [])
        ]
        errores = self.Errores + self.ErroresFormato
        self.ErrCode = " ".join(["%(codigo)s" % err for err in errores])
        self.ErrMsg = "\n".join(
            ["%(codigo)s: %(descripcion)s" % err for err in errores]
        )

    def __analizar_observaciones(self, ret):
        "Comprueba y extrae observaciones si existen en la respuesta XML"
        self.Observaciones = [
            obs["codigoDescripcion"] for obs in ret.get("arrayObservaciones", [])
        ]
        self.Obs = "\n".join(
            ["%(codigo)s: %(descripcion)s" % obs for obs in self.Observaciones]
        )

    def __analizar_evento(self, ret):
        "Comprueba y extrae el wvento informativo si existen en la respuesta XML"
        evt = ret.get("evento")
        if evt:
            self.Eventos = [evt]
            self.Evento = "%(codigo)s: %(descripcion)s" % evt

    @inicializar_y_capturar_excepciones
    def CrearRemito(
        self,
        tipo_comprobante,
        punto_emision,
        tipo_movimiento,
        categoria_emisor,
        cuit_titular_mercaderia,
        cod_dom_origen,
        tipo_receptor,
        categoria_receptor=None,
        cuit_receptor=None,
        cuit_depositario=None,
        cod_dom_destino=None,
        cod_rem_redestinar=None,
        cod_remito=None,
        estado=None,
        **kwargs
    ):
        "Inicializa internamente los datos de un remito para autorizar"
        self.remito = {
            "tipoComprobante": tipo_comprobante,
            "puntoEmision": punto_emision,
            "categoriaEmisor": categoria_emisor,
            "cuitTitularMercaderia": cuit_titular_mercaderia,
            "cuitDepositario": cuit_depositario,
            "tipoReceptor": tipo_receptor,
            "categoriaReceptor": categoria_receptor,
            "cuitReceptor": cuit_receptor,
            "codDomOrigen": cod_dom_origen,
            "codDomDestino": cod_dom_destino,
            "tipoMovimiento": tipo_movimiento,
            "estado": estado,
            "codRemito": cod_remito,
            "codRemRedestinado": cod_rem_redestinar,
            "arrayMercaderias": [],
            "arrayContingencias": [],
        }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarViaje(
        self,
        cuit_transportista=None,
        cuit_conductor=None,
        fecha_inicio_viaje=None,
        distancia_km=None,
        **kwargs
    ):
        "Agrega la información referente al viaje del remito electrónico cárnico"
        self.remito["viaje"] = {
            "cuitTransportista": cuit_transportista,
            "cuitConductor": cuit_conductor,
            "fechaInicioViaje": fecha_inicio_viaje,
            "distanciaKm": distancia_km,
            "vehiculo": {},
        }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarVehiculo(self, dominio_vehiculo=None, dominio_acoplado=None, **kwargs):
        "Agrega la información referente al vehiculo usado en el viaje del remito electrónico cárnico"
        self.remito["viaje"]["vehiculo"] = {
            "dominioVehiculo": dominio_vehiculo,
            "dominioAcoplado": dominio_acoplado,
        }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarMercaderia(
        self,
        orden=None,
        cod_tipo_prod=None,
        kilos=None,
        unidades=None,
        tropa=None,
        kilos_rec=None,
        unidades_rec=None,
        **kwargs
    ):
        "Agrega la información referente a la mercadería del remito electrónico cárnico"
        mercaderia = dict(
            orden=orden,
            tropa=tropa,
            codTipoProd=cod_tipo_prod,
            kilos=kilos,
            unidades=unidades,
            kilosRec=kilos_rec,
            unidadesRec=unidades_rec,
        )
        self.remito["arrayMercaderias"].append(dict(mercaderia=mercaderia))
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDatosAutorizacion(
        self,
        nro_remito=None,
        cod_autorizacion=None,
        fecha_emision=None,
        fecha_vencimiento=None,
        **kwargs
    ):
        "Agrega la información referente a los datos de autorización del remito electrónico cárnico"
        self.remito["datosEmision"] = dict(
            nroRemito=nro_remito,
            codAutorizacion=cod_autorizacion,
            fechaEmision=fecha_emision,
            fechaVencimiento=fecha_vencimiento,
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarContingencias(self, tipo=None, observacion=None, **kwargs):
        "Agrega la información referente a los opcionales de la liq. seq."
        contingencia = dict(tipoContingencia=tipo, observacion=observacion)
        self.remito["arrayContingencias"].append(dict(contingencia=contingencia))
        return True

    @inicializar_y_capturar_excepciones
    def GenerarRemito(self, id_req, archivo="qr.png"):
        "Informar los datos necesarios para la generación de un remito nuevo"
        if not self.remito.get("arrayContingencias"):
            if "arrayContingencias" in self.remito:
                del self.remito["arrayContingencias"]
        response = self.client.generarRemito(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            idReq=id_req,
            remito=self.remito,
        )
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
            self.CodRemito = ret.get("codRemito")
            self.TipoComprobante = ret.get("tipoComprobante")
            self.PuntoEmision = ret.get("puntoEmision")
            datos_aut = ret.get("datosEmision")
            if datos_aut:
                self.NroRemito = datos_aut.get("nroRemito")
                self.CodAutorizacion = str(datos_aut.get("codAutorizacion"))
                self.FechaEmision = datos_aut.get("fechaEmision")
                self.FechaVencimiento = datos_aut.get("fechaVencimiento")
            self.Estado = ret.get("estado")
            self.Resultado = ret.get("resultado")
            self.QR = ret.get("qr") or ""
            if archivo:
                f = open(archivo, "wb")
                f.write((self.QR).encode('ascii'))
                f.close()

    @inicializar_y_capturar_excepciones
    def EmitirRemito(self, archivo="qr.png"):
        "Emitir Remitos que se encuentren en estado Pendiente de Emitir."
        response = self.client.emitirRemito(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            codRemito=self.remito["codRemito"],
            viaje=self.remito.get("viaje"),
        )
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
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            codRemito=self.remito["codRemito"],
            estado=self.remito["estado"],
        )
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
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            codRemito=self.remito["codRemito"],
        )
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
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            tipoComprobante=tipo_comprobante,
            puntoEmision=punto_emision,
        )
        ret = response.get("consultarUltimoRemitoReturn", {})
        id_req = ret.get("idReq", 0)
        rec = ret.get("remito", {})
        self.__analizar_errores(ret)
        self.__analizar_observaciones(ret)
        self.__analizar_evento(ret)
        self.AnalizarRemito(rec)
        return id_req

    @inicializar_y_capturar_excepciones
    def ConsultarRemito(
        self,
        cod_remito=None,
        id_req=None,
        tipo_comprobante=None,
        punto_emision=None,
        nro_comprobante=None,
        cuit_emisor=None,
    ):
        "Obtener los datos de un remito generado"
        response = self.client.consultarRemito(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            codRemito=cod_remito,
            idReq=id_req,
            cuitEmisor=cuit_emisor,
            tipoComprobante=tipo_comprobante,
            puntoEmision=punto_emision,
            nroComprobante=nro_comprobante,
        )
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
        results = self.client.dummy()["dummyReturn"]
        self.AppServerStatus = str(results["appserver"])
        self.DbServerStatus = str(results["dbserver"])
        self.AuthServerStatus = str(results["authserver"])

    @inicializar_y_capturar_excepciones
    def ConsultarTiposComprobante(self, sep="||"):
        "Obtener el código y descripción para tipo de comprobante"
        ret = self.client.consultarTiposComprobante(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarTiposComprobanteReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayTiposComprobante", [])
        lista = [it["codigoDescripcion"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposContingencia(self, sep="||"):
        "Obtener el código y descripción para cada tipo de contingencia que puede reportar"
        ret = self.client.consultarTiposContingencia(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarTiposContingenciaReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayTiposContingencia", [])
        lista = [it["codigoDescripcion"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposCategoriaEmisor(self, sep="||"):
        "Obtener el código y descripción para tipos de categorías de emisor"
        ret = self.client.consultarTiposCategoriaEmisor(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarCategoriasEmisorReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCategoriasEmisor", [])
        lista = [it["codigoDescripcionString"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposCategoriaReceptor(self, sep="||"):
        "Obtener el código y descripción para cada tipos de categorías de receptor"
        ret = self.client.consultarTiposCategoriaReceptor(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarCategoriasReceptorReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCategoriasReceptor", [])
        lista = [it["codigoDescripcionString"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposEstado(self, sep="||"):
        "Obtener el código y descripción para cada estado posibles en los que puede estar un remito cárnico"
        ret = self.client.consultarTiposEstado(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarTiposEstadoReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayTiposEstado", [])
        lista = [it["codigoDescripcionString"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarGruposCarne(self, sep="||"):
        "Obtener el código y descripción para los grupos de los distintos tipos de cortes de carne"
        ret = self.client.consultarGruposCarne(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarGruposCarneReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayGruposCarne", [])
        lista = [it["codigoDescripcionString"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposCarne(self, cod_grupo_carne=1, sep="||"):
        "Obtener el código y descripción para tipos de corte de carne"
        ret = self.client.consultarTiposCarne(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            codGrupoCarne=cod_grupo_carne,
        )["consultarTiposCarneReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayTiposCarne", [])
        lista = [it["codigoDescripcionString"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarCodigosDomicilio(self, cuit_titular=1, sep="||"):
        "Obtener el código de depositos que tiene habilitados para operar el cuit informado"
        ret = self.client.consultarCodigosDomicilio(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            cuitTitularDomicilio=cuit_titular,
        )["consultarCodigosDomicilioReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayDomicilios", [])
        lista = [it["codigoDescripcion"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarReceptoresValidos(self, cuit_titular, sep="||"):
        "Obtener el código de depositos que tiene habilitados para operar el cuit informado"
        res = self.client.consultarReceptoresValidos(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                            arrayReceptores=[{"receptores": {"cuitReceptor": cuit_titular}}],
                            )
        ret = res['consultarReceptoresValidosReturn']
        self.Resultado = ret["resultado"]
        return True


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"):
    basepath = __file__
elif sys.frozen == "dll":
    import win32api

    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = WSRemCarne.InstallDir = get_install_dir()


def main():
    global DEBUG, XML, CONFIG_FILE, HOMO
    if "--ayuda" in sys.argv:
        print(LICENCIA)
        print(AYUDA)
        return

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register

        win32com.server.register.UseCommandLine(WSRemCarne)
        sys.exit(0)

    from configparser import SafeConfigParser

    try:

        if "--version" in sys.argv:
            print("Versión: ", __version__)

        for arg in sys.argv[1:]:
            if arg.startswith("--"):
                break
            print("Usando configuración:", arg)
            CONFIG_FILE = arg

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get("WSAA", "CERT")
        PRIVATEKEY = config.get("WSAA", "PRIVATEKEY")
        CUIT = config.get("WSRemCarne", "CUIT")
        ENTRADA = config.get("WSRemCarne", "ENTRADA")
        SALIDA = config.get("WSRemCarne", "SALIDA")

        if config.has_option("WSAA", "URL") and not HOMO:
            wsaa_url = config.get("WSAA", "URL")
        else:
            wsaa_url = None
        if config.has_option("WSRemCarne", "URL") and not HOMO:
            wsremcarne_url = config.get("WSRemCarne", "URL")
        else:
            wsremcarne_url = WSDL[HOMO]

        if config.has_section("DBF"):
            conf_dbf = dict(config.items("DBF"))
            if DEBUG:
                print("conf_dbf", conf_dbf)
        else:
            conf_dbf = {}

        DEBUG = "--debug" in sys.argv
        XML = "--xml" in sys.argv

        if DEBUG:
            print("Usando Configuración:")
            print("wsaa_url:", wsaa_url)
            print("wsremcarne_url:", wsremcarne_url)

        # obteniendo el TA
        from pyafipws.wsaa import WSAA

        wsaa = WSAA()
        ta = wsaa.Autenticar("wsremcarne", CERT, PRIVATEKEY, wsaa_url, debug=DEBUG)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wsremcarne = WSRemCarne()
        wsremcarne.Conectar(wsdl=wsremcarne_url)
        wsremcarne.SetTicketAcceso(ta)
        wsremcarne.Cuit = CUIT
        ok = None

        if "--dummy" in sys.argv:
            ret = wsremcarne.Dummy()
            print("AppServerStatus", wsremcarne.AppServerStatus)
            print("DbServerStatus", wsremcarne.DbServerStatus)
            print("AuthServerStatus", wsremcarne.AuthServerStatus)
            return

        if "--ult" in sys.argv:
            try:
                pto_emision = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError as ValueError:
                pto_emision = 1
            try:
                tipo_cbte = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError as ValueError:
                tipo_comprobante = 995
            rec = {}
            print(
                "Consultando ultimo remito pto_emision=%s tipo_comprobante=%s"
                % (pto_emision, tipo_comprobante)
            )
            ok = wsremcarne.ConsultarUltimoRemitoEmitido(tipo_comprobante, pto_emision)
            if wsremcarne.Excepcion:
                print("EXCEPCION:", wsremcarne.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wsremcarne.Traceback, file=sys.stderr)
            print("Ultimo Nro de Remito", wsremcarne.NroRemito)
            print("Errores:", wsremcarne.Errores)

        if "--consultar" in sys.argv:
            try:
                cod_remito = sys.argv[sys.argv.index("--consultar") + 1]
            except IndexError as ValueError:
                cod_remito = None
            rec = {}
            print("Consultando remito cod_remito=%s" % (cod_remito,))
            ok = wsremcarne.ConsultarRemito(cod_remito)
            if wsremcarne.Excepcion:
                print("EXCEPCION:", wsremcarne.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wsremcarne.Traceback, file=sys.stderr)
            print("Ultimo Nro de Remito", wsremcarne.NroRemito)
            print("Errores:", wsremcarne.Errores)
            if DEBUG:
                import pprint

                pprint.pprint(wsremcarne.remito)

        if "--prueba" in sys.argv:
            rec = dict(
                tipo_comprobante=995,
                punto_emision=1,
                categoria_emisor=1,
                tipo_movimiento="ENV",  # ENV: Envio Normal, PLA: Retiro en planta, REP: Reparto, RED: Redestino
                cuit_titular_mercaderia="20222222223",
                cod_dom_origen=1,
                tipo_receptor="EM",  # 'EM': DEPOSITO EMISOR, 'MI': MERCADO INTERNO, 'RP': REPARTO
                categoria_receptor=1,
                id_req=int(time.time()),
                cuit_receptor="20111111112",
                cuit_depositario=None,
                cod_dom_destino=1,
                cod_rem_redestinar=None,
                cod_remito=30,
            )
            if "--autorizar" in sys.argv:
                rec["estado"] = "A"  # 'A': Autorizar, 'D': Denegar
            rec["viaje"] = dict(
                cuit_transportista="20333333334",
                cuit_conductor="20333333334",
                fecha_inicio_viaje="2018-10-01",
                distancia_km=999,
            )
            rec["viaje"]["vehiculo"] = dict(
                dominio_vehiculo="AAA000", dominio_acoplado="ZZZ000"
            )
            rec["mercaderias"] = [
                dict(orden=1, tropa=1, cod_tipo_prod="2.13", kilos=10, unidades=1)
            ]
            rec[
                "datos_autorizacion"
            ] = None  # dict(nro_remito=None, cod_autorizacion=None, fecha_emision=None, fecha_vencimiento=None)
            rec["contingencias"] = [dict(tipo=1, observacion="anulacion")]
            with open(ENTRADA, "w") as archivo:
                json.dump(rec, archivo, sort_keys=True, indent=4)

        if "--cargar" in sys.argv:
            with open(ENTRADA, "r") as archivo:
                rec = json.load(archivo)
            wsremcarne.CrearRemito(**rec)
            wsremcarne.AgregarViaje(**rec["viaje"])
            wsremcarne.AgregarVehiculo(**rec["viaje"]["vehiculo"])
            for mercaderia in rec["mercaderias"]:
                wsremcarne.AgregarMercaderia(**mercaderia)
            datos_aut = rec["datos_autorizacion"]
            if datos_aut:
                wsremcarne.AgregarDatosAutorizacion(**datos_aut)
            for contingencia in rec["contingencias"]:
                wsremcarne.AgregarContingencias(**contingencia)

        if "--generar" in sys.argv:
            if "--testing" in sys.argv:
                wsremcarne.LoadTestXML("tests/xml/wsremcarne.xml")  # cargo respuesta

            ok = wsremcarne.GenerarRemito(id_req=rec["id_req"], archivo="qr.jpg")

        if "--emitir" in sys.argv:
            ok = wsremcarne.EmitirRemito()

        if "--autorizar" in sys.argv:
            ok = wsremcarne.AutorizarRemito()

        if "--anular" in sys.argv:
            ok = wsremcarne.AnularRemito()

        if ok is not None:
            print("Resultado: ", wsremcarne.Resultado)
            print("Cod Remito: ", wsremcarne.CodRemito)
            if wsremcarne.CodAutorizacion:
                print("Numero Remito: ", wsremcarne.NroRemito)
                print("Cod Autorizacion: ", wsremcarne.CodAutorizacion)
                print("Fecha Emision", wsremcarne.FechaEmision)
                print("Fecha Vencimiento", wsremcarne.FechaVencimiento)
            print("Estado: ", wsremcarne.Estado)
            print("Observaciones: ", wsremcarne.Observaciones)
            print("Errores:", wsremcarne.Errores)
            print("Errores Formato:", wsremcarne.ErroresFormato)
            print("Evento:", wsremcarne.Evento)
            rec["nro_remito"] = wsremcarne.NroRemito
            rec["cod_autorizacion"] = wsremcarne.CodAutorizacion
            rec["cod_remito"] = wsremcarne.CodRemito
            rec["resultado"] = wsremcarne.Resultado
            rec["observaciones"] = wsremcarne.Observaciones
            rec["fecha_emision"] = wsremcarne.FechaEmision
            rec["fecha_vencimiento"] = wsremcarne.FechaVencimiento
            rec["errores"] = wsremcarne.Errores
            rec["errores_formato"] = wsremcarne.ErroresFormato
            rec["evento"] = wsremcarne.Evento

        if "--grabar" in sys.argv:
            with open(SALIDA, "w") as archivo:
                json.dump(
                    rec, archivo, sort_keys=True, indent=4, default=json_serializer
                )

        # Recuperar parámetros:

        if "--tipos_comprobante" in sys.argv:
            ret = wsremcarne.ConsultarTiposComprobante()
            print("\n".join(ret))

        if "--tipos_contingencia" in sys.argv:
            ret = wsremcarne.ConsultarTiposContingencia()
            print("\n".join(ret))

        if "--tipos_categoria_emisor" in sys.argv:
            ret = wsremcarne.ConsultarTiposCategoriaEmisor()
            print("\n".join(ret))

        if "--tipos_categoria_receptor" in sys.argv:
            ret = wsremcarne.ConsultarTiposCategoriaReceptor()
            print("\n".join(ret))

        if "--tipos_estados" in sys.argv:
            ret = wsremcarne.ConsultarTiposEstado()
            print("\n".join(ret))

        if "--grupos_carne" in sys.argv:
            ret = wsremcarne.ConsultarGruposCarne()
            print("\n".join(ret))

        if "--tipos_carne" in sys.argv:
            for grupo_carne in wsremcarne.ConsultarGruposCarne(sep=None):
                ret = wsremcarne.ConsultarTiposCarne(grupo_carne["codigo"])
                print("\n".join(ret))

        if "--codigos_domicilio" in sys.argv:
            cuit = input("Cuit Titular Domicilio: ")
            ret = wsremcarne.ConsultarCodigosDomicilio(cuit)
            print("\n".join(ret))

        if '--receptores' in sys.argv:
            try:
                cuit = int(sys.argv[-1])
            except:
                cuit = raw_input("Cuit Receptor: ")
            ret = wsremcarne.ConsultarReceptoresValidos(cuit)
            print("Resultado:", wsremcarne.Resultado)

        if wsremcarne.Errores or wsremcarne.ErroresFormato:
            print("Errores:", wsremcarne.Errores, wsremcarne.ErroresFormato)

        print("hecho.")

    except SoapFault as e:
        print("Falla SOAP:", e.faultcode, e.faultstring.encode("ascii", "ignore"))
        sys.exit(3)
    except Exception as e:
        ex = utils.exception_info()
        print(ex)
        if DEBUG:
            raise
        sys.exit(5)

if __name__ == "__main__":
    main()