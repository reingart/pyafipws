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

"""Módulo para autorizar facturas electrónicas ("refactory" de wsaa y wsfe)
"""

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.0"

import wsfe
import wsaa
from php import SimpleXMLElement, SoapClient

# WARNING:
# Esto por el momento NO FUNCIONA, ver TODOs y habria que analizarlo mejor
# TODO: Tambien habria que reemplazar los exits de wsaa y wsfe por excepciones

class EFacturaWS:
    "Objeto para facturación electrónica"
    def __init__(self,cuit):
        self.cuit = cuit
    
    def login(self,cert,privatekey,wsaa_url):
        tra = wsaa.create_tra(service="wsfe")
        cms = wsaa.sign_tra(tra,cert,privatekey)
        ta = wsaa.call_wsaa(cms,wsaa_url)
    
        # convertir el ticket de acceso en un objeto xml y extrar datos
        ta = SimpleXMLElement(ta_string)
        self.token = str(ta.credentials.token)
        self.sign = str(ta.credentials.sign)
    
    def connect(self,wsfe_url):
        self.client = SoapClient(wsfe_url, 
            action = wsfe.SOAP_ACTION, 
            namespace = wsfe.SOAP_NS,
            trace = False)

    def dummy(self):
        "Consultar estado del WebService"
        wsfe.dummy(self.client)
        
    def recuperar_qty(self):
        "Recupera cantidad de registros"
        return wsfe.recuperar_qty(self.client, self.token, sefl.sign, self.cuit)
        
    def ultnro(self):
        "Obtiene último número de secuencia (id) de autorización"
        return wsfe.ultnro(self.client, sefl.token, self.sign, self.cuit)
            
    def recuperar_last_cmp(self, ptovta, tipocbte):
        "Recupera el último número de comprobante"
        return recuperar_last_cmp(self.client, self.token, self.sign, self.cuit, 
            ptovta, tipocbte)
    
    def aut(self, detalles_facuturas, presta_serv = 0):
        "Facturador (Solicitud de Autorización de Factura Electrónica)"
        # detalle_factura es una lista de "registros" DetalleFactura a autorizar
        last_id = self.ultnro()

        results = self.client.FEAutRequest(
            argAuth = {'Token': token, 'Sign': sign, 'cuit':cuit},
            Fer= {
                'Fecr': {
                    'id': last_id,
                    'cantidadreg': len(detalle_facuturas),
                    'presta_serv': presta_serv,
                },
                'Fedr': [{'FEDetalleRequest': detalle_facutura} 
                        for detalle_facutura in detalles_facuturas ]
                #TODO: revisar serialización de listas y objetos en SoapClient
                }
            )

        if int(results.FEAutRequestResult.RError.percode) != 0:
            print "Percode: %d\nPerrmsg: %s" % (
                results.RError.percode,
                results.RError.perrmsg
            )
            return False
        
        #TODO: hacer implementación de __iter__ en SimpleXMLElement
        #además, habria que indicar a que DetalleFactura pertenece cada CAE
        return [str(FEDetalleResponse.cae) for FEDetalleResponse
                    in results.FEAutRequestResult.FedResp]

#TODO: Constantes para tipo_doc y tipo_cbte

class DetalleFactura:
    def __init__(tipo_doc = 80, nro_doc = 23111111113L, tipo_cbte = 1,
        punto_vta = 1, cbt_desde = 0, cbt_hasta = 99999999, imp_total = 121.0,
        imp_tot_conc= 0, imp_neto= 100.0, impto_liq= 21.0, impto_liq_rni= 0.0,
        imp_op_ex= 0.0, fecha_cbte= None, fecha_venc_pago = None):
        self.tipo_doc = tipo_doc
        #TODO: terminar ...
        fecha_cbte = date('Ymd')
        fecha_venc_pago = date('Ymd')
