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

"""Módulo para acceder a los datos de un contribuyente registrado en el Padrón
de AFIP (WS-SR-PADRON de AFIP). Consulta a Padrón Alcance 4 version 1.1
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2017 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.02b"

import datetime
import decimal
import json
import os
import sys

from utils import verifica, inicializar_y_capturar_excepciones, BaseWS, get_install_dir, json_serializer
from ConfigParser import SafeConfigParser
from padron import TIPO_CLAVE, PROVINCIAS


HOMO = False
LANZAR_EXCEPCIONES = True
WSDL = "https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA4?wsdl"
CONFIG_FILE = "rece.ini"


class WSSrPadronA4(BaseWS):
    "Interfaz para el WebService de Factura Electrónica Comprobantes Turismo"
    _public_methods_ = ['Consultar',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'SetParametros', 'SetTicketAcceso', 'GetParametro',
                        'Dummy', 'Conectar', 'DebugLog', 'SetTicketAcceso']
    _public_attrs_ = ['Token', 'Sign', 'Cuit',
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
        'XmlRequest', 'XmlResponse', 'Version', 'InstallDir', 
        'LanzarExcepciones', 'Excepcion', 'Traceback',
        'Persona', 'data',
        'denominacion', 'imp_ganancias', 'imp_iva',
        'monotributo', 'integrante_soc', 'empleador',
        'actividad_monotributo', 'cat_iva', 'domicilios',
        'tipo_doc', 'nro_doc',
        'tipo_persona', 'estado', 'impuestos', 'actividades',
        'direccion', 'localidad', 'provincia', 'cod_postal',
        ]

    _reg_progid_ = "WSSrPadronA4"
    _reg_clsid_ = "{C2270008-4324-46F6-A2D3-60836EE63BD7}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    Reprocesar = True  # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES
    factura = None

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Persona = ''
        self.Reproceso = '' # no implementado
        self.cuit = self.dni = 0
        self.tipo_persona = ""                      # FISICA o JURIDICA
        self.tipo_doc = 0
        self.estado = ""                            # ACTIVO
        self.denominacion = ""
        self.direccion = self.localidad = self.provincia = self.cod_postal = ""
        self.domicilios = []
        self.impuestos = []
        self.actividades = []
        self.imp_iva = self.empleador = self.integrante_soc = self.cat_iva = ""
        self.monotributo = self.actividad_monotributo = ""
        self.data = {}

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        ret = self.client.dummy()
        result = ret['dummyReturn']
        self.AppServerStatus = result['appserver']
        self.DbServerStatus = result['dbserver']
        self.AuthServerStatus = result['authserver']
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
        ret = res.get('personaReturn', {})
        # obtengo el resultado de AFIP (dict):
        data = ret.get('persona', None)
        if isinstance(data, list):
            data = data[0]
        self.data = data
        # lo serializo
        self.Persona = json.dumps(self.data,
                                  default=json_serializer)
        # extraigo los campos principales:
        self.cuit = data["idPersona"]
        self.tipo_persona = data["tipoPersona"]
        self.tipo_doc = TIPO_CLAVE.get(data["tipoClave"])
        self.nro_doc = data.get("numeroDocumento")
        self.estado = data.get("estadoClave")
        if not "razonSocial" in data:
            self.denominacion = ", ".join([data.get("apellido", ""),
                                          data.get("nombre", "")])
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
        # analizo impuestos:
        self.impuestos = [imp["idImpuesto"] for imp in data.get("impuesto", [])
                          if imp['estado'] == u'ACTIVO']
        self.actividades = [act["idActividad"] for act in data.get("actividad", [])]
        if 32 in self.impuestos:
            self.imp_iva = "EX"
        elif 33 in self.impuestos:
            self.imp_iva = "NI"
        elif 34 in self.impuestos:
            self.imp_iva = "NA"
        else:
            self.imp_iva = "S" if 30 in self.impuestos else "N"
        mt = [cat for cat in data.get("categoria", [])
              if cat["idImpuesto"] in (20, 21) and cat["estado"] == "ACTIVO"]
        mt.sort(key=lambda cat: cat["idImpuesto"])
        self.monotributo = "S" if mt else "N"
        self.actividad_monotributo = mt[0].get("descripcionCategoria") if mt else ""
        self.integrante_soc = ""
        self.empleador = "S" if 301 in self.impuestos else "N"
        self.cat_iva = ""
        return True


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time
    global CONFIG_FILE
    if len(sys.argv)>1 and sys.argv[1][0] in ".\\/":
        CONFIG_FILE = sys.argv.pop(1)
    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    if config.has_section('WSAA'):
        crt = config.get('WSAA', 'CERT')
        key = config.get('WSAA', 'PRIVATEKEY')
        cuit = config.get('WS-SR-PADRON-A4', 'CUIT')
    else:
        crt, key = "reingart.crt", "reingart.key"
        cuit = "20267565393"
    url_wsaa = url_wsa4 = None
    if config.has_option('WSAA','URL'):
        url_wsaa = config.get('WSAA', 'URL') 
    if config.has_option('WS-SR-PADRON-A4','URL') and not HOMO:
        url_wsa4 = config.get('WS-SR-PADRON-A4', 'URL')

    DEBUG = '--debug' in sys.argv

    # obteniendo el TA para pruebas
    from wsaa import WSAA

    cache = ""
    ta = WSAA().Autenticar("ws_sr_padron_a4", crt, key, url_wsaa)

    wssrpadron4 = WSSrPadronA4()
    wssrpadron4.SetTicketAcceso(ta)
    wssrpadron4.Cuit = cuit
    wssrpadron4.Conectar(cache, url_wsa4, cacert="conf/afip_ca_info.crt")

    if "--dummy" in sys.argv:
        print wssrpadron4.client.help("dummy")
        wssrpadron4.Dummy()
        print "AppServerStatus", wssrpadron4.AppServerStatus
        print "DbServerStatus", wssrpadron4.DbServerStatus
        print "AuthServerStatus", wssrpadron4.AuthServerStatus

    try:

        if "--prueba" in sys.argv:
            id_persona = "20000000516"
        else:
            id_persona = len(sys.argv)>1 and sys.argv[1] or "20267565393"

        print "Consultando AFIP online via webservice...",
        ok = wssrpadron4.Consultar(id_persona)

        if DEBUG:
            print "Persona", wssrpadron4.Persona
            print wssrpadron4.Excepcion

        padron = wssrpadron4
        print 'ok' if ok else "error", padron.Excepcion
        print "Denominacion:", padron.denominacion
        print "Tipo:", padron.tipo_persona, padron.tipo_doc, padron.nro_doc
        print "Estado:", padron.estado
        print "Direccion:", padron.direccion
        print "Localidad:", padron.localidad
        print "Provincia:", padron.provincia
        print "Codigo Postal:", padron.cod_postal
        print "Impuestos:", padron.impuestos
        print "Actividades:", padron.actividades
        print "IVA", padron.imp_iva
        print "MT", padron.monotributo, padron.actividad_monotributo
        print "Empleador", padron.empleador

    except:
        raise
        print wssrpadron4.XmlRequest
        print wssrpadron4.XmlResponse


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSSrPadronA4.InstallDir = get_install_dir()


if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSSrPadronA4)
    else:
        main()

