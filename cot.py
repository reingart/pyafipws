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

# Based on MultipartPostHandler.py (C) 02/2006 Will Holcomb <wholcomb@gmail.com>
# Ejemplos iniciales gracias a "Matias Gieco matigro@gmail.com"

"Módulo para obtener remito electrónico automático (COT)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.02h"

import os, sys, traceback
from pysimplesoap.simplexml import SimpleXMLElement

from utils import WebClient

HOMO = False
CACERT = "conf/arba.crt"   # establecimiento de canal seguro (en producción)

##URL = "https://cot.ec.gba.gob.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"
# Nuevo servidor para el "Remito Electrónico Automático"
URL = "http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"  # testing
#URL = "https://cot.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"  # prod.


class COT:
    "Interfaz para el servicio de Remito Electronico ARBA"
    _public_methods_ = ['Conectar', 'PresentarRemito', 'LeerErrorValidacion', 
                        'LeerValidacionRemito',
                        'AnalizarXml', 'ObtenerTagXml']
    _public_attrs_ = ['Usuario', 'Password', 'XmlResponse', 
        'Version', 'Excepcion', 'Traceback', 'InstallDir',
        'CuitEmpresa', 'NumeroComprobante', 'CodigoIntegridad', 'NombreArchivo',
        'TipoError', 'CodigoError', 'MensajeError',
        'NumeroUnico', 'Procesado',
        ]
        
    _reg_progid_ = "COT"
    _reg_clsid_ = "{7518B2CF-23E9-4821-BC55-D15966E15620}"

    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    
    def __init__(self):
        self.Usuario = self.Password = None
        self.TipoError = self.CodigoError = self.MensajeError = ""
        self.LastID = self.LastCMP = self.CAE = self.CAEA = self.Vencimiento = ''
        self.InstallDir = INSTALL_DIR
        self.client = None
        self.xml = None
        self.limpiar()

    def limpiar(self):
        self.remitos = []
        self.errores = []
        self.XmlResponse = ""
        self.Excepcion = self.Traceback = ""
        self.TipoError = self.CodigoError = self.MensajeError = ""
        self.CuitEmpresa = self.NumeroComprobante = ""
        self.NombreArchivo = self.CodigoIntegridad  = ""
        self.NumeroUnico = self.Procesado = ""

    def Conectar(self, url=None, proxy="", wrapper=None, cacert=None, trace=False):
        if HOMO or not url:
            url = URL
        self.client = WebClient(location=url, trace=trace, cacert=cacert)

    def PresentarRemito(self, filename, testing=""):
        self.limpiar()
        try:
            if not os.path.exists(filename):
                self.Excepcion = "Archivo no encontrado: %s" % filename
                return False

            archivo = open(filename,"rb")
            if not testing:
                response = self.client(user=self.Usuario, password=self.Password, 
                                   file=archivo)
            else:
                response = open(testing).read()
            self.XmlResponse = response
            self.xml = SimpleXMLElement(response)  
            if 'tipoError' in self.xml:
                self.TipoError = str(self.xml.tipoError)
                self.CodigoError = str(self.xml.codigoError)
                self.MensajeError = str(self.xml.mensajeError).decode('latin1').encode("ascii", "replace")
            if 'cuitEmpresa' in self.xml:
                self.CuitEmpresa = str(self.xml.cuitEmpresa)
                self.NumeroComprobante = str(self.xml.numeroComprobante)
                self.NombreArchivo = str(self.xml.nombreArchivo)
                self.CodigoIntegridad  = str(self.xml.codigoIntegridad)
                if 'validacionesRemitos' in self.xml:
                    for remito in self.xml.validacionesRemitos.remito:
                        d = {
                            'NumeroUnico': str(remito.numeroUnico),
                            'Procesado': str(remito.procesado),
                            'Errores': [],
                            }
                        if 'errores' in remito:
                            for error in remito.errores.error:
                                d['Errores'].append((
                                    str(error.codigo), 
                                    str(error.descripcion).decode('latin1').encode("ascii", "replace")))
                        self.remitos.append(d)
                    # establecer valores del primer remito (sin eliminarlo)
                    self.LeerValidacionRemito(pop=False)
            return True      
        except Exception, e:
                ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
                self.Traceback = ''.join(ex)
                try:
                    self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
                except:
                    self.Excepcion = u"<no disponible>"
                return False

    def LeerValidacionRemito(self, pop=True):
        "Leeo el próximo remito"
        # por compatibilidad hacia atras, la primera vez no remueve de la lista
        # (llamado de PresentarRemito con pop=False)
        if self.remitos:
            remito = self.remitos[0]
            if pop:
                del self.remitos[0]
            self.NumeroUnico = remito['NumeroUnico']
            self.Procesado = remito['Procesado']
            self.errores = remito['Errores']
            return True
        else:
            self.NumeroUnico = ""
            self.Procesado = ""
            self.errores = []
            return False

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
        except Exception, e:
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
                    xml = xml(tag) # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = u"%s" % (e)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__=="__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(COT)
        sys.exit(0)
    elif len(sys.argv)<4:
        print "Se debe especificar el nombre de archivo, usuario y clave como argumentos!"
        sys.exit(1)
        
    cot = COT()
    filename = sys.argv[1]      # TB_20111111112_000000_20080124_000001.txt
    cot.Usuario = sys.argv[2]   # 20267565393
    cot.Password = sys.argv[3]  # 23456

    if '--testing' in sys.argv:
        test_response = "cot_response_multiple_errores.xml"
        #test_response = "cot_response_2_errores.xml"
        #test_response = "cot_response_3_sinerrores.xml"
    else:
        test_response = ""

    if not HOMO:
        for i, arg in enumerate(sys.argv):
            if arg.startswith("--prod"):
                URL = URL.replace("http://cot.test.arba.gov.ar", 
                                  "https://cot.arba.gov.ar")
                print "Usando URL:", URL
                break
            if arg.startswith("https"):
                URL = arg
                print "Usando URL:", URL
                break
        
    cot.Conectar(URL, trace='--trace' in sys.argv, cacert=CACERT)
    cot.PresentarRemito(filename, testing=test_response)
    
    if cot.Excepcion:
        print "Excepcion:", cot.Excepcion
        print "Traceback:", cot.Traceback

    # datos generales:
    print "CUIT Empresa:", cot.CuitEmpresa
    print "Numero Comprobante:", cot.NumeroComprobante
    print "Nombre Archivo:", cot.NombreArchivo
    print "Codigo Integridad:", cot.CodigoIntegridad

    print "Error General:", cot.TipoError, "|", cot.CodigoError, "|", cot.MensajeError
    
    # recorro los remitos devueltos e imprimo sus datos por cada uno:
    while cot.LeerValidacionRemito():
        print "Numero Unico:", cot.NumeroUnico
        print "Procesado:", cot.Procesado
        while cot.LeerErrorValidacion():
            print "Error Validacion:", "|", cot.CodigoError, "|", cot.MensajeError

    # Ejemplos de uso ObtenerTagXml
    if False:
        print "cuit", cot.ObtenerTagXml('cuitEmpresa')
        print "p0", cot.ObtenerTagXml('validacionesRemitos', 'remito', 0, 'procesado')
        print "p1", cot.ObtenerTagXml('validacionesRemitos', 'remito', 1, 'procesado')
