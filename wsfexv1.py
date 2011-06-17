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

"""Módulo para obtener código de autorización de impresión o 
electrónico del web service WSFEXv1 de AFIP (Factura Electrónica Exportación V1)
"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.00a"

import datetime
import decimal
import os
import socket
import sys
import traceback
from cStringIO import StringIO
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper
from wsfev1 import inicializar_y_capturar_excepciones

HOMO = True

WSDL="https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL"


class WSFEXv1:
    "Interfaz para el WebService de Factura Electrónica Exportación Versión 1"
    _public_methods_ = ['CrearFactura', 'AgregarItem', 'Authorize', 'GetCMP',
                        'AgregarPermiso', 'AgregarCmpAsoc',
                        'GetParamMon', 'GetParamTipoCbte', 'GetParamTipoExpo', 
                        'GetParamIdiomas', 'GetParamUMed', 'GetParamIncoterms', 
                        'GetParamDstPais','GetParamDstCUIT',
                        'GetParamCtz',
                        'Dummy', 'Conectar', 'GetLastCMP', 'GetLastID' ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version', 'DebugLog', 
        'Resultado', 'Obs', 'Reproceso',
        'CAE','Vencimiento', 'Eventos', 'ErrCode', 'ErrMsg',
        'Excepcion', 'LanzarExcepciones', 'Traceback', "InstallDir",
        'PuntoVenta', 'CbteNro', 'FechaCbte', 'ImpTotal']
        
    _reg_progid_ = "WSFEXv1"
    _reg_clsid_ = "{8106F039-D132-4F87-8AFE-ADE47B5503D4}"

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
        self.CbteNro = self.FechaCbte = self.PuntoVenta = self.ImpTotal = None
        self.ErrCode = self.ErrMsg = None
        self.LanzarExcepciones = True
        self.Traceback = self.Excepcion = ""
        self.InstallDir = INSTALL_DIR
        self.DebugLog = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'FEXErr' in ret:
            errores = [ret['FEXErr']]
            self.Errores = []
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['ErrCode'],
                    error['ErrMsg'],
                    ))
            self.ErrCode = ' '.join([str(error['ErrCode']) for error in errores])
            self.ErrMsg = '\n'.join(self.Errores)
        if 'FEXEvents' in ret:
            events = [ret['FEXEvents']]
            self.Eventos = ['%s: %s' % (evt['EventCode'], evt.get('EventMsg',"")) for evt in events]

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
        self.DebugLog += "Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict)
        self.client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            cacert = cacert,
            trace = "--trace" in sys.argv)
        return True

        
    def CrearFactura(self, tipo_cbte=19, punto_vta=1, cbte_nro=0, fecha_cbte=None,
            imp_total=0.0, tipo_expo=1, permiso_existente="N", pais_dst_cmp=None,
            nombre_cliente="", cuit_pais_cliente="", domicilio_cliente="",
            id_impositivo="", moneda_id="PES", moneda_ctz=1.0,
            obs_comerciales="", obs_generales="", forma_pago="", incoterms="", 
            idioma_cbte=7, incoterms_ds=None):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación 

        fact = {'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbte_nro': cbte_nro, 'fecha_cbte': fecha_cbte,
                'tipo_doc': 80, 'nro_doc':  cuit_pais_cliente,
                'imp_total': imp_total, 
                'permiso_existente': permiso_existente, 
                'pais_dst_cmp': pais_dst_cmp,
                'nombre_cliente': nombre_cliente,
                'domicilio_cliente': domicilio_cliente,
                'id_impositivo': id_impositivo,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'obs_comerciales': obs_comerciales,
                'obs_generales': obs_generales,
                'forma_pago': forma_pago,
                'incoterms': incoterms,
                'incoterms_ds': incoterms_ds,
                'tipo_expo': tipo_expo,
                'idioma_cbte': idioma_cbte,
                'cbtes_asoc': [],
                'permisos': [],
                'detalles': [],
            }
        self.factura = fact

        return True
    
    def AgregarItem(self, codigo, ds, qty, umed, precio, importe, bonif=None):
        "Agrego un item a una factura (interna)"
        # Nota: no se calcula total (debe venir calculado!)
        self.factura['detalles'].append({
                'codigo': codigo,                
                'ds': ds,
                'qty': qty,
                'umed': umed,
                'precio': precio,
                'bonif': bonif,
                'importe': importe,
                })
        return True
       
    def AgregarPermiso(self, id_permiso, dst_merc):
        "Agrego un permiso a una factura (interna)"
        self.factura['permisos'].append({
                'id_permiso': id_permiso,
                'dst_merc': dst_merc,
                })        
        return True
        
    def AgregarCmpAsoc(self, cbte_tipo=19, cbte_punto_vta=0, cbte_nro=0, cbte_cuit=None):
        "Agrego un comprobante asociado a una factura (interna)"
        self.factura['cbtes_asoc'].append({
            'cbte_tipo': cbte_tipo, 'cbte_punto_vta': cbte_punto_vta, 
            'cbte_nro': cbte_nro, 'cbte_cuit': cbte_cuit})
        return True

    @inicializar_y_capturar_excepciones
    def Authorize(self, id):
        "Autoriza la factura cargada en memoria"
        f = self.factura
        ret = self.client.FEXAuthorize(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Cmp={
                'Id': id,
                'Fecha_cbte': f['fecha_cbte'],
                'Cbte_Tipo': f['tipo_cbte'],
                'Punto_vta': f['punto_vta'],
                'Cbte_nro': f['cbte_nro'],
                'Tipo_expo': f['tipo_expo'],
                'Permiso_existente': f['permiso_existente'],
                'Permisos': [
                    {'Permiso': {
                        'Id_permiso': p['id_permiso'],
                        'Dst_merc': p['dst_merc'],
                    }} for p in f['permisos']],
                'Dst_cmp': f['pais_dst_cmp'],
                'Cliente': f['nombre_cliente'],
                'Cuit_pais_cliente': f['nro_doc'],
                'Domicilio_cliente': f['domicilio_cliente'],
                'Id_impositivo': f['id_impositivo'],
                'Moneda_Id': f['moneda_id'],
                'Moneda_ctz': f['moneda_ctz'],                
                'Obs_comerciales': f['obs_comerciales'],
                'Imp_total': f['imp_total'],
                'Obs': f['obs_generales'],
                'Cmps_asoc': [
                    {'Cmp_asoc': {
                        'Cbte_tipo': c['cbte_tipo'],
                        'Cbte_punto_vta': c['cbte_punto_vta'],
                        'Cbte_nro': c['cbte_nro'],
                        'Cbte_cuit': c['cbte_cuit'],
                    }} for c in f['cbtes_asoc']],
                'Forma_pago': f['forma_pago'],
                'Incoterms': f['incoterms'],
                'Incoterms_Ds': f['incoterms_ds'],
                'Idioma_cbte':  f['idioma_cbte'],
                'Items': [
                    {'Item': {
                        'Pro_codigo': d['codigo'],
                        'Pro_ds': d['ds'],
                        'Pro_qty': d['qty'],
                        'Pro_umed': d['umed'],
                        'Pro_precio_uni': d['precio'],
                        'Pro_bonificacion': d['bonif'],
                        'Pro_total_item': d['importe'],
                     }} for d in f['detalles']],                    
            })

        result = ret['FEXAuthorizeResult']
        self.__analizar_errores(result)
        if 'FEXResultAuth' in result:
            auth = result['FEXResultAuth']
            # Resultado: A: Aceptado, R: Rechazado
            self.Resultado = auth['Resultado']
            # Obs:
            self.Obs = auth['Motivos_Obs']
            self.Reproceso = auth['Reproceso']
            self.CAE = auth['Cae']
            self.CbteNro  = auth['Cbte_nro']
            vto = str(auth['Fch_venc_Cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            return self.CAE

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.FEXDummy()['FEXDummyResult']
        self.__analizar_errores(result)
        self.AppServerStatus = str(result['AppServer'])
        self.DbServerStatus = str(result['DbServer'])
        self.AuthServerStatus = str(result['AuthServer'])
        return True

    @inicializar_y_capturar_excepciones
    def GetCMP(self, tipo_cbte, punto_vta, cbte_nro):
        "Recuperar los datos completos de un comprobante ya autorizado"
        ret = self.client.FEXGetCMP(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Cmp={
                'Cbte_tipo': tipo_cbte,
                'Pto_vta': punto_vta,
                'Cbte_nro': cbte_nro,
            })
        result = ret['FEXGetCMPResult']
        self.__analizar_errores(result)
        if 'FEXResultGet' in result:
            resultget = result['FEXResultGet']
                
            # Obs, cae y fecha cae
            self.Obs = resultget['Motivos_Obs'].strip(" ")
            self.CAE = resultget['Cae']
            vto = str(resultget['Fch_venc_Cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            self.FechaCbte = resultget['Fecha_cbte'] #.strftime("%Y/%m/%d")
            self.PuntoVenta = resultget['Punto_vta'] # 4000
            self.Resultado = resultget['Resultado']
            self.CbteNro =resultget['Cbte_nro']
            self.ImpTotal = resultget['Imp_total']
            return self.CAE
        else:
            return 0
    
    @inicializar_y_capturar_excepciones
    def GetLastCMP(self, tipo_cbte, punto_vta):
        "Recuperar último número de comprobante emitido"
        ret = self.client.FEXGetLast_CMP(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit,
                  'Cbte_Tipo': tipo_cbte,
                  'Pto_venta': punto_vta,
            })
        result = ret['FEXGetLast_CMPResult']
        self.__analizar_errores(result)
        if 'FEXResult_LastCMP' in result:
            resultget = result['FEXResult_LastCMP']
            self.CbteNro =resultget.get('Cbte_nro')
            self.FechaCbte = resultget.get('Cbte_fecha') #.strftime("%Y/%m/%d")
            return self.CbteNro
            
    @inicializar_y_capturar_excepciones
    def GetLastID(self):
        "Recuperar último número de transacción (ID)"
        ret = self.client.FEXGetLast_ID(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit, })
        result = ret['FEXGetLast_IDResult']
        self.__analizar_errores(result)
        if 'FEXResultGet' in result:
            resultget = result['FEXResultGet']
            return resultget.get('Id')


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == "__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSFEXv1)
    else:

        # Crear objeto interface Web Service de Factura Electrónica de Exportación
        wsfexv1 = WSFEXv1()
        # Setear token y sing de autorización (pasos previos)

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        tra = wsaa.CreateTRA(service="wsfex")
        cms = wsaa.SignTRA(tra,"reingart.crt","reingart.key")
        url = "" # "https://wsaa.afip.gov.ar/ws/services/LoginCms"
        wsaa.Conectar("", url)
        ta = wsaa.LoginCMS(cms)
        # fin TA

        wsfexv1.Token = wsaa.Token
        wsfexv1.Sign = wsaa.Sign

        # CUIT del emisor (debe estar registrado en la AFIP)
        wsfexv1.Cuit = "20267565393"

        # Conectar al Servicio Web de Facturación (homologación)
        ok = wsfexv1.Conectar("","http://wswhomo.afip.gov.ar/WSFEXv1/service.asmx")

        if '--dummy' in sys.argv:
            #wsfexv1.LanzarExcepciones = False
            print wsfexv1.Dummy()
            print wsfexv1.XmlRequest
            print wsfexv1.XmlResponse
        
        if "--prueba" in sys.argv:
            try:
                # Establezco los valores de la factura a autorizar:
                tipo_cbte = 19 # FC Expo (ver tabla de parámetros)
                punto_vta = 7
                # Obtengo el último número de comprobante y le agrego 1
                cbte_nro = int(wsfexv1.GetLastCMP(tipo_cbte, punto_vta)) + 1
                fecha_cbte = datetime.datetime.now().strftime("%Y%m%d")
                tipo_expo = 1 # tipo de exportación (ver tabla de parámetros)
                permiso_existente = "S"
                dst_cmp = 203 # país destino
                cliente = "Joao Da Silva"
                cuit_pais_cliente = "50000000016"
                domicilio_cliente = "Rua 76 km 34.5 Alagoas"
                id_impositivo = "PJ54482221-l"
                moneda_id = "012" # para reales, "DOL" o "PES" (ver tabla de parámetros)
                moneda_ctz = 0.5
                obs_comerciales = "Observaciones comerciales"
                obs = "Sin observaciones"
                forma_pago = "30 dias"
                incoterms = "FOB" # (ver tabla de parámetros)
                incoterms_ds = "Flete a Bordo" 
                idioma_cbte = 1 # (ver tabla de parámetros)
                imp_total = "250.00"
                
                # Creo una factura (internamente, no se llama al WebService):
                ok = wsfexv1.CrearFactura(tipo_cbte, punto_vta, cbte_nro, fecha_cbte, 
                        imp_total, tipo_expo, permiso_existente, dst_cmp, 
                        cliente, cuit_pais_cliente, domicilio_cliente, 
                        id_impositivo, moneda_id, moneda_ctz, 
                        obs_comerciales, obs, forma_pago, incoterms, 
                        idioma_cbte, incoterms_ds)
                
                # Agrego un item:
                codigo = "PRO1"
                ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
                qty = 2
                precio = "150.00"
                umed = 1 # Ver tabla de parámetros (unidades de medida)
                bonif = "50.00"
                imp_total = "250.00" # importe total final del artículo
                # lo agrego a la factura (internamente, no se llama al WebService):
                ok = wsfexv1.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)

                # Agrego un permiso (ver manual para el desarrollador)
                id = "99999AAXX999999A"
                dst = 225 # país destino de la mercaderia
                ok = wsfexv1.AgregarPermiso(id, dst)

                # Agrego un comprobante asociado (solo para N/C o N/D)
                if tipo_cbte in (20,21): 
                    cbteasoc_tipo = 19
                    cbteasoc_pto_vta = 2
                    cbteasoc_nro = 1234
                    cbteasoc_cuit = 20111111111
                    wsfexv1.AgregarCmpAsoc(cbteasoc_tipo, cbteasoc_pto_vta, cbteasoc_nro, cbteasoc_cuit)
                    
                ##id = "99000000000100" # número propio de transacción
                # obtengo el último ID y le adiciono 1 
                # (advertencia: evitar overflow y almacenar!)
                id = long(wsfexv1.GetLastID()) + 1

                # Llamo al WebService de Autorización para obtener el CAE
                cae = wsfexv1.Authorize(id)

                print "Resultado", wsfexv1.Resultado
                print "CAE", wsfexv1.CAE
                print "Vencimiento", wsfexv1.Vencimiento
                            
                print wsfexv1.client.help("FEXGetCMP").encode("latin1")
                wsfexv1.GetCMP(tipo_cbte, punto_vta, cbte_nro)
                print "CAE consulta", wsfexv1.CAE, wsfexv1.CAE==cae 
                print "NRO consulta", wsfexv1.CbteNro, wsfexv1.CbteNro==cbte_nro 
                print "TOTAL consulta", wsfexv1.ImpTotal, wsfexv1.ImpTotal==imp_total

            except:
                print wsfexv1.XmlRequest        
                print wsfexv1.XmlResponse        
                print wsfexv1.ErrCode
                print wsfexv1.ErrMsg
                print wsfexv1.Excepcion
                print wsfexv1.Traceback
                import pdb; pdb.set_trace()
                raise

            
