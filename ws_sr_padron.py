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

"""Módulo para acceder a los datos de un contribuyente registrado en el Padrón
de AFIP (WS-SR-PADRON de AFIP). Consulta a Padrón Alcance 4 version 1.1
Consulta de Padrón Constancia Inscripción Alcance 5 version 2.0
"""
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from builtins import next

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2017-2023 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.05a"

import csv
import datetime
import decimal
import json
import os
import sys

from pyafipws.utils import (
    inicializar_y_capturar_excepciones,
    BaseWS,
    get_install_dir,
    json_serializer,
    abrir_conf,
    norm,
    SoapFault,
    safe_console,
)
from configparser import SafeConfigParser
from pyafipws.padron import TIPO_CLAVE, PROVINCIAS


HOMO = False
LANZAR_EXCEPCIONES = True
WSDL = "https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA4?wsdl"
CONFIG_FILE = "rece.ini"


class WSSrPadronA4(BaseWS):
    "Interfaz para el WebService de Consulta Padrón Contribuyentes Alcance 4"
    _public_methods_ = [
        "Consultar",
        "AnalizarXml",
        "ObtenerTagXml",
        "LoadTestXML",
        "SetParametros",
        "SetTicketAcceso",
        "GetParametro",
        "Dummy",
        "Conectar",
        "DebugLog",
        "SetTicketAcceso",
    ]
    _public_attrs_ = [
        "Token",
        "Sign",
        "Cuit",
        "AppServerStatus",
        "DbServerStatus",
        "AuthServerStatus",
        "XmlRequest",
        "XmlResponse",
        "Version",
        "InstallDir",
        "LanzarExcepciones",
        "Excepcion",
        "Traceback",
        "Persona",
        "data",
        "denominacion",
        "imp_ganancias",
        "imp_iva",
        "monotributo",
        "integrante_soc",
        "empleador",
        "actividad_monotributo",
        "cat_iva",
        "domicilios",
        "tipo_doc",
        "nro_doc",
        "tipo_persona",
        "estado",
        "es_sucesion",
        "impuestos",
        "actividades",
        "direccion",
        "localidad",
        "provincia",
        "cod_postal",
    ]

    _reg_progid_ = "WSSrPadronA4"
    _reg_clsid_ = "{C2270008-4324-46F6-A2D3-60836EE63BD7}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and "Homologación" or "")
    Reprocesar = True  # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES
    factura = None

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Persona = ""
        self.Reproceso = ""  # no implementado
        self.cuit = self.dni = 0
        self.tipo_persona = ""  # FISICA o JURIDICA
        self.tipo_doc = self.nro_doc = 0
        self.estado = ""  # ACTIVO
        self.es_sucesion = ""
        self.denominacion = ""
        self.direccion = self.localidad = self.provincia = self.cod_postal = ""
        self.domicilios = []
        self.impuestos = []
        self.actividades = []
        self.imp_iva = self.empleador = self.integrante_soc = self.cat_iva = ""
        self.monotributo = self.actividad_monotributo = ""
        self.data = {}
        self.errores = []

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        ret = self.client.dummy()
        result = ret["dummyReturn"]
        self.AppServerStatus = result["appserver"]
        self.DbServerStatus = result["dbserver"]
        self.AuthServerStatus = result["authserver"]
        return True

    @inicializar_y_capturar_excepciones
    def Consultar(self, id_persona):
        "Devuelve el detalle de todos los datos del contribuyente solicitado"
        # llamar al webservice:
        res = self.client.getPersona(
            sign=self.Sign,
            token=self.Token,
            cuitRepresentada=self.Cuit,
            idPersona=id_persona,
        )
        ret = res.get("personaReturn", {})
        # obtengo el resultado de AFIP (dict):
        data = ret.get("persona", None)
        if isinstance(data, list):
            data = data[0]
        self.data = data
        # lo serializo
        self.Persona = json.dumps(self.data, default=json_serializer)
        # extraigo los campos principales:
        self.cuit = data["idPersona"]
        self.tipo_persona = data["tipoPersona"]
        self.tipo_doc = TIPO_CLAVE.get(data["tipoClave"])
        self.nro_doc = data.get("numeroDocumento")
        self.estado = data.get("estadoClave")
        if not "razonSocial" in data:
            self.denominacion = ", ".join(
                [data.get("apellido", ""), data.get("nombre", "")]
            )
        else:
            self.denominacion = data.get("razonSocial", "")
        # analizo el domicilio, dando prioridad al FISCAL, luego LEGAL/REAL
        domicilios = data.get("domicilio", [])
        domicilios.sort(key=lambda item: item["tipoDomicilio"] != "FISCAL")
        if domicilios:
            domicilio = domicilios[0]
            self.direccion = domicilio.get("direccion", "")
            self.localidad = domicilio.get("localidad", "")  # no usado en CABA
            self.provincia = PROVINCIAS.get(domicilio.get("idProvincia"), "")
            self.cod_postal = domicilio.get("codPostal")
        else:
            self.direccion = self.localidad = self.provincia = ""
            self.cod_postal = ""
        # retrocompatibilidad:
        self.domicilios = domicilios
        self.domicilio = "%s - %s (%s) - %s" % (
            self.direccion,
            self.localidad,
            self.cod_postal,
            self.provincia,
        )
        # analizo impuestos:
        self.impuestos = [
            imp["idImpuesto"]
            for imp in data.get("impuesto", [])
            if imp["estado"] == u"ACTIVO"
        ]
        self.actividades = [act["idActividad"] for act in data.get("actividad", [])]
        mt = [
            cat
            for cat in data.get("categoria", [])
            if cat["idImpuesto"] in (20, 21) and cat["estado"] == "ACTIVO"
        ]
        mt.sort(key=lambda cat: cat["idImpuesto"])
        self.analizar_datos(mt[0] if mt else {})
        return True

    def analizar_datos(self, cat_mt):
        # intenta determinar situación de IVA:
        if 32 in self.impuestos:
            self.imp_iva = "EX"
        elif 33 in self.impuestos:
            self.imp_iva = "NI"
        elif 34 in self.impuestos:
            self.imp_iva = "NA"
        else:
            self.imp_iva = "S" if 30 in self.impuestos else "N"
        self.monotributo = "S" if cat_mt else "N"
        self.actividad_monotributo = (
            cat_mt.get("descripcionCategoria") if cat_mt else ""
        )
        self.integrante_soc = ""
        self.empleador = "S" if 301 in self.impuestos else "N"
        # intenta determinar categoría de IVA (confirmar)
        if self.imp_iva in ("AC", "S"):
            self.cat_iva = 1  # RI
        elif self.imp_iva == "EX":
            self.cat_iva = 4  # EX
        elif self.monotributo == "S":
            self.cat_iva = 6  # MT
        else:
            self.cat_iva = 5  # CF
        return True


class WSSrPadronA5(WSSrPadronA4):
    "Interfaz para el WebService de Consulta Padrón Constancia de Inscripción Alcance 5"

    _reg_progid_ = "WSSrPadronA5"
    _reg_clsid_ = "{DF7447DD-EEF3-4E6B-A93B-F969B5075EC8}"

    WSDL = WSDL.replace("personaServiceA4", "personaServiceA5")

    @inicializar_y_capturar_excepciones
    def Consultar(self, id_persona):
        "Devuelve el detalle de todos los datos del contribuyente solicitado"
        # llamar al webservice:
        res = self.client.getPersona(
            sign=self.Sign,
            token=self.Token,
            cuitRepresentada=self.Cuit,
            idPersona=id_persona,
        )
        ret = res.get("personaReturn", {})
        # obtengo el resultado de AFIP (dict):
        data = ret.get("datosGenerales", {})
        if isinstance(data, list):
            data = data[0]
        self.data = data
        # lo serializo
        self.Persona = json.dumps(ret, default=json_serializer)
        for er in "errorConstancia", "errorMonotributo", "errorRegimenGeneral":
            if er in ret:
                self.errores.extend(ret[er])
        self.Excepcion = "\n\r".join([er["error"] for er in self.errores])
        # extraigo los campos principales:
        self.tipo_persona = data.get("tipoPersona")
        self.tipo_doc = TIPO_CLAVE.get(data.get("tipoClave"))
        self.nro_doc = data.get("idPersona")
        self.cuit = self.nro_doc
        self.estado = data.get("estadoClave")
        self.es_sucesion = data.get("esSucesion")
        if not "razonSocial" in data:
            self.denominacion = ", ".join(
                [data.get("apellido", ""), data.get("nombre", "")]
            )
        else:
            self.denominacion = data.get("razonSocial", "")
        # analizo el domicilio, dando prioridad al FISCAL, luego LEGAL/REAL
        domicilio = data.get("domicilioFiscal", [])
        if domicilio:
            self.direccion = domicilio.get("direccion", "")
            self.localidad = domicilio.get("localidad", "")  # no usado en CABA
            self.provincia = PROVINCIAS.get(domicilio.get("idProvincia"), "")
            self.cod_postal = domicilio.get("codPostal")
        else:
            self.direccion = self.localidad = self.provincia = ""
            self.cod_postal = ""
        # retrocompatibilidad:
        self.domicilios = [domicilio]
        self.domicilio = "%s - %s (%s) - %s" % (
            self.direccion,
            self.localidad,
            self.cod_postal,
            self.provincia,
        )
        # extraer datos impositivos (inscripción / opción) para unificarlos:
        data_mt = ret.get("datosMonotributo", {})
        data_rg = ret.get("datosRegimenGeneral", {})
        # analizo impuestos:
        impuestos = data_mt.get("impuesto", []) + data_rg.get("impuesto", [])
        self.impuestos = [imp["idImpuesto"] for imp in impuestos]
        actividades = data_rg.get("actividad", []) + data_mt.get(
            "actividadMonotributista", []
        )
        self.actividades = [act["idActividad"] for act in actividades]
        cat_mt = data_mt.get("categoriaMonotributo", {})
        self.analizar_datos(cat_mt)
        return not self.errores


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    global CONFIG_FILE

    DEBUG = "--debug" in sys.argv
    safe_console()

    if "--constancia" in sys.argv:
        padron = WSSrPadronA5()
        SECTION = "WS-SR-PADRON-A5"
        service = "ws_sr_constancia_inscripcion"
    else:
        padron = WSSrPadronA4()
        SECTION = "WS-SR-PADRON-A4"
        service = "ws_sr_padron_a4"

    config = abrir_conf(CONFIG_FILE, DEBUG)
    if config.has_section("WSAA"):
        crt = config.get("WSAA", "CERT")
        key = config.get("WSAA", "PRIVATEKEY")
        cuit = config.get(SECTION, "CUIT")
    else:
        crt, key = "reingart.crt", "reingart.key"
        cuit = "20267565393"
    url_wsaa = url_ws = None
    if config.has_option("WSAA", "URL"):
        url_wsaa = config.get("WSAA", "URL")
    if config.has_option(SECTION, "URL") and not HOMO:
        url_ws = config.get(SECTION, "URL")

    # obteniendo el TA para pruebas
    from pyafipws.wsaa import WSAA

    cache = ""
    wsaa = WSAA()
    ta = wsaa.Autenticar(service, crt, key, url_wsaa)
    if DEBUG:
        print("WSAA.Excepcion:", wsaa.Excepcion)
        print("WSAA.Traceback:", wsaa.Traceback)

    padron.SetTicketAcceso(ta)
    padron.Cuit = cuit
    padron.Conectar(cache, url_ws, cacert="conf/afip_ca_info.crt")

    if "--dummy" in sys.argv:
        print(padron.client.help("dummy"))
        padron.Dummy()
        print("AppServerStatus", padron.AppServerStatus)
        print("DbServerStatus", padron.DbServerStatus)
        print("AuthServerStatus", padron.AuthServerStatus)

    if "--csv" in sys.argv:
        csv_reader = csv.reader(
            open("tests/entrada.csv", "r"), dialect="excel", delimiter=","
        )
        csv_writer = csv.writer(open("salida.csv", "w"), dialect="excel", delimiter=",")
        encabezado = next(csv_reader)
        columnas = [
            "cuit",
            "denominacion",
            "estado",
            "direccion",
            "localidad",
            "provincia",
            "cod_postal",
            "impuestos",
            "actividades",
            "imp_iva",
            "monotributo",
            "actividad_monotributo",
            "empleador",
            "imp_ganancias",
            "integrante_soc",
        ]
        csv_writer.writerow(columnas)

        for fila in csv_reader:
            cuit = (fila[0] if fila else "").replace("-", "")
            if cuit.isdigit():
                print("Consultando AFIP online...", cuit, end=" ")
                try:
                    ok = padron.Consultar(cuit)
                except SoapFault as e:
                    ok = None
                    if e.faultstring != "No existe persona con ese Id":
                        raise
                print("ok" if ok else "error", padron.Excepcion)
                # domicilio posiblemente esté en Latin1, normalizar
                csv_writer.writerow(
                    [norm(getattr(padron, campo, "")) for campo in columnas]
                )
        return

    try:

        if "--prueba" in sys.argv:
            id_persona = "20000000516"
        else:
            id_persona = len(sys.argv) > 1 and sys.argv[1] or "20267565393"

        if "--testing" in sys.argv:
            padron.LoadTestXML("tests/xml/%s_resp.xml" % service)
        print("Consultando AFIP online via webservice...", end=" ")
        ok = padron.Consultar(id_persona)

        if DEBUG:
            print("Persona", padron.Persona)
            print(padron.Excepcion)

        print("ok" if ok else "error", padron.Excepcion)
        print("Denominacion:", padron.denominacion)
        print("Tipo:", padron.tipo_persona, padron.tipo_doc, padron.nro_doc)
        print("Estado:", padron.estado)
        print("Es Sucesion:", padron.es_sucesion)
        print("Direccion:", padron.direccion)
        print("Localidad:", padron.localidad)
        print("Provincia:", padron.provincia)
        print("Codigo Postal:", padron.cod_postal)
        print("Impuestos:", padron.impuestos)
        print("Actividades:", padron.actividades)
        print("IVA", padron.imp_iva)
        print("MT", padron.monotributo, padron.actividad_monotributo)
        print("Empleador", padron.empleador)

        if padron.Excepcion:
            print("Excepcion:", padron.Excepcion)
            # ver padron.errores para el detalle

    except:
        raise
        print(padron.XmlRequest)
        print(padron.XmlResponse)
    
    return padron


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSSrPadronA4.InstallDir = WSSrPadronA5.InstallDir = get_install_dir()


if __name__ == "__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register

        win32com.server.register.UseCommandLine(WSSrPadronA4)
        win32com.server.register.UseCommandLine(WSSrPadronA5)
    else:
        main()
