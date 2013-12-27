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

"Módulo para utilizar el servicio web Constatación de Comprobantes de AFIP"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

import sys, os, traceback
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper

# Constantes (si se usa el script de linea de comandos)
WSDL = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL" 
HOMO = False

# No debería ser necesario modificar nada despues de esta linea


class WSCDC:
    "Interfaz para el WebService de Constatación de Comprobantes"
    _public_methods_ = ['Conectar',
                        'AnalizarXml', 'ObtenerTagXml', 'Expirado',
                        'Constatar', 'Dummy',
                        'ComprobantesModalidadConsultar',
                        'ComprobantesTipoConsultar',
                        'DocumentosTipoConsultar', 'OpcionalesTipoConsultar',                        
                        ]
    _public_attrs_ = ['Token', 'Sign', 'ExpirationTime', 'Version', 
                      'XmlRequest', 'XmlResponse', 
                      'InstallDir', 'Traceback', 'Excepcion',
                      'SoapFault', 'LanzarExcepciones',
                    ]
    _readonly_attrs_ = _public_attrs_[:-1]
    _reg_progid_ = "WSCDC"
    _reg_clsid_ = "{6206DF5E-3EEF-47E9-A532-CD81EBBAF3AA}"

    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    
    def __init__(self):
        self.Token = self.Sign = None
        self.InstallDir = INSTALL_DIR
        self.Excepcion = self.Traceback = ""
        self.LanzarExcepciones = True
        self.XmlRequest = self.XmlResponse = ""
        self.xml = None

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None):
        # cliente soap del web service
        try:
            if wrapper:
                Http = set_http_wrapper(wrapper)
                self.Version = WSAA.Version + " " + Http._wrapper_version
            if not isinstance(proxy,dict):
                proxy_dict = parse_proxy(proxy)
            else:
                proxy_dict = proxy
            if HOMO or not wsdl:
                wsdl = WSDL
            if not cache or HOMO:
                # use 'cache' from installation base directory 
                cache = os.path.join(self.InstallDir, 'cache')
            self.client = SoapClient(
                wsdl = wsdl,        
                cache = cache,
                proxy = proxy_dict,
                cacert = cacert,
                trace = "--trace" in sys.argv)
            return True
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            if self.LanzarExcepciones:
                raise
        return False


    def Dummy(self):
        "Método Dummy para verificación de funcionamiento de infraestructura"
        result = self.client.ComprobanteDummy()['ComprobanteDummyResult']
        self.AppServerStatus = result['AppServer']
        self.DbServerStatus = result['DbServer']
        self.AuthServerStatus = result['AuthServer']
        return True


    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto el ticket de acceso)"
        try:
            if not xml or xml=='XmlResponse':
                xml = self.XmlResponse 
            elif xml=='XmlRequest':
                xml = self.XmlRequest 
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception, e:
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

    def ObtenerTagXml(self, *tags):
        "Busca en el Xml analizado y devuelve el tag solicitado"
        # convierto el xml a un objeto
        try:
            if self.xml:
                xml = self.xml
                # por cada tag, lo busco segun su nombre o posición
                for tag in tags:
                    xml = xml(tag) # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]

    def Expirado(self, fecha=None):
        "Comprueba la fecha de expiración, devuelve si ha expirado"
        try:
            if not fecha:
                fecha = self.ObtenerTagXml('expirationTime')
            now = datetime.datetime.now()
            d = datetime.datetime.strptime(fecha[:19], '%Y-%m-%dT%H:%M:%S')
            return now > d
        except Exception, e:
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
        
        
# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))

if hasattr(sys, 'frozen'):
    # we are running as py2exe-packed executable
    import pythoncom
    pythoncom.frozen = 1
    sys.argv[0] = sys.executable


def main():
    wscdc = WSCDC()
    ok = wscdc.Conectar()
    
    if "--dummy" in sys.argv:
        #print wscdc.client.help("ComprobanteDummy")
        wscdc.Dummy()
        print "AppServerStatus", wscdc.AppServerStatus
        print "DbServerStatus", wscdc.DbServerStatus
        print "AuthServerStatus", wscdc.AuthServerStatus
        sys.exit(0)

    # obteniendo el TA
    TA = "TA-wscdc.xml"
    if 'wsaa' in sys.argv or not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wscdc")
        cms = wsaa.sign_tra(tra,"reingart.crt","reingart.key")
        url = "" # "https://wsaa.afip.gov.ar/ws/services/LoginCms"
        ta_string = wsaa.call_wsaa(cms, url)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    # fin TA
    wscdc.Token = str(ta.credentials.token)
    wscdc.Sign = str(ta.credentials.sign)


if __name__=="__main__":
    
    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSCDC)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([WSCDC._reg_clsid_])
    else:
        main()

