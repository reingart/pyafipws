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

"Módulo para Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP Disp. 3683/2011"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.02a"

import os
import socket
import sys
import traceback
import pysimplesoap.client
from pysimplesoap.client import SoapClient, SoapFault, parse_proxy, \
                                set_http_wrapper
from pysimplesoap.simplexml import SimpleXMLElement
from cStringIO import StringIO

HOMO = True

WSDL = "https://186.153.145.2:9050/trazamed.WebService?wsdl"
LOCATION = "https://186.153.145.2:9050/trazamed.WebService"
#WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService?wsdl"


class TrazaMed:
    "Interfaz para el WebService de Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP"
    _public_methods_ = ['SendMedicamentos',
                        'SendCancelacTransacc',
                        'SendMedicamentosDHSerie',
                        'Conectar']
    _public_attrs_ = [
        'Username', 'Password', 
        'CodigoTransaccion', 'Errores', 'Resultado',
        'XmlRequest', 'XmlResponse', 
        'Version', 'InstallDir', 
        'Traceback', 'Excepcion',
        ]

    _reg_progid_ = "TrazaMed"
    _reg_clsid_ = "{8472867A-AE6F-487F-8554-C2C896CFFC3E}"

    Version = "%s %s %s" % (__version__, HOMO and 'Homologación' or '', 
                            pysimplesoap.client.__version__)

    def __init__(self):
        self.Username = self.Password = None
        self.CodigoTransaccion = self.Errores = self.Resultado = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = ''
        self.client = None
        self.Traceback = self.Excepcion = ""
        self.Log = None
        self.InstallDir = INSTALL_DIR

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.Errores = []
        if 'arrayErrores' in ret:
            errores = ret['arrayErrores']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['codigoDescripcion']['codigo'],
                    error['codigoDescripcion']['descripcion'],
                    ))

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None):
        # cliente soap del web service
		try:
			if wrapper:
				Http = set_http_wrapper(wrapper)
				self.Version = TrazaMed.Version + " " + Http._wrapper_version
			proxy_dict = parse_proxy(proxy)
			if HOMO or not wsdl:
				wsdl = WSDL
			if not wsdl.endswith("?wsdl") and wsdl.startswith("http"):
				wsdl += "?wsdl"
			if not cache or HOMO:
				# use 'cache' from installation base directory 
				cache = os.path.join(self.InstallDir, 'cache')
			#self.__log("Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict))
			self.client = SoapClient(
				wsdl = wsdl,        
				cache = cache,
				proxy = proxy_dict,
				ns="tzmed",
				cacert=cacert,
				soap_ns="soapenv",
				#soap_server="jbossas6",
				trace = "--trace" in sys.argv)
				
			self.client.services['IWebServiceService']['ports']['IWebServicePort']['location'] = LOCATION
			
			# Establecer credenciales de seguridad:
			self.client['wsse:Security'] = {
				'wsse:UsernameToken': {
					'wsse:Username': self.Username,
					'wsse:Password': self.Password,
					}
				}
			return True
		except:
			ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
			self.Traceback = ''.join(ex)
			try:
				self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
			except:
				self.Excepcion = u"<no disponible>"
			return False

    def SendMedicamentos(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         numero_serial, id_obra_social, id_evento,
                         cuit_origen, cuit_destino, apellido, nombres,
                         tipo_docmento, n_documento, sexo,
                         direccion, numero, piso, depto, localidad, provincia,
                         n_postal, fecha_nacimiento, telefono,
                         ):
        "Realiza el registro de una transacción de medicamentos. "
        res = self.client.sendMedicamentos(
            arg0={  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'numero_serial': numero_serial, 
                    'id_obra_social': id_obra_social, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_docmento': tipo_docmento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    }, 
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret[0]['codigoTransaccion']
        self.Errores = ["%s: %s" % (it['errores']['_c_error'], it['errores']['_d_error'])
                        for it in ret if 'errores' in it]
        self.Resultado = ret[-1]['resultado']

        return True

        
    def SendMedicamentosDHSerie(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         desde_numero_serial, hasta_numero_serial,
                         id_obra_social, id_evento,
                         cuit_origen, cuit_destino, apellido, nombres,
                         tipo_docmento, n_documento, sexo,
                         direccion, numero, piso, depto, localidad, provincia,
                         n_postal, fecha_nacimiento, telefono,
                         ):
        "Envía un lote de medicamentos informando el desde-hasta número de serie"
        res = self.client.sendMedicamentosDHSerie(
            arg0={  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'desde_numero_serial': desde_numero_serial, 
                    'hasta_numero_serial': hasta_numero_serial, 
                    'id_obra_social': id_obra_social, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_docmento': tipo_docmento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    }, 
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret[0]['codigoTransaccion']
        self.Errores = ["%s: %s" % (it['errores']['_c_error'], it['errores']['_d_error'])
                        for it in ret if 'errores' in it]
        self.Resultado = ret[-1]['resultado']

        return True

    def SendCancelacTransacc(self, usuario, password, codigo_transaccion):
        " Realiza la cancelación de una transacción"
        res = self.client.sendCancelacTransacc(
            arg0=codigo_transaccion, 
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret[0]['codigoTransaccion']
        self.Errores = ["%s: %s" % (it['errores']['_c_error'], it['errores']['_d_error'])
                        for it in ret if 'errores' in it]
        self.Resultado = ret[-1]['resultado']

        return True

def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = '--debug' in sys.argv

    ws = TrazaMed()
    
    ws.Username = 'testwservice'
    ws.Password = 'testwservicepsw'
    
    ws.Conectar()
    
    #print ws.client.services
    #op = ws.client.get_operation("sendMedicamentos")
    #import pdb;pdb.set_trace()
    if '--test' in sys.argv:
        ws.SendMedicamentos(
            usuario='pruebasws', password='pruebasws',
            f_evento="25/11/2011", h_evento="04:24", 
            gln_origen="glnws", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento="30/11/2011", gtin="GTIN1", lote="1111",
            numero_serial="12345", id_obra_social=None, id_evento=133,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_docmento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="B1688FDD", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",)
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Erroes", ws.Errores
    elif '--testdh' in sys.argv:
        print "Informando medicamentos..."
        ws.SendMedicamentosDHSerie(
            usuario='pruebasws', password='pruebasws',
            f_evento="25/11/2011", h_evento="04:24", 
            gln_origen="glnws", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento="30/11/2011", gtin="GTIN1", lote="1111",
            desde_numero_serial="2224", hasta_numero_serial="2225", 
            id_obra_social=None, id_evento=133,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_docmento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="B1688FDD", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",)
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Erroes", ws.Errores
        codigo_transaccion = ws.CodigoTransaccion
        print "Cancelando..."
        ws.SendCancelacTransacc(
            usuario='pruebasws', password='pruebasws',
            codigo_transaccion=codigo_transaccion)
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Erroes", ws.Errores
    else:
        ws.SendMedicamentos(*sys.argv[1:])
        print "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|" % (
                ws.Resultado,
                ws.CodigoTransaccion,
                '|'.join(ws.Errores),
                )

# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(TrazaMed)
    else:
        main()
