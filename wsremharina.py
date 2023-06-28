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

"""Módulo para obtener Remito Electronico Harinero:
del servicio web RemHarinaService versión 2.0 de AFIP (RG4514/19)
"""
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import input

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2018-2023 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.07c"

LICENCIA = """
wsremhairna.py: Interfaz para generar Remito Electrónico Harinero AFIP v2.0
traslado de harinas de trigo y subproductos derivados de la molienda de trigo.
Resolución General Conjunta 4514/2019
Copyright (C) 2019 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoHarinero

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
  --tipos_mercaderia: tipo de mercaderias
  --tipos_unidades: tipo de mercaderias
  --tipos_embalaje: tipos de embalajes
  --tipos_estados: estados posibles en los que puede estar un remito harinero
  --paises: consulta cuit y codigos de paises
  --puntos_emision: puntos de emision habilitados
  --codigos_domicilio: codigos de depositos habilitados para el cuit

Ver wsremharina.ini para parámetros de configuración (URL, certificados, etc.)"
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
    "https://serviciosjava.afip.gob.ar/wsremharina/RemHarinaService?wsdl",
    "https://fwshomo.afip.gov.ar/wsremharina/RemHarinaService?wsdl",
]

DEBUG = False
XML = False
CONFIG_FILE = "wsremharina.ini"
HOMO = False
ENCABEZADO = []


class WSRemHarina(BaseWS):
    "Interfaz para el WebService de Remito Electronico Carnico (Version 3)"
    _public_methods_ = [
        "Conectar",
        "Dummy",
        "SetTicketAcceso",
        "DebugLog",
        "GenerarRemito",
        "EmitirRemito",
        "AutorizarRemito",
        "AnularRemito",
        "ConsultarRemito",
        "InformarContingencia",
        "ModificarViaje",
        "RegistrarRecepcion",
        "ConsultarUltimoRemitoEmitido",
        "CrearRemito",
        "AgregarViaje",
        "AgregarVehiculo",
        "AgregarMercaderia",
        "AgregarReceptor",
        "AgregarDepositario",
        "AgregarTransportista",
        "AgregarDatosAutorizacion",
        "AgregarContingencia",
        "ConsultarTiposMercaderia",
        "ConsultarTiposEmbalaje",
        "ConsultarTiposUnidades",
        "ConsultarTiposComprobante",
        "ConsultarPaises",
        "ConsultarReceptoresValidos",
        "ConsultarTiposEstado",
        "ConsultarTiposContingencia",
        "ConsultarCodigosDomicilio",
        "ConsultarPuntosEmision",
        "SetParametros",
        "SetParametro",
        "GetParametro",
        "AnalizarXml",
        "ObtenerTagXml",
        "LoadTestXML",
    ]
    _public_attrs_ = [
        "XmlRequest",
        "XmlResponse",
        "Version",
        "Traceback",
        "Excepcion",
        "LanzarExcepciones",
        "Token",
        "Sign",
        "Cuit",
        "AppServerStatus",
        "DbServerStatus",
        "AuthServerStatus",
        "CodRemito",
        "TipoComprobante",
        "PuntoEmision",
        "NroRemito",
        "CodAutorizacion",
        "FechaVencimiento",
        "FechaEmision",
        "Estado",
        "Resultado",
        "QR",
        "ErrCode",
        "ErrMsg",
        "Errores",
        "ErroresFormato",
        "Observaciones",
        "Obs",
        "Evento",
        "Eventos",
    ]
    _reg_progid_ = "WSRemHarina"
    _reg_clsid_ = "{72BFB9B9-0FD9-497C-8C62-5D41F7029377}"

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
        cuit_titular,
        es_entrega_mostrador=None,
        es_mercaderia_consignacion=None,
        importe_cot=None,
        tipo_emisor=None,
        ruca_est_emisor=None,
        cod_rem_redestinar=None,
        cod_remito=None,
        estado=None,
        observaciones=None,
        **kwargs
    ):
        "Inicializa internamente los datos de un remito para autorizar"
        self.remito = {
            "tipoCmp": tipo_comprobante,
            "puntoEmision": punto_emision,
            "tipoEmisor": tipo_emisor,
            "cuitTitular": cuit_titular,
            "tipoMovimiento": tipo_movimiento,
            "esEntregaMostrador": es_entrega_mostrador,  # S o N
            "esMercaderiaEnConsignacion": es_mercaderia_consignacion,  # S o N
            "importeCot": importe_cot,
            "estado": estado,
            "codRemito": cod_remito,
            "codRemRedestinado": cod_rem_redestinar,
            "rucaEstEmisor": ruca_est_emisor,
            "observaciones": observaciones,
            "arrayMercaderia": [],
            "arrayContingencias": [],
        }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarReceptor(
        self,
        cuit_pais_receptor,
        cuit_receptor=None,
        tipo_dom_receptor=None,
        cod_dom_receptor=None,
        cuit_despachante=None,
        codigo_aduana=None,
        denominacion_receptor=None,
        domicilio_receptor=None,
        **kwargs
    ):
        "Agrega la información referente al receptor  del remito electrónico azucarero"
        receptor = {"cuitPaisReceptor": cuit_pais_receptor}
        if cuit_receptor:
            receptor["receptorNacional"] = {
                "codDomReceptor": cod_dom_receptor,
                "tipoDomReceptor": tipo_dom_receptor,
                "cuitReceptor": cuit_receptor,
            }
        else:
            receptor["receptorExtranjero"] = {
                "codigoAduana": codigo_aduana,
                "cuitDespachante": cuit_despachante,
                "denominacionReceptor": denominacion_receptor,
                "domicilioReceptor": domicilio_receptor,
            }
        self.remito["receptor"] = receptor
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDepositario(
        self,
        tipo_depositario,
        cuit_depositario=None,
        ruca_est_depositario=None,
        tipo_dom_origen=None,
        cod_dom_origen=None,
        **kwargs
    ):
        "Agrega la información referente al depositario del remito electrónico"
        self.remito["depositario"] = {
            "codDomOrigen": cod_dom_origen,
            "cuitDepositario": cuit_depositario,
            "rucaEstDepositario": ruca_est_depositario,
            "tipoDepositario": tipo_depositario,
            "tipoDomOrigen": tipo_dom_origen,
        }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarViaje(self, fecha_inicio_viaje=None, distancia_km=None, **kwargs):
        "Agrega la información referente al viaje del remito electrónico harinero"
        self.remito["viaje"] = {
            "fechaInicioViaje": fecha_inicio_viaje,
            "distanciaKm": distancia_km,
            "vehiculo": {},
        }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarTransportista(
        self,
        cod_pais_transportista=None,
        cuit_transportista=None,
        cuit_conductor=None,
        apellido_conductor=None,
        cedula_conductor=None,
        denom_transportista=None,
        id_impositivo=None,
        nombre_conductor=None,
        **kwargs
    ):
        "Agrega la información referente al transportista del remito electrónico harinero"
        self.remito["viaje"]["transportista"] = {
            "codPaisTransportista": cod_pais_transportista,
        }
        if cuit_transportista:
            self.remito["viaje"]["transportista"]["transporteNacional"] = {
                "cuitTransportista": cuit_transportista,
                "cuitConductor": cuit_conductor,
            }
        else:
            self.remito["viaje"]["transportista"]["transporteExtranjero"] = {
                "apellidoConductor": apellido_conductor,
                "cedulaConductor": cedula_conductor,
                "denomTransportista": denom_transportista,
                "idImpositivo": id_impositivo,
                "nombreConductor": nombre_conductor,
            }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarVehiculo(self, dominio_vehiculo, dominio_acoplado=None, **kwargs):
        "Agrega la información referente al vehiculo usado en el viaje del remito electrónico harinero"
        vehiculo = {
            "dominioVehiculo": dominio_vehiculo,
            "arrayDominioAcoplado": [{"identificador": dominio_acoplado}],
        }
        self.remito["viaje"]["vehiculo"] = {"automotor": vehiculo}
        return True

    @inicializar_y_capturar_excepciones
    def AgregarMercaderia(
        self,
        orden,
        cod_tipo,
        cod_tipo_emb,
        cantidad_emb,
        cod_tipo_unidad,
        cant_unidad,
        peso_neto_kg=None,
        peso_neto_rec_kg=None,
        peso_neto_per_kg=None,
        peso_neto_red_kg=None,
        peso_neto_rei_kg=None,
        cod_comer=None,
        desc_comer=None,
        **kwargs
    ):
        "Agrega la información referente a la mercadería del remito electrónico harinero"
        mercaderia = dict(
            orden=orden,
            codTipo=cod_tipo,
            codComer=cod_comer,
            descComer=desc_comer,
            codTipoEmb=cod_tipo_emb,
            cantidadEmb=cantidad_emb,
            codTipoUnidad=cod_tipo_unidad,
            cantidadUnidad=cant_unidad,
            pesoNetoKg=peso_neto_kg,
            pesoNetoRecKg=peso_neto_rec_kg,
            pesoNetoPerKg=peso_neto_per_kg,
            pesoNetoRedKg=peso_neto_red_kg,
            pesoNetoReiKg=peso_neto_rei_kg,
        )
        self.remito["arrayMercaderia"].append(dict(mercaderia=mercaderia))
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
        "Agrega la información referente a los datos de autorización del remito electrónico harinero"
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
        if not self.remito["arrayContingencias"]:
            del self.remito["arrayContingencias"]
        response = self.client.generarRemito(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            idReqCliente=id_req,
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
            out = ret.get("remitoOutput")
            datos_aut = out.get("datosAutAFIP")
            if datos_aut:
                self.NroRemito = datos_aut.get("nroRemito")
                self.CodAutorizacion = datos_aut.get("codAutorizacion")
                self.FechaEmision = datos_aut.get("fechaEmision")
                self.FechaVencimiento = datos_aut.get("fechaVencimiento")
            self.Estado = out.get("estado", ret.get("estadoRemito"))
            self.Resultado = ret.get("resultado")
            self.QR = out.get("qr") or ""
            if archivo:
                f = open(archivo, "wb")
                f.write(self.QR)
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
        self.remito = ret = ret.get("remitoOutput", {})
        rec = ret.get("remito", {})
        id_req = ret.get("idReqCliente", 0)
        self.__analizar_errores(ret)
        self.__analizar_observaciones(ret)
        self.__analizar_evento(ret)
        self.AnalizarRemito(ret)
        return id_req

    @inicializar_y_capturar_excepciones
    def ConsultarRemito(
        self,
        cod_remito=None,
        id_req=None,
        archivo="qr.jpg",
        tipo_comprobante=None,
        punto_emision=None,
        nro_comprobante=None,
        cuit_emisor=None,
        **kwargs
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
        self.remito = rec = ret.get("remitoOutput", {})
        self.__analizar_errores(ret)
        self.__analizar_observaciones(ret)
        self.__analizar_evento(ret)
        self.AnalizarRemito(rec, archivo)
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
        )["codigoDescripcionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCodigoDescripcion", [])
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
        )["codigoDescripcionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCodigoDescripcion", [])
        lista = [it["codigoDescripcion"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposMercaderia(self, sep="||"):
        "Obtener el código y descripción  códigos y la descripción para cada tipo de mercadería"
        ret = self.client.consultarTiposMercaderia(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["codigoDescripcionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCodigoDescripcion", [])
        lista = [it["codigoDescripcion"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposEmbalaje(self, sep="||"):
        "Obtener el código y descripción  códigos y la descripción para cada tipo de embalaje"
        ret = self.client.consultarTiposEmbalaje(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["codigoDescripcionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCodigoDescripcion", [])
        lista = [it["codigoDescripcion"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposUnidades(self, sep="||"):
        "Obtener el código y descripción  códigos y la descripción para cada tipo de unidades de venta"
        ret = self.client.consultarUnidadesVenta(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["codigoDescripcionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCodigoDescripcion", [])
        lista = [it["codigoDescripcion"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposEstado(self, sep="||"):
        "Obtener el código y descripción  códigos y la descripción para cada tipo de estados por los cuales puede pasar un remito"
        ret = self.client.consultarTiposEstado(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["codigoDescripcionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayCodigoDescripcion", [])
        lista = [it["codigoDescripcionString"] for it in array]
        return [
            (u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it)
            if sep
            else it
            for it in lista
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarPaises(self, sep="||"):
        "Obtener el código y descripción para los paises"
        ret = self.client.consultarPaises(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarCodigosPaisReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayPaises", [])
        lista = [it["pais"] for it in array]
        return [
            (
                u"%s {codigo} %s {cuit} %s {nombre} %s {tipoSujeto} %s"
                % (sep, sep, sep, sep, sep)
            ).format(**it)
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

    def ConsultarPuntosEmision(self, sep="||"):
        "Retorna los Puntos de Emision que posee la CUIT representada."
        ret = self.client.consultarPuntosEmision(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )["consultarPuntosEmisionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("arrayPuntosEmision", [])
        if sep is None:
            return dict([(it["codigo"], it["descripcion"]) for it in array])
        else:
            return [
                ("%s %%s %s %%s %s" % (sep, sep, sep))
                % (it["codigo"], it["descripcion"])
                for it in array
            ]

    @inicializar_y_capturar_excepciones
    def ConsultarReceptoresValidos(self, cuit_titular, sep="||"):
        "Obtener el código de depositos que tiene habilitados para operar el cuit informado"
        res = self.client.consultarReceptoresValidos(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            arrayReceptores=[{"receptores": {"cuitReceptor": cuit_titular}}],
        )
        ret = res["consultarReceptoresValidosReturn"]
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
INSTALL_DIR = WSRemHarina.InstallDir = get_install_dir()


def main():
    global DEBUG, XML, CONFIG_FILE, HOMO
    if "--ayuda" in sys.argv:
        print(LICENCIA)
        print(AYUDA)
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register

        win32com.server.register.UseCommandLine(WSRemHarina)
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
        CUIT = config.get("WSRemHarina", "CUIT")
        ENTRADA = config.get("WSRemHarina", "ENTRADA")
        SALIDA = config.get("WSRemHarina", "SALIDA")

        if config.has_option("WSAA", "URL") and not HOMO:
            wsaa_url = config.get("WSAA", "URL")
        else:
            wsaa_url = None
        if config.has_option("WSRemHarina", "URL") and not HOMO:
            wsremharina_url = config.get("WSRemHarina", "URL")
        else:
            wsremharina_url = WSDL[HOMO]

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
            print("wsremharina_url:", wsremharina_url)

        # obteniendo el TA
        from pyafipws.wsaa import WSAA

        wsaa = WSAA()
        ta = wsaa.Autenticar("wsremharina", CERT, PRIVATEKEY, wsaa_url, debug=DEBUG)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wsremharina = WSRemHarina()
        wsremharina.Conectar(wsdl=wsremharina_url)
        wsremharina.SetTicketAcceso(ta)
        wsremharina.Cuit = CUIT
        ok = None

        if "--dummy" in sys.argv:
            ret = wsremharina.Dummy()
            print("AppServerStatus", wsremharina.AppServerStatus)
            print("DbServerStatus", wsremharina.DbServerStatus)
            print("AuthServerStatus", wsremharina.AuthServerStatus)
            sys.exit(0)

        if "--ult" in sys.argv:
            try:
                pto_emision = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError as ValueError:
                pto_emision = 1
            try:
                tipo_comprobante = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError as ValueError:
                tipo_comprobante = 995
            rec = {}
            print(
                "Consultando ultimo remito pto_emision=%s tipo_comprobante=%s"
                % (pto_emision, tipo_comprobante)
            )
            ok = wsremharina.ConsultarUltimoRemitoEmitido(tipo_comprobante, pto_emision)
            if wsremharina.Excepcion:
                print("EXCEPCION:", wsremharina.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wsremharina.Traceback, file=sys.stderr)
            print("Ultimo Nro de Remito", wsremharina.NroRemito)
            print("Errores:", wsremharina.Errores)

        if "--prueba" in sys.argv:
            rec = dict(
                tipo_comprobante=993,  # 993 o 994
                punto_emision=1,
                tipo_movimiento="ENV",  # ENV: envio, RET: retiro, CAN: canje, RED: redestino
                cuit_titular="20287531894",
                es_entrega_mostrador="N",
                importe_cot="10000.0",
                tipo_emisor="I",  # U: Usiario de molienda de trigo I: Industrial
                ruca_est_emisor=1031,
                cod_rem_redestinar=None,
                cod_remito=None,
                estado=None,
                id_req=int(time.time()),
            )
            rec["receptor"] = dict(
                cuit_pais_receptor="55000002002",
                cuit_receptor="20111111112",
                tipo_dom_receptor=1,  # 1: fiscal, 3: comercial
                cod_dom_receptor=1234,
                cuit_despachante=None,
                codigo_aduana=None,
                denominacion_receptor=None,
                domicilio_receptor=None,
            )
            rec["depositario"] = dict(
                tipo_depositario="E",  # I: Industrial de Molino/Trigo
                # E: Emisor D: Depositario
                cuit_depositario="23000000019",
                ruca_est_depositario=7297,
                tipo_dom_origen=1,
                cod_dom_origen=1,
            )
            if "--autorizar" in sys.argv:
                rec["estado"] = "A"  # 'A': Autorizar, 'D': Denegar
            rec["viaje"] = dict(fecha_inicio_viaje="2018-10-01", distancia_km=999)
            rec["viaje"]["transportista"] = dict(
                cod_pais_transportista=200,
                cuit_transportista="20138835899",
                cuit_conductor="20333333334",
            )
            rec["viaje"]["vehiculo"] = dict(
                dominio_vehiculo="AAA000", dominio_acoplado="ZZZ000"
            )
            rec["mercaderias"] = [
                dict(
                    orden=1,
                    cod_tipo=0,
                    cod_tipo_emb=0,
                    cantidad_emb=0,
                    cod_tipo_unidad=0,
                    cant_unidad=0,
                )
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
            wsremharina.CrearRemito(**rec)
            wsremharina.AgregarReceptor(**rec["receptor"])
            wsremharina.AgregarDepositario(**rec["depositario"])
            wsremharina.AgregarViaje(**rec["viaje"])
            wsremharina.AgregarVehiculo(**rec["viaje"]["vehiculo"])
            wsremharina.AgregarTransportista(**rec["viaje"]["transportista"])
            for mercaderia in rec["mercaderias"]:
                wsremharina.AgregarMercaderia(**mercaderia)
            datos_aut = rec["datos_autorizacion"]
            if datos_aut:
                wsremharina.AgregarDatosAutorizacion(**datos_aut)
            for contingencia in rec["contingencias"]:
                wsremharina.AgregarContingencias(**contingencia)

        if "--consultar" in sys.argv:
            if not "--cargar" in sys.argv:
                try:
                    cod_remito = sys.argv[sys.argv.index("--consultar") + 1]
                    rec = {"cod_remito": cod_remito}
                except IndexError as ValueError:
                    cod_remito = None
            print(
                "Consultando remito cod_remito=%s nro_comprobante=%s"
                % (rec.get("cod_remito"), rec.get("nro_comprobante"))
            )
            rec["cuit_emisor"] = wsremharina.Cuit
            ok = wsremharina.ConsultarRemito(**rec)
            if wsremharina.Excepcion:
                print("EXCEPCION:", wsremharina.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wsremharina.Traceback, file=sys.stderr)
            print("Ultimo Nro de Remito", wsremharina.NroRemito)
            print("Errores:", wsremharina.Errores)
            if DEBUG:
                import pprint

                pprint.pprint(wsremharina.remito)

        if "--generar" in sys.argv:
            if "--testing" in sys.argv:
                wsremharina.LoadTestXML("tests/xml/wsremharina.xml")  # cargo respuesta

            ok = wsremharina.GenerarRemito(id_req=rec["id_req"], archivo="qr.jpg")

        if "--emitir" in sys.argv:
            ok = wsremharina.EmitirRemito()

        if "--autorizar" in sys.argv:
            ok = wsremharina.AutorizarRemito()

        if "--anular" in sys.argv:
            ok = wsremharina.AnularRemito()

        if ok is not None:
            print("Resultado: ", wsremharina.Resultado)
            print("Cod Remito: ", wsremharina.CodRemito)
            if wsremharina.CodAutorizacion:
                print("Numero Remito: ", wsremharina.NroRemito)
                print("Cod Autorizacion: ", wsremharina.CodAutorizacion)
                print("Fecha Emision", wsremharina.FechaEmision)
                print("Fecha Vencimiento", wsremharina.FechaVencimiento)
            print("Estado: ", wsremharina.Estado)
            print("Observaciones: ", wsremharina.Observaciones)
            print("Errores:", wsremharina.Errores)
            print("Errores Formato:", wsremharina.ErroresFormato)
            print("Evento:", wsremharina.Evento)
            rec["cod_remito"] = wsremharina.CodRemito
            rec["resultado"] = wsremharina.Resultado
            rec["observaciones"] = wsremharina.Observaciones
            rec["fecha_emision"] = wsremharina.FechaEmision
            rec["fecha_vencimiento"] = wsremharina.FechaVencimiento
            rec["errores"] = wsremharina.Errores
            rec["errores_formato"] = wsremharina.ErroresFormato
            rec["evento"] = wsremharina.Evento

        if "--grabar" in sys.argv:
            with open(SALIDA, "w") as archivo:
                json.dump(
                    rec, archivo, sort_keys=True, indent=4, default=json_serializer
                )

        # Recuperar parámetros:

        if "--tipos_comprobante" in sys.argv:
            ret = wsremharina.ConsultarTiposComprobante()
            print("\n".join(ret))

        if "--tipos_contingencia" in sys.argv:
            ret = wsremharina.ConsultarTiposContingencia()
            print("\n".join(ret))

        if "--tipos_mercaderia" in sys.argv:
            ret = wsremharina.ConsultarTiposMercaderia()
            print("\n".join(ret))

        if "--tipos_embalaje" in sys.argv:
            ret = wsremharina.ConsultarTiposEmbalaje()
            print("\n".join(ret))

        if "--tipos_unidades" in sys.argv:
            ret = wsremharina.ConsultarTiposUnidades()
            print("\n".join(ret))

        if "--tipos_estados" in sys.argv:
            ret = wsremharina.ConsultarTiposEstado()
            print("\n".join(ret))

        if "--paises" in sys.argv:
            ret = wsremharina.ConsultarPaises()
            print("\n".join(ret))

        if "--codigos_domicilio" in sys.argv:
            cuit = input("Cuit Titular Domicilio: ")
            ret = wsremharina.ConsultarCodigosDomicilio(cuit)
            print("\n".join(ret))

        if "--puntos_emision" in sys.argv:
            ret = wsremharina.ConsultarPuntosEmision()
            print("\n".join(ret))

        if "--receptores" in sys.argv:
            try:
                cuit = int(sys.argv[-1])
            except:
                cuit = raw_input("Cuit Receptor: ")
            ret = wsremharina.ConsultarReceptoresValidos(cuit)
            print("Resultado:", wsremharina.Resultado)

        if wsremharina.Errores or wsremharina.ErroresFormato:
            print("Errores:", wsremharina.Errores, wsremharina.ErroresFormato)

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