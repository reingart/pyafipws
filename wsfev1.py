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
__version__ = "1.03a"

import datetime
import decimal
import sys
import traceback
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy

HOMO = True

#WSDL="https://www.sistemasagiles.com.ar/simulador/wsfev1/call/soap?WSDL=None"
WSDL="https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"


def inicializar_y_capturar_execepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Resultado = self.CAE = self.Vencimiento = ""
            self.Evento = self.Obs = ""
            self.FechaCbte = self.CbteNro = self.PuntoVenta = self.ImpTotal = None
            self.ImpIVA = self.ImpOpEx = self.ImpNeto = self.ImptoLiq = self.ImpTrib = None
            self.CbtDesde = self.CbtHasta = self.FechaCbte = None
            self.Errores = []
            self.Observaciones = []
            self.Eventos = []
            self.Traceback = ""
            self.ErrCode = ""
            self.ErrMsg = ""
            self.CAEA = ""

            # llamo a la función
            return func(self, *args, **kwargs)
        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            raise
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class WSFEv1:
    "Interfase para el WebService de Factura Electrónica Version 1"
    _public_methods_ = ['CrearFactura', 'AgregarIva', 'CAESolicitar', 
                        'AgregarTributo', 'AgregarCmpAsoc',
                        'CompUltimoAutorizado', 'CompConsultar',
                        'ParamGetTiposCbte',
                        'ParamGetTiposConcepto',
                        'ParamGetTiposDoc',
                        'ParamGetTiposIva',
                        'ParamGetTiposMonedas',
                        'ParamGetTiposOpcional',
                        'ParamGetTiposTributos',
                        'ParamGetCotizacion',
                        'Dummy', 'Conectar', ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Obs', 'Observaciones', 'Traceback',
        'CAE','Vencimiento', 'Eventos', 'Errors', 'ErrCode', 'ErrMsg',
        'CbteNro', 'CbtDesde', 'CbtHasta', 'FechaCbte', 
        'ImpTotal', 'ImpNeto', 'ImptoLiq', 'ImpOpEx'
        'ImptIVA', 'ImpOpEx', 'ImpTrib',]
        
    _reg_progid_ = "WSFEv1"
    _reg_clsid_ = "{CA0E604D-E3D7-493A-8880-F6CDD604185E}"

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
        self.ImpIVA = self.ImpOpEx = self.ImpNeto = self.ImptoLiq = self.ImpTrib = None
        self.Traceback = ""
        self.CAEA = ""
        self.Periodo = self.Orden = ""
        self.FchVigDesde = self.FchVigHasta = ""
        self.FchTopeInf = self.FchProceso = ""
        
    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'Errors' in ret:
            errores = ret['Errors']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['Err']['Code'],
                    error['Err']['Msg'],
                    ))
            self.ErrMsg = '\n'.join(self.Errores)
        if 'Events' in ret:
            events = ret['Events']
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]


    @inicializar_y_capturar_execepciones
    def Conectar(self, cache="cache", wsdl=None, proxy=""):
        # cliente soap del web service
        proxy_dict = parse_proxy(proxy)
        if HOMO or not wsdl:
            wsdl = WSDL
        self.client = SoapClient( 
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            trace = "--trace" in sys.argv)
        return True

    @inicializar_y_capturar_execepciones
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
            moneda_id="PES", moneda_ctz="1.0000", **kwargs
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
        self.factura = fact
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwarg):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'tipo': tipo, 'pto_vta': pto_vta, 'nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg):
        "Agrego un tributo a una factura (interna)"
        tributo = { 'id': id, 'desc': desc, 'base_imp': base_imp, 
                    'alic': alic, 'importe': importe}
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = { 'id': id, 'base_imp': base_imp, 'importe': importe }
        self.factura['iva'].append(iva)
        return True

    @inicializar_y_capturar_execepciones
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
            self.Resultado = fecabresp['Resultado']
            ##print result['FeDetResp']
            fedetresp = result['FeDetResp'][0]['FECAEDetResponse']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAE = fedetresp['CAE'] and str(fedetresp['CAE']) or ""
            self.Vencimiento = fedetresp['CAEFchVto']
            self.FechaCbte = fedetresp['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = fedetresp['CbteHasta'] # 1L
            self.PuntoVenta = fecabresp['PtoVta'] # 4000
            self.CbtDesde =fedetresp['CbteDesde']
            self.CbtHasta = fedetresp['CbteHasta']
            self.__analizar_errores(result)
        return self.CAE

    @inicializar_y_capturar_execepciones
    def CompUltimoAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.FECompUltimoAutorizado(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            PtoVta=punto_vta,
            CbteTipo=tipo_cbte,
            )
        
        result = ret['FECompUltimoAutorizadoResult']
        self.CbteNro = result['CbteNro']        
        self.__analizar_errores(result)
        return self.CbteNro and str(self.CbteNro) or ''

    @inicializar_y_capturar_execepciones
    def CompConsultar(self, tipo_cbte, punto_vta, cbte_nro):
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
            self.FechaCbte = resultget['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = resultget['CbteHasta'] # 1L
            self.PuntoVenta = resultget['PtoVta'] # 4000
            self.Vencimiento = resultget['FchVto'] #.strftime("%Y/%m/%d")
            self.ImpTotal = str(resultget['ImpTotal'])
            self.CAE = resultget['CodAutorizacion'] and str(resultget['CodAutorizacion']) or ''# 60423794871430L
            self.Resultado = resultget['Resultado']
            self.CbtDesde =resultget['CbteDesde']
            self.CbtHasta = resultget['CbteHasta']
            self.ImpTotal = resultget['ImpTotal']
            self.ImpNeto = resultget['ImpNeto']
            self.ImptoLiq = self.ImpIVA = resultget['ImpIVA']
            self.ImpOpEx = resultget['ImpOpEx']
            self.ImpTrib = resultget['ImpTrib']

        self.__analizar_errores(result)
        return self.CAE


    @inicializar_y_capturar_execepciones
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
    

    @inicializar_y_capturar_execepciones
    def ParamGetTiposCbte(self):
        "Recuperador de valores referenciales de códigos de Tipos de Comprobantes"
        ret = self.client.FEParamGetTiposCbte(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposCbteResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['CbteTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_execepciones
    def ParamGetTiposConcepto(self):
        "Recuperador de valores referenciales de códigos de Tipos de Conceptos"
        ret = self.client.FEParamGetTiposConcepto(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposConceptoResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['ConceptoTipo']
                 for p in res['ResultGet']]
                

    @inicializar_y_capturar_execepciones
    def ParamGetTiposDoc(self):
        "Recuperador de valores referenciales de códigos de Tipos de Documentos"
        ret = self.client.FEParamGetTiposDoc(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposDocResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['DocTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_execepciones
    def ParamGetTiposIva(self):
        "Recuperador de valores referenciales de códigos de Tipos de Alícuotas"
        ret = self.client.FEParamGetTiposIva(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposIvaResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['IvaTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_execepciones
    def ParamGetTiposMonedas(self):
        "Recuperador de valores referenciales de códigos de Monedas"
        ret = self.client.FEParamGetTiposMonedas(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposMonedasResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['Moneda']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_execepciones
    def ParamGetTiposOpcional(self):
        "Recuperador de valores referenciales de códigos de Tipos de datos opcionales"
        ret = self.client.FEParamGetTiposOpcional(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposOpcionalResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['OpcionalTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_execepciones
    def ParamGetTiposTributos(self):
        "Recuperador de valores referenciales de códigos de Tipos de Tributos"
        "Este método permite consultar los tipos de tributos habilitados en este WS"
        ret = self.client.FEParamGetTiposTributos(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposTributosResult']
        return [u"%(Id)s: %(Desc)s (%(FchDesde)s-%(FchHasta)s)" % p['TributoTipo']
                 for p in res['ResultGet']]

    @inicializar_y_capturar_execepciones
    def ParamGetCotizacion(self, moneda_id):
        "Recuperador de cotización de moneda"
        ret = self.client.FEParamGetCotizacion(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            MonId=moneda_id,
            )
        self.__analizar_errores(ret)
        res = ret['FEParamGetCotizacionResult']['ResultGet']
        return str(res.get('MonCotiz',""))


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    wsfev1 = WSFEv1()

    wsfev1.Conectar()
    
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
        cms = wsaa.sign_tra(tra,"homo.crt","homo.key")
        ta_string = wsaa.call_wsaa(cms)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    # fin TA

    DEBUG = '--debug' in sys.argv

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
        cbte_nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)
        fecha = datetime.datetime.now().strftime("%Y%m%d")
        concepto = 2
        tipo_doc = 80; nro_doc = "33693450239" # CUIT AFIP
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
        
        wsfev1.CAESolicitar()
        
        print "Resultado", wsfev1.Resultado
        print "CAE", wsfev1.CAE
        
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

    if "--cotizacion" in sys.argv:
        print wsfev1.ParamGetCotizacion('DOL')


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

if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSFEv1)
    else:
        main()
