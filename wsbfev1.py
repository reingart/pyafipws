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

"""Módulo para obtener código de autorización electrónico (CAE) del web service 
WSBFEv1 de AFIP (Bonos Fiscales electronicos v1.1 - Factura Electrónica RG)
a fin de gestionar los Bonos en la Secretaría de Industria según RG 2557
"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2013-2016 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.06f"

import datetime
import decimal
import os
import sys
from utils import inicializar_y_capturar_excepciones, BaseWS, get_install_dir

HOMO = False
LANZAR_EXCEPCIONES = True      # valor por defecto: True
WSDL="https://wswhomo.afip.gov.ar/wsbfev1/service.asmx?WSDL"


class WSBFEv1(BaseWS):
    "Interfaz para el WebService de Bono Fiscal Electrónico V1 (FE Bs. Capital)"
    _public_methods_ = ['CrearFactura', 'AgregarItem', 'Authorize', 'GetCMP',
                        'GetParamMon', 'GetParamTipoCbte', 'GetParamUMed', 
                        'GetParamTipoIVA', 'GetParamNCM', 'GetParamZonas',
                        'GetParamTipoDoc',
                        'Dummy', 'Conectar', 'GetLastCMP', 'GetLastID',
                        'GetParamCtz', 'LoadTestXML',
                        'AnalizarXml', 'ObtenerTagXml', 'DebugLog', 
                        'SetParametros', 'SetTicketAcceso', 'GetParametro',
                        'Dummy', 'Conectar', 'SetTicketAcceso']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Obs', 'Reproceso', 'FechaCAE',
        'CAE','Vencimiento', 'Eventos', 'ErrCode', 'ErrMsg', 'FchVencCAE',
        'Excepcion', 'LanzarExcepciones', 'Traceback', "InstallDir",
        'PuntoVenta', 'CbteNro', 'FechaCbte', 'ImpTotal', 'ImpNeto', 'ImptoLiq',
        ]
        
    _reg_progid_ = "WSBFEv1"
    _reg_clsid_ = "{EE4ABEE2-76DD-450F-880B-66710AE464D6}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    factura = None

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.CbteNro = self.FechaCbte = self.PuntoVenta = self.ImpTotal = None
        self.ImpNeto = self.ImptoLiq = None
        self.LanzarExcepciones = LANZAR_EXCEPCIONES
        self.InstallDir = INSTALL_DIR
        self.FechaCAE = self.FchVencCAE = ""   # retrocompatibilidad

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'BFEErr' in ret:
            errores = [ret['BFEErr']]
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['ErrCode'],
                    error['ErrMsg'],
                    ))
            self.ErrCode = ' '.join([str(error['ErrCode']) for error in errores])
            self.ErrMsg = '\n'.join(self.Errores)
        if 'BFEEvents' in ret:
            events = [ret['BFEEvents']]
            self.Eventos = ['%s: %s' % (evt['EventCode'], evt.get('EventMsg',"")) for evt in events]
        
    def CrearFactura(self, tipo_doc=80, nro_doc=23111111113,
            zona=0, tipo_cbte=1, punto_vta=1, cbte_nro=0, fecha_cbte=None,
            imp_total=0.0, imp_neto=0.0, impto_liq=0.0,
            imp_tot_conc=0.0, impto_liq_rni=0.00, imp_op_ex=0.00,
            imp_perc=0.00, imp_iibb=0.00, imp_perc_mun=0.00, imp_internos=0.00,
            imp_moneda_id=0, imp_moneda_ctz=1.0, **kwargs):
        "Creo un objeto factura (interna)"
        # Creo una factura para bonos fiscales electrónicos

        fact = {'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta, 
                'cbte_nro': cbte_nro, 'fecha_cbte': fecha_cbte, 'zona': zona,
                'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'imp_total': imp_total, 'imp_neto': imp_neto,
                'impto_liq': impto_liq, 'impto_liq_rni': impto_liq_rni, 
                'imp_op_ex': imp_op_ex, 'imp_tot_conc': imp_tot_conc,
                'imp_perc': imp_perc, 'imp_perc_mun': imp_perc_mun, 
                'imp_iibb': imp_iibb, 'imp_internos': imp_internos, 
                'imp_moneda_id': imp_moneda_id, 'imp_moneda_ctz': imp_moneda_ctz,
                'cbtes_asoc': [],
                'iva': [],
                'detalles': [],
            }
        self.factura = fact
        return True
    
    def AgregarItem(self, ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total, **kwargs):
        "Agrego un item a una factura (interna)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        self.factura['detalles'].append({
                'ncm': ncm, 'sec': sec,
                'ds': ds,
                'qty': qty,
                'umed': umed,
                'precio': precio,
                'bonif': bonif,
                'iva_id': iva_id,
                'imp_total': imp_total,
                })
        return True
        
    @inicializar_y_capturar_excepciones
    def Authorize(self, id):
        "Autoriza la factura cargada en memoria"
        f = self.factura
        ret = self.client.BFEAuthorize(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Cmp={
                'Id': id,
                'Zona': f['zona'], 
                'Fecha_cbte': f['fecha_cbte'],
                'Tipo_cbte': f['tipo_cbte'],
                'Punto_vta': f['punto_vta'],
                'Cbte_nro': f['cbte_nro'],
                'Tipo_doc': f['tipo_doc'], 'Nro_doc': f['nro_doc'], 
                'Imp_moneda_Id': f['imp_moneda_id'],
                'Imp_moneda_ctz': f['imp_moneda_ctz'],                
                'Imp_total': f['imp_total'],
                'Imp_tot_conc': f['imp_tot_conc'], 'Imp_op_ex': f['imp_op_ex'],
                'Imp_neto': f['imp_neto'], 'Impto_liq': f['impto_liq'], 
                'Impto_liq_rni': f['impto_liq_rni'],
                'Imp_perc': f['imp_perc'], 'Imp_perc_mun': f['imp_perc_mun'],                
                'Imp_iibb': f['imp_iibb'],
                'Imp_internos': f['imp_internos'],
                'Items': [
                    {'Item': {
                        'Pro_codigo_ncm': d['ncm'],
                        'Pro_codigo_sec': d['sec'],
                        'Pro_ds': d['ds'],
                        'Pro_qty': d['qty'],
                        'Pro_umed': d['umed'],
                        'Pro_precio_uni': d['precio'],
                        'Imp_bonif': d['bonif'],
                        'Imp_total': d['imp_total'],
                        'Iva_id': d['iva_id'],
                     }} for d in f['detalles']],                    
            })

        result = ret['BFEAuthorizeResult']
        self.__analizar_errores(result)
        if 'BFEResultAuth' in result:
            auth = result['BFEResultAuth']
            # Resultado: A: Aceptado, R: Rechazado
            self.Resultado = auth.get('Resultado', "")
            # Obs:
            self.Obs = auth.get('Obs', "")
            self.Reproceso = auth.get('Reproceso', "")
            self.CAE = auth.get('Cae', "")
            self.CbteNro  = auth.get('Fch_cbte', "")
            self.ImpTotal = str(auth.get('Imp_total', ''))
            self.ImptoLiq = str(auth.get('Impto_liq', ''))
            self.ImpNeto = str(auth.get('Imp_neto', ''))
            vto = str(auth.get('Fch_venc_Cae', ''))
            self.FchVencCAE = vto
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            return self.CAE

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.BFEDummy()['BFEDummyResult']
        self.__analizar_errores(result)
        self.AppServerStatus = str(result.get('AppServer', ""))
        self.DbServerStatus = str(result.get('DbServer', ""))
        self.AuthServerStatus = str(result.get('AuthServer', ""))
        return True

    @inicializar_y_capturar_excepciones
    def GetCMP(self, tipo_cbte, punto_vta, cbte_nro):
        "Recuperar los datos completos de un comprobante ya autorizado"
        ret = self.client.BFEGetCMP(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Cmp={"Tipo_cbte": tipo_cbte,
             "Punto_vta": punto_vta, "Cbte_nro": cbte_nro}) 
        result = ret['BFEGetCMPResult']
        self.__analizar_errores(result)
        if 'BFEResultGet' in result:
            resultget = result['BFEResultGet']
            # Obs, cae y fecha cae
            if 'Cae' in resultget:
                self.Obs = resultget['Obs'] and resultget['Obs'].strip(" ") or ''
                self.CAE = resultget['Cae']
                vto = str(resultget['Fch_venc_Cae'])
                self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
                self.FechaCbte = resultget['Fecha_cbte_orig'] #.strftime("%Y/%m/%d")
                self.FechaCAE = resultget['Fecha_cbte_cae'] #.strftime("%Y/%m/%d")            
                self.PuntoVenta = resultget['Punto_vta'] # 4000
                self.Resultado = resultget['Resultado']
                self.CbteNro =resultget['Cbte_nro']
                self.ImpTotal = resultget['Imp_total']
                self.ImptoLiq = resultget['Impto_liq']
                self.ImpNeto = resultget['Imp_neto']
            return self.CAE
        else:
            return 0
    
    @inicializar_y_capturar_excepciones
    def GetLastCMP(self, tipo_cbte, punto_vta):
        "Recuperar último número de comprobante emitido"
        ret = self.client.BFEGetLast_CMP(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit,
                  "Tipo_cbte": tipo_cbte,
                  "Pto_venta": punto_vta,
            })
        result = ret['BFEGetLast_CMPResult']
        self.__analizar_errores(result)
        if 'BFEResult_LastCMP' in result:
            resultget = result['BFEResult_LastCMP']
            self.CbteNro =resultget.get('Cbte_nro')
            self.FechaCbte = resultget.get('Cbte_fecha') #.strftime("%Y/%m/%d")
            return self.CbteNro
            
    @inicializar_y_capturar_excepciones
    def GetLastID(self):
        "Recuperar último número de transacción (ID)"
        ret = self.client.BFEGetLast_ID(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetLast_IDResult']
        self.__analizar_errores(result)
        if 'BFEResultGet' in result:
            resultget = result['BFEResultGet']
            return resultget.get('Id')
 
    @inicializar_y_capturar_excepciones
    def GetParamUMed(self):
        ret = self.client.BFEGetPARAM_UMed(
            auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetPARAM_UMedResult']
        self.__analizar_errores(result)
     
        umeds = [] # unidades de medida
        for u in result['BFEResultGet']:
            u = u['ClsBFEResponse_UMed']
            try:
                umed = {'id': u.get('Umed_Id'), 'ds': u.get('Umed_Ds'), 
                        'vig_desde': u.get('Umed_vig_desde'), 
                        'vig_hasta': u.get('Umed_vig_hasta')}
            except Exception, e:
                print e
                if u is None:
                    # <ClsFEXResponse_UMed xsi:nil="true"/> WTF!
                    umed = {'id':'', 'ds':'','vig_desde':'','vig_hasta':''}
                    #import pdb; pdb.set_trace()
                    #print u
                
            
            umeds.append(umed)
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in umeds]

    @inicializar_y_capturar_excepciones
    def GetParamMon(self):
        ret = self.client.BFEGetPARAM_MON(
            auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetPARAM_MONResult']
        self.__analizar_errores(result)
     
        mons = [] # unidades de medida
        for m in result['BFEResultGet']:
            m = m['ClsBFEResponse_Mon']
            try:
                mon = {'id': m.get('Mon_Id'), 'ds': m.get('Mon_Ds'), 
                        'vig_desde': m.get('Mon_vig_desde'), 
                        'vig_hasta': m.get('Mon_vig_hasta')}
            except Exception, e:
                raise
                if m is None:
                    # <ClsFEXResponse_UMed xsi:nil="true"/> WTF!
                    mon = {'id':'', 'ds':'','vig_desde':'','vig_hasta':''}
                    #import pdb; pdb.set_trace()
                    #print u
            mons.append(mon)
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in mons]        

    @inicializar_y_capturar_excepciones
    def GetParamTipoIVA(self):
        "Recuperar lista de valores referenciales de tipos de IVA (alícuotas)"
        ret = self.client.BFEGetPARAM_Tipo_IVA(
            auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetPARAM_Tipo_IVAResult']
        self.__analizar_errores(result)
     
        ivas = [] # tipos de iva
        for i in result['BFEResultGet']:
            i = i['ClsBFEResponse_Tipo_IVA']
            try:
                iva = {'id': i.get('IVA_Id'), 'ds': i.get('IVA_Ds'), 
                        'vig_desde': i.get('IVA_vig_desde'), 
                        'vig_hasta': i.get('IVA_vig_hasta')}
                ivas.append(iva)
            except Exception, e:
                pass
                raise
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in ivas]

    @inicializar_y_capturar_excepciones
    def GetParamTipoDoc(self):
        "Recuperar lista de valores referenciales de tipos de documentos"
        ret = self.client.BFEGetPARAM_Tipo_doc(
            auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetPARAM_Tipo_docResult']
        self.__analizar_errores(result)
     
        docs = [] # tipos de documentos
        for d in result['BFEResultGet']:
            d = d['ClsBFEResponse_Tipo_doc']
            try:
                doc = {'id': d.get('Doc_Id'), 'ds': d.get('Doc_Ds'), 
                        'vig_desde': d.get('Doc_vig_desde'), 
                        'vig_hasta': d.get('Doc_vig_hasta')}
                docs.append(doc)
            except Exception, e:
                pass
                raise
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % d for d in docs]

    def GetParamTipoCbte(self):
        "Recuperar lista de valores referenciales de Tipos de Comprobantes"
        ret = self.client.BFEGetPARAM_Tipo_Cbte(
            auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetPARAM_Tipo_CbteResult']
        self.__analizar_errores(result)
     
        tipos = [] # tipos de comprobantes
        for t in result['BFEResultGet']:
            t = t['ClsBFEResponse_Tipo_Cbte']
            try:
                tipo = {'id': t.get('Cbte_Id'), 'ds': t.get('Cbte_Ds'), 
                        'vig_desde': t.get('Cbte_vig_desde'), 
                        'vig_hasta': t.get('Cbte_vig_hasta')}
                tipos.append(tipo)
            except Exception, e:
                pass
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in tipos]

    def GetParamNCM(self):
        "Recuperar lista de valores referenciales de códigos del Nomenclador Común del Mercosur"
        ret = self.client.BFEGetPARAM_NCM(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetPARAM_NCMResult']
        self.__analizar_errores(result)
     
        ncms = [] # nomenclador comun del mercosur
        for n in result['BFEResultGet']:
            n = n['ClsBFEResponse_NCM']
            try:
                ncm = {'id': n.get('NCM_Codigo'), 'ds': n.get('NCM_Ds'), 
                        'vig_desde': n.get('NCM_vig_desde'), 
                        'vig_hasta': n.get('NCM_vig_hasta')}
                ncms.append(ncm)
            except Exception, e:
                pass
        return [u'%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in ncms]

    def GetParamZonas(self):
        "Recuperar lista de valores referenciales de Zonas"
        ret = self.client.BFEGetPARAM_Zonas(
            auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['BFEGetPARAM_ZonasResult']
        self.__analizar_errores(result)
     
        zonas = [] # zonas
        for z in result['BFEResultGet']:
            z = z['ClsBFEResponse_Zon']
            try:
                zona = {'id': z.get('Zon_Id'), 'ds': z.get('Zon_Ds'), 
                        'vig_desde': z.get('Zon_vig_desde'), 
                        'vig_hasta': z.get('Zon_vig_hasta')}
                zonas.append(zona)
            except Exception, e:
                pass
        return ['%(id)s: %(ds)s (%(vig_desde)s - %(vig_hasta)s)' % p for p in zonas]

    @inicializar_y_capturar_excepciones
    def GetParamCtz(self, moneda_id):
        "Recuperador de cotización de moneda"
        ret = self.client.BFEGetPARAM_Ctz(
            auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            MonId=moneda_id,
            )
        self.__analizar_errores(ret['BFEGetPARAM_CtzResult'])
        res = ret['BFEGetPARAM_CtzResult'].get('BFEResultGet')
        if res:
            ctz = str(res.get('Mon_ctz',""))
        else:
            ctz = ''
        return ctz
    


class WSBFE(WSBFEv1):
    "Wrapper para retrocompatibilidad con WSBFE"
    
    _reg_progid_ = "WSBFE"
    _reg_clsid_ = "{02CBC6DA-455D-4EE6-8302-411D13253CBF}"
    
    def __init__(self):
        WSBFEv1.__init__(self)
        self.Version = "%s %s WSBFEv1" % (__version__, HOMO and 'Homologación' or '')

    def Conectar(self, cache=None, url="", **kwargs):
        # Ajustar URL de V0 a V1:
        if url in ("https://wswhomo.afip.gov.ar/wsfex/service.asmx",
                   "http://wswhomo.afip.gov.ar/WSFEX/service.asmx"):
            url = "https://wswhomo.afip.gov.ar/wsbfev1/service.asmx"
        elif url in ("https://servicios1.afip.gov.ar/wsfex/service.asmx",
                     "http://servicios1.afip.gov.ar/WSFEX/service.asmx"):
            url = "https://servicios1.afip.gov.ar/wsbfev1/service.asmx"
        return WSBFEv1.Conectar(self, cache=cache, wsdl=url, **kwargs)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSBFEv1.InstallDir = get_install_dir()


def p_assert_eq(a,b):
    print a, a==b and '==' or '!=', b


if __name__ == "__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSBFEv1)
        if '--wsbfe' in sys.argv:
            win32com.server.register.UseCommandLine(WSBFE)
    else:

        # Crear objeto interface Web Service de Factura Electrónica de Exportación
        wsbfev1 = WSBFEv1()
        # Setear token y sing de autorización (pasos previos)

        # obteniendo el TA para pruebas
        from wsaa import WSAA
        ta = WSAA().Autenticar("wsbfe", "reingart.crt", "reingart.key")
        wsbfev1.SetTicketAcceso(ta)

        # CUIT del emisor (debe estar registrado en la AFIP)
        wsbfev1.Cuit = "20267565393"

        # Conectar al Servicio Web de Facturación (homologación)
        wsdl = "http://wswhomo.afip.gov.ar/WSBFEv1/service.asmx"
        cache = proxy = ""
        wrapper = "httplib2"
        cacert = open("conf/afip_ca_info.crt").read()
        ok = wsbfev1.Conectar(cache, wsdl, proxy, wrapper, cacert)
    
        if '--dummy' in sys.argv:
            #wsbfev1.LanzarExcepciones = False
            print wsbfev1.Dummy()
            print "AppServerStatus", wsbfev1.AppServerStatus
            print "DbServerStatus", wsbfev1.DbServerStatus
            print "AuthServerStatus", wsbfev1.AuthServerStatus
        
        if "--prueba" in sys.argv:
            try:
                # Establezco los valores de la factura a autorizar:
                tipo_cbte = '--nc' in sys.argv and 3 or 1 # FC/NC Expo (ver tabla de parámetros)
                punto_vta = 5
                tipo_doc = 80 
                nro_doc = 23111111113
                zona = 0
                # Obtengo el último número de comprobante y le agrego 1
                cbte_nro = int(wsbfev1.GetLastCMP(tipo_cbte, punto_vta)) + 1
                fecha_cbte = datetime.datetime.now().strftime("%Y%m%d")
                imp_moneda_id = "PES"  # (ver tabla de parámetros)
                imp_moneda_ctz = 1
                imp_neto = "390.00"
                impto_liq = "81.90"      # 21% IVA
                impto_liq_rni = imp_tot_conc = imp_op_ex = "0.00"
                imp_perc = imp_iibb = imp_perc_mun = imp_internos = "0.00"
                imp_total = "471.90"
                
                # Creo una factura (internamente, no se llama al WebService):
                ok = wsbfev1.CrearFactura(tipo_doc, nro_doc,
                    zona, tipo_cbte, punto_vta, cbte_nro, fecha_cbte,
                    imp_total, imp_neto, impto_liq,
                    imp_tot_conc, impto_liq_rni, imp_op_ex,
                    imp_perc, imp_iibb, imp_perc_mun, imp_internos,
                    imp_moneda_id, imp_moneda_ctz)
                
                # Agrego un item:
                ncm = '7308.10.00'
                sec = ''
                umed = 7  # unidades
                ds = 'prueba Anafe economico'
                qty = "2.00"
                precio = "100.00"
                bonif = "0.00"
                iva_id = 5
                imp_total = "242.00"
                ok = wsbfev1.AgregarItem(ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total)

                # Agrego otro item:
                ncm = '7308.20.00'
                sec = ''
                umed = 7  # unidades
                ds = 'prueba 2'
                qty = "4.00"
                precio = "50.00"
                bonif = "10.00"
                iva_id = 5
                imp_total = "229.90"
                ok = wsbfev1.AgregarItem(ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total)
                    
                ##id = "99000000000100" # número propio de transacción
                # obtengo el último ID y le adiciono 1 
                # (advertencia: evitar overflow y almacenar!)
                id = long(wsbfev1.GetLastID()) + 1

                # Llamo al WebService de Autorización para obtener el CAE
                cae = wsbfev1.Authorize(id)

                print "Comprobante", tipo_cbte, wsbfev1.CbteNro
                print "Resultado", wsbfev1.Resultado
                print "CAE", wsbfev1.CAE
                print "Vencimiento", wsbfev1.Vencimiento

                if wsbfev1.Resultado and False:
                    print wsbfev1.client.help("FEXGetCMP").encode("latin1")
                    wsbfev1.GetCMP(tipo_cbte, punto_vta, cbte_nro)
                    print "CAE consulta", wsbfev1.CAE, wsbfev1.CAE==cae 
                    print "NRO consulta", wsbfev1.CbteNro, wsbfev1.CbteNro==cbte_nro 
                    print "TOTAL consulta", wsbfev1.ImpTotal, wsbfev1.ImpTotal==imp_total

            except Exception, e:
                print wsbfev1.XmlRequest        
                print wsbfev1.XmlResponse        
                print wsbfev1.ErrCode
                print wsbfev1.ErrMsg
                print wsbfev1.Excepcion
                print wsbfev1.Traceback
                raise

        if "--get" in sys.argv:
            tipo_cbte = 1
            punto_vta = 5
            cbte_nro = wsbfev1.GetLastCMP(tipo_cbte, punto_vta)

            wsbfev1.GetCMP(tipo_cbte, punto_vta, cbte_nro)

            print "FechaCbte = ", wsbfev1.FechaCbte
            print "CbteNro = ", wsbfev1.CbteNro
            print "PuntoVenta = ", wsbfev1.PuntoVenta
            print "ImpTotal =", wsbfev1.ImpTotal
            print "CAE = ", wsbfev1.CAE
            print "Vencimiento = ", wsbfev1.Vencimiento

            wsbfev1.AnalizarXml("XmlResponse")
            p_assert_eq(wsbfev1.ObtenerTagXml('Cae'), str(wsbfev1.CAE))
            p_assert_eq(wsbfev1.ObtenerTagXml('Fecha_cbte_orig'), wsbfev1.FechaCbte)
            p_assert_eq(wsbfev1.ObtenerTagXml('Imp_moneda_Id'), "PES")
            p_assert_eq(wsbfev1.ObtenerTagXml('Imp_moneda_ctz'), "1")
            p_assert_eq(wsbfev1.ObtenerTagXml('Items', 'Item', 1, 'Pro_ds'), "prueba 2")

        if "--params" in sys.argv:
            import codecs, locale
            sys.stdout = codecs.getwriter('latin1')(sys.stdout); 

            print "=== Tipos de Comprobante ==="
            print u'\n'.join(wsbfev1.GetParamTipoCbte())

            print "=== Zonas ==="
            print u'\n'.join(wsbfev1.GetParamZonas())
                
            print "=== Monedas ==="
            print u'\n'.join(wsbfev1.GetParamMon())

            print "=== Tipos de Documentos ==="
            print u'\n'.join(wsbfev1.GetParamTipoDoc())

            print "=== Tipos de IVA ==="
            print u'\n'.join(wsbfev1.GetParamTipoIVA())

            print "=== Unidades de medida ==="
            print u'\n'.join(wsbfev1.GetParamUMed())

            print u"=== Códigos NCM ==="
            print u'\n'.join(wsbfev1.GetParamNCM())
            
        if "--ctz" in sys.argv:
            print wsbfev1.GetParamCtz('DOL')

