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

"Módulo de Servidor COM para interfaz con Windows"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.26c"

import sys
import wsfe, wsbfe, wsfex, wsctg, wdigdepfiel
from php import SimpleXMLElement, SoapFault, SoapClient, parse_proxy
import traceback
from win32com.server.exception import COMException
import winerror
import socks
import pythoncom

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


class WSFE:
    "Interfaz para el WebService de Factura Electrónica"
    _public_methods_ = ['RecuperarQty', 'UltNro', 'RecuperaLastCMP', 'Aut', 'Dummy', 'Conectar' ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Motivo', 'Reproceso',
        'CbtDesde', 'CbtHasta', 'FechaCbte', 'ImpTotal', 'ImpNeto', 'ImptoLiq',
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
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.CbtDesde = self.CbtHasta = self.FechaCbte = None
        self.ImpTotal = self.ImpNeto = self.ImptoLiq = None
        
    def Conectar(self, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = wsfe.WSFEURL
        proxy_dict = parse_proxy(proxy)
        try:
            self.client = SoapClient(url, 
                action = wsfe.SOAP_ACTION, 
                namespace = wsfe.SOAP_NS,
                trace = False,
                exceptions = True, proxy = proxy_dict)
            return True
        except Exception, e:
            ##raise
            raisePythonException(e)

    def RecuperarQty(self):
        "Recuperar cantidad máxima de registros de detalle"
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
        "Recuperar el último número de transacción (id)"
        results = self.client.FEUltNroRequest(argAuth= {
            'Token': self.Token, 'Sign' : self.Sign, 'cuit' : long(self.Cuit)})
        checkError(results.FEUltNroRequestResult)
        nro = results.FEUltNroRequestResult.nro.value
        self.LastID = str(nro)
        return str(nro)

    def RecuperaLastCMP(self, ptovta, tipocbte):
        "Recuperar último número de comprobante autorizado"
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
        "Autorizar la factura y devuelve CAE"
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
            
            # completo los campos devueltos
            self.CbtDesde = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.cbt_desde)
            self.CbtHasta = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.cbt_hasta)
            self.FechaCbte = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.fecha_cbte)
            self.ImpTotal = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.imp_total)
            self.ImpNeto = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.imp_neto)
            self.ImptoLiq = str(results.FEAutRequestResult.FedResp.FEDetalleResponse.impto_liq)

            return self.CAE
        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo los mensajes para depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.FEDummy()
        self.AppServerStatus = str(results.appserver)
        self.DbServerStatus = str(results.dbserver)
        self.AuthServerStatus = str(results.authserver)
        

class WSBFE:
    "Interfaz para el WebService de Bono Fiscal Electrónico (FE Bs. Capital)"
    _public_methods_ = ['CrearFactura', 'AgregarItem', 'Authorize', 'GetCMP',
                        'GetParamMon', 'GetParamTipoCbte', 'GetParamUMed', 'GetParamTipoIVA', 'GetParamNCM',
                        'Dummy', 'Conectar', 'GetLastCMP', 'GetLastID' ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Obs', 'Reproceso',
        'CAE','Vencimiento', 'Eventos', 
        'FechaCbte', 'ImpNeto', 'ImptoLiq','ImpTotal']
        
    _reg_progid_ = "WSBFE"
    _reg_clsid_ = "{02CBC6DA-455D-4EE6-8302-411D13253CBF}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.Obs = None
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.factura = None
        self.FechaCbte = ImpNeto = ImptoLiq = ImpTotal = None

    def Conectar(self, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = wsbfe.WSBFEURL
        proxy_dict = parse_proxy(proxy)
        try:
            self.client = SoapClient(url, 
                action = wsbfe.SOAP_ACTION, 
                namespace = wsbfe.SOAP_NS,
                trace = False,
                exceptions = True, proxy = proxy_dict)
            return True
        except Exception, e:
            ##raise
            raisePythonException(e)

    def CrearFactura(self, tipo_doc=80, nro_doc=23111111113,
            zona=0, tipo_cbte=1, punto_vta=1, cbte_nro=0, fecha_cbte=None,
            imp_total=0.0, imp_neto=0.0, impto_liq=0.0,
            imp_tot_conc=0.0, impto_liq_rni=0.00, imp_op_ex=0.00,
            imp_perc=0.00, imp_iibb=0.00, imp_perc_mun=0.00, imp_internos=0.00,
            imp_moneda_id=0, imp_moneda_ctz=1.0):
        "Creo un objeto factura (interna)"
        # Creo una factura para bonos fiscales electrónicos
        factura = wsbfe.FacturaBF()
        # Establezco el encabezado
        factura.tipo_doc = tipo_doc
        factura.nro_doc = nro_doc
        factura.zona = zona
        factura.tipo_cbte = tipo_cbte
        factura.punto_vta = punto_vta
        factura.cbte_nro = cbte_nro
        factura.fecha_cbte = fecha_cbte
        factura.imp_total = imp_total
        factura.imp_neto = imp_neto
        factura.impto_liq = impto_liq
        factura.imp_tot_conc = imp_tot_conc
        factura.impto_liq_rni = impto_liq_rni
        factura.imp_op_ex = imp_op_ex
        factura.imp_perc = imp_perc
        factura.imp_iibb = imp_iibb
        factura.imp_perc_mun = imp_perc_mun
        factura.imp_internos = imp_internos
        factura.imp_moneda_id = imp_moneda_id
        factura.imp_moneda_ctz = imp_moneda_ctz
        self.factura = factura
        
    def AgregarItem(self, ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total):
        "Agrego un item a una factura (interna)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        item = wsbfe.ItemBF(ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total)
        self.factura.items.append(item)

    def Authorize(self, id):
        "Autoriza la factura en memoria (interna)"
        try:
            # llamo al web service
            auth, events = wsbfe.authorize(self.client, 
                                     self.Token, self.Sign, self.Cuit, 
                                     id=id, factura=self.factura.to_dict())
                       
            # Resultado: A: Aceptado, R: Rechazado
            self.Resultado = auth['resultado']
            # Obs:
            self.Obs = auth['obs'].strip(" ")
            self.Reproceso = auth['reproceso']
            self.CAE = auth['cae']
            vto = str(auth['fch_venc_cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]
            return self.CAE
        except wsbfe.BFEError, e:
            raise COMException(scode = vbObjectError + int(e.code),
                               desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
        
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = wsbfe.dummy(self.client)
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    def GetCMP(self, tipo_cbte, punto_vta, cbte_nro):
        try:
            cbt, events = wsbfe.get_cmp(self.client, 
                                    self.Token, self.Sign, self.Cuit, 
                                    tipo_cbte, punto_vta, cbte_nro)
            
            self.FechaCbte = cbt['fch_cbte']
            self.ImpTotal = cbt['imp_total']
            self.ImpNeto = cbt['imp_neto']
            self.ImptoLiq = cbt['impto_liq']

            # Obs, cae y fecha cae
            self.Obs = cbt['obs'].strip(" ")
            self.CAE = cbt['cae']
            vto = str(cbt['fch_venc_cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]
            return self.CAE

        except wsbfe.BFEError, e:
            raise COMException(scode = vbObjectError + int(e.code),
                               desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    def Factura(self):
        return self.factura

    def GetLastCMP(self, tipo_cbte, punto_vta):
        "Recuperar último número de comprobante emitido"
        try:
            cbte_nro, cbte_fecha, events = wsbfe.get_last_cmp(self.client, 
                                    self.Token, self.Sign, self.Cuit, 
                                    tipo_cbte, punto_vta)
            return cbte_nro
        except wsbfe.BFEError, e:
            raise COMException(scode = vbObjectError + int(e.code),
                               desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            raiseSoapError(e)
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    def GetLastID(self):
        "Recuperar último número de transacción (ID)"
        try:
            id, events = wsbfe.get_last_id(self.client, 
                                    self.Token, self.Sign, self.Cuit)
            return id
        except wsbfe.BFEError, e:
            raise COMException(scode = vbObjectError + int(e.code),
                               desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            raiseSoapError(e)
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    def GetParamMon(self):
        "Recuperar lista de valores referenciales de codigos de Moneda"
        params = wsbfe.get_param_mon(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]

    def GetParamTipoCbte(self):
        "Recuperar lista de valores referenciales de códigos de Tipos de comprobante"
        params = wsbfe.get_param_tipo_cbte(self.client, self.Token, self.Sign, self.Cuit)
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]    

    def GetParamUMed(self):
        "Recuperar lista de valores referenciales de Unidades de Medidas"
        params = wsbfe.get_param_umed(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]
    
    def GetParamTipoIVA(self):
        "Recuperar lista de valores referenciales de tipos de IVA (alícuotas)"
        params = wsbfe.get_param_tipo_iva(self.client, self.Token, self.Sign, self.Cuit)
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]
    
    def GetParamNCM(self):
        "Recuperar lista de valores referenciales de códigos del Nomenclador Común del Mercosur"
        params = wsbfe.get_param_ncm(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%(codigo)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]


class WSFEX:
    "Interfaz para el WebService de Factura Electrónica Exportación"
    _public_methods_ = ['CrearFactura', 'AgregarItem', 'Authorize', 'GetCMP',
                        'AgregarPermiso', 'AgregarCmpAsoc',
                        'GetParamMon', 'GetParamTipoCbte', 'GetParamTipoExpo', 
                        'GetParamIdiomas', 'GetParamUMed', 'GetParamIncoterms', 
                        'GetParamDstPais','GetParamDstCUIT',
                        'GetParamCtz',
                        'Dummy', 'Conectar', 'GetLastCMP', 'GetLastID' ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Obs', 'Reproceso',
        'CAE','Vencimiento', 'Eventos', 'ErrCode', 'ErrMsg',
        'Excepcion', 'LanzarExcepciones', 'Traceback',
        'CbteNro', 'FechaCbte', 'ImpTotal']
        
    _reg_progid_ = "WSFEX"
    _reg_clsid_ = "{B3C8D3D3-D5DA-44C9-B003-11845803B2BD}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.factura = None
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.ErrCode = self.ErrMsg = None
        self.LanzarExcepciones = True
        self.Traceback = self.Excepcion = ""

    def Conectar(self, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = wsfex.WSFEXURL
        proxy_dict = parse_proxy(proxy)
        try:
            self.client = SoapClient(url, 
                action = wsfex.SOAP_ACTION, 
                namespace = wsfex.SOAP_NS,
                trace = False,
                exceptions = True, proxy = proxy_dict)
            return True
        except Exception, e:
            ##raise
            raisePythonException(e)

    def CrearFactura(self, tipo_cbte=19, punto_vta=1, cbte_nro=0, fecha_cbte=None,
            imp_total=0.0, tipo_expo=1, permiso_existente="N", dst_cmp=None,
            cliente="", cuit_pais_cliente="", domicilio_cliente="",
            id_impositivo="", moneda_id="PES", moneda_ctz=1.0,
            obs_comerciales="", obs="", forma_pago="", incoterms="", 
            idioma_cbte=7):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación 
        factura = wsfex.FacturaEX()
        # Establezco el encabezado
        factura.tipo_cbte = tipo_cbte
        factura.punto_vta = punto_vta
        factura.cbte_nro = cbte_nro
        factura.fecha_cbte = fecha_cbte
        factura.tipo_expo = tipo_expo
        factura.permiso_existente = permiso_existente
        factura.dst_cmp = dst_cmp
        factura.cliente = cliente
        factura.cuit_pais_cliente = cuit_pais_cliente
        factura.domicilio_cliente = domicilio_cliente
        factura.id_impositivo = id_impositivo
        factura.moneda_id = moneda_id
        factura.moneda_ctz = moneda_ctz
        factura.obs_comerciales = obs_comerciales
        factura.obs = obs
        factura.forma_pago = forma_pago
        factura.incoterms = incoterms
        factura.idioma_cbte = idioma_cbte
        factura.imp_total = imp_total
        self.factura = factura
        
    def AgregarItem(self, codigo, ds, qty, umed, precio, imp_total):
        "Agrego un item a una factura (interna)"
        # Nota: no se calcula total (debe venir calculado!)
        item = wsfex.ItemFEX(codigo, ds, qty, umed, precio, imp_total)
        self.factura.items.append(item)
       
    def AgregarPermiso(self, id, dst):
        "Agrego un permiso a una factura (interna)"
        permiso = wsfex.PermisoFEX(id, dst)
        self.factura.add_permiso(permiso)

    def AgregarCmpAsoc(self, tipo=19, punto_vta=0, cbte_nro=0):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = wsfex.CmpAsocFEX(tipo, punto_vta, cbte_nro)
        self.factura.add_cmp_asoc(cmp_asoc)

    def Authorize(self, id):
        "Autoriza la factura cargada en memoria"
        try:
            # limpio errores
            self.Exception = self.Traceback = ""
            self.ErrCode = self.ErrMsg = ""
            # llamo al web service
            auth, events = wsfex.authorize(self.client, 
                                     self.Token, self.Sign, self.Cuit, 
                                     id=id, factura=self.factura.to_dict())
                       
            # Resultado: A: Aceptado, R: Rechazado
            self.Resultado = auth['resultado']
            # Obs:
            self.Obs = auth['obs'].strip(" ")
            self.Reproceso = auth['reproceso']
            self.CAE = auth['cae']
            self.CbteNro  = auth['cbte_nro']
            vto = str(auth['fch_venc_cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]
            return self.CAE
        except wsfex.FEXError, e:
            self.ErrCode = unicode(e.code)
            self.ErrMsg = unicode(e.msg)
            if self.LanzarExcepciones:
                raise COMException(scode = vbObjectError + int(e.code),
                                   desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            if self.LanzarExcepciones:
                raiseSoapError(e)
        except COMException:
            if self.LanzarExcepciones:
                raise
        except Exception, e:
            if self.LanzarExcepciones:
                raisePythonException(e)
            else:
                ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
                self.Traceback = ''.join(ex)
                try:
                    self.Excepcion = u"%s" % (e)
                except:
                    pass
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
        
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = wsfex.dummy(self.client)
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    def GetCMP(self, tipo_cbte, punto_vta, cbte_nro):
        "Recuperar los datos completos de un comprobante ya autorizado"
        try:
            # limpio errores
            self.Exception = self.Traceback = ""
            self.ErrCode = self.ErrMsg = ""
            # llamo al web service
            cbt, events = wsfex.get_cmp(self.client, 
                                    self.Token, self.Sign, self.Cuit, 
                                    tipo_cbte, punto_vta, cbte_nro)
            
            self.FechaCbte = cbt['fch_cbte']
            self.ImpTotal = cbt['imp_total']

            # Obs, cae y fecha cae
            self.Obs = cbt['obs'].strip(" ")
            self.CAE = cbt['cae']
            vto = str(cbt['fch_venc_cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])

            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]
            return self.CAE

        except wsfex.FEXError, e:
            self.ErrCode = unicode(e.code)
            self.ErrMsg = unicode(e.msg)
            if self.LanzarExcepciones:
                raise COMException(scode = vbObjectError + int(e.code),
                                   desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            if self.LanzarExcepciones:
                raiseSoapError(e)
        except Exception, e:
            if self.LanzarExcepciones:
                raisePythonException(e)
            else:
                ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
                self.Traceback = ''.join(ex)
                try:
                    self.Excepcion = u"%s" % (e)
                except:
                    pass
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
    
    def Factura(self):
        return self.factura

    def GetLastCMP(self, tipo_cbte, punto_vta):
        "Recuperar último número de comprobante emitido"
        try:
            # limpio errores
            self.Exception = self.Traceback = ""
            self.ErrCode = self.ErrMsg = ""
            # llamo al web service
            cbte_nro, cbte_fecha, events = wsfex.get_last_cmp(self.client, 
                                    self.Token, self.Sign, self.Cuit, 
                                    tipo_cbte, punto_vta)
            return cbte_nro
        except wsfex.FEXError, e:
            self.ErrCode = unicode(e.code)
            self.ErrMsg = unicode(e.msg)
            if self.LanzarExcepciones:
                raise COMException(scode = vbObjectError + int(e.code),
                                   desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            if self.LanzarExcepciones:
                raiseSoapError(e)
        except Exception, e:
            if self.LanzarExcepciones:
                raisePythonException(e)
            else:
                ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
                self.Traceback = ''.join(ex)
                try:
                    self.Excepcion = u"%s" % (e)
                except:
                    pass
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
            
    def GetLastID(self):
        "Recuperar último número de transacción (ID)"
        try:
            # limpio errores
            self.Exception = self.Traceback = ""
            self.ErrCode = self.ErrMsg = ""
            # llamo al web service
            id, events = wsfex.get_last_id(self.client, 
                                    self.Token, self.Sign, self.Cuit)
            return id
        except wsfex.FEXError, e:
            self.ErrCode = unicode(e.code)
            self.ErrMsg = unicode(e.msg)
            if self.LanzarExcepciones:
                raise COMException(scode = vbObjectError + int(e.code),
                                   desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            if self.LanzarExcepciones:
                raiseSoapError(e)
        except Exception, e:
            if self.LanzarExcepciones:
                raisePythonException(e)
            else:
                ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
                self.Traceback = ''.join(ex)
                try:
                    self.Excepcion = u"%s" % (e)
                except:
                    pass
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    def GetParamMon(self):
        "Recuperar lista de valores referenciales de codigos de Moneda"
        params = wsfex.get_param_mon(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]

    def GetParamTipoCbte(self):
        "Recuperar lista de valores referenciales de códigos de Tipos de comprobante"
        params = wsfex.get_param_tipo_cbte(self.client, self.Token, self.Sign, self.Cuit)
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]
    
    def GetParamTipoExpo(self):
        "Recuperar lista de valores referenciales de códigos de Tipo de exportación"
        params = wsfex.get_param_tipo_expo(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]
    
    def GetParamIdiomas(self):
        "Recuperar lista de valores referenciales de códigos de Idiomas"
        params = wsfex.get_param_idiomas(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]
    
    def GetParamUMed(self):
        "Recuperar lista de valores referenciales de Unidades de Medidas"
        params = wsfex.get_param_umed(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]
    
    def GetParamIncoterms(self):
        "Recuperar lista de valores referenciales de Incoterms"
        params = wsfex.get_param_incoterms(self.client, self.Token, self.Sign, self.Cuit)
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in params]
    
    def GetParamDstPais(self):
        "Recuperar lista de valores referenciales de códigos de Países"
        params = wsfex.get_param_dst_pais(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%s: %s' % (p['codigo'],p['ds']) for p in params]

    def GetParamDstCUIT(self):
        "Recuperar lista de valores referenciales de CUIT de Países"
        params = wsfex.get_param_dst_cuit(self.client, self.Token, self.Sign, self.Cuit)    
        return ['%s: %s' % (p['cuit'],p['ds']) for p in params]

    def GetParamCtz(self, moneda_id='DOL'):
        "Recuperar cotización de moneda"
        try:
            param = wsfex.get_param_ctz(self.client, self.Token, self.Sign, self.Cuit, moneda_id)
            return "%(fecha)s: %(ctz)s" % param
        except wsfex.FEXError, e:
            self.ErrCode = unicode(e.code)
            self.ErrMsg = unicode(e.msg)
            raise COMException(scode = vbObjectError + int(e.code),
                               desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response


class WSCTG:
    "Interfaz para el WebService de Código de Trazabilidad de Granos"    
    _public_methods_ = ['Conectar','Dummy','SolicitarCTG','ConfirmarCTG']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version', 'NumeroCTG',
        'CodigoTransaccion', 'Observaciones']
    _reg_progid_ = "WSCTG"
    _reg_clsid_ = "{8F1CE1EA-6D7A-45E7-A5BB-B17E2EB1F965}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.CodError = self.DescError = ''
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.NumeroCTG = ''
        self.CodigoTransaccion = self.Observaciones = ''
        
    
    def Conectar(self, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = wsctg.WSCTGURL
        proxy_dict = parse_proxy(proxy)
        try:
            self.client = SoapClient(url,
                action = wsctg.SOAP_ACTION, 
                namespace = wsctg.SOAP_NS,
                trace = False, ns = 'ctg', soap_ns = 'soapenv',
                exceptions = True, proxy = proxy_dict)
            return True
        except Exception, e:
            ##raise
            raisePythonException(e)

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        try:
            results = wsctg.dummy(self.client)
            self.AppServerStatus = str(results['appserver'])
            self.DbServerStatus = str(results['dbserver'])
            self.AuthServerStatus = str(results['authserver'])
        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    def SolicitarCTG(self, numero_carta_de_porte, codigo_especie,
        cuit_remitente_comercial, cuit_destino, cuit_destinatario, codigo_localidad_origen,
        codigo_localidad_destino, codigo_cosecha, peso_neto_carga, cant_horas, 
        patente_vehiculo, cuit_transportista):
        "Obtener Número de CTG"
        try:
            ret = wsctg.solicitar_ctg(self.client, self.Token, self.Sign, self.Cuit, 
                    numeroCartaDePorte=numero_carta_de_porte, codigoEspecie=codigo_especie,
                    cuitRemitenteComercial=cuit_remitente_comercial, 
                    cuitDestino=cuit_destino, 
                    cuitDestinatario=cuit_destinatario, 
                    codigoLocalidadOrigen=codigo_localidad_origen,
                    codigoLocalidadDestino=codigo_localidad_destino, 
                    codigoCosecha=codigo_cosecha, 
                    pesoNetoCarga=peso_neto_carga, cantHoras=cant_horas,
                    patenteVehiculo=patente_vehiculo, cuitTransportista=cuit_transportista)
            self.NumeroCTG = ret
            return self.NumeroCTG
        
        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    def ConfirmarCTG(self, numero_carta_de_porte, numero_CTG, cuit_transportista, peso_neto_carga):
        "Confirma número de CTG"
        try:
            ret = wsctg.confirmar_ctg(self.client, self.Token, self.Sign, self.Cuit, 
                        numeroCartaDePorte=numero_carta_de_porte, 
                        numeroCTG=numero_CTG,
                        cuitTransportista=cuit_transportista, 
                        pesoNetoCarga=peso_neto_carga)
            self.CodigoTransaccion, self.Observaciones = ret
            return self.CodigoTransaccion
        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
            
            
class wDigDepFiel:
    "Interfaz para el WebService de Depositario Fiel"
    _public_methods_ = ['Conectar', 'Dummy', 'AvisoDigit', 'AvisoRecepAcept', 'IniciarAviso', 'AgregarFamilia']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'CodError', 'DescError']
    _reg_progid_ = "wDigDepFiel"
    _reg_clsid_ = "{20516CB7-2B85-4562-8821-8F9D699CCAB6}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.CodError = self.DescError = ''
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    
    def Conectar(self, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = wdigdepfiel.WSDDFURL
        proxy_dict = parse_proxy(proxy)
        try:
            self.client = SoapClient(url,
                action = wdigdepfiel.SOAP_ACTION, 
                namespace = wdigdepfiel.SOAP_NS,
                trace = False, ns = 'ar', soap_ns='soap',
                exceptions = True, proxy = proxy_dict)
            return True
        except Exception, e:
            ##raise
            raisePythonException(e)

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = wdigdepfiel.dummy(self.client)
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    def AvisoRecepAcept(self, tipo_agente, rol, 
                        nro_legajo, cuit_declarante, cuit_psad, cuit_ie,
                        codigo, fecha_hora_acept, ticket):
        "Aviso de Recepción y Aceptación"
        try:
            ret = wdigdepfiel.aviso_recep_acept(
                    self.client, self.Token, self.Sign, self.Cuit, tipo_agente, rol,
                    nro_legajo, cuit_declarante, cuit_psad, cuit_ie,
                    codigo, fecha_hora_acept, ticket)
            
            self.CodError, self.DescError  = ret
            return self.CodError

        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response

    def IniciarAviso(self):
        "Inicializar familias para Aviso de Digitalización"
        self.familias = []

    def AgregarFamilia(self, codigo, cantidad):
        "Agregar famila para Aviso de Digitalización"
        self.familias.append({'Familia': {'codigo': codigo, 'cantidad': cantidad}})

    def AvisoDigit(self, tipo_agente, rol,
                         nro_legajo, cuit_declarante, cuit_psad, cuit_ie, cuit_ata,
                         codigo, url, ticket, hashing, cantidad_total):
        "Aviso de Digitalización"
        try:
            familias = self.familias
            ret = wdigdepfiel.aviso_digit(
                    self.client, self.Token, self.Sign, self.Cuit, tipo_agente, rol,
                    nro_legajo, cuit_declarante, cuit_psad, cuit_ie, cuit_ata,
                    codigo, url, familias, ticket, hashing, cantidad_total)
            
            self.CodError, self.DescError  = ret
            return self.CodError

        except SoapFault,e:
            raiseSoapError(e)
        except COMException:
            raise
        except Exception, e:
            raisePythonException(e)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response


if __name__ == '__main__':
    if len(sys.argv)==1:
        sys.argv.append("/register")

    import win32com.server.register
    win32com.server.register.UseCommandLine(WSFE)
    win32com.server.register.UseCommandLine(WSBFE)
    win32com.server.register.UseCommandLine(WSFEX)
    win32com.server.register.UseCommandLine(WSCTG)
    win32com.server.register.UseCommandLine(wDigDepFiel)
