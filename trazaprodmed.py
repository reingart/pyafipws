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

"""Módulo para Trazabilidad de Productos Médicos ANMAT - Disp. 2303/2014
según Especificación Técnica para Pruebas de Servicios (17/09/2015)"""
from __future__ import print_function
from __future__ import absolute_import

# Información adicional y documentación:
# http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosMedicos

from future import standard_library

standard_library.install_aliases()
__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2016-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.01b"

import os
import socket
import sys
import datetime, time
import traceback
import pysimplesoap.client
from pysimplesoap.client import SoapClient, SoapFault, parse_proxy, set_http_wrapper
from pysimplesoap.simplexml import SimpleXMLElement
from io import StringIO

# importo funciones compartidas:
from .utils import (
    leer,
    escribir,
    leer_dbf,
    guardar_dbf,
    N,
    A,
    I,
    json,
    dar_nombre_campo_dbf,
    get_install_dir,
    BaseWS,
    inicializar_y_capturar_excepciones,
)

HOMO = False
TYPELIB = False

WSDL = "https://servicios.pami.org.ar/trazaenprodmed.WebService?wsdl"
WSDL_PROD = "https://servicios.pami.org.ar/trazaprodmed.WebService?wsdl"


class TrazaProdMed(BaseWS):
    "Interfaz para el WebService de Trazabilidad de Productos Médicos ANMAT - PAMI - INSSJP"
    _public_methods_ = [
        "InformarProducto",
        "CrearTransaccion",
        "SendCancelacTransacc",
        "SendCancelacTransaccParcial",
        "GetTransaccionesWS",
        "GetCatalogoElectronicoByGTIN",
        "GetCatalogoElectronicoByGLN",
        "GetMedico",
        "Conectar",
        "LeerError",
        "LeerTransaccion",
        "SetUsername",
        "SetPassword",
        "SetParametro",
        "GetParametro",
        "GetCodigoTransaccion",
        "GetResultado",
        "LoadTestXML",
    ]

    _public_attrs_ = [
        "Username",
        "Password",
        "CodigoTransaccion",
        "Errores",
        "Resultado",
        "XmlRequest",
        "XmlResponse",
        "Version",
        "InstallDir",
        "Traceback",
        "Excepcion",
        "LanzarExcepciones",
        "CantPaginas",
        "HayError",
        "TransaccionesWS",
    ]

    _reg_progid_ = "TrazaProdMed"
    _reg_clsid_ = "{D4112556-EF2E-45D3-A2A2-7A2849A364D9}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s %s" % (
        __version__,
        HOMO and "Homologación" or "",
        pysimplesoap.client.__version__,
    )

    def __init__(self, reintentos=1):
        self.Username = self.Password = None
        self.Transacciones = []
        BaseWS.__init__(self, reintentos)

    def inicializar(self):
        BaseWS.inicializar(self)
        self.CodigoTransaccion = self.Errores = self.Resultado = None
        self.Resultado = ""
        self.Errores = []  # lista de strings para la interfaz
        self.errores = []  # lista de diccionarios (uso interno)
        self.CantPaginas = self.HayError = None

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.errores = ret.get("errores", [])
        self.Errores = [
            "%s: %s" % (it["c_error"], it["d_error"]) for it in ret.get("errores", [])
        ]
        self.Resultado = ret.get("resultado")

    def Conectar(
        self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30
    ):
        # Conecto usando el método estandard:
        print("timeout", timeout)
        ok = BaseWS.Conectar(
            self, cache, wsdl, proxy, wrapper, cacert, timeout, soap_server="jetty"
        )

        if ok:
            # Establecer credenciales de seguridad:
            self.client["wsse:Security"] = {
                "wsse:UsernameToken": {
                    "wsse:Username": self.Username,
                    "wsse:Password": self.Password,
                }
            }
        return ok

    @inicializar_y_capturar_excepciones
    def CrearTransaccion(
        self,
        f_evento,
        h_evento,
        gln_origen,
        gln_destino,
        n_remito,
        n_factura,
        vencimiento,
        gtin,
        lote,
        numero_serial,
        id_evento,
        cuit_medico=None,
        id_obra_social=None,
        apellido="",
        nombres="",
        tipo_documento="",
        n_documento="",
        sexo="",
        calle="",
        numero="",
        piso="",
        depto="",
        localidad="",
        provincia="",
        n_postal="",
        fecha_nacimiento="",
        telefono="",
        nro_afiliado=None,
        cod_diagnostico=None,
        cod_hiv=None,
        id_motivo_devolucion=None,
        otro_motivo_devolucion=None,
    ):
        "Inicializa internamente una estructura TransaccionDTO para informar"
        # creo la transacción con los parámetros para llamar a InformarProducto
        tx = {
            "fEvento": f_evento,
            "hEvento": h_evento,
            "glnOrigen": gln_origen,
            "glnDestino": gln_destino,
            "nroFactura": n_factura,
            "nroRemito": n_remito,
            "vencimiento": vencimiento,
            "gtin": gtin,
            "idEvento": id_evento,
            "nroSerial": numero_serial,
            "lote": lote,
            "cuitMedico": cuit_medico,
            "apellidos": apellido,
            "nombres": nombres,
            "telefono": telefono,
            "calle": calle,
            "nroCalle": numero,
            "departamento": depto,
            "piso": piso,
            "localidad": localidad,
            "provincia": provincia,
            "codPostal": n_postal,
            "fechaNacimiento": fecha_nacimiento,
            "sexo": sexo,
            "idTipoDocumento": tipo_documento,
            "nroDocumento": n_documento,
            "codDiagnostico": cod_diagnostico,
            "codHiv": cod_hiv,
            "idObraSocial": id_obra_social,
            "nroAfiliado": nro_afiliado,
            "idMotivoDevolucion": id_motivo_devolucion,
            "otroMotivoDevolucion": otro_motivo_devolucion,
        }
        self.Transacciones.append(tx)
        return True

    @inicializar_y_capturar_excepciones
    def InformarProducto(self, usuario, password):
        "Realiza el registro de una transacción de producto."
        # El usuario (titular del registro/distribuidor/médico/establecimiento
        # asistencial) informa el evento ocurrido para cada uno de los productos.
        res = self.client.informarProducto(
            transacciones=self.Transacciones,
            usuario=usuario,
            password=password,
        )

        ret = res["return"]

        self.CodigoTransaccion = ret["codigoTransaccion"]
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransacc(self, usuario, password, codigo_transaccion):
        "Realiza la cancelación de una transacción"
        res = self.client.sendCancelacTransacc(
            transaccion=codigo_transaccion,
            usuario=usuario,
            password=password,
        )

        ret = res["return"]

        self.CodigoTransaccion = ret.get("codigoTransaccion")
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransaccParcial(
        self, usuario, password, codigo_transaccion, gtin=None, numero_serial=None
    ):
        "Realiza la cancelación parcial de una transacción"
        res = self.client.sendCancelacTransaccParcial(
            transaccion=codigo_transaccion,
            usuario=usuario,
            password=password,
            gtin=gtin,
            serie=numero_serial,
        )
        ret = res["return"]
        self.CodigoTransaccion = ret.get("codigoTransaccion")
        self.__analizar_errores(ret)
        return True

    def LeerTransaccion(self):
        "Recorro Transacciones devueltas por GetTransaccionesWS"
        # usar GetParametro para consultar el valor retornado por el webservice

        if self.Transacciones:
            # extraigo el primer item
            self.params_out = self.Transacciones.pop(0)
            return True
        else:
            # limpio los parámetros
            self.params_out = {}
            return False

    def LeerError(self):
        "Recorro los errores devueltos y devuelvo el primero si existe"

        if self.Errores:
            # extraigo el primer item
            er = self.Errores.pop(0)
            return er
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def GetTransaccionesWS(
        self,
        usuario,
        password,
        id_transaccion=None,
        gln_agente_origen=None,
        gln_agente_destino=None,
        gtin=None,
        lote=None,
        serie=None,
        id_evento=None,
        fecha_desde_op=None,
        fecha_hasta_op=None,
        fecha_desde_t=None,
        fecha_hasta_t=None,
        fecha_desde_v=None,
        fecha_hasta_v=None,
        n_remito=None,
        n_factura=None,
        id_provincia=None,
        id_estado=None,
        nro_pag=1,
        offset=100,
    ):
        "Obtiene los movimientos realizados y permite filtros de búsqueda"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if id_transaccion is not None:
            kwargs["idTransaccion"] = id_transaccion
        if gln_agente_origen is not None:
            kwargs["glnAgenteOrigen"] = gln_agente_origen
        if gln_agente_destino is not None:
            kwargs["glnAgenteDestino"] = gln_agente_destino
        if gtin is not None:
            kwargs["gtin"] = gtin
        if lote is not None:
            kwargs["lote"] = lote
        if serie is not None:
            kwargs["serie"] = serie
        if id_evento is not None:
            kwargs["idEvento"] = id_evento
        if fecha_desde_op is not None:
            kwargs["fechaOperacionDesde"] = fecha_desde_op
        if fecha_hasta_op is not None:
            kwargs["fechaOperacionHasta"] = fecha_hasta_op
        if fecha_desde_t is not None:
            kwargs["fechaTransaccionDesde"] = fecha_desde_t
        if fecha_hasta_t is not None:
            kwargs["fechaTransaccionHasta"] = fecha_hasta_t
        if fecha_desde_v is not None:
            kwargs["fechaVencimientoDesde"] = fecha_desde_v
        if fecha_hasta_v is not None:
            kwargs["fechaVencimientoHasta"] = fecha_hasta_v
        if n_remito is not None:
            kwargs["remito"] = n_remito
        if n_factura is not None:
            kwargs["factura"] = n_factura
        if id_provincia is not None:
            kwargs["idProvincia"] = id_provincia
        if id_estado is not None:
            kwargs["idEstadoTransaccion"] = id_estado
        if nro_pag is not None:
            kwargs["pagina"] = nro_pag
        if offset is not None:
            kwargs["offset"] = offset

        # llamo al webservice
        res = self.client.getTransaccionesWS(
            usuario=usuario, password=password, **kwargs
        )
        ret = res["return"]
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get("cantPaginas")
            self.HayError = ret.get("hay_error")
            self.Transacciones = [it for it in ret.get("list", [])]
        return True

    @inicializar_y_capturar_excepciones
    def GetCatalogoElectronicoByGTIN(
        self,
        usuario,
        password,
        gtin=None,
        gln=None,
        marca=None,
        modelo=None,
        cuit=None,
        id_nombre_generico=None,
        nro_pag=1,
        offset=100,
    ):
        "Obtiene el Catálogo Electrónico de Medicamentos"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if cuit is not None:
            kwargs["cuit"] = cuit
        if gtin is not None:
            kwargs["gtin"] = gtin
        if gln is not None:
            kwargs["gln"] = gln
        if marca is not None:
            kwargs["marca"] = marca
        if modelo is not None:
            kwargs["modelo"] = modelo
        if id_nombre_generico is not None:
            kwargs["id_nombre_generico"] = id_nombre_generico
        if nro_pag is not None:
            kwargs["pagina"] = nro_pag
        if offset is not None:
            kwargs["offset"] = offset

        # llamo al webservice
        res = self.client.getCatalogoElectronicoByGTIN(
            usuario=usuario, password=password, **kwargs
        )

        ret = res["return"]
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get("cantPaginas")
            self.HayError = ret.get("hay_error")
            self.params_out = dict(
                [(i, it) for i, it in enumerate(ret.get("lstProductos", []))]
            )
            return len(self.params_out)
        else:
            return 0

    def SetUsername(self, username):
        "Establezco el nombre de usuario"
        self.Username = username

    def SetPassword(self, password):
        "Establezco la contraseña"
        self.Password = password

    def GetCodigoTransaccion(self):
        "Devuelvo el código de transacción"
        return self.CodigoTransaccion

    def GetResultado(self):
        "Devuelvo el resultado"
        return self.Resultado


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time, sys

    global WSDL, LOCATION

    DEBUG = "--debug" in sys.argv

    ws = TrazaProdMed()

    ws.Username = "testwservice"
    ws.Password = "testwservicepsw"

    if "--prod" in sys.argv and not HOMO:
        WSDL = WSDL_PROD
        print("Usando WSDL:", WSDL)
        sys.argv.pop(sys.argv.index("--prod"))

    # Inicializo las variables y estructuras para el archivo de intercambio:
    transacciones = []
    errores = []
    formatos = []

    if "--formato" in sys.argv:
        print("Formato:")
        for msg, formato, lista in formatos:
            comienzo = 1
            print("=== %s ===" % msg)
            print(
                "|| %-25s || %-12s || %-5s || %-4s || %-10s ||"
                % ("Nombre", "Tipo", "Long.", "Pos(txt)", "Campo(dbf)")
            )
            claves = []
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                clave_dbf = dar_nombre_campo_dbf(clave, claves)
                claves.append(clave_dbf)
                print(
                    "|| %-25s || %-12s || %5d ||   %4d   || %-10s ||"
                    % (clave, tipo, longitud, comienzo, clave_dbf)
                )
                comienzo += longitud
        sys.exit(0)

    if "--cargar" in sys.argv:
        if "--dbf" in sys.argv:
            leer_dbf(formatos[:1], {})
        elif "--json" in sys.argv:
            for formato in formatos[:1]:
                archivo = open(formato[0].lower() + ".json", "r")
                d = json.load(archivo)
                formato[2].extend(d)
                archivo.close()
        else:
            for formato in formatos[:1]:
                archivo = open(formato[0].lower() + ".txt", "r")
                for linea in archivo:
                    d = leer(linea, formato[1])
                    formato[2].append(d)
                archivo.close()

    ws.Conectar("", WSDL)

    if ws.Excepcion:
        print(ws.Excepcion)
        print(ws.Traceback)
        sys.exit(-1)

    # Datos de pruebas:

    if "--test" in sys.argv:
        ws.CrearTransaccion(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"),
            gln_origen="7791234567801",
            gln_destino="7791234567801",
            n_remito="R0001-12341234",
            n_factura="A0001-12341234",
            vencimiento=(datetime.datetime.now() + datetime.timedelta(30)).strftime(
                "%d/%m/%Y"
            ),
            gtin="07791234567810",
            lote=datetime.datetime.now().strftime("%Y"),  # R4556567
            numero_serial=int(time.time() * 10),  # A23434
            id_evento=1,
            cuit_medico="30711622507",
            id_obra_social=465667,
            apellido="Reingart",
            nombres="Mariano",
            tipo_documento="96",
            n_documento="28510785",
            sexo="M",
            calle="San Martin",
            numero="5656",
            piso="",
            depto="1",
            localidad="Berazategui",
            provincia="Buenos Aires",
            n_postal="1700",
            fecha_nacimiento="20/12/1972",
            telefono="5555-5555",
            nro_afiliado="9999999999999",
            cod_diagnostico="B30",
            cod_hiv="NOAP31121970",
            id_motivo_devolucion=1,
            otro_motivo_devolucion="producto fallado",
        )

    # Opciones principales:

    if "--cancela" in sys.argv:
        if "--loadxml" in sys.argv:
            ws.LoadTestXML("tests/xml/trazaprodmed_cancela_err.xml")  # cargo respuesta
        ws.SendCancelacTransacc(*sys.argv[sys.argv.index("--cancela") + 1 :])
    elif "--cancela_parcial" in sys.argv:
        ws.SendCancelacTransaccParcial(
            *sys.argv[sys.argv.index("--cancela_parcial") + 1 :]
        )
    elif "--consulta" in sys.argv:
        ws.GetTransaccionesWS(*sys.argv[sys.argv.index("--consulta") + 1 :])
        print("CantPaginas", ws.CantPaginas)
        print("HayError", ws.HayError)
        # print "TransaccionPlainWS", ws.TransaccionPlainWS
        # parametros comunes de salida (columnas de la tabla):
        TRANSACCIONES = list(ws.Transacciones[0].keys()) if ws.Transacciones else []
        claves = [k for k in TRANSACCIONES]
        # extiendo la lista de resultado para el archivo de intercambio:
        transacciones.extend(ws.Transacciones)
        # encabezado de la tabla:
        print("||", "||".join(["%s" % clave for clave in claves]), "||")
        # recorro los datos devueltos (TransaccionPlainWS):
        while ws.LeerTransaccion():
            for clave in claves:
                print("||", ws.GetParametro(clave), end=" ")  # imprimo cada fila
            print("||")
    elif "--catalogo" in sys.argv:
        ret = ws.GetCatalogoElectronicoByGTIN(
            *sys.argv[sys.argv.index("--catalogo") + 1 :]
        )
        for catalogo in list(ws.params_out.values()):
            print(catalogo)  # imprimo cada fila
    else:
        argv = [argv for argv in sys.argv if not argv.startswith("--")]
        if not transacciones:
            if len(argv) > 16:
                ws.CrearTransaccion(*argv[3:])
            else:
                print("ERROR: no se indicaron todos los parámetros requeridos")
        if ws.Transacciones:
            try:
                usuario, password = argv[1:3]
            except:
                print("ADVERTENCIA: no se indico parámetros usuario y passoword")
                usuario = password = "pruebasws"
            ws.InformarProducto(usuario, password)
            for i, tx in enumerate(transacciones):
                print("Procesando registro", i)
                tx["codigo_transaccion"] = ws.CodigoTransaccion
                errores.extend(ws.errores)
            print(
                "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|"
                % (
                    ws.Resultado,
                    ws.CodigoTransaccion,
                    "|".join(ws.Errores or []),
                )
            )
        else:
            print("ERROR: no se especificaron productos a informar")

    if ws.Excepcion:
        print(ws.Traceback)

    if "--grabar" in sys.argv:
        if "--dbf" in sys.argv:
            guardar_dbf(formatos, True, {})
        elif "--json" in sys.argv:
            for formato in formatos:
                archivo = open(formato[0].lower() + ".json", "w")
                json.dump(formato[2], archivo, sort_keys=True, indent=4)
                archivo.close()
        else:
            for formato in formatos:
                archivo = open(formato[0].lower() + ".txt", "w")
                for it in formato[2]:
                    archivo.write(escribir(it, formato[1]))
            archivo.close()


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = TrazaProdMed.InstallDir = get_install_dir()


if __name__ == "__main__":

    # ajusto el encoding por defecto (si se redirije la salida)
    if not hasattr(sys.stdout, "encoding") or sys.stdout.encoding is None:
        import codecs, locale

        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(
            sys.stdout, "replace"
        )
        sys.stderr = codecs.getwriter(locale.getpreferredencoding())(
            sys.stderr, "replace"
        )

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import pythoncom

        if TYPELIB:
            if "--register" in sys.argv:
                tlb = os.path.abspath(
                    os.path.join(INSTALL_DIR, "typelib", "trazaprodmed.tlb")
                )
                print("Registering %s" % (tlb,))
                tli = pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif "--unregister" in sys.argv:
                k = TrazaProdMed
                pythoncom.UnRegisterTypeLib(
                    k._typelib_guid_,
                    k._typelib_version_[0],
                    k._typelib_version_[1],
                    0,
                    pythoncom.SYS_WIN32,
                )
                print("Unregistered typelib")
        import win32com.server.register

        win32com.server.register.UseCommandLine(TrazaProdMed)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver

        # win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([TrazaProdMed._reg_clsid_])
    else:
        main()
