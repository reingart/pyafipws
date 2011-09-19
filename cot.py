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

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.01a"

import os,sys
from simplexml import SimpleXMLElement
import httplib2
from urllib import urlencode
import mimetools, mimetypes
import os, stat, traceback
from cStringIO import StringIO

HOMO = True

#URL = "https://cot.ec.gba.gob.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"
URL = "https://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do" # testing

class WebClient:
    "Minimal webservice client to do POST request with multipart encoded FORM data"

    def __init__(self, location=URL, trace=False):
        self.http = httplib2.Http('.cache')
        self.trace = trace
        self.location = location


    def multipart_encode(self, vars):
        "Enconde form data (vars dict)"
        boundary = mimetools.choose_boundary()
        buf = StringIO()
        for key, value in vars.items():
            if not isinstance(value, file):
                buf.write('--%s\r\n' % boundary)
                buf.write('Content-Disposition: form-data; name="%s"' % key)
                buf.write('\r\n\r\n' + value + '\r\n')
            else:
                fd = value
                file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
                filename = fd.name.split('/')[-1]
                contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                buf.write('--%s\r\n' % boundary)
                buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
                buf.write('Content-Type: %s\r\n' % contenttype)
                # buffer += 'Content-Length: %s\r\n' % file_size
                fd.seek(0)
                buf.write('\r\n' + fd.read() + '\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf

    def __call__(self, **vars):
        "Perform a POST request and return the response"
        boundary, body = self.multipart_encode(vars)
        headers={
            'Content-type': 'multipart/form-data; boundary=%s' % boundary,
            'Content-length': str(len(body)),
                }
        if self.trace:
            print "-"*80
            print "POST %s" % self.location
            print '\n'.join(["%s: %s" % (k,v) for k,v in headers.items()])
            print "\n%s" % body
        response, content = self.http.request(
            self.location,"POST", body=body, headers=headers )
        self.response = response
        self.content = content
        if self.trace: 
            print 
            print '\n'.join(["%s: %s" % (k,v) for k,v in response.items()])
            print content
            print "="*80
        return content


class COT:
    "Interfaz para el servicio de Remito Electronico ARBA"
    _public_methods_ = ['PresentarRemito', 'LeerErrores']
    _public_attrs_ = ['Usuario', 'Password', 'XmlResponse', 
        'Version', 'Excepcion', 'Traceback',
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
        self.client = WebClient(location=URL, trace=trace)

    def PresentarRemito(self, filename, testing=False):
        self.limpiar()
        try:
            archivo = open(filename,"rb")
            response = self.client(user=self.Usuario, password=self.Password, 
                                   file=archivo)
            if testing:
                response = open("cot_response_2_errores.xml").read()
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
                    self.NumeroUnico = str(self.xml.validacionesRemitos.remito.numeroUnico)
                    self.Procesado = str(self.xml.validacionesRemitos.remito.procesado)
                    for error in self.xml.validacionesRemitos.remito.errores.error:
                        self.errores.append((
                            str(error.codigo), 
                            str(error.descripcion).decode('latin1').encode("ascii", "replace")))
                return True      
        except Exception, e:
                ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
                self.Traceback = ''.join(ex)
                try:
                    self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
                except:
                    self.Excepcion = u"<no disponible>"
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

    if len(sys.argv)<4:
        print "Se debe especificar el nombre de archivo, usuario y clave como argumentos!"
        sys.exit(1)
        
    cot = COT()
    filename = sys.argv[1]      # TB_20111111112_000000_20080124_000001.txt
    cot.Usuario = sys.argv[2]   # 20267565393
    cot.Password = sys.argv[3]  # 23456

    cot.Conectar(URL, trace='--trace' in sys.argv)
    cot.PresentarRemito(filename, testing='--testing' in sys.argv)
    
    if cot.Excepcion:
        print "Excepcion:", cot.Excepcion
        print "Traceback:", cot.Traceback
        
    print "Error General:", cot.TipoError, "|", cot.CodigoError, "|", cot.MensajeError
    while cot.LeerErrorValidacion():
        print "Error Validacion:", cot.TipoError, "|", cot.CodigoError, "|", cot.MensajeError
    
    print "CUIT Empresa:", cot.CuitEmpresa
    print "Numero Comprobante:", cot.NumeroComprobante
    print "Nombre Archivo:", cot.NombreArchivo
    print "Codigo Integridad:", cot.CodigoIntegridad
    print "Numero Unico:", cot.NumeroUnico
    print "Procesado:", cot.Procesado
