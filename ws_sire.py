#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para emitir un certificado C2005 en AFIP mediante WebService (SOAP), 
por parte de los sistemas del agente de retención.
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2020 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.01b"

import datetime
import decimal
import json
import os
import sys

from utils import inicializar_y_capturar_excepciones, BaseWS, get_install_dir, json_serializer, abrir_conf, norm, SoapFault, SimpleXMLElement
from ConfigParser import SafeConfigParser


HOMO = False
LANZAR_EXCEPCIONES = True
WSDL = "https://ws-aplicativos-reca.homo.afip.gob.ar/sire/ws/v1/c2005/2005?wsdl"
CONFIG_FILE = "rece.ini"


XML_CERTIFICADO_BASE = """<?xml version = "1.0" encoding = "ISO-8859-1"?><certificado/>"""


class WSSIREc2005(BaseWS):
    "Interfaz para el WebService de SIRE certificado 2005"
    _public_methods_ = ['Emitir',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'SetParametros', 'SetTicketAcceso', 'GetParametro',
                        'Dummy', 'Conectar', 'DebugLog', 'SetTicketAcceso']
    _public_attrs_ = ['Token', 'Sign', 'Cuit',
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
        'CertificadoNro', 'CodigoSeguridad',
        'XmlRequest', 'XmlResponse', 'Version', 'InstallDir', 
        'LanzarExcepciones', 'Excepcion', 'Traceback',
        ]

    _reg_progid_ = "WSSIREc2005"
    _reg_clsid_ = "{}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    Reprocesar = True  # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.data = {}
        self.errores = []

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30, soap_server="oracle"):
        return BaseWS.Conectar(self, cache, wsdl, proxy, wrapper, cacert, timeout, soap_server)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.dummy()
        self.AppServerStatus = result['appserver']
        self.DbServerStatus = result['dbserver']
        self.AuthServerStatus = result['authserver']
        return True

    @inicializar_y_capturar_excepciones
    def Emitir(self,
                version=100,
                impuesto=216,
                regimen=831,
                fecha_retencion='2019-11-26T11:22:00.969-03:00',
                importe_retencion=0,
                importe_base_calculo=0,
                regimen_exclusion=False,
                tipo_comprobante=1,
                fecha_comprobante='2019-11-26T11:22:00.969-03:00',
                importe_comprobante=0.00,
                cuit_retenido='30500010912',
                fecha_retencion_certificado_original='2019-11-26T11:22:00.969-03:00',
                codigo_trazabilidad=None,
                condicion=1,    # 1: Inscripto, 2: No inscriptio
                imposibilidad_retencion=False,
                motivo_no_retencion=None,
                porcentaje_exclusion=None,
                fecha_publicacion=None, 
                numero_comprobante='99999-99999999',
                coe=None,
                coe_original=None,
                cae=None,
                motivo_emision_nota_credito=None,
                numero_certificado_original=None,
                importe_certificado_original=None,
                motivo_anulacion=None,
        ):
        """"Método para emitir el certificado 2005.
        
        Args:
            Certificado que se desea emitir.
        Return:
            Devuelve el Nro de certificado 
            Código de seguridad del certificado emitido.
        """
        # llamar al webservice:
        res = self.client.emitir(
            sign=self.Sign,
            token=self.Token,
            cuitAgente=self.Cuit,
            certificado=dict(
                version=version,
                codigoTrazabilidad=codigo_trazabilidad,
                impuesto=impuesto,
                regimen=regimen,
                fechaRetencion=fecha_retencion,
                condicion=condicion,  #opt
                imposibilidadRetencion=imposibilidad_retencion, # opt
                motivoNoRetencion=motivo_no_retencion, # opt motivoNoRetencion>
                importeRetencion=importe_retencion,
                importeBaseCalculo=importe_base_calculo,
                regimenExclusion=regimen_exclusion,
                porcentajeExclusion=porcentaje_exclusion, # opt
                fechaPublicacion=fecha_publicacion, 
                tipoComprobante=tipo_comprobante,
                fechaComprobante=fecha_comprobante,
                numeroComprobante=numero_comprobante, # opt
                coe=coe,
                coeOriginal=coe_original, # opt
                cae=cae,
                importeComprobante=importe_comprobante,
                motivoEmisionNotaCredito=motivo_emision_nota_credito, # opt
                cuitRetenido=cuit_retenido, # opt
                numeroCertificadoOriginal=numero_certificado_original,
                fechaRetencionCertificadoOriginal=fecha_retencion_certificado_original,
                importeCertificadoOriginal=importe_certificado_original,
                motivoAnulacion=motivo_anulacion,
                )
            )
        # obtengo el resultado de AFIP :
        self.CertificadoNro = res["certificadoNro"]
        self.CodigoSeguridad = res["codigoSeguridad"]
        return True


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time
    global CONFIG_FILE

    DEBUG = '--debug' in sys.argv

    sire = WSSIREc2005()
    SECTION = 'WSSIREc2005'
    service = "sire-ws"

    config = abrir_conf(CONFIG_FILE, DEBUG)
    if config.has_section('WSAA'):
        crt = config.get('WSAA', 'CERT')
        key = config.get('WSAA', 'PRIVATEKEY')
        cuit = config.get(SECTION, 'CUIT')
    else:
        crt, key = "reingart.crt", "reingart.key"
        cuit = "20267565393"
    url_wsaa = url_ws = None
    if config.has_option('WSAA','URL'):
        url_wsaa = config.get('WSAA', 'URL')
    if config.has_option(SECTION,'URL') and not HOMO:
        url_ws = config.get(SECTION, 'URL')

    # obteniendo el TA para pruebas
    from wsaa import WSAA

    cache = ""
    ta = WSAA().Autenticar(service, crt, key, url_wsaa)

    sire.SetTicketAcceso(ta)
    sire.Cuit = cuit
    sire.Conectar(cache, url_ws, cacert="conf/afip_ca_info.crt")

    if "--dummy" in sys.argv:
        print sire.client.help("dummy")
        sire.Dummy()
        print "AppServerStatus", sire.AppServerStatus
        print "DbServerStatus", sire.DbServerStatus
        print "AuthServerStatus", sire.AuthServerStatus

    try:

        if "--testing" in sys.argv:
            sire.LoadTestXML("tests/xml/%s_resp.xml" % service)
        print "Consultando AFIP online via webservice...",
        ok = sire.Emitir(
                version=100,
                impuesto=216,
                regimen=831,
                fecha_retencion='2020-07-11T11:16:00.000-03:00',
                importe_retencion=2100.00,
                importe_base_calculo=20000.00,
                regimen_exclusion=False,
                tipo_comprobante=1,
                fecha_comprobante='2020-07-11T11:15:53.000-03:00',
                importe_comprobante=22200.00,
                cuit_retenido='30500010912',
                fecha_retencion_certificado_original='2020-07-11T11:16:00.000-03:00',
                codigo_trazabilidad=None,
                condicion=1,    # 1: Inscripto, 2: No inscriptio
                imposibilidad_retencion=False,
                motivo_no_retencion=None,
                porcentaje_exclusion=None,
                fecha_publicacion=None,
                numero_comprobante='00003-00008497',
                coe=None,
                coe_original=None,
                cae=None,
                motivo_emision_nota_credito=None,
                numero_certificado_original=None,
                importe_certificado_original=None,
                motivo_anulacion=None,

            )

        print "CertificadoNro: ", sire.CertificadoNro
        print "CodigoSeguridad: ", sire.CodigoSeguridad

        print 'ok' if ok else "error!"
        if sire.Excepcion:
            print "Excepcion:", sire.Excepcion

    except:
        raise
        print sire.XmlRequest
        print sire.XmlResponse


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSSIREc2005.InstallDir = get_install_dir()


if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSSrPadronA4)
        win32com.server.register.UseCommandLine(WSSrPadronA5)
    else:
        main()

