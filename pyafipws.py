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

"Módulo de Servidor COM para interface con Windows"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.08"

import sys
import wsaa,wsfe
from php import SimpleXMLElement, SoapFault, SoapClient
import traceback
from win32com.server.exception import COMException
import winerror

HOMO = True

debugging = 1
if debugging:
    from win32com.server.dispatcher import DefaultDebugDispatcher
    useDispatcher = DefaultDebugDispatcher
else:
    useDispatcher = None

vbObjectError= -2147221504
def raiseSoapError(e):
    raise COMException(scode=vbObjectError,
    desc=unicode(e.faultstring),source=u"SOAP "+unicode(e.faultcode))
def checkError(result):
    if int(result.RError.percode) != 0:
        raise COMException(scode = vbObjectError + int(result.RError.percode),
        desc=unicode(result.RError.perrmsg), source="WebService")
def raisePythonException(e):
    ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
    raise COMException(scode = vbObjectError, desc=''.join(ex),source=u"Python")

class WSAA:
    _public_methods_ = ['CreateTRA', 'SignTRA', 'CallWSAA']
    _public_attrs_ = ['Token', 'Sign', 'Version']
    _readonly_attrs_ = _public_attrs_
    _reg_progid_ = "WSAA"
    _reg_clsid_ = "{6268820C-8900-4AE9-8A2D-F0A1EBD4CAC5}"
    
    def __init__(self):
        self.Token = self.Sign = None
        self.Version = __version__
        
    def CreateTRA(self):
        return wsaa.create_tra()

    def SignTRA(self, tra, cert, privatekey):
        return wsaa.sign_tra(str(tra),str(cert),str(privatekey))

    def CallWSAA(self, cms, url=""):
        try:
            if HOMO or not url: url = wsaa.WSAAURL
            xml = wsaa.call_wsaa(str(cms),url)
            ta = SimpleXMLElement(xml)
            self.Token = str(ta.credentials.token)
            self.Sign = str(ta.credentials.sign)
            return xml
        except SoapFault,e:
            raiseSoapError(e)
        except Exception, e:
            raisePythonException(e)

class WSFE:
    _public_methods_ = ['RecuperarQty', 'UltNro', 'RecuperaLastCMP', 'Aut', 'Dummy', 'Conectar' ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Motivo', 'Reproceso',
        'LastID','LastCMP','CAE','Vencimiento']
    _reg_progid_ = "WSFE"
    _reg_clsid_ = "{247A418E-BF48-48B4-B936-D6FF158C0168}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.client = None
        self.Version = __version__

    def Conectar(self, url=""):
        if HOMO or not url: url = wsfe.WSFEURL
        try:
            self.client = SoapClient(url, 
                action = wsfe.SOAP_ACTION, 
                namespace = wsfe.SOAP_NS,
                trace = False,
                exceptions = True)
            return True
        except:
            raise
            #raisePythonException(e)

    def RecuperarQty(self):
        try:
            results = self.client.FERecuperaQTYRequest( argAuth= {
                "Token": self.Token, "Sign": self.Sign, "cuit":long(self.Cuit)})
            checkError(results.FERecuperaQTYRequestResult)
            return int(results.FERecuperaQTYRequestResult.qty.value)
        except COMException:
            raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            raise RuntimeError(''.join(ex))

    def UltNro(self):
        results = self.client.FEUltNroRequest(argAuth= {
            'Token': self.Token, 'Sign' : self.Sign, 'cuit' : long(self.Cuit)})
        checkError(results.FEUltNroRequestResult)
        nro = results.FEUltNroRequestResult.nro.value
        self.LastID = str(nro)
        return str(nro)

    def RecuperaLastCMP(self, ptovta, tipocbte):
        results = self.client.FERecuperaLastCMPRequest(argAuth={
            'Token': self.Token, 'Sign' : self.Sign, 'cuit': long(self.Cuit)},
            argTCMP={'PtoVta': ptovta, 'TipoCbte': tipocbte } )
        checkError(results.FERecuperaLastCMPRequestResult)
        nro = results.FERecuperaLastCMPRequestResult.cbte_nro
        self.LastCMP = str(nro)
        return int(nro)
    
    def Aut(self, id, presta_serv, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            impto_liq, impto_liq_rni, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde="", fecha_serv_hasta=""):
        try:
            detalle = { 'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                        'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                        'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta,
                        'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                        'imp_neto': imp_neto, 'impto_liq': impto_liq,
                        'impto_liq_rni': impto_liq_rni, 'imp_op_ex': imp_op_ex,
                        'fecha_cbte': fecha_cbte,
                        'fecha_venc_pago': fecha_venc_pago,
                        }
            if fecha_serv_desde: detalle['fecha_serv_desde'] = fecha_serv_desde
            if fecha_serv_hasta: detalle['fecha_serv_hasta'] = fecha_serv_hasta

            results = self.client.FEAutRequest(argAuth={
                'Token': self.Token, 'Sign' : self.Sign, 'cuit' : long(self.Cuit)},
                Fer={'Fecr':{
                    'id': long(id), 'cantidadreg': 1, 'presta_serv': int(presta_serv) },
                    'Fedr': {'FEDetalleRequest': detalle,}}) 
            
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
            
            if not 'FEAutRequestResult' in results:
                return ''
            checkError(results.FEAutRequestResult)
            self.Resultado = str(results.FEAutRequestResult.resultado)
            # Motivo general:
            self.Motivo = str(results.FEAutRequestResult.motivo)
            # Motivo del detalle:
            motivo = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.motivo)
            if self.Motivo in ("NULL", '00') and motivo not in ("NULL", "00"):
                self.Motivo = motivo
            self.Reproceso = str(results.FEAutRequestResult.reproceso)
            self.CAE = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.cae)
            vto = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.fecha_vto)
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            return self.CAE
        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        
    def Dummy(self):
        results = self.client.FEDummy()
        self.AppServerStatus = str(results.appserver)
        self.DbServerStatus = str(results.dbserver)
        self.AuthServerStatus = str(results.authserver)
        

if __name__ == '__main__':
    if len(sys.argv)==1:
        sys.argv.append("/register")
    import win32com.server.register
    win32com.server.register.UseCommandLine(WSAA)
    win32com.server.register.UseCommandLine(WSFE)
