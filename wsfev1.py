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

"""Módulo para obtener código de autorización electrónico del web service 
WSFEv1 de AFIP (Factura Electrónica Nacional - Version 1 - RG2904 opción B)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.12c"

import datetime
import decimal
import os
import socket
import sys
import traceback
from cStringIO import StringIO
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper

HOMO = True

#WSDL="https://www.sistemasagiles.com.ar/simulador/wsfev1/call/soap?WSDL=None"
WSDL="https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"


def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Resultado = self.CAE = self.CAEA = self.Vencimiento = ""
            self.Evento = self.Obs = ""
            self.FechaCbte = self.CbteNro = self.PuntoVenta = self.ImpTotal = None
            self.ImpIVA = self.ImpOpEx = self.ImpNeto = self.ImptoLiq = self.ImpTrib = None
            self.CbtDesde = self.CbtHasta = self.FechaCbte = None
            self.Reproceso = self.EmisionTipo = ''
            self.Errores = []
            self.Observaciones = []
            self.Eventos = []
            self.Traceback = self.Excepcion = ""
            self.ErrCode = ""
            self.ErrMsg = ""
            self.CAEA = ""

            # llamo a la función (con reintentos)
            retry = 5
            while retry:
                try:
                    retry -= 1
                    return func(self, *args, **kwargs)
                except socket.error, e:
                    if e[0] != 10054:
                        # solo reintentar si el error es de conexión
                        # (10054, 'Connection reset by peer')
                        raise

        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            if self.LanzarExcepciones:
                raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = u"%s" % (e)
            if self.LanzarExcepciones:
                raise
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class WSFEv1:
    "Interfaz para el WebService de Factura Electrónica Version 1"
    _public_methods_ = ['CrearFactura', 'AgregarIva', 'CAESolicitar', 
                        'AgregarTributo', 'AgregarCmpAsoc',
                        'CompUltimoAutorizado', 'CompConsultar',
                        'CAEASolicitar', 'CAEAConsultar', 'CAEARegInformativo',
                        'ParamGetTiposCbte',
                        'ParamGetTiposConcepto',
                        'ParamGetTiposDoc',
                        'ParamGetTiposIva',
                        'ParamGetTiposMonedas',
                        'ParamGetTiposOpcional',
                        'ParamGetTiposTributos',
                        'ParamGetCotizacion', 
                        'ParamGetPtosVenta',
                        'AnalizarXml', 'ObtenerTagXml',
                        'Dummy', 'Conectar', 'DebugLog', 'Eval']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version', 'Excepcion', 'LanzarExcepciones',
        'Resultado', 'Obs', 'Observaciones', 'Traceback', 'InstallDir',
        'CAE','Vencimiento', 'Eventos', 'Errores', 'ErrCode', 'ErrMsg',
        'Reprocesar', 'Reproceso', 'EmisionTipo', 'CAEA',
        'CbteNro', 'CbtDesde', 'CbtHasta', 'FechaCbte', 
        'ImpTotal', 'ImpNeto', 'ImptoLiq', 'ImpOpEx'
        'ImptIVA', 'ImpOpEx', 'ImpTrib',]
        
    _reg_progid_ = "WSFEv1"
    _reg_clsid_ = "{CA0E604D-E3D7-493A-8880-F6CDD604185E}"

    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    
    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.CAEA = self.Vencimiento = ''
        self.client = None
        self.factura = None
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.ImpIVA = self.ImpOpEx = self.ImpNeto = self.ImptoLiq = self.ImpTrib = None
        self.Traceback = ""
        self.CAEA = ""
        self.Periodo = self.Orden = ""
        self.FchVigDesde = self.FchVigHasta = ""
        self.FchTopeInf = self.FchProceso = ""
        self.Log = None
        self.InstallDir = INSTALL_DIR
        self.Reprocesar = True # recuperar automaticamente CAE emitidos
        self.LanzarExcepciones = True
        self.Traceback = self.Excepcion = ""
        self.XmlRequest = self.XmlResponse = ""
        self.xml = None
        
    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'Errors' in ret:
            errores = ret['Errors']
            self.Errores = []
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['Err']['Code'],
                    error['Err']['Msg'],
                    ))
            self.ErrCode = ' '.join([str(error['Err']['Code']) for error in errores])
            self.ErrMsg = '\n'.join(self.Errores)
        if 'Events' in ret:
            events = ret['Events']
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]

    def __log(self, msg):
        if not isinstance(msg, unicode):
            msg = unicode(msg, 'utf8', 'ignore')
        if not self.Log:
            self.Log = StringIO()
        self.Log.write(msg)
        self.Log.write('\n\r')
    
    def Eval(self, code):
        "Devolver el resultado de ejecutar una expresión (para depuración)"
        if not HOMO:
            return str(eval(code))
    
    def DebugLog(self):
        "Devolver y limpiar la bitácora de depuración"
        if self.Log:
            msg = self.Log.getvalue()
            # limpiar log
            self.Log.close()
            self.Log = None
        else:
            msg = u''
        return msg    

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None):
        # cliente soap del web service
        if wrapper:
            Http = set_http_wrapper(wrapper)
            self.Version = WSFEv1.Version + " " + Http._wrapper_version
        if isinstance(proxy, dict):
            proxy_dict = proxy
        else:
            proxy_dict = parse_proxy(proxy)
        if HOMO or not wsdl:
            wsdl = WSDL
        if not wsdl.endswith("?WSDL") and wsdl.startswith("http"):
            wsdl += "?WSDL"
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        self.__log("Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict))
        self.client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            cacert = cacert,
            trace = "--trace" in sys.argv)
        return True

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.FEDummy()['FEDummyResult']
        self.AppServerStatus = result['AppServer']
        self.DbServerStatus = result['DbServer']
        self.AuthServerStatus = result['AuthServer']
        return True

    def CrearFactura(self, concepto=1, tipo_doc=80, nro_doc="", tipo_cbte=1, punto_vta=0,
            cbt_desde=0, cbt_hasta=0, imp_total=0.00, imp_tot_conc=0.00, imp_neto=0.00,
            imp_iva=0.00, imp_trib=0.00, imp_op_ex=0.00, fecha_cbte="", fecha_venc_pago="", 
            fecha_serv_desde=None, fecha_serv_hasta=None, #--
            moneda_id="PES", moneda_ctz="1.0000", caea=None, **kwargs
            ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación 
        fact = {'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto, 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'cbtes_asoc': [],
                'tributos': [],
                'iva': [],
            }
        if fecha_serv_desde: fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fecha_serv_hasta'] = fecha_serv_hasta
        if caea: fact['caea'] = caea

        self.factura = fact
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwarg):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'tipo': tipo, 'pto_vta': pto_vta, 'nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, tributo_id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg):
        "Agrego un tributo a una factura (interna)"
        tributo = { 'id': tributo_id, 'desc': desc, 'base_imp': base_imp, 
                    'alic': alic, 'importe': importe}
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, iva_id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = { 'id': iva_id, 'base_imp': base_imp, 'importe': importe }
        self.factura['iva'].append(iva)
        return True

    @inicializar_y_capturar_excepciones
    def CAESolicitar(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEReq={
                'FeCabReq': {'CantReg': 1, 
                    'PtoVta': f['punto_vta'], 
                    'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],                
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                            }}
                        for iva in f['iva']],
                    }
                }]
            })
        
        result = ret['FECAESolicitarResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEDetResponse']
            
            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and ('Errors' in result or 'Observaciones' in fedetresp):
                for error in result.get('Errors',[])+fedetresp.get('Observaciones',[]):
                    err_code = str(error.get('Err', error.get('Obs'))['Code'])
                    if fedetresp['Resultado']=='R' and err_code=='10016':
                        # guardo los mensajes xml originales
                        xml_request = self.client.xml_request
                        xml_response = self.client.xml_response
                        cae = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if cae and self.EmisionTipo=='CAE':
                            self.Reproceso = 'S'
                            return cae
                        self.Reproceso = 'N'
                        # reestablesco los mensajes xml originales
                        self.client.xml_request = xml_request
                        self.client.xml_response = xml_response
                        
            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAE = fedetresp['CAE'] and str(fedetresp['CAE']) or ""
            self.EmisionTipo = 'CAE'
            self.Vencimiento = fedetresp['CAEFchVto']
            self.FechaCbte = fedetresp.get('CbteFch', "") #.strftime("%Y/%m/%d")
            self.CbteNro = fedetresp.get('CbteHasta', 0) # 1L
            self.PuntoVenta = fecabresp.get('PtoVta', 0) # 4000
            self.CbtDesde =fedetresp.get('CbteDesde', 0)
            self.CbtHasta = fedetresp.get('CbteHasta', 0)
        self.__analizar_errores(result)
        return self.CAE

    @inicializar_y_capturar_excepciones
    def CompTotXRequest(self):
        ret = self.client.FECompTotXRequest (
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        
        result = ret['FECompTotXRequestResult']
        return result['RegXReq']

    @inicializar_y_capturar_excepciones
    def CompUltimoAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.FECompUltimoAutorizado(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            PtoVta=punto_vta,
            CbteTipo=tipo_cbte,
            )
        
        result = ret['FECompUltimoAutorizadoResult']
        self.CbteNro = result['CbteNro']        
        self.__analizar_errores(result)
        return self.CbteNro is not None and str(self.CbteNro) or ''

    @inicializar_y_capturar_excepciones
    def CompConsultar(self, tipo_cbte, punto_vta, cbte_nro, reproceso=False):
        difs = [] # si hay reproceso, verifico las diferencias con AFIP

        ret = self.client.FECompConsultar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCompConsReq={
                'CbteTipo': tipo_cbte,
                'CbteNro': cbte_nro,
                'PtoVta': punto_vta,
            })
        
        result = ret['FECompConsultarResult']
        if 'ResultGet' in result:
            resultget = result['ResultGet']
            
            if reproceso:
                # verifico los campos registrados coincidan con los enviados:
                f = self.factura
                verificaciones = {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': float(f['imp_total']),
                    'ImpTotConc': float(f['imp_tot_conc']),
                    'ImpNeto': float(f['imp_neto']),
                    'ImpOpEx': float(f['imp_op_ex']),
                    'ImpTrib': float(f['imp_trib']),
                    'ImpIVA': float(f['imp_iva']),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': float(f['moneda_ctz']),
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': float(tributo['base_imp']),
                            'Alic': float(tributo['alic']),
                            'Importe': float(tributo['importe']),
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['id'],
                            'BaseImp': float(iva['base_imp']),
                            'Importe': float(iva['importe']),
                            }}
                        for iva in f['iva']],
                    }
                def verifica(ver_list,res_dict):
                    for k, v in ver_list.items():
                        if isinstance(v, list):
                            if v and not k in res_dict and v:
                                difs.append("falta tag %s: %s %s" % (k, repr(v), repr(res_dict.get(k))))
                            elif len(res_dict.get(k, []))!=len(v or []):
                                difs.append("tag %s len !=: %s %s" % (k, repr(v), repr(res_dict.get(k))))
                            else:
                                for i, vl in enumerate(v):
                                    verifica(vl, res_dict[k][i])
                        elif isinstance(v, dict):
                            verifica(v, res_dict.get(k, {}))
                        elif res_dict.get(k) is None or v is None:
                            if v=="":
                                v = None
                            r = res_dict.get(k)
                            if r=="":
                                r = None
                            if not (r is None and v is None):
                                difs.append("%s: nil %s!=%s" % (k, repr(v), repr(r)))
                        elif unicode(res_dict.get(k)) != unicode(v):
                            difs.append("%s: %s!=%s" % (k, repr(v), repr(res_dict.get(k))))
                        else:
                            pass
                            #print "%s: %s==%s" % (k, repr(v), repr(res_dict[k]))
                verifica(verificaciones, resultget)
                if difs:
                    print "Diferencias:", difs
                    self.__log("Diferencias: %s" % difs)
            self.FechaCbte = resultget['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = resultget['CbteHasta'] # 1L
            self.PuntoVenta = resultget['PtoVta'] # 4000
            self.Vencimiento = resultget['FchVto'] #.strftime("%Y/%m/%d")
            self.ImpTotal = str(resultget['ImpTotal'])
            cod_aut = resultget['CodAutorizacion'] and str(resultget['CodAutorizacion']) or ''# 60423794871430L
            self.Resultado = resultget['Resultado']
            self.CbtDesde =resultget['CbteDesde']
            self.CbtHasta = resultget['CbteHasta']
            self.ImpTotal = resultget['ImpTotal']
            self.ImpNeto = resultget['ImpNeto']
            self.ImptoLiq = self.ImpIVA = resultget['ImpIVA']
            self.ImpOpEx = resultget['ImpOpEx']
            self.ImpTrib = resultget['ImpTrib']
            self.EmisionTipo = resultget['EmisionTipo']
            if self.EmisionTipo=='CAE':
                self.CAE = cod_aut
            elif self.EmisionTipo=='CAEA':
                self.CAEA = cod_aut

        self.__analizar_errores(result)
        if not difs:
            return self.CAE or self.CAEA
        else:
            return ''


    @inicializar_y_capturar_excepciones
    def CAESolicitarLote(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEReq={
                'FeCabReq': {'CantReg': 250, 
                    'PtoVta': f['punto_vta'], 
                    'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde']+k,
                    'CbteHasta': f['cbt_hasta']+k,
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],                
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                            }}
                        for iva in f['iva']],
                    }
                } for k in range (250)]
            })
        
        result = ret['FECAESolicitarResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEDetResponse']
            
            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and 'Errors' in result:
                for error in result['Errors']:
                    err_code = str(error['Err']['Code'])
                    if fedetresp['Resultado']=='R' and err_code=='10016':
                        cae = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if cae and self.EmisionTipo=='CAEA':
                            self.Reproceso = 'S'
                            return cae
                        self.Reproceso = 'N'
            
            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAE = fedetresp['CAE'] and str(fedetresp['CAE']) or ""
            self.EmisionTipo = 'CAE'
            self.Vencimiento = fedetresp['CAEFchVto']
            self.FechaCbte = fedetresp['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = fedetresp['CbteHasta'] # 1L
            self.PuntoVenta = fecabresp['PtoVta'] # 4000
            self.CbtDesde =fedetresp['CbteDesde']
            self.CbtHasta = fedetresp['CbteHasta']
            self.__analizar_errores(result)
        return self.CAE


    @inicializar_y_capturar_excepciones
    def CAEASolicitar(self, periodo, orden):
        ret = self.client.FECAEASolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Periodo=periodo, 
            Orden=orden,
            )
        
        result = ret['FECAEASolicitarResult']
        self.__analizar_errores(result)

        if 'ResultGet' in result:
            result = result['ResultGet']
            if 'CAEA' in result:
                self.CAEA = result['CAEA']
                self.Periodo = result['Periodo']
                self.Orden = result['Orden']
                self.FchVigDesde = result['FchVigDesde']
                self.FchVigHasta = result['FchVigHasta']
                self.FchTopeInf = result['FchTopeInf']
                self.FchProceso = result['FchProceso']

        return self.CAEA and str(self.CAEA) or ''


    @inicializar_y_capturar_excepciones
    def CAEAConsultar(self, periodo, orden):
        "Método de consulta de CAEA"
        ret = self.client.FECAEAConsultar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Periodo=periodo, 
            Orden=orden,
            )
        
        result = ret['FECAEAConsultarResult']
        self.__analizar_errores(result)

        if 'ResultGet' in result:
            result = result['ResultGet']
            if 'CAEA' in result:
                self.CAEA = result['CAEA']
                self.Periodo = result['Periodo']
                self.Orden = result['Orden']
                self.FchVigDesde = result['FchVigDesde']
                self.FchVigHasta = result['FchVigHasta']
                self.FchTopeInf = result['FchTopeInf']
                self.FchProceso = result['FchProceso']

        return self.CAEA and str(self.CAEA) or ''
    
    @inicializar_y_capturar_excepciones
    def CAEARegInformativo(self):
        "Método para informar comprobantes emitidos con CAEA"
        f = self.factura
        ret = self.client.FECAEARegInformativo(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEARegInfReq={
                'FeCabReq': {'CantReg': 1, 
                    'PtoVta': f['punto_vta'], 
                    'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEADetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],                
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                            }}
                        for iva in f['iva']],
                    'CAEA': f['caea'],
                    }
                }]
            })
        
        result = ret['FECAEARegInformativoResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEADetResponse']
            
            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and 'Errors' in result:
                for error in result['Errors']:
                    err_code = str(error['Err']['Code'])
                    if fedetresp['Resultado']=='R' and err_code=='703':
                        caea = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if caea and self.EmisionTipo=='CAE':
                            self.Reproceso = 'S'
                            return caea
                        self.Reproceso = 'N'

            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAEA = fedetresp['CAEA'] and str(fedetresp['CAEA']) or ""
            self.EmisionTipo = 'CAEA'
            self.FechaCbte = fedetresp['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = fedetresp['CbteHasta'] # 1L
            self.PuntoVenta = fecabresp['PtoVta'] # 4000
            self.CbtDesde =fedetresp['CbteDesde']
            self.CbtHasta = fedetresp['CbteHasta']
            self.__analizar_errores(result)
        return self.CAEA

    @inicializar_y_capturar_excepciones
    def ParamGetTiposCbte(self):
        "Recuperador de valores referenciales de códigos de Tipos de Comprobantes"
        ret = self.client.FEParamGetTiposCbte(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposCbteResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['CbteTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposConcepto(self):
        "Recuperador de valores referenciales de códigos de Tipos de Conceptos"
        ret = self.client.FEParamGetTiposConcepto(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposConceptoResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['ConceptoTipo']
                 for p in res['ResultGet']]
                

    @inicializar_y_capturar_excepciones
    def ParamGetTiposDoc(self):
        "Recuperador de valores referenciales de códigos de Tipos de Documentos"
        ret = self.client.FEParamGetTiposDoc(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposDocResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['DocTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposIva(self):
        "Recuperador de valores referenciales de códigos de Tipos de Alícuotas"
        ret = self.client.FEParamGetTiposIva(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposIvaResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['IvaTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposMonedas(self):
        "Recuperador de valores referenciales de códigos de Monedas"
        ret = self.client.FEParamGetTiposMonedas(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposMonedasResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['Moneda']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposOpcional(self):
        "Recuperador de valores referenciales de códigos de Tipos de datos opcionales"
        ret = self.client.FEParamGetTiposOpcional(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposOpcionalResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['OpcionalTipo']
                 for p in res.get('ResultGet', [])]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposTributos(self):
        "Recuperador de valores referenciales de códigos de Tipos de Tributos"
        "Este método permite consultar los tipos de tributos habilitados en este WS"
        ret = self.client.FEParamGetTiposTributos(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposTributosResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['TributoTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetCotizacion(self, moneda_id):
        "Recuperador de cotización de moneda"
        ret = self.client.FEParamGetCotizacion(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            MonId=moneda_id,
            )
        self.__analizar_errores(ret)
        res = ret['FEParamGetCotizacionResult']['ResultGet']
        return str(res.get('MonCotiz',""))
        
    @inicializar_y_capturar_excepciones
    def ParamGetPtosVenta(self):
        "Recuperador de valores referenciales Puntos de Venta registrados"
        ret = self.client.FEParamGetPtosVenta(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret.get('FEParamGetPtosVentaResult', {})
        return [u"%(Nro)s: EmisionTipo:%(EmisionTipo)s Bloqueado:%(Bloqueado)s FchBaja:%(FchBaja)s" % p['PtoVenta']
                 for p in res.get('ResultGet', [])]

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto la respuesta)"
        try:
            if not xml or xml=='XmlResponse':
                xml = self.XmlResponse 
            elif xml=='XmlRequest':
                xml = self.XmlRequest 
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


def p_assert_eq(a,b):
    print a, a==b and '==' or '!=', b

def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = '--debug' in sys.argv

    if DEBUG:
        from pysimplesoap.client import __version__ as soapver
        print "pysimplesoap.__version__ = ", soapver

    wsfev1 = WSFEv1()

    cache = None
    wsdl = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"
    proxy = ""
    wrapper = "pycurl"
    cacert = "geotrust.crt"

    wsfev1.Conectar(cache, wsdl, proxy, wrapper, cacert)

    if DEBUG:
        print "LOG: ", wsfev1.DebugLog()
        
    if "--dummy" in sys.argv:
        print wsfev1.client.help("FEDummy")
        wsfev1.Dummy()
        print "AppServerStatus", wsfev1.AppServerStatus
        print "DbServerStatus", wsfev1.DbServerStatus
        print "AuthServerStatus", wsfev1.AuthServerStatus
        sys.exit(0)


    # obteniendo el TA
    TA = "TA-wsfe.xml"
    if 'wsaa' in sys.argv or not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsfe")
        cms = wsaa.sign_tra(tra,"reingart.crt","reingart.key")
        ta_string = wsaa.call_wsaa(cms)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    # fin TA

    if '--cuit' in sys.argv:
        cuit = sys.argv[sys.argv.index("--cuit")+1]
    else:
        cuit = "20267565393"

    wsfev1.Cuit = cuit
    wsfev1.Token = str(ta.credentials.token)
    wsfev1.Sign = str(ta.credentials.sign)
    
    if "--prueba" in sys.argv:
        print wsfev1.client.help("FECAESolicitar").encode("latin1")

        tipo_cbte = 2
        punto_vta = 4001
        cbte_nro = long(wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta) or 0)
        fecha = datetime.datetime.now().strftime("%Y%m%d")
        concepto = 2
        tipo_doc = 80; nro_doc = "30500010912" # CUIT BNA
        cbt_desde = cbte_nro + 1; cbt_hasta = cbte_nro + 1
        imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
        imp_iva = "21.00"; imp_trib = "1.00"; imp_op_ex = "0.00"
        fecha_cbte = fecha; fecha_venc_pago = fecha
        # Fechas del período del servicio facturado (solo si concepto = 1?)
        fecha_serv_desde = fecha; fecha_serv_hasta = fecha
        moneda_id = 'PES'; moneda_ctz = '1.000'

        wsfev1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde, fecha_serv_hasta, #--
            moneda_id, moneda_ctz)
        
        if tipo_cbte not in (1, 2):
            tipo = 19
            pto_vta = 2
            nro = 1234
            wsfev1.AgregarCmpAsoc(tipo, pto_vta, nro)
        
        id = 99
        desc = 'Impuesto Municipal Matanza'
        base_imp = 100
        alic = 1
        importe = 1
        wsfev1.AgregarTributo(id, desc, base_imp, alic, importe)

        id = 5 # 21%
        base_im = 100
        importe = 21
        wsfev1.AgregarIva(id, base_imp, importe)
        
        import time
        t0 = time.time()
        wsfev1.CAESolicitar()
        t1 = time.time()
        
        print "Resultado", wsfev1.Resultado
        print "Reproceso", wsfev1.Reproceso
        print "CAE", wsfev1.CAE
        if DEBUG:
            print "t0", t0
            print "t1", t1
            print "lapso", t1-t0
            open("xmlrequest.xml","wb").write(wsfev1.XmlRequest)
            open("xmlresponse.xml","wb").write(wsfev1.XmlResponse)

        wsfev1.AnalizarXml("XmlResponse")
        p_assert_eq(wsfev1.ObtenerTagXml('CAE'), str(wsfev1.CAE))
        p_assert_eq(wsfev1.ObtenerTagXml('Concepto'), '2')
        p_assert_eq(wsfev1.ObtenerTagXml('Obs',0,'Code'), "10063")
        print wsfev1.ObtenerTagXml('Obs',0,'Msg')
    
    if "--get" in sys.argv:
        tipo_cbte = 2
        punto_vta = 4001
        cbte_nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)

        wsfev1.CompConsultar(tipo_cbte, punto_vta, cbte_nro)

        print "FechaCbte = ", wsfev1.FechaCbte
        print "CbteNro = ", wsfev1.CbteNro
        print "PuntoVenta = ", wsfev1.PuntoVenta
        print "ImpTotal =", wsfev1.ImpTotal
        print "CAE = ", wsfev1.CAE
        print "Vencimiento = ", wsfev1.Vencimiento
        print "EmisionTipo = ", wsfev1.EmisionTipo
        
        wsfev1.AnalizarXml("XmlResponse")
        p_assert_eq(wsfev1.ObtenerTagXml('CodAutorizacion'), str(wsfev1.CAE))
        p_assert_eq(wsfev1.ObtenerTagXml('CbteFch'), wsfev1.FechaCbte)
        p_assert_eq(wsfev1.ObtenerTagXml('MonId'), "PES")
        p_assert_eq(wsfev1.ObtenerTagXml('MonCotiz'), "1")
        p_assert_eq(wsfev1.ObtenerTagXml('DocTipo'), "80")
        p_assert_eq(wsfev1.ObtenerTagXml('DocNro'), "30500010912")
            
    if "--parametros" in sys.argv:
        import codecs, locale, traceback
        if sys.stdout.encoding is None:
            sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
            sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");

        print "=== Tipos de Comprobante ==="
        print u'\n'.join(wsfev1.ParamGetTiposCbte())
        print "=== Tipos de Concepto ==="
        print u'\n'.join(wsfev1.ParamGetTiposConcepto())
        print "=== Tipos de Documento ==="
        print u'\n'.join(wsfev1.ParamGetTiposDoc())
        print "=== Alicuotas de IVA ==="
        print u'\n'.join(wsfev1.ParamGetTiposIva())
        print "=== Monedas ==="
        print u'\n'.join(wsfev1.ParamGetTiposMonedas())
        print "=== Tipos de datos opcionales ==="
        print u'\n'.join(wsfev1.ParamGetTiposOpcional())
        print "=== Tipos de Tributo ==="
        print u'\n'.join(wsfev1.ParamGetTiposTributos())
        print "=== Puntos de Venta ==="
        print u'\n'.join(wsfev1.ParamGetPtosVenta())

    if "--cotizacion" in sys.argv:
        print wsfev1.ParamGetCotizacion('DOL')

    if "--comptox" in sys.argv:
        print wsfev1.CompTotXRequest()

    if "--solicitar-caea" in sys.argv:
        periodo = sys.argv[sys.argv.index("--solicitar-caea")+1]
        orden = sys.argv[sys.argv.index("--solicitar-caea")+2]

        if DEBUG: 
            print "Solicitando CAEA para periodo %s orden %s" % (periodo, orden)
        
        caea = wsfev1.CAEASolicitar(periodo, orden)
        print "CAEA:", caea

        if wsfev1.Errores:
            print "Errores:"
            for error in wsfev1.Errores:
                print error
            
        if DEBUG:
            print "periodo:", wsfev1.Periodo 
            print "orden:", wsfev1.Orden 
            print "fch_vig_desde:", wsfev1.FchVigDesde 
            print "fch_vig_hasta:", wsfev1.FchVigHasta 
            print "fch_tope_inf:", wsfev1.FchTopeInf 
            print "fch_proceso:", wsfev1.FchProceso

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
        win32com.server.register.UseCommandLine(WSFEv1)
    else:
        main()
