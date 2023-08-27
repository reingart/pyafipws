#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.

"Módulo para consultar percepciones / retenciones ARBA IIBB"
from __future__ import print_function
from __future__ import absolute_import

from builtins import str
from builtins import object

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.01b"

import os, sys, tempfile, traceback
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
from pysimplesoap.simplexml import SimpleXMLElement

from pyafipws.utils import WebClient

HOMO = False
CACERT = "conf/arba.crt"  # establecimiento de canal seguro (en producción)

URL = "https://dfe.test.arba.gov.ar/DomicilioElectronico/SeguridadCliente/dfeServicioConsulta.do"  # testing
##URL = "https://dfe.arba.gov.ar/DomicilioElectronico/SeguridadCliente/dfeServicioConsulta.do"  # produccion


XML_ENTRADA_BASE = """<?xml version = "1.0" encoding = "ISO-8859-1"?>
<CONSULTA-ALICUOTA>
    <cantidadContribuyentes>1</cantidadContribuyentes>
      <contribuyentes class="list">
        <contribuyente>
        </contribuyente>
      </contribuyentes>
</CONSULTA-ALICUOTA>
"""


class IIBB(object):
    "Interfaz para el servicio de IIBB ARBA"
    _public_methods_ = [
        "Conectar",
        "ConsultarContribuyentes",
        "LeerContribuyente",
        "LeerErrorValidacion",
        "AnalizarXml",
        "ObtenerTagXml",
    ]
    _public_attrs_ = [
        "Usuario",
        "Password",
        "XmlResponse",
        "Version",
        "Excepcion",
        "Traceback",
        "InstallDir",
        "NumeroComprobante",
        "CantidadContribuyentes",
        "CodigoHash",
        "CuitContribuyente",
        "AlicuotaPercepcion",
        "AlicuotaRetencion",
        "GrupoPercepcion",
        "GrupoRetencion",
        "TipoError",
        "CodigoError",
        "MensajeError",
    ]

    _reg_progid_ = "IIBB"
    _reg_clsid_ = "{2C7E29D2-0C99-49D8-B04B-A16B807BB123}"

    Version = "%s %s" % (__version__, HOMO and "Homologación" or "")

    def __init__(self):
        self.Usuario = self.Password = None
        self.TipoError = self.CodigoError = self.MensajeError = ""
        self.InstallDir = INSTALL_DIR
        self.client = None
        self.xml = None
        self.limpiar()

    def limpiar(self):
        self.NumeroComprobante = self.CodigoHash = ""
        self.CantidadContribuyentes = 0
        self.CuitContribuyente = ""
        self.AlicuotaPercepcion = 0
        self.AlicuotaRetencion = 0
        self.GrupoPercepcion = 0
        self.GrupoRetencion = 0
        self.contribuyentes = []
        self.errores = []
        self.XmlResponse = ""
        self.Excepcion = self.Traceback = ""
        self.TipoError = self.CodigoError = self.MensajeError = ""

    def Conectar(
        self, url=None, proxy="", wrapper=None, cacert=None, trace=False, testing=""
    ):
        if HOMO or not url:
            url = URL
        self.client = WebClient(location=url, trace=trace, cacert=cacert)
        self.testing = testing

    def ConsultarContribuyentes(self, fecha_desde, fecha_hasta, cuit_contribuyente):
        "Realiza la consulta remota a ARBA, estableciendo los resultados"
        self.limpiar()
        try:

            self.xml = SimpleXMLElement(XML_ENTRADA_BASE)
            self.xml.fechaDesde = fecha_desde
            self.xml.fechaHasta = fecha_hasta
            self.xml.contribuyentes.contribuyente.cuitContribuyente = cuit_contribuyente

            xml = self.xml.as_xml()
            self.CodigoHash = md5(xml).hexdigest()
            nombre = "DFEServicioConsulta_%s.xml" % self.CodigoHash

            # guardo el xml en el archivo a enviar y luego lo re-abro:
            with open(os.path.join(tempfile.gettempdir(), nombre), "wb") as archivo:
                archivo.write(xml)

            if not self.testing:
                with open(os.path.join(tempfile.gettempdir(), nombre), "r") as archivo:
                    response = self.client(
                        user=self.Usuario, password=self.Password, file=archivo)
            else:
                with open(self.testing) as archivo:
                    response = archivo.read()
            self.XmlResponse = response
            self.xml = SimpleXMLElement(response)
            if "tipoError" in self.xml:
                self.TipoError = str(self.xml.tipoError)
                self.CodigoError = str(self.xml.codigoError)
                self.MensajeError = (
                    str(self.xml.mensajeError)
                )
            if "numeroComprobante" in self.xml:
                self.NumeroComprobante = str(self.xml.numeroComprobante)
                self.CantidadContribuyentes = int(self.xml.cantidadContribuyentes)
                if "contribuyentes" in self.xml:
                    for contrib in self.xml.contribuyente:
                        c = {
                            "CuitContribuytente": str(contrib.cuitContribuyente),
                            "AlicuotaPercepcion": str(contrib.alicuotaPercepcion),
                            "AlicuotaRetencion": str(contrib.alicuotaRetencion),
                            "GrupoPercepcion": str(contrib.grupoPercepcion),
                            "GrupoRetencion": str(contrib.grupoRetencion),
                            "Errores": [],
                        }
                        self.contribuyentes.append(c)
                    # establecer valores del primer contrib (sin eliminarlo)
                    self.LeerContribuyente(pop=False)
            return True
        except Exception as e:
            ex = traceback.format_exception(
                sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]
            )
            self.Traceback = "".join(ex)
            try:
                self.Excepcion = traceback.format_exception_only(
                    sys.exc_info()[0], sys.exc_info()[1]
                )[0]
            except:
                self.Excepcion = u"<no disponible>"
            return False

    def LeerContribuyente(self, pop=True):
        "Leeo el próximo contribuyente"
        # por compatibilidad hacia atras, la primera vez no remueve de la lista
        # (llamado de ConsultarContribuyentes con pop=False)
        if self.contribuyentes:
            contrib = self.contribuyentes[0]
            if pop:
                del self.contribuyentes[0]
        else:
            contrib = {}
        self.CuitContribuyente = contrib.get("CuitContribuytente", "")
        self.AlicuotaPercepcion = contrib.get("AlicuotaPercepcion", "")
        self.AlicuotaRetencion = contrib.get("AlicuotaRetencion", "")
        self.GrupoPercepcion = contrib.get("GrupoPercepcion", "")
        self.GrupoRetencion = contrib.get("GrupoRetencion", "")
        self.errores = contrib.get("Errores", [])
        return len(contrib) > 0

    def LeerErrorValidacion(self):
        if self.errores:
            error = self.errores.pop()
            self.TipoError = ""
            self.CodigoError = error[0]
            self.MensajeError = error[1]
            return True
        else:
            self.TipoError = ""
            self.CodigoError = ""
            self.MensajeError = ""
            return False

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto la respuesta)"
        try:
            if not xml:
                xml = self.XmlResponse
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception as e:
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
                    xml = xml(tag)  # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception as e:
            self.Excepcion = u"%s" % (e)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"):
    basepath = __file__
elif sys.frozen == "dll":
    import win32api

    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


def main():
    global CACERT, URL, HOMO
    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register

        win32com.server.register.UseCommandLine(IIBB)
        sys.exit(0)
    elif len(sys.argv) < 6:
        print(
            "Se debe especificar usuario, clave, fecha desde/hasta y cuit como argumentos!"
        )
        sys.exit(1)

    iibb = IIBB()
    iibb.Usuario = sys.argv[1]  # 20267565393
    iibb.Password = sys.argv[2]  # 23456
    fecha_desde = sys.argv[3]  # 20150301
    fecha_hasta = sys.argv[4]  # 20150331
    cuit_contribuyente = sys.argv[5]  # 30123456780

    if "--testing" in sys.argv:
        test_response = "iibb_response.xml"
        # test_response = "iibb_response_2_errores.xml"
    else:
        test_response = ""

    if not HOMO:
        for i, arg in enumerate(sys.argv):
            if arg.startswith("--prod"):
                URL = URL.replace(
                    "https://dfe.test.arba.gov.ar/", "https://dfe.arba.gov.ar/"
                )
                print("Usando URL:", URL)
                break
            if arg.startswith("https"):
                URL = arg
                print("Usando URL:", URL)
                break

    iibb.Conectar(
        URL, trace="--trace" in sys.argv, cacert=CACERT, testing=test_response
    )
    iibb.ConsultarContribuyentes(fecha_desde, fecha_hasta, cuit_contribuyente)

    if iibb.Excepcion:
        print("Excepcion:", iibb.Excepcion)
        print("Traceback:", iibb.Traceback)

    # datos generales:
    print("Numero Comprobante:", iibb.NumeroComprobante)
    print("Codigo HASH:", iibb.CodigoHash)
    print(
        "Error General:", iibb.TipoError, "|", iibb.CodigoError, "|", iibb.MensajeError
    )

    # recorro los contribuyentes devueltos e imprimo sus datos por cada uno:
    while iibb.LeerContribuyente():
        print("CUIT Contribuytente:", iibb.CuitContribuyente)
        print("AlicuotaPercepcion:", iibb.AlicuotaPercepcion)
        print("AlicuotaRetencion:", iibb.AlicuotaRetencion)
        print("GrupoPercepcion:", iibb.GrupoPercepcion)
        print("GrupoRetencion:", iibb.GrupoRetencion)

    # Ejemplos de uso ObtenerTagXml
    if False:
        print("desde", iibb.ObtenerTagXml("fechaDesde"))
        print("hasta", iibb.ObtenerTagXml("fechaHasta"))
        print(
            "cuit",
            iibb.ObtenerTagXml(
                "contribuyentes", "contribuyente", 0, "cuitContribuyente"
            ),
        )
        print(
            "alicuota",
            iibb.ObtenerTagXml(
                "contribuyentes", "contribuyente", 0, "alicuotapercepcion"
            ),
        )

if __name__ == "__main__":
    main()
