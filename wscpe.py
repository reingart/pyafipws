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

from __future__ import print_function
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import input

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

AYUDA = """  # grey
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --prueba: genera y autoriza una rec de prueba (no usar en producción!)
  --dummy: consulta estado de servidores

Ver wscpe.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import base64
import datetime
import os
import sys
import time
import traceback

from pyafipws.utils import date
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
    "https://serviciosjava.afip.gob.ar/cpe-ws/services/wscpe?wsdl",
    "https://fwshomo.afip.gov.ar/wscpe/services/soap?wsdl",
]

# Seteado para ambiente de homologacion/debug.
DEBUG = True
XML = False
CONFIG_FILE = "wscpe.ini"
HOMO = True
ENCABEZADO = []


class WSCPE(BaseWS):
    "Interfaz para el WebService de Carta Porte Electrónica"
    _public_methods_ = [
        "Conectar",
        "Dummy",
        "SetTicketAcceso",
        "DebugLog",
        "AgregarCabecera",
        "AgregarOrigen",
        "AgregarRetiroProductor",
        "AgregarIntervinientes",
        "AgregarDatosCarga",
        "AgregarDestino",
        "AgregarTransporte",
        "AgregarContingencia",
        "DescargadoDestinoCPE",
        "NuevoDestinoDestinatarioCPEFerroviaria",
        "AutorizarCPEAutomotor",
        "ConsultarLocalidadesPorProvincia",
        "ConfirmarArriboCPE",
        "AnularCPE",
        "ConsultaCPEFerroviariaPorNroOperativo",
        "InformarContingencia",
        "ConsultarCPEFerroviaria",
        "ConfirmacionDefinitivaCPEFerroviaria",
        "CerrarContingenciaCPEFerroviaria",
        "ConsultarUltNroOrden",
        "ConsultarCPEAutomotor",
        "NuevoDestinoDestinatarioCPEAutomotor",
        "RegresoOrigenCPEFerroviaria",
        "RegresoOrigenCPEAutomotor",
        "ConsultarLocalidadesProductor",
        "RechazoCPE",
        "ConfirmacionDefinitivaCPEAutomotor",
        "ConsultarProvincias",
        "DesvioCPEFerroviaria",
        "ConsultarTiposGrano",
        "AutorizarCPEFerroviaria",
        "DesvioCPEAutomotor",
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
        "CodCPE",
        "NroOrden",
        "FechaInicioEstado",
        "FechaEmision",
        "FechaVencimiento",
        "Estado",
        "Resultado",
        "PDF",
        "ErrCode",
        "ErrMsg",
        "Errores",
        "ErroresFormato",
        "Observaciones",
        "Obs",
        "Evento",
        "Eventos",
    ]
    _reg_progid_ = "WSCPE"
    _reg_clsid_ = "{37F6A7B5-344E-45C5-9198-0CF7B206F409}"

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
        self.CodCPE = self.NroOrden = None
        self.FechaInicioEstado = self.FechaVencimiento = self.FechaEmision = None
        self.Estado = self.Resultado = self.PDF = None
        self.Errores = []
        self.Evento = self.ErrCode = self.ErrMsg = self.Obs = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = self.Errores = [err["error"] for err in ret.get("errores", [])]
        if errores:
            errores = errores[0]
        self.ErrCode = " ".join(["%(codigo)s" % err for err in errores])
        self.ErrMsg = "\n".join(["%(codigo)s: %(descripcion)s" % err for err in errores])

    def __analizar_observaciones(self, ret):
        "Comprueba y extrae observaciones si existen en la respuesta XML"
        self.Observaciones = [obs["codigoDescripcion"] for obs in ret.get("arrayObservaciones", [])]
        self.Obs = "\n".join(["%(codigo)s: %(descripcion)s" % obs for obs in self.Observaciones])

    def __analizar_evento(self, ret):
        "Comprueba y extrae el wvento informativo si existen en la respuesta XML"
        evt = ret.get("evento")
        if evt:
            self.Eventos = [evt]
            self.Evento = "%(codigo)s: %(descripcion)s" % evt

    @inicializar_y_capturar_excepciones
    def AgregarCabeceraFerroviaria(self, sucursal, nro_orden, planta, **kwargs):
        """Inicializa internamente los datos de cabecera para cpe ferroviaria."""
        self.cpe_ferroviaria["cabecera"] = {
            "sucursal": sucursal,
            "nroOrden": nro_orden,
            "planta": planta,
        }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRetiroProductorFerroviaria(
        self,
        corresponde_retiro_productor=None,
        certificado_coe=None,
        cuit_remitente_comercial_productor=None,
        **kwargs,
    ):
        """Inicializa internamente los datos de retiro de productor para cpe ferroviario."""
        self.cpe_ferroviaria.update({"correspondeRetiroProductor": corresponde_retiro_productor})

        if corresponde_retiro_productor:
            self.cpe_ferroviaria["retiroProductor"] = {
                "certificadoCOE": certificado_coe,
                "cuitRemitenteComercialProductor": cuit_remitente_comercial_productor,
            }
        else:
            self.cpe_ferroviaria["retiroProductor"] = {}
        return True

    @inicializar_y_capturar_excepciones
    def AgregarIntervinientesFerroviaria(
        self,
        cuit_intermediario,
        cuit_remitente_comercial_venta_primaria,
        cuit_remitente_comercial_venta_secundaria,
        cuit_mercado_a_termino,
        cuit_corredor_venta_primaria,
        cuit_corredor_venta_secundaria,
        cuit_representante_entregador,
        **kwargs,
    ):
        """Inicializa internamente los datos de intervinientes para cpe ferroviario."""
        intervinientes = {
            "cuitIntermediario": cuit_intermediario,
            "cuitRemitenteComercialVentaPrimaria": cuit_remitente_comercial_venta_primaria,
            "cuitRemitenteComercialVentaSecundaria": cuit_remitente_comercial_venta_secundaria,
            "cuitMercadoATermino": cuit_mercado_a_termino,
            "cuitCorredorVentaPrimaria": cuit_corredor_venta_primaria,
            "cuitCorredorVentaSecundaria": cuit_corredor_venta_secundaria,
            "cuitRepresentanteEntregador": cuit_representante_entregador,
        }
        self.cpe_ferroviaria["intervinientes"] = intervinientes
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDatosCargaFerroviaria(self, cod_grano, cosecha, peso_bruto, peso_tara, **kwargs):
        """Inicializa internamente los datos de carga para cpe ferroviario."""

        datos_carga = {
            "codGrano": cod_grano,
            "cosecha": cosecha,
            "pesoBruto": peso_bruto,
            "pesoTara": peso_tara,
        }
        self.cpe_ferroviaria["datosCarga"] = datos_carga
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDestinoFerroviaria(
        self,
        cuit_destino,
        cod_provincia,
        cod_localidad,
        planta,
        cuit_destinatario,
        **kwargs,
    ):
        """Inicializa internamente los datos de destino para cpe ferroviario."""
        destino = {
            "cuit": cuit_destino,
            "codProvincia": cod_provincia,
            "codLocalidad": cod_localidad,
            "planta": planta,
        }
        cuit_destinatario = {"cuit": cuit_destinatario}
        self.cpe_ferroviaria["destino"] = destino
        self.cpe_ferroviaria["destinatario"] = cuit_destinatario
        return True

    @inicializar_y_capturar_excepciones
    def AgregarTransporteFerroviaria(
        self,
        cuit_transportista,
        cuit_transportista_tramo2,
        nro_vagon,
        nro_precinto,
        nro_operativo,
        fecha_hora_partida_tren,
        km_recorrer,
        cuit_pagador_flete,
        mercaderia_fumigada,
        codigo,
        descripcion=None,
        **kwargs,
    ):
        """Inicializa internamente los datos de transporte para cpe ferroviario."""
        transporte = {
            "cuitTransportista": cuit_transportista,
            "cuitTransportistaTramo2": cuit_transportista_tramo2,
            "nroVagon": nro_vagon,
            "nroPrecinto": nro_precinto,
            "nroOperativo": nro_operativo,
            "fechaHoraPartidaTren": fecha_hora_partida_tren,
            "kmRecorrer": km_recorrer,
            "cuitPagadorFlete": cuit_pagador_flete,
            "mercaderiaFumigada": mercaderia_fumigada,
        }
        ramal = {"codigo": codigo, "descripcion": descripcion}
        transporte["ramal"] = ramal
        self.cpe_ferroviaria["transporte"] = transporte
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarCPEFerroviaria(self, archivo="cpe_ferroviaria.pdf"):  # green
        """Informar los datos necesarios para la generación de una nueva carta porte."""
        response = self.client.autorizarCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe_ferroviaria,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
            # self.AnalizarCPEFerroviario(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def AnalizarCPEFerroviario(self, ret, archivo=None):
        pass

    @inicializar_y_capturar_excepciones
    def AgregarCabeceraAutomotor(self, tipo_cp=None, cuit_solicitante=None, sucursal=None, nro_orden=None, **kwargs):
        """Inicializa internamente los datos de cabecera para cpe automotor."""
        cabecera = {
            "tipoCP": tipo_cp,
            "cuitSolicitante": cuit_solicitante,
            "sucursal": sucursal,
            "nroOrden": nro_orden,
        }
        # creo el diccionario para agregar datos cpe
        self.cpe_automotor = {"cabecera": cabecera}
        return True

    @inicializar_y_capturar_excepciones
    def AgregarOrigenAutomotor(
        self,
        cod_provincia=None,
        cod_localidad_operador=None,
        planta=None,
        cod_localidad_productor=None,
        **kwargs,
    ):
        """Inicializa internamente los datos de origen para cpe automotor."""
        operador = {
            "codProvincia": cod_provincia,
            "codLocalidad": cod_localidad_operador,
            "planta": planta,
        }
        productor = {
            "codLocalidad": cod_localidad_productor,
        }
        origen = {"operador": operador, "productor": productor}
        self.cpe_automotor["origen"] = origen
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRetiroProductorAutomotor(
        self,
        corresponde_retiro_productor=None,
        es_solicitante_campo=None,
        certificado_coe=None,
        cuit_remitente_comercial_productor=None,
        **kwargs,
    ):
        """Inicializa internamente los datos de retiro de productor para cpe automotor."""
        retiro_productor = {
            "certificadoCOE": certificado_coe,
            "cuitRemitenteComercialProductor": cuit_remitente_comercial_productor,
        }
        self.cpe_automotor["correspondeRetiroProductor"] = corresponde_retiro_productor
        self.cpe_automotor["esSolicitanteCampo"] = es_solicitante_campo
        self.cpe_automotor["retiroProductor"] = retiro_productor
        return True

    @inicializar_y_capturar_excepciones
    def AgregarIntervinientesAutomotor(
        self,
        cuit_intermediario=None,
        cuit_remitente_comercial_venta_primaria=None,
        cuit_remitente_comercial_venta_secundaria=None,
        cuit_mercado_a_termino=None,
        cuit_corredor_venta_primaria=None,
        cuit_corredor_venta_secundaria=None,
        cuit_representante_entregador=None,
        **kwargs,
    ):
        """Inicializa internamente los datos de los intervinientes para cpe automotor."""
        intervinientes = {
            "cuitIntermediario": cuit_intermediario,
            "cuitRemitenteComercialVentaPrimaria": cuit_remitente_comercial_venta_primaria,
            "cuitRemitenteComercialVentaSecundaria": cuit_remitente_comercial_venta_secundaria,
            "cuitMercadoATermino": cuit_mercado_a_termino,
            "cuitCorredorVentaPrimaria": cuit_corredor_venta_primaria,
            "cuitCorredorVentaSecundaria": cuit_corredor_venta_secundaria,
            "cuitRepresentanteEntregador": cuit_representante_entregador,
        }
        self.cpe_automotor["intervinientes"] = intervinientes
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDatosCargaAutomotor(self, cod_grano=None, cosecha=None, peso_bruto=None, peso_tara=None, **kwargs):
        """Inicializa internamente los datos de carga para cpe automotor."""
        datos_carga = {
            "codGrano": cod_grano,
            "cosecha": cosecha,
            "pesoBruto": peso_bruto,
            "pesoTara": peso_tara,
        }
        self.cpe_automotor["datosCarga"] = datos_carga
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDestinoAutomotor(
        self,
        cuit_destino=None,
        es_destino_campo=None,
        cod_provincia=None,
        cod_localidad=None,
        planta=None,
        cuit_destinatario=None,
        **kwargs,
    ):
        """Inicializa internamente los datos de destino para cpe automotor."""
        destino = {
            "cuit": cuit_destino,
            "esDestinoCampo": es_destino_campo,
            "codProvincia": cod_provincia,
            "codLocalidad": cod_localidad,
            "planta": planta,
        }
        cuit_destinatario = {"cuit": cuit_destinatario}
        self.cpe_automotor["destino"] = destino
        self.cpe_automotor["destinatario"] = cuit_destinatario
        return True

    @inicializar_y_capturar_excepciones
    def AgregarTransporteAutomotor(
        self,
        cuit_transportista=None,
        dominio=None,  # 1 or more repetitions
        fecha_hora_partida=None,
        km_recorrer=None,
        codigo_turno=None,
        **kwargs,
    ):
        """Inicializa internamente los datos de transporte para cpe automotor."""
        transporte = {
            "cuitTransportista": cuit_transportista,
            "dominio": dominio,
            "fechaHoraPartida": fecha_hora_partida,
            "kmRecorrer": km_recorrer,
            "codigoTurno": codigo_turno,
        }
        self.cpe_automotor["transporte"] = transporte
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarCPEAutomotor(self, archivo="cpe_automotor.pdf"):  # green
        """Informar los datos necesarios para la generación de una nueva carta porte."""
        response = self.client.autorizarCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe_automotor,
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPEAutomotor(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def AnalizarCPEAutomotor(self, ret, archivo="cpe_automotor.pdf"):
        "Extrae los resultados de autorización de una carta porte automotor."
        cab = ret["cabecera"]
        self.NroCPE = cab["nroCPE"]
        self.FechaEmision = cab["fechaEmision"]
        self.Estado = cab["estado"]
        self.FechaInicioEstado = cab["fechaInicioEstado"]
        self.FechaVencimiento = cab["fechaVencimiento"]
        # self.CPEAutomotorPDF = cab["pdf"]  # base64
        # cpe_automotor_bytes = self.CPEAutomotorPDF.encode('utf-8')  # si vienen bytes, no hace falta
        # cpe_automotor_pdf = base64.b64decode(cpe_automotor_bytes)
        # with open(archivo, "wb") as fh:
        #     fh.write(cpe_automotor_pdf)

    @inicializar_y_capturar_excepciones  # green
    def AnularCPE(self):
        "Informar los datos necesarios para la generación de una nueva carta porte."
        response = self.client.anularCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def RechazoCPE(self):
        "Informar el rechazo de una carta de porte existente."
        response = self.client.rechazoCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def ConsultarCPEFerroviaria(self):
        "Busca una CPE existente según parámetros de búsqueda y retorna información de la misma."
        response = self.client.consultarCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
            },
        )
        ret = response.get("respuesta")
        print(ret)
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones
    def ConsultaCPEFerroviariaPorNroOperativo(self):  # green
        "Información resumida de cartas de porte asociadas a un mismo número de operativo."
        response = self.client.consultaCPEFerroviariaPorNroOperativo(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={"nroOperativo": 1111111111},
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def ConfirmarArriboCPE(self):
        "Informar la confirmación de arribo."
        response = self.client.confirmarArriboCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
            },
        )
        ret = response.get("respuesta")
        print(ret)
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones
    def ConfirmacionDefinitivaCPEFerroviaria(self):  # green
        "Informar la confirmación definitiva de una carta de porte existente."
        response = self.client.confirmacionDefinitivaCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
                "intervinientes": {
                    "cuitIntermediario": 20222222223,
                    "cuitRemitenteComercialVentaSecundaria": 20222222223,
                    "cuitRemitenteComercialVentaPrimaria": 20222222223,
                    "cuitCorredorVentaPrimaria": 20222222223,
                    "cuitCorredorVentaSecundaria": 20222222223,
                },
                "destinatario": {"cuit": 30000000006},
                "pesoBrutoDescarga": 1000,
                "pesoTaraDescarga": 1000,
                "ramalDescarga": {"codigo": 99, "descripcion": "XXXX"},
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def ConsultarCPEAutomotor(self):
        "Busca una CPE existente según parámetros de búsqueda y retorna información de la misma."
        response = self.client.consultarCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={"cartaPorte": {"tipoCPE": 74, "sucursal": 1, "nroOrden": 1}},
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def ConfirmacionDefinitivaCPEAutomotor(self):
        "Informar la confirmación definitiva de una carta de porte existente."
        response = self.client.confirmacionDefinitivaCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 74, "sucursal": 1, "nroOrden": 1},
                "pesoBrutoDescarga": 1000,
                "pesoTaraDescarga": 1000,
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def InformarContingencia(self):
        "informa de contingencia de una CPE existente."
        response = self.client.informarContingencia(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cartaPorte": {"tipoCPE": 74, "sucursal": 1, "nroOrden": 1},
                "contingencia": {"concepto": "F", "descripcion": "XXXXX"},  # otros
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones
    def CerrarContingenciaCPEFerroviaria(self):  # green
        "Informar del cierre de una contingencia asociado a una carta de porte ferroviaria."
        response = self.client.cerrarContingenciaCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
                "concepto": "?",
                "reactivacionDestino": {
                    "cuitTransportista": 20333333334,
                    "nroOperativo": 1,
                },
                "motivoDesactivacionCP": {"concepto": "A", "descripcion": "XXXXX"},
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green!!!
    def ConsultarUltNroOrden(self):
        "Obtiene el último número de orden de CPE autorizado según número de sucursal."
        response = self.client.consultarUltNroOrden(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={"sucursal": 1, "tipoCPE": 74},
        )
        ret = response.get("respuesta")
        self.NroOrden = ret["nroOrden"]
        print(self.NroOrden)
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def NuevoDestinoDestinatarioCPEFerroviaria(self):
        "Informar el regreso a origen de una carta de porte existente."
        response = self.client.nuevoDestinoDestinatarioCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
                "destino": {
                    "cuit": 20111111112,
                    "codProvincia": 1,
                    "codLocalidad": 10216,  # newton
                    "planta": 1,
                },
                "destinatario": {  # opcional
                    "cuit": 30000000006,
                },
                "transporte": {
                    "ramal": {
                        "codigo": 99,  # otro, tambien acepta del 1->6
                        "descripcion": "XXXXX",
                    },
                    "fechaHoraPartidaTren": datetime.datetime.now(),
                    "kmRecorrer": 333,
                },
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def RegresoOrigenCPEFerroviaria(self):
        "Informar el regreso a origen de una carta de porte existente."
        response = self.client.regresoOrigenCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
                "transporte": {
                    "ramal": {
                        "codigo": 99,  # otro, tambien acepta del 1->6
                        "descripcion": "Ok",
                    },
                    "fechaHoraPartidaTren": datetime.datetime.now(),
                    "kmRecorrer": 333,
                },
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def DesvioCPEFerroviaria(self):
        "Informar el desvío de una carta de porte existente."
        response = self.client.desvioCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 75, "sucursal": 1, "nroOrden": 1},
                "destino": {
                    "cuit": 20111111112,
                    "codProvincia": 1,
                    "codLocalidad": 10216,  # newton
                    "planta": 1,
                },
                "transporte": {
                    "ramal": {
                        "codigo": 99,  # otro, tambien acepta del 1->6
                        "descripcion": "Ok",
                    },
                    "fechaHoraPartidaTren": datetime.datetime.now(),
                    "kmRecorrer": 333,
                },
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def DescargadoDestinoCPE(self):
        "indicar por el solicitante de la Carta de Porte que la mercadería ha sido enviada."
        response = self.client.descargadoDestinoCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 74, "sucursal": 1, "nroOrden": 1},
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def NuevoDestinoDestinatarioCPEAutomotor(self):
        "Informar el nuevo destino o destinatario de una carta deporte existente."
        response = self.client.nuevoDestinoDestinatarioCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cartaPorte": {"tipoCPE": 74, "sucursal": 1, "nroOrden": 1},
                "destino": {
                    "cuit": 20111111112,
                    "codProvincia": 1,
                    "codLocalidad": 10216,  # newton
                    "planta": 1,
                    "esDestinoCampo": "M",  # string
                },
                # "destinatario": {"cuit": 30000000006},
                "transporte": {
                    "fechaHoraPartida": datetime.datetime.now(),
                    "kmRecorrer": 333,
                },
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def RegresoOrigenCPEAutomotor(self):
        "Informar el regreso a origen de una carta de porte existente."
        response = self.client.regresoOrigenCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cartaPorte": {"tipoCPE": 74, "sucursal": 1, "nroOrden": 1},
                "destinatario": {"cuit": 30000000006},
                "transporte": {
                    "fechaHoraPartida": datetime.datetime.now(),
                    "kmRecorrer": 100,
                },
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones  # green
    def DesvioCPEAutomotor(self):
        "Informar el desvío de una carta de porte existente."
        response = self.client.desvioCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={
                "cuitSolicitante": 20267565393,
                "cartaPorte": {"tipoCPE": 74, "sucursal": 1, "nroOrden": 1},
                "destino": {
                    "cuit": 20111111112,
                    "codProvincia": 1,
                    "codLocalidad": 10216,  # newton
                    "planta": 1,
                    "esDestinoCampo": "N",  # string
                },
                "transporte": {
                    "fechaHoraPartida": datetime.datetime.now(),
                    "kmRecorrer": 333,
                },
            },
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)

    @inicializar_y_capturar_excepciones
    def ConsultarProvincias(self, sep="||"):
        "Obtener los códigos numéricos de las provincias."
        response = self.client.consultarProvincias(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        array = ret.get("provincia", [])
        return [("%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarLocalidadesPorProvincia(self, cod_provincia=1, sep="||"):
        "Obtener los códigos de las localidades por provincia."
        response = self.client.consultarLocalidadesPorProvincia(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={"codProvincia": cod_provincia},
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        array = ret.get("localidad", [])
        return [("%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposGrano(self, sep="||"):
        "Obtener los códigos numéricos de los tipos de granos."
        response = self.client.consultarTiposGrano(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        array = ret.get("grano", [])
        return [("%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarLocalidadesProductor(self, cuit_productor=1, sep="||"):
        "Obtener de localidades del cuit asociado al productor."
        response = self.client.consultarLocalidadesProductor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={"cuit": cuit_productor},
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        array = ret.get("localidad", [])
        return [("%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in array]

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()["respuesta"]
        self.AppServerStatus = str(results["appserver"])
        self.DbServerStatus = str(results["dbserver"])
        self.AuthServerStatus = str(results["authserver"])


INSTALL_DIR = WSCPE.InstallDir = get_install_dir()

if __name__ == "__main__":
    # obteniendo el TA
    from pyafipws.wsaa import WSAA

    wsaa_url = ""
    wscpe_url = WSDL[HOMO]

    CERT = "reingart.crt"
    PRIVATEKEY = "reingart.key"
    CUIT = os.environ["CUIT"]

    wsaa = WSAA()
    ta = wsaa.Autenticar("wscpe", CERT, PRIVATEKEY, wsaa_url, debug=DEBUG)
    if not ta:
        sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

    # cliente soap del web service
    wscpe = WSCPE()
    wscpe.Conectar(wsdl=wscpe_url)
    wscpe.SetTicketAcceso(ta)
    wscpe.Cuit = CUIT
    ok = None

    if "--dummy" in sys.argv:
        ret = wscpe.Dummy()
        print("AppServerStatus", wscpe.AppServerStatus)
        print("DbServerStatus", wscpe.DbServerStatus)
        print("AuthServerStatus", wscpe.AuthServerStatus)
        sys.exit(0)

    if "--autorizar_cpe_automotor" in sys.argv:
        cabecera = {"tipo_cp": 1, "cuit_solicitante": 20267565393, "sucursal": 1, "nro_orden": 1}
        origen = {"planta": 1, "cod_provincia": 12, "cod_localidad_operador": 5544, "cod_localidad_productor": 3059}
        retiro_productor = {
            "certificado_coe": 330100025869,
            "cuit_remitente_comercial_productor": 20111111112,
        }
        intervinientes = {
            "cuit_mercado_a_termino": 20222222223,
            "cuit_corredor_venta_primaria": 20222222223,
            "cuit_corredor_venta_secundaria": 20222222223,
            "cuit_remitente_comercial_venta_secundaria": 20222222223,
            "cuit_intermediario": 20222222223,
            "cuit_remitente_comercial_venta_primaria": 20222222223,
            "cuit_representante_entregador": 20222222223,
        }
        datos_carga = {
            "peso_tara": 1000,
            "cod_grano": 31,
            "peso_bruto": 1000,
            "cosecha": 910,
        }
        destinatario = {"cuit_destinatario": 30000000006}
        destino = {
            "planta": 1,
            "cod_provincia": 12,
            "es_destino_campo": "M",
            "cod_localidad": 3058,
            "cuit_destino": 20111111112,
        }
        destino.update(destinatario)
        retiro_productor_final = {
            "corresponde_retiro_productor": True,
            "es_solicitante_campo": "N",
        }
        retiro_productor_final.update(retiro_productor)
        transporte = {
            "cuit_transportista": 20333333334,
            "fecha_hora_partida": datetime.datetime.now(),
            "codigo_turno": "00",
            "dominio": ["ZZZ000", "ZZZ999"],  # 1 or more repetitions
            "km_recorrer": 500,
        }
        wscpe.AgregarCabeceraAutomotor(**cabecera)
        wscpe.AgregarOrigenAutomotor(**origen)
        wscpe.AgregarDestinoAutomotor(**destino)
        wscpe.AgregarTransporteAutomotor(**transporte)
        wscpe.AgregarRetiroProductorAutomotor(**retiro_productor_final)
        wscpe.AgregarIntervinientesAutomotor(**intervinientes)
        wscpe.AgregarDatosCargaAutomotor(**datos_carga)
        wscpe.AutorizarCPEAutomotor()
        if wscpe.CodCPE:
            print(wscpe.Planta)
            print(wscpe.NroCPE)
            print(wscpe.FechaEmision)
            print(wscpe.Estado)
            print(wscpe.FechaInicioEstado)
            print(wscpe.FechaVencimiento)
            # print(wscpe.CPEAutomotorPDF)  # base64

    if "--autorizar_cpe_ferroviaria" in sys.argv:
        wscpe.AutorizarCPEFerroviaria()

    if "--anular_cpe" in sys.argv:
        wscpe.AnularCPE()

    if "--rechazo_cpe" in sys.argv:
        wscpe.RechazoCPE()

    if "--consultar_cpe_ferroviaria" in sys.argv:
        wscpe.ConsultarCPEFerroviaria()

    if "--consulta_cpe_ferroviaria_por_nro_operativo" in sys.argv:
        wscpe.ConsultaCPEFerroviariaPorNroOperativo()

    if "--confirmar_arribo_cpe" in sys.argv:
        wscpe.ConfirmarArriboCPE()

    if "--confirmacion_definitiva_cpe_ferroviaria" in sys.argv:
        wscpe.ConfirmacionDefinitivaCPEFerroviaria()

    if "--consultar_cpe_automotor" in sys.argv:
        wscpe.ConsultarCPEAutomotor()

    if "--informar_contingencia" in sys.argv:
        wscpe.InformarContingencia()

    if "--confirmacion_definitiva_cpe_automotor" in sys.argv:
        wscpe.ConfirmacionDefinitivaCPEAutomotor()

    if "--cerrar_contingencia_cpe_ferroviaria" in sys.argv:
        wscpe.CerrarContingenciaCPEFerroviaria()

    if "--ult" in sys.argv:
        wscpe.ConsultarUltNroOrden()

    if "--nuevo_destino_destinatario_cpe_ferroviaria" in sys.argv:
        wscpe.NuevoDestinoDestinatarioCPEFerroviaria()

    if "--regreso_origen_cpe_ferroviaria" in sys.argv:
        wscpe.RegresoOrigenCPEFerroviaria()

    if "--desvio_cpe_ferroviario" in sys.argv:
        wscpe.DesvioCPEFerroviaria()

    if "--descargado_destino_cpe" in sys.argv:
        wscpe.DescargadoDestinoCPE()

    if "--nuevo_destino_destinatario_cpe_automotor" in sys.argv:
        wscpe.NuevoDestinoDestinatarioCPEAutomotor()

    if "--regreso_origen_cpe_automotor" in sys.argv:
        wscpe.RegresoOrigenCPEAutomotor()

    if "--desvio_cpe_automotor" in sys.argv:
        wscpe.DesvioCPEAutomotor()

    if "--provincias" in sys.argv:
        ret = wscpe.ConsultarProvincias()
        print("\n".join(ret))

    if "--localidades_por_provincias" in sys.argv:
        ret = wscpe.ConsultarLocalidadesPorProvincia()
        print("\n".join(ret))

    if "--tipos_grano" in sys.argv:
        ret = wscpe.ConsultarTiposGrano()
        print("\n".join(ret))

    if "--localidades_productor" in sys.argv:
        ret = wscpe.ConsultarLocalidadesProductor(cuit_productor=20267565393)
        print("\n".join(ret))

    if "--debug" in sys.argv:
        with open("xml_response.xml", "wb") as bh:
            bh.write(wscpe.XmlResponse)
        with open("xml_request.xml", "wb") as bh:
            bh.write(wscpe.XmlRequest)

    if wscpe.Errores:
        print(wscpe.ErrMsg)
