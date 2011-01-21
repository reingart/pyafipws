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

"""Módulo de ejemplo para obtener código de autorización de impresión o 
electrónico del web service WSFE de AFIP (factura electrónica)
Basado en wsfe-client.php de Gerardo Fisanotti - DvSHyS/DiOPIN/AFIP - 08-jun-07
Definir WSDL, WSFEURL, TA
Devuelve CAE (Código de autorización de impresión o electrónico de WSFE)
"""

__author__ = "Marcelo Alaniz (alanizmarcelo@gmail.com)"
__copyright__ = "Copyright (C) 2008 Marcelo Alaniz"
__license__ = "LGPL 3.0"
__version__ = "1.0"

import sys
from php import date, SimpleXMLElement, SoapClient

WSDL = 'wsfe.wsdl'
WSFEURL = "https://wswhomo.afip.gov.ar/wsfe/service.asmx"
#WSFEURL = "https://wsw.afip.gov.ar/wsfe/service.asmx"
SOAP_ACTION = 'http://ar.gov.afip.dif.facturaelectronica/' # Revisar WSDL
SOAP_NS = "http://ar.gov.afip.dif.facturaelectronica/"     # Revisar WSDL 

TA = 'TA.xml'
CUIT = long(20139999999)


class WSFEError(RuntimeError):
    "Clase para informar errores del WSFE"
    def __init__(self, rerror):
        self.code = str(rerror.percode)
        self.msg = unicode(rerror.perrmsg)

def recuperar_qty(client, token, sign, cuit):
    "Recuperador de cantidad máxima de registros de detalle"
    results = client.FERecuperaQTYRequest(
        argAuth= {"Token": token, "Sign": sign, "cuit":long(cuit)}
    )
    if int(results.FERecuperaQTYRequestResult.RError.percode) != 0:
        print "Percode: %s" % results.FERecuperaQTYRequestResult.RError.percode
        print "MSGerror: %s" % results.FERecuperaQTYRequestResult.RError.perrmsg
        sys.exit(3)
    return int(results.FERecuperaQTYRequestResult.qty.value)
 
def ultnro(client, token, sign, cuit):
    "Recuperador de último número de transacción"
    results = client.FEUltNroRequest(
        argAuth= 
        {
            'Token': token,
            'Sign' : sign,
            'cuit' : cuit
        }
    )

    if int(results.FEUltNroRequestResult.RError.percode) != 0:
        raise WSFEError(results.RError)
    return int(results.FEUltNroRequestResult.nro.value)

def recuperar_last_cmp(client, token, sign, cuit, ptovta, tipocbte):
    "Recuperador de último número de comprobante"
    results = client.FERecuperaLastCMPRequest(
            argAuth =  
            {
                'Token': token,
                'Sign' : sign,
                'cuit' : cuit
            },
            argTCMP=
            {
                'PtoVta' : ptovta,
                'TipoCbte' : tipocbte
            }
    )
    if int(results.FERecuperaLastCMPRequestResult.RError.percode) != 0:
        raise WSFEError(results.RError)
    return int(results.FERecuperaLastCMPRequestResult.cbte_nro)

def aut(client, token, sign, cuit, id, tipo_doc=80, nro_doc=23111111113,
    tipo_cbte=1, punto_vta=1, cbt_desde=0, cbt_hasta=0,
    imp_total=0, imp_neto=0, impto_liq=0.0,
    imp_tot_conc=0, impto_liq_rni=0.00, imp_op_ex=0.00, 
    fecha_cbte=None, fecha_venc_pago=None, 
    presta_serv = 0, fecha_serv_desde=None, fecha_serv_hasta=None, **kwargs ):
    "Facturador (Solicitud de Autorización de Factura Electrónica)"
    
    if fecha_cbte is None: fecha_cbte = date('Ymd')
    if fecha_venc_pago is None: fecha_venc_pago = date('Ymd')
    
    detalle = {
        'tipo_doc': tipo_doc,
        'nro_doc':  nro_doc,
        'tipo_cbte': tipo_cbte,
        'punto_vta': punto_vta,
        'cbt_desde': cbt_desde,
        'cbt_hasta': cbt_hasta,
        'imp_total': imp_total,
        'imp_tot_conc': imp_tot_conc,
        'imp_neto': imp_neto,
        'impto_liq': impto_liq,
        'impto_liq_rni': impto_liq_rni,
        'imp_op_ex': imp_op_ex,
        'fecha_cbte': fecha_cbte,
        'fecha_venc_pago': fecha_venc_pago
    }

    if fecha_serv_desde and fecha_serv_hasta:
        detalle['fecha_serv_desde'] = fecha_serv_desde
        detalle['fecha_serv_hasta'] = fecha_serv_hasta
        
    results = client.FEAutRequest(
            argAuth={'Token': token, 'Sign': sign, 'cuit': long(cuit)},
            Fer={
                'Fecr': {'id': id, 'cantidadreg': 1, 'presta_serv': presta_serv},
                'Fedr': {'FEDetalleRequest': detalle}
            }
        )

    if int(results.FEAutRequestResult.RError.percode) != 0:
        raise WSFEError(results.RError)

    # Resultado: Aceptado o Rechazado
    resultado = str(results.FEAutRequestResult.resultado)
    # Motivo general/del detalle:
    motivo = str(results.FEAutRequestResult.motivo)
    if motivo in ("NULL", '00'):
        motivo = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.motivo)
    reproceso = str(results.FEAutRequestResult.reproceso)
    cae = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.cae)
    fecha_vto = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.fecha_vto)
    #fecha_vto = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
    
    return dict(cae=cae, fecha_vto=fecha_vto, resultado=resultado,
                motivo=motivo, reproceso=reproceso)

def dummy(client):
    results = client.FEDummy()
    print "appserver status %s" % results.appserver
    print "dbserver status %s" % results.dbserver
    print "authserver status %s" % results.authserver
#    if is_soap_fault(results):
#        print "Fault: %s" % results.faultcode
#        print "FaultString: %s " % results.faultstring
#        sys.exit(1)
    return
    

def main():
    # cliente soap del web service
    client = SoapClient(WSFEURL, 
        action = SOAP_ACTION, 
        namespace = SOAP_NS,
        trace = True)

    # obteniendo el TA
    ta_string = open(TA).read()
    ta = SimpleXMLElement(ta_string)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    # fin TA

    CUIT = sys.argv[1]
    punto_vta = 2
    tipo_cbte = 1 # 1: A 6: B
    
    dummy(client)
    
    qty = recuperar_qty(client, token, sign, CUIT)
    last_id = ultnro(client, token, sign, CUIT)
    last_cbte = recuperar_last_cmp(client, token, sign, CUIT, punto_vta, tipo_cbte)
    #import pdb; pdb.set_trace()
    dic = aut(client, token, sign,
        CUIT, id=last_id +1, cbt_desde=last_cbte +1, cbt_hasta=last_cbte +1,
        tipo_doc=80, nro_doc=23111111113, 
        punto_vta=punto_vta, tipo_cbte=tipo_cbte,
        imp_total=0.01, imp_neto=0.01, impto_liq=0.00)
    
    cae = dic['cae']
    
    print "QTY: %s" % qty
    print "Last CBTE: %s" % last_cbte
    print "Last Id: %s" % last_id
    print "CAE: %s" % cae


if __name__ == '__main__':
    main()
