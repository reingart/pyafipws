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
from future.utils import string_types

standard_library.install_aliases()
from builtins import str
from builtins import input

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2021- Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.01b"

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

from pysimplesoap.client import SoapFault

# importo funciones compartidas:
from pyafipws.utils import (
    date,
    leer,
    escribir,
    leer_dbf,
    guardar_dbf,
    N,
    A,
    I,
    json,
    BaseWS,
    inicializar_y_capturar_excepciones,
    get_install_dir,
    json_serializer,
)


# constantes de estado cpe.
ESTADO_CPE = {
    "AC": "Activa",
    "AN": "Anulada",
    "BR": "Borrador",
    "CF": "Activa con confirmacion de arribo",
    "CN": "confirmada",
    "CO": "Activa con contingencia",
    "DE": "Desactivada",
    "RE": "Rechazada",
    "PA": "Pendiente de Aceptacion por el Productor",
    "AP": "Anulacion por el Productor",
    "DD": "Descargado en destino",
}

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
        "EditarCPEAutomotor",
        "EditarCPEFerroviaria",
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
        "NroCTG",
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
        self.NroCTG = self.NroOrden = None
        self.FechaInicioEstado = self.FechaVencimiento = self.FechaEmision = None
        self.Estado = self.Resultado = self.PDF = None
        self.Errores = []
        self.Evento = self.ErrCode = self.ErrMsg = self.Obs = ""
        if not hasattr(self, "cpe"):
            self.cpe = {}
        if not hasattr(self, "_actualizar"):
            self._actualizar = True

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = self.Errores = [err["error"] for err in ret.get("errores", [])]
        if errores:
            errores = errores[0]
        self.ErrCode = " ".join(["%(codigo)s" % err for err in errores])
        self.ErrMsg = "\n".join(["%(codigo)s - %(descripcion)s" % err for err in errores])

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

    def CrearCPE(self):
        """Cambia la estructura de datos en AgregarCabecera para crear una CPE."""
        self._actualizar = False
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCabecera(
        self,
        tipo_cpe=None,
        cuit_solicitante=None,
        sucursal=None,
        nro_orden=None,
        planta=None,
        carta_porte=None,
        nro_ctg=None,
        **kwargs
    ):
        """Inicializa internamente los datos de cabecera para una cpe."""
        # cabecera para modificaciones, rechazos o anulaciones.
        if self._actualizar:
            cabecera = {
                "cuitSolicitante": cuit_solicitante,
                "nroCTG": nro_ctg,
                "cartaPorte": {
                    "tipoCPE": tipo_cpe,
                    "sucursal": sucursal,
                    "nroOrden": nro_orden,
                },
            }
            if not sucursal:
                del cabecera["cartaPorte"]
            self.cpe = cabecera
        else:
            cabecera = {
                "tipoCP": tipo_cpe,
                "cuitSolicitante": cuit_solicitante,
                "sucursal": sucursal,
                "nroOrden": nro_orden,
                "planta": planta,
            }
            # creo el diccionario para agregar datos cpe
            self.cpe = {"cabecera": cabecera}
        return True

    @inicializar_y_capturar_excepciones
    def AgregarOrigen(
        self,
        cod_provincia_operador=None,
        cod_localidad_operador=None,
        planta=None,
        cod_provincia_productor=None,
        cod_localidad_productor=None,
        **kwargs
    ):
        """Inicializa internamente los datos de origen para una cpe."""
        operador = {
            "codProvincia": cod_provincia_operador,
            "codLocalidad": cod_localidad_operador,
            "planta": planta,
        }
        productor = {
            "codProvincia": cod_provincia_productor,
            "codLocalidad": cod_localidad_productor,
        }
        origen = {}
        if planta:
            origen["operador"] = operador
        if cod_localidad_productor:
            origen["productor"] = productor
        self.cpe["origen"] = origen
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRetiroProductor(
        self,
        corresponde_retiro_productor=None,
        es_solicitante_campo=None,
        certificado_coe=None,
        cuit_remitente_comercial_productor=None,
        **kwargs
    ):
        """Inicializa internamente los datos de retiro de productor para una cpe."""
        retiro_productor = {
            "certificadoCOE": certificado_coe,
            "cuitRemitenteComercialProductor": cuit_remitente_comercial_productor,
        }
        self.cpe["correspondeRetiroProductor"] = corresponde_retiro_productor
        self.cpe["esSolicitanteCampo"] = es_solicitante_campo
        if certificado_coe:
            self.cpe["retiroProductor"] = retiro_productor
        return True

    @inicializar_y_capturar_excepciones
    def AgregarIntervinientes(
        self,
        cuit_intermediario=None,
        cuit_remitente_comercial_venta_primaria=None,
        cuit_remitente_comercial_venta_secundaria=None,
        cuit_mercado_a_termino=None,
        cuit_corredor_venta_primaria=None,
        cuit_corredor_venta_secundaria=None,
        cuit_representante_entregador=None,
        cuit_representante_recibidor=None,
        **kwargs
    ):
        """Inicializa internamente los datos de los intervinientes para una cpe."""
        intervinientes = {
            "cuitIntermediario": cuit_intermediario,
            "cuitRemitenteComercialVentaPrimaria": cuit_remitente_comercial_venta_primaria,
            "cuitRemitenteComercialVentaSecundaria": cuit_remitente_comercial_venta_secundaria,
            "cuitMercadoATermino": cuit_mercado_a_termino,
            "cuitCorredorVentaPrimaria": cuit_corredor_venta_primaria,
            "cuitCorredorVentaSecundaria": cuit_corredor_venta_secundaria,
            "cuitRepresentanteEntregador": cuit_representante_entregador,
            "cuitRepresentanteRecibidor": cuit_representante_recibidor,
        }
        self.cpe["intervinientes"] = intervinientes
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDatosCarga(self, cod_grano=None, cosecha=None, peso_bruto=None, peso_tara=None, **kwargs):
        """Inicializa internamente los datos de carga para una cpe."""
        datos_carga = {
            "codGrano": cod_grano,
            "cosecha": cosecha,
            "pesoBruto": peso_bruto,
            "pesoTara": peso_tara,
        }
        if not datos_carga["cosecha"]:
            self.cpe["pesoBrutoDescarga"] = peso_bruto
            self.cpe["pesoTaraDescarga"] = peso_tara
        else:
            self.cpe["datosCarga"] = datos_carga
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDestino(
        self,
        cuit_destino=None,
        es_destino_campo=None,
        cod_provincia=None,
        cod_localidad=None,
        planta=None,
        cuit_destinatario=None,
        **kwargs
    ):
        """Inicializa internamente los datos de destino para una cpe."""
        destino = {
            "cuit": cuit_destino,
            "esDestinoCampo": es_destino_campo,
            "codProvincia": cod_provincia,
            "codLocalidad": cod_localidad,
            "planta": planta,
        }
        cuit_destinatario = {"cuit": cuit_destinatario}
        # maneja distintos campos para diferentes metodos
        if destino["cuit"]:
            self.cpe["destino"] = destino
        if cuit_destinatario["cuit"]:
            self.cpe["destinatario"] = cuit_destinatario
        return True

    @inicializar_y_capturar_excepciones
    def AgregarTransporte(
        self,
        cuit_transportista=None,
        cuit_transportista_tramo2=None,
        nro_vagon=None,
        nro_precinto=None,
        nro_operativo=None,
        dominio=None,  # 1 or more repetitions
        fecha_hora_partida=None,
        km_recorrer=None,
        codigo_turno=None,
        cuit_chofer=None,
        tarifa=None,
        cuit_pagador_flete=None,
        mercaderia_fumigada=None,
        cuit_intermediario_flete=None,
        codigo_ramal=None,
        descripcion_ramal=None,
        **kwargs
    ):
        """Inicializa internamente los datos de transporte para una cpe."""
        if codigo_ramal:  # cpe ferroviaria
            transporte = {
                "cuitTransportista": cuit_transportista,
                "cuitTransportistaTramo2": cuit_transportista_tramo2,
                "nroVagon": nro_vagon,
                "nroPrecinto": nro_precinto,
                "nroOperativo": nro_operativo,
                "fechaHoraPartidaTren": fecha_hora_partida,
                "kmRecorrer": km_recorrer,
                "cuitPagadorFlete": cuit_pagador_flete,
                "mercaderiaFumigada": mercaderia_fumigada,
            }
            ramal = {"codigo": codigo_ramal, "descripcion": descripcion_ramal}
            # ajuste para confirmacion_definitiva_cpe_ferroviaria
            # ajuste para desviocpeferroviaria
            if cuit_transportista or km_recorrer:
                transporte["ramal"] = ramal
            else:
                transporte["ramalDescarga"] = ramal
        else:
            transporte = {
                "cuitTransportista": cuit_transportista,
                "dominio": dominio,
                "fechaHoraPartida": fecha_hora_partida,
                "kmRecorrer": km_recorrer,  # obligatorio en todos los metodos que lo solicitan
                "codigoTurno": codigo_turno,
                "cuitChofer": cuit_chofer,
                "tarifa": tarifa,
                "cuitPagadorFlete": cuit_pagador_flete,
                "cuitIntermediarioFlete": cuit_intermediario_flete,
                "mercaderiaFumigada": mercaderia_fumigada,
            }
        # ajuste para confirmacion_definitiva_cpe_ferroviaria
        if transporte["kmRecorrer"]:
            self.cpe["transporte"] = transporte
        else:
            self.cpe.update(transporte)
        return True

    def AgregarContingencia(
        self,
        concepto=None,
        descripcion=None,  # solo necesario si la opcion es F "otros"
    ):
        """Inicialliza datos para contingencias en cpe."""
        self.cpe["contingencia"] = {"concepto": concepto, "descripcion": descripcion}
        return True

    def AgregarCerrarContingenciaFerroviaria(
        self,
        concepto=None,
        cuit_transportista=None,
        nro_operativo=None,
        concepto_desactivacion=None,
        descripcion=None,
        **kwrags
    ):
        """Inicializa datos para el cierre, la reactivacion, extension de una contingencias en cpe ferroviaria.

            A: Reactivación para descarga en destino.
            B: Extensión cierre contingencia.
            C: Desactivar definitivamente la CP.
        """
        if concepto == "A":
            motivo = {
                "concepto": concepto,  # A, B, C
                "reactivacionDestino": {
                    "cuitTransportista": cuit_transportista,
                    "nroOperativo": nro_operativo,
                }
            }
        else:
            motivo = {
                "concepto": concepto,  # A, B, C - distintos para la desactivacion
                "motivoDesactivacionCP": {"concepto": concepto_desactivacion, "descripcion": descripcion}
            }
        self.cpe.update(motivo)

    @inicializar_y_capturar_excepciones
    def AutorizarCPEFerroviaria(self, archivo="cpe_ferroviaria.pdf"):
        """Informar los datos necesarios para la generación de una nueva carta porte."""
        response = self.client.autorizarCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarCPEAutomotor(self, archivo="cpe.pdf"):
        """Informar los datos necesarios para la generación de una nueva carta porte."""
        response = self.client.autorizarCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def AnalizarCPE(self, ret, archivo="cpe.pdf"):
        "Extrae los resultados de autorización de una carta porte automotor."
        cab = ret["cabecera"]
        self.NroCTG = cab["nroCTG"]
        self.FechaEmision = cab["fechaEmision"]
        self.Estado = cab["estado"]
        self.FechaInicioEstado = cab["fechaInicioEstado"]
        self.FechaVencimiento = cab["fechaVencimiento"]
        self.PDF = ret["pdf"]  # base64
        cpe_bytes = self.PDF
        if isinstance(cpe_bytes, string_types):
            cpe_bytes = cpe_bytes.encode("utf-8")
        with open(archivo, "wb") as fh:
            fh.write(cpe_bytes)

    @inicializar_y_capturar_excepciones
    def AnularCPE(self, archivo="cpe.pdf"):
        """Informar los datos necesarios para la generación de una nueva carta porte."""
        response = self.client.anularCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def RechazoCPE(self, archivo="cpe.pdf"):
        """Informar el rechazo de una carta de porte existente."""
        response = self.client.rechazoCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def InformarContingencia(self, archivo="cpe.pdf"):
        """informa de contingencia de una CPE existente."""
        response = self.client.informarContingencia(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def ConfirmarArriboCPE(self, archivo="cpe.pdf"):
        "Informar la confirmación de arribo."
        response = self.client.confirmarArriboCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def DescargadoDestinoCPE(self, archivo="cpe.pdf"):
        "indicar por el solicitante de la Carta de Porte que la mercadería ha sido enviada."
        response = self.client.descargadoDestinoCPE(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def EditarCPEFerroviaria(
        self,
        nro_ctg=None,
        cuit_intermediario=None,
        cuit_corredor_venta_primaria=None,
        cuit_corredor_venta_secundaria=None,
        cuit_remitente_comercial_venta_primaria=None,
        cuit_remitente_comercial_venta_secundaria=None,
        peso_bruto=None,
        cod_grano=None,
        archivo="cpe.pdf",
        **kwargs
    ):
        """Modificar datos de una CP Ferroviaria en estado Activo."""
        solicitud = {
            "nroCTG": nro_ctg,
            "cuitIntermediario": cuit_intermediario,
            "cuitCorredorVentaPrimaria": cuit_corredor_venta_primaria,
            "cuitCorredorVentaSecundaria": cuit_corredor_venta_secundaria,
            "cuitRemitenteComercialVentaPrimaria": cuit_remitente_comercial_venta_primaria,
            "cuitRemitenteComercialVentaSecundaria": cuit_remitente_comercial_venta_secundaria,
            "pesoBruto": peso_bruto,
            "codGrano": cod_grano,
        }
        response = self.client.editarCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=solicitud,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarCPEFerroviaria(
        self, tipo_cpe=None, cuit_solicitante=None, sucursal=None, nro_orden=None, nro_ctg=None, archivo="cpe.pdf"
    ):
        """Busca una CPE existente según parámetros de búsqueda y retorna información de la misma."""
        if not nro_ctg:
            solicitud = {
                "cartaPorte": {
                    "tipoCPE": tipo_cpe,
                    "sucursal": sucursal,
                    "nroOrden": nro_orden,
                },
            }
        else:
            solicitud = {
                "nroCTG": nro_ctg,
            }
        solicitud["cuitSolicitante"] = cuit_solicitante
        response = self.client.consultarCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=solicitud,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultaCPEFerroviariaPorNroOperativo(self, nro_operativo=1111111111):
        """Información resumida de cartas de porte asociadas a un mismo número de operativo."""
        response = self.client.consultaCPEFerroviariaPorNroOperativo(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={"nroOperativo": nro_operativo},
        )
        ret = response.get("respuesta")
        # respuesta distinta devuelve un array de resultados 'resumenCartaPorte'
        if ret:
            self.__analizar_errores(ret)
        if 'resumenCartaPorte' in ret:
            cps = [
                '\n'.join('{}: {}'.format(campo, valor) for campo, valor in carta_porte.items())
                for carta_porte in ret['resumenCartaPorte']
            ]
            return '\n==========\n'.join(cps)

    @inicializar_y_capturar_excepciones
    def ConfirmacionDefinitivaCPEFerroviaria(self, archivo="cpe.pdf"):
        """Informar la confirmación definitiva de una carta de porte existente."""
        response = self.client.confirmacionDefinitivaCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def CerrarContingenciaCPEFerroviaria(self, archivo="cpe.pdf"):
        """Informar del cierre de una contingencia asociado a una carta de porte ferroviaria."""
        response = self.client.cerrarContingenciaCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def NuevoDestinoDestinatarioCPEFerroviaria(self, archivo="cpe.pdf"):
        """Informar el regreso a origen de una carta de porte existente."""
        response = self.client.nuevoDestinoDestinatarioCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def RegresoOrigenCPEFerroviaria(self, archivo="cpe.pdf"):
        """Informar el regreso a origen de una carta de porte existente."""
        response = self.client.regresoOrigenCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def DesvioCPEFerroviaria(self, archivo="cpe.pdf"):
        """Informar el desvío de una carta de porte existente."""
        response = self.client.desvioCPEFerroviaria(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def EditarCPEAutomotor(
        self,
        nro_ctg=None,
        cuit_intermediario=None,
        cuit_corredor_venta_primaria=None,
        cuit_corredor_venta_secundaria=None,
        cuit_remitente_comercial_venta_primaria=None,
        cuit_remitente_comercial_venta_secundaria=None,
        peso_bruto=None,
        cod_grano=None,
        dominio=None,
        archivo="cpe.pdf",
        **kwargs
    ):
        """Modificar datos de una CP Automotor en estado Activo."""
        solicitud = {
            "nroCTG": nro_ctg,
            "cuitIntermediario": cuit_intermediario,
            "cuitCorredorVentaPrimaria": cuit_corredor_venta_primaria,
            "cuitCorredorVentaSecundaria": cuit_corredor_venta_secundaria,
            "cuitRemitenteComercialVentaPrimaria": cuit_remitente_comercial_venta_primaria,
            "cuitRemitenteComercialVentaSecundaria": cuit_remitente_comercial_venta_secundaria,
            "pesoBruto": peso_bruto,
            "codGrano": cod_grano,
            "dominio": dominio,
        }
        response = self.client.editarCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=solicitud,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarCPEAutomotor(
        self, tipo_cpe=None, cuit_solicitante=None, sucursal=None, nro_orden=None, nro_ctg=None, archivo="cpe.pdf"
    ):
        """Busca una CPE existente según parámetros de búsqueda y retorna información de la misma."""
        if not nro_ctg:
            solicitud = {
                "cartaPorte": {
                    "tipoCPE": tipo_cpe,
                    "sucursal": sucursal,
                    "nroOrden": nro_orden,
                },
            }
        else:
            solicitud = {
                "nroCTG": nro_ctg,
            }
        solicitud["cuitSolicitante"] = cuit_solicitante
        response = self.client.consultarCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=solicitud,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def ConfirmacionDefinitivaCPEAutomotor(self, archivo="cpe.pdf"):
        """Informar la confirmación definitiva de una carta de porte existente."""
        response = self.client.confirmacionDefinitivaCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        if ret:
            self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def NuevoDestinoDestinatarioCPEAutomotor(self, archivo="cpe.pdf"):
        """Informar el nuevo destino o destinatario de una carta deporte existente."""
        response = self.client.nuevoDestinoDestinatarioCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def RegresoOrigenCPEAutomotor(self, archivo="cpe.pdf"):
        """Informar el regreso a origen de una carta de porte existente."""
        response = self.client.regresoOrigenCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def DesvioCPEAutomotor(self, archivo="cpe.pdf"):
        """Informar el desvío de una carta de porte existente."""
        response = self.client.desvioCPEAutomotor(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud=self.cpe,
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        if "cabecera" in ret:
            self.AnalizarCPE(ret, archivo)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarUltNroOrden(self, sucursal=None, tipo_cpe=None):
        """Obtiene el último número de orden de CPE autorizado según número de sucursal."""
        response = self.client.consultarUltNroOrden(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitud={"sucursal": sucursal, "tipoCPE": tipo_cpe},
        )
        ret = response.get("respuesta")
        self.__analizar_errores(ret)
        if "nroOrden" in ret:
            self.NroOrden = ret["nroOrden"]
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarProvincias(self, sep="||"):
        """Obtener los códigos numéricos de las provincias."""
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
        """Obtener los códigos de las localidades por provincia."""
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
        """Obtener los códigos numéricos de los tipos de granos."""
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
    def ConsultarLocalidadesProductor(self, cuit_productor=None, sep="||"):
        """Obtener de localidades del cuit asociado al productor."""
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
        """Obtener el estado de los servidores de la AFIP."""
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

    CERT = os.getenv("CERT", "reingart.crt")
    PRIVATEKEY = os.getenv("PKEY", "reingart.key")
    CUIT = os.getenv("CUIT", "20267565393")

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
        ok = wscpe.ConsultarUltNroOrden(sucursal=221, tipo_cpe=74)
        nro_orden = wscpe.NroOrden + 1
        ok = wscpe.CrearCPE()
        ok = wscpe.AgregarCabecera(tipo_cpe=74, cuit_solicitante=CUIT, sucursal=221, nro_orden=nro_orden)
        ok = wscpe.AgregarOrigen(
            planta=1,
            cod_provincia_operador=12,
            cod_localidad_operador=7717,
            # cod_provincia_productor=12,
            # cod_localidad_productor=7717
        )
        ok = wscpe.AgregarDestino(
            planta=1938,
            cod_provincia=12,
            es_destino_campo=True,
            cod_localidad=7717,
            cuit_destino=CUIT,
            cuit_destinatario=CUIT,
        )
        ok = wscpe.AgregarRetiroProductor(
            # certificado_coe=330100025869,
            # cuit_remitente_comercial_productor=20111111112,
            corresponde_retiro_productor=False,  # chequear dice booleano
            es_solicitante_campo=True,  # chequear dice booleano
        )
        ok = wscpe.AgregarIntervinientes(
            # cuit_mercado_a_termino=20222222223,
            # cuit_corredor_venta_primaria=20200000006,
            # cuit_corredor_venta_secundaria=20222222223,
            # cuit_remitente_comercial_venta_secundaria=20222222223,
            cuit_intermediario=20400000000,
            cuit_remitente_comercial_venta_primaria=27000000014,
            # cuit_representante_entregador=20222222223,
            # cuit_representante_recibidor=20222222223
        )
        ok = wscpe.AgregarDatosCarga(
            peso_tara=10,
            cod_grano=23,
            peso_bruto=110,
            cosecha=2021,
        )
        ok = wscpe.AgregarTransporte(
            cuit_transportista=20120372913,
            fecha_hora_partida=datetime.datetime.now() + datetime.timedelta(days=1),
            # codigo_turno="00",
            dominio=["AA001ST"],  # 1 or more repetitions
            km_recorrer=500,
            cuit_chofer=20333333334,
            # tarifa=100.10,
            # cuit_pagador_flete=20333333334,
            # cuit_intermediario_flete=20333333334,
            mercaderia_fumigada=True,
        )
        wscpe.LanzarExcepciones = False
        ok = wscpe.AutorizarCPEAutomotor()
        if wscpe.NroCTG:
            print("Numero de ctg:", wscpe.NroCTG)
            print("Fecha de emision:", wscpe.FechaEmision)
            print("Estado:", wscpe.Estado, "-", ESTADO_CPE[wscpe.Estado])
            print("Fecha de inicio de estado:", wscpe.FechaInicioEstado)
            print("Fecha de vencimiento:", wscpe.FechaVencimiento)

        with open("wscpe.xml", "w") as x:
            import xml.dom.minidom

            dom = xml.dom.minidom.parseString(wscpe.XmlRequest)
            x.write(dom.toprettyxml())

    if "--autorizar_cpe_ferroviaria" in sys.argv:
        ok = wscpe.CrearCPE()
        ok = wscpe.AgregarCabecera(sucursal=1, nro_orden=1, planta=1)
        ok = wscpe.AgregarDestino(
            cuit_destinatario=30000000006,
            cuit_destino=20111111112,
            es_destino_campo=True,
            planta=1,
            cod_provincia=12,
            cod_localidad=3058,
        )
        ok = wscpe.AgregarRetiroProductor(
            # certificado_coe=330100025869,
            # cuit_remitente_comercial_productor=20111111112,
            corresponde_retiro_productor=False,
        )
        # ok = wscpe.AgregarIntervinientes(
        #     cuit_mercado_a_termino=20222222223,
        #     cuit_corredor_venta_primaria=20222222223,
        #     cuit_corredor_venta_secundaria=20222222223,
        #     cuit_remitente_comercial_venta_secundaria=20222222223,
        #     cuit_intermediario=20222222223,
        #     cuit_remitente_comercial_venta_primaria=20222222223,
        #     cuit_representante_entregador=20222222223,
        #     cuit_representante_recibidor=20222222223,  # nuevo
        # )
        ok = wscpe.AgregarDatosCarga(
            peso_tara=1000,
            cod_grano=31,
            peso_bruto=1000,
            cosecha=910,
        )
        ok = wscpe.AgregarTransporte(
            # cuit_pagador_flete=20333333335,
            cuit_transportista=20333333334,
            # cuit_transportista_tramo2=20222222223,
            nro_vagon=55555555,
            nro_precinto=1,
            nro_operativo=1111111111,
            fecha_hora_partida=datetime.datetime.now(),
            km_recorrer=500,
            codigo_ramal=99,
            descripcion_ramal="XXXXX",
            mercaderia_fumigada=True,
        )
        wscpe.AutorizarCPEFerroviaria()
        if wscpe.NroCTG:
            print(wscpe.NroCTG)
            print(wscpe.FechaEmision)
            print(wscpe.Estado)
            print(wscpe.FechaInicioEstado)
            print(wscpe.FechaVencimiento)

        with open("wscpe.xml", "w") as x:
            import xml.dom.minidom

            dom = xml.dom.minidom.parseString(wscpe.XmlRequest)
            x.write(dom.toprettyxml())

    if "--ult" in sys.argv:
        wscpe.ConsultarUltNroOrden(sucursal=221, tipo_cpe=74)
        if wscpe.NroOrden:
            print("Nro Orden: ", wscpe.NroOrden)

    if "--anular_cpe" in sys.argv:
        wscpe.AgregarCabecera(tipo_cpe=74, sucursal=1, nro_orden=1)
        wscpe.AnularCPE()

    if "--rechazo_cpe" in sys.argv:
        wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=1, nro_orden=1)
        wscpe.RechazoCPE()

    if "--confirmar_arribo_cpe" in sys.argv:
        wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=1, nro_orden=1)
        wscpe.ConfirmarArriboCPE()

    if "--informar_contingencia" in sys.argv:
        wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=1, nro_orden=1)
        wscpe.AgregarContingencia(concepto="F", descripcion="XXXXX")
        wscpe.InformarContingencia()

    if "--descargado_destino_cpe" in sys.argv:
        wscpe.AgregarCabecera(
            cuit_solicitante=CUIT,
            tipo_cpe=74,
            sucursal=1,
            nro_orden=1,
        )
        wscpe.DescargadoDestinoCPE()

    if "--editar_cpe_ferroviaria" in sys.argv:
        wscpe.EditarCPEFerroviaria(
            nro_ctg=10100000542,
            cuit_intermediario=20111111113,
            cuit_corredor_venta_primaria=20222222223,
            cuit_corredor_venta_secundaria=20222222223,
            cuit_remitente_comercial_venta_primaria=20222222223,
            cuit_remitente_comercial_venta_secundaria=20222222223,
            peso_bruto=1000,
            cod_grano=31,
        )

    if "--consultar_cpe_ferroviaria" in sys.argv:
        wscpe.ConsultarCPEFerroviaria(tipo_cpe=75, sucursal=1, nro_orden=1, cuit_solicitante=CUIT)

    if "--consulta_cpe_ferroviaria_por_nro_operativo" in sys.argv:
        wscpe.ConsultaCPEFerroviariaPorNroOperativo(nro_operativo=1111111111)

    if "--confirmacion_definitiva_cpe_ferroviaria" in sys.argv:
        wscpe.AgregarCabecera(
            cuit_solicitante=CUIT, tipo_cpe=75, sucursal=1, nro_orden=1
        )
        # wscpe.AgregarDestino(
        #     cuit_destinatario=30000000006,
        # )
        # wscpe.AgregarIntervinientes(
        #     cuit_intermediario=20222222223,
        #     cuit_corredor_venta_primaria=20222222223,
        #     cuit_corredor_venta_secundaria=20222222223,
        #     cuit_remitente_comercial_venta_primaria=20222222223,
        #     cuit_remitente_comercial_venta_secundaria=20222222223,
        #     cuit_representante_recibidor=20222222223,  # nuevo
        # )
        wscpe.AgregarDatosCarga(peso_bruto=1000, peso_tara=10000)
        wscpe.AgregarTransporte(
            codigo_ramal=99,
            descripcion_ramal="XXXXX",
        )
        wscpe.ConfirmacionDefinitivaCPEFerroviaria()

    if "--cerrar_contingencia_cpe_ferroviaria" in sys.argv:
        wscpe.AgregarCabecera(
            tipo_cpe=75,
            sucursal=1,
            nro_orden=1,
        )
        wscpe.AgregarCerrarContingenciaFerroviaria(
            concepto="A",
            # cuit_transportista=20333333334,
            # nro_operativo=1111111111,
            # concepto_desactivacion="A",
            # descripcion="bloqueo"
        )
        wscpe.CerrarContingenciaCPEFerroviaria()

    if "--nuevo_destino_destinatario_cpe_ferroviaria" in sys.argv:
        wscpe.AgregarCabecera(
            tipo_cpe=75,
            sucursal=1,
            nro_orden=1,
        )
        wscpe.AgregarDestino(
            # cuit_destinatario=30000000006,
            cuit_destino=20111111112,
            cod_provincia=1,
            cod_localidad=10216,
            planta=1,
        )
        wscpe.AgregarTransporte(
            codigo_ramal=99,
            descripcion_ramal="Ok",
            fecha_hora_partida=datetime.datetime.now()+datetime.timedelta(days=1),
            km_recorrer=333,
        )
        wscpe.NuevoDestinoDestinatarioCPEFerroviaria()

    if "--regreso_origen_cpe_ferroviaria" in sys.argv:
        wscpe.AgregarCabecera(
            cuit_solicitante=CUIT,
            tipo_cpe=75,
            sucursal=1,
            nro_orden=1,
        )
        # wscpe.AgregarDestino(
        #     cuit_destinatario=30000000006
        # )
        wscpe.AgregarTransporte(
            codigo_ramal=99,
            descripcion_ramal="Ok",
            fecha_hora_partida=datetime.datetime.now(),
            km_recorrer=333,
        )
        wscpe.RegresoOrigenCPEFerroviaria()

    if "--desvio_cpe_ferroviaria" in sys.argv:
        wscpe.AgregarCabecera(
            cuit_solicitante=CUIT,
            tipo_cpe=75,
            sucursal=1,
            nro_orden=1,
        )
        wscpe.AgregarDestino(
            cuit_destino=20111111112,
            cod_provincia=1,
            cod_localidad=10216,
            planta=1,
            # es_destino_campo=True,
        )
        wscpe.AgregarTransporte(
            codigo_ramal=99,
            descripcion_ramal="Ok",
            fecha_hora_partida=datetime.datetime.now() + datetime.timedelta(days=1),
            km_recorrer=333,
        )
        wscpe.DesvioCPEFerroviaria()

    if "--editar_cpe_automotor" in sys.argv:
        wscpe.EditarCPEAutomotor(
            nro_ctg=10100000542,
            cuit_intermediario=20222222223,
            cuit_corredor_venta_primaria=20222222223,
            cuit_corredor_venta_secundaria=20222222223,
            cuit_remitente_comercial_venta_primaria=20222222223,
            cuit_remitente_comercial_venta_secundaria=20222222223,
            peso_bruto=1000,
            cod_grano=31,
            dominio=["AA001ST"],
        )

    if "--consultar_cpe_automotor" in sys.argv:
        wscpe.ConsultarCPEAutomotor(tipo_cpe=74, sucursal=1, nro_orden=1, cuit_solicitante=CUIT)

    if "--confirmacion_definitiva_cpe_automotor" in sys.argv:
        wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=1, nro_orden=1)
        # wscpe.AgregarIntervinientes(cuit_representante_recibidor=20222222223)
        wscpe.AgregarDatosCarga(peso_bruto=1000, peso_tara=10000)
        wscpe.ConfirmacionDefinitivaCPEAutomotor()

    if "--nuevo_destino_destinatario_cpe_automotor" in sys.argv:
        wscpe.AgregarCabecera(tipo_cpe=74, sucursal=1, nro_orden=1)
        wscpe.AgregarDestino(
            cuit_destino=20111111112, cod_provincia=1, cod_localidad=10216, planta=1, es_destino_campo=True, cuit_destinatario=30000000006
        )
        wscpe.AgregarTransporte(fecha_hora_partida=datetime.datetime.now(), km_recorrer=333, codigo_turno="00")
        wscpe.NuevoDestinoDestinatarioCPEAutomotor()

    if "--regreso_origen_cpe_automotor" in sys.argv:
        wscpe.AgregarCabecera(tipo_cpe=74, sucursal=1, nro_orden=1)
        wscpe.AgregarDestino(
            cuit_destinatario=30000000006,
        )
        wscpe.AgregarTransporte(fecha_hora_partida=datetime.datetime.now(), km_recorrer=333, codigo_turno="00")
        wscpe.RegresoOrigenCPEAutomotor()

    if "--desvio_cpe_automotor" in sys.argv:
        wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=1, nro_orden=1)
        wscpe.AgregarDestino(
            cuit_destino=20111111112, cod_provincia=1, cod_localidad=10216, planta=1, es_destino_campo=True  # newton
        )
        wscpe.AgregarTransporte(fecha_hora_partida=datetime.datetime.now(), km_recorrer=333, codigo_turno="00")
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
        ret = wscpe.ConsultarLocalidadesProductor(cuit_productor=CUIT)
        print("\n".join(ret))

    if "--debug" in sys.argv:
        with open("xml_response.xml", "wb") as bh:
            bh.write(wscpe.XmlResponse)
        with open("xml_request.xml", "wb") as bh:
            bh.write(wscpe.XmlRequest)

    if wscpe.Errores:
        print("Error:", wscpe.ErrMsg)
