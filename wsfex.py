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
electrónico del web service WSFEX de AFIP (Factura Electrónica Exportación)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.23e"

import sys
from php import date, SimpleXMLElement, SoapClient

WSFEXURL = "https://wswhomo.afip.gov.ar/wsfex/service.asmx"
##WSFEXURL = "https://servicios1.afip.gov.ar/wsfex/service.asmx"
SOAP_ACTION = 'http://ar.gov.afip.dif.fex/'
SOAP_NS = "http://ar.gov.afip.dif.fex/"

class FEXError(RuntimeError):
    "Clase para informar errores del WSFEX"
    def __init__(self, fexerror):
        self.code = str(fexerror.ErrCode)
        self.msg = unicode(fexerror.ErrMsg)

    def __unicode__(self):
        return u"FEXError %s: %s" % (self.code, self.msg)

def dummy(client):
    "Metodo dummy para verificacion de funcionamiento"
    response = client.FEXDummy()
    result = response.FEXDummyResult
    appserver = dbserver = authserver = None
    try:
        appserver = str(result.AppServer)
        dbserver = str(result.DbServer)
        authserver = str(result.AuthServer)
    except (RuntimeError, IndexError, AttributeError), e:
        pass
    return {'appserver': appserver,
            'dbserver': dbserver,
            'authserver': authserver}

def get_param_mon(client, token, sign, cuit):
    "Recuperador de valores referenciales de codigos de Moneda"
    response = client.FEXGetPARAM_MON(
        Auth={"Token": token, "Sign": sign, "Cuit":long(cuit)})
    
    if int(response.FEXGetPARAM_MONResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_MONResult.FEXErr)

    mons = [] # monedas
    for m in response.FEXGetPARAM_MONResult.FEXResultGet.ClsFEXResponse_Mon:
        mon = {'id': str(m.Mon_Id), 'ds': str(m.Mon_Ds).decode('utf8'), 
               'vig_desde': str(m.Mon_vig_desde), 
               'vig_hasta': str(m.Mon_vig_hasta)}
        mons.append(mon)
    return mons
 
def get_param_tipo_cbte(client, token, sign, cuit):
    "Recuperador de valores referenciales de códigos de Tipos de comprobante"
    response = client.FEXGetPARAM_Tipo_Cbte(
        Auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.FEXGetPARAM_Tipo_CbteResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_Tipo_CbteResult.FEXErr)

    cbtes = [] # tipos de comprobantes
    for c in response.FEXGetPARAM_Tipo_CbteResult.FEXResultGet.ClsFEXResponse_Tipo_Cbte:
        cbte = {'id': int(c.Cbte_Id), 'ds': str(c.Cbte_Ds).decode('utf8'), 
                'vig_desde': str(c.Cbte_vig_desde), 
                'vig_hasta': str(c.Cbte_vig_hasta)}
        cbtes.append(cbte)
    return cbtes

def get_param_tipo_expo(client, token, sign, cuit):
    "Recuperador de valores referenciales de códigos de Tipo de exportación"
    response = client.FEXGetPARAM_Tipo_Expo(
        Auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.FEXGetPARAM_Tipo_ExpoResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_Tipo_ExpoResult.FEXErr)

    tipos = [] # tipos de exportación
    for t in response.FEXGetPARAM_Tipo_ExpoResult.FEXResultGet.ClsFEXResponse_Tex:
        tipo = {'id': int(t.Tex_Id), 'ds': str(t.Tex_Ds).decode('utf8'), 
                'vig_desde': str(t.Tex_vig_desde), 
                'vig_hasta': str(t.Tex_vig_hasta)}
        tipos.append(tipo)
    return tipos

def get_param_idiomas(client, token, sign, cuit):
    "Recuperador de valores referenciales de códigos de Idiomas"
    response = client.FEXGetPARAM_Idiomas(
        Auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.FEXGetPARAM_IdiomasResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_IdiomasResult.FEXErr)

    tipos = [] # tipos de exportación
    for t in response.FEXGetPARAM_IdiomasResult.FEXResultGet.ClsFEXResponse_Idi:
        tipo = {'id': int(t.Idi_Id), 'ds': str(t.Idi_Ds).decode('utf8'), 
                'vig_desde': str(t.Idi_vig_desde), 
                'vig_hasta': str(t.Idi_vig_hasta)}
        tipos.append(tipo)
    return tipos

def get_param_umed(client, token, sign, cuit):
    "Recuperador de valores referenciales de Unidades de Medidas"
    response = client.FEXGetPARAM_UMed(
        Auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.FEXGetPARAM_UMedResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_UMedResult.FEXErr)

    umeds = [] # unidades de medida
    for u in response.FEXGetPARAM_UMedResult.FEXResultGet.ClsFEXResponse_UMed:
        umed = {'id': int(u.Umed_Id), 'ds': str(u.Umed_Ds).decode('utf8'), 
                'vig_desde': str(u.Umed_vig_desde), 
                'vig_hasta': str(u.Umed_vig_hasta)}
        umeds.append(umed)
    return umeds

def get_param_dst_pais(client, token, sign, cuit):
    "Recuperador de valores referenciales de códigos de Países"
    response = client.FEXGetPARAM_DST_pais(
        Auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.FEXGetPARAM_DST_paisResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_DST_paisResult.FEXErr)

    paises = [] 
    for p in response.FEXGetPARAM_DST_paisResult.FEXResultGet.ClsFEXResponse_DST_pais:
        pais = {'codigo': int(p.DST_Codigo), 'ds': str(p.DST_Ds).decode('utf8')}
        paises.append(pais)
    return paises

def get_param_dst_cuit(client, token, sign, cuit):
    "Recuperador de valores referenciales de CUITs de Paises"
    response = client.FEXGetPARAM_DST_CUIT(
        Auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.FEXGetPARAM_DST_CUITResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_DST_CUITResult.FEXErr)

    paises = [] 
    for p in response.FEXGetPARAM_DST_CUITResult.FEXResultGet.ClsFEXResponse_DST_cuit:
        pais = {'cuit': int(p.DST_CUIT), 'ds': str(p.DST_Ds).decode('utf8')}
        paises.append(pais)
    return paises

def get_param_ctz(client, token, sign, cuit, moneda_id):
    "Recuperador de cotización de moneda"
    response = client.FEXGetPARAM_Ctz(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit)}, 
        Mon_id=moneda_id)
    
    if int(response.FEXGetPARAM_CtzResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_CtzResult.FEXErr)

    m = response.FEXGetPARAM_CtzResult.FEXResultGet
    return {'ctz': str(m.Mon_ctz), 'fecha': str(m.Mon_fecha)}

def get_param_pto_venta(client, token, sign, cuit):
    "Recuperador de los puntos de venta asignados a WSFEX"
    response = client.FEXGetPARAM_PtoVenta(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit)})
    
    if int(response.FEXGetPARAM_PtoVentaResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_PtoVentaResult.FEXErr)

    pto_vtas = [] 
    try:
        for p in response.FEXGetPARAM_PtoVentaResult.FEXResultGet.ClsFEXResponse_PtoVenta:
            pais = {'nro': int(p.Pve_Nro), 'bloqueado': str(p.Pve_Bloqueado).decode('utf8'),
                    'baja': str(p.Pve_FchBaja), }
            pto_vtas.append(pais)
    except AttributeError:
        pass # no devolvió ningún pv (testing)
    return pto_vtas

def get_param_incoterms(client, token, sign, cuit):
    "Recuperador de valores referenciales de Incoterms"
    response = client.FEXGetPARAM_Incoterms(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit)})
    
    if int(response.FEXGetPARAM_IncotermsResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetPARAM_IncotermsResult.FEXErr)

    incoterms = []
    for p in response.FEXGetPARAM_IncotermsResult.FEXResultGet.ClsFEXResponse_Inc:
        pais = {'id': str(p.Inc_Id), 'ds': str(p.Inc_Ds).decode('utf8'),
                'vig_desde': str(p.Inc_vig_desde), 
                'vig_hasta': str(p.Inc_vig_hasta), }
        incoterms.append(pais)
    return incoterms

def get_last_cmp(client, token, sign, cuit, tipo_cbte, punto_vta):
    "Recuperador de ultimo valor de comprobante autorizado"
    response = client.FEXGetLast_CMP(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit),
              "Tipo_cbte": tipo_cbte,
              "Pto_venta": punto_vta}) 

    if int(response.FEXGetLast_CMPResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetLast_CMPResult.FEXErr)

    result = response.FEXGetLast_CMPResult.FEXResult_LastCMP    
    cbte_nro = int(result.Cbte_nro)
    try:
        cbte_fecha = str(result.Cbte_fecha)
    except AttributeError:
        cbte_fecha = ""
        
    events = []
    for FEX_event in response.FEXGetLast_CMPResult.FEXEvents:
        code = FEX_event.EventCode
        try:
            msg = FEX_event.EventMsg
        except AttributeError:
            msg = ''
        events.append(dict(code=code, msg=msg))
    return cbte_nro, cbte_fecha, events

def get_last_id(client, token, sign, cuit):
    "Recupera el ultimo ID y su fecha"
    response = client.FEXGetLast_ID(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit)},
        ) 

    if int(response.FEXGetLast_IDResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetLast_IDResult.FEXErr)

    result = response.FEXGetLast_IDResult.FEXResultGet    
    id = int(result.Id)
    events = []
    for FEX_event in response.FEXGetLast_IDResult.FEXEvents:
        code = FEX_event.EventCode
        try:
            msg = FEX_event.EventMsg
        except AttributeError:
            msg = ''
        events.append(dict(code=code, msg=msg))
    return id, events


def authorize(client, token, sign, cuit, id, factura):
    "Autorizador: recibe la factura como un dict, devuelve auth y events"
    
    # Información de la autenticación
    auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}
    # Información de la factura de ingreso
    cmp={"Id": id,}
    cmp.update(factura)

    # llamo al webservice para autorizar la factura
    response = client.FEXAuthorize(Auth=auth, Cmp=cmp)

    # hubo error?
    if int(response.FEXAuthorizeResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXAuthorizeResult.FEXErr)

    # extraigo la respuesta (auth y eventos)
    result = response.FEXAuthorizeResult.FEXResultAuth
    auth = dict(id=int(result.Id), cuit=int(result.Cuit), cae=str(result.Cae), 
               fch_cbte=str(result.Fch_cbte), fch_venc_cae=str(result.Fch_venc_Cae),
               resultado=str(result.Resultado), cbte_nro=str(result.Cbte_nro), 
               reproceso=str(result.Reproceso), obs=str(result.Motivos_Obs))
    events = []
    for FEX_event in response.FEXAuthorizeResult.FEXEvents:
        code = FEX_event.EventCode
        try:
            msg = FEX_event.EventMsg
        except AttributeError:
            msg = ''
        events.append(dict(code=code, msg=msg))

    return auth, events

def get_cmp(client, token, sign, cuit, tipo_cbte, punto_vta, cbte_nro):
    "Recupera los datos completos de un comprobante ya autorizado"
    response = client.FEXGetCMP(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit)},
        Cmp={"Tipo_cbte": tipo_cbte,
             "Punto_vta": punto_vta, "Cbte_nro": cbte_nro}) 

    if int(response.FEXGetCMPResult.FEXErr.ErrCode) != 0:
        raise FEXError(response.FEXGetCMPResult.FEXErr)

    result = response.FEXGetCMPResult.FEXResultGet    
    ##print result.Id
    cbt = dict(cuit=int(result.Cuit_pais_cliente), cae=str(result.Cae), 
               fch_cbte=str(result.Fecha_cbte), 
               fch_venc_cae=str(result.Fch_venc_Cae),
               imp_total=str(result.Imp_total),
               obs=str(result.Obs))
    events = []
    for FEX_event in response.FEXGetCMPResult.FEXEvents:
        code = FEX_event.EventCode
        try:
            msg = FEX_event.EventMsg
        except AttributeError:
            msg = ''
        events.append(dict(code=code, msg=msg))
    return cbt, events


   
# Clases para facilitar la autorización de facturas

class FacturaEX:
    "Factura Electrónica Exportación"
        # valores por defecto del encabezado de la factura
    tipo_cbte = 19; punto_vta = 1; cbte_nro = 0; fecha_cbte = None
    imp_total = 0.0
    tipo_expo = 1; permiso_existente = 1
    dst_cmp = None; 
    cliente = cuit_pais_cliente = domicilio_cliente = id_impositivo = ""
    moneda_id = "PES"; moneda_ctz = 1.0
    obs_comerciales = obs = forma_pago = incoterms = ""
    idioma_cbte = 7
    items = None

    def __init__(self,**kwargs):
        self.items = []
        self.permisos = []
        self.cmps_asoc = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def add_item(self, item, calcular=True):
        self.items.append(item)
        if calcular:
            self.imp_total += item.imp_total

    def add_permiso(self, permiso):
        self.permisos.append(permiso)
    
    def add_cmp_asoc(self, cmp_asoc):
        self.cmps_asoc.append(cmp_asoc)

    def to_dict(self, completo=False):
        "Convierte el objeto factura en un diccionario serializable por xml"
        dic = {
            'Fecha_cbte': self.fecha_cbte,
            'Tipo_cbte': self.tipo_cbte,
            'Punto_vta': self.punto_vta,
            'Cbte_nro': self.cbte_nro,
            'Tipo_expo': self.tipo_expo,
            'Permiso_existente': self.permiso_existente,
            'Dst_cmp': self.dst_cmp,
            'Cliente': self.cliente,
            'Cuit_pais_cliente': self.cuit_pais_cliente,
            'Domicilio_cliente': self.domicilio_cliente,
            'Id_impositivo': self.id_impositivo,
            'Moneda_Id': self.moneda_id,
            'Moneda_ctz': self.moneda_ctz,
            'Obs_comerciales': self.obs_comerciales,
            'Imp_total': self.imp_total,
            'Obs': self.obs,
            'Forma_pago': self.forma_pago,
            'Incoterms': self.incoterms,
            'Idioma_cbte': self.idioma_cbte,
            'Items': [item.to_dict() for item in self.items],
            }
        if self.permisos:
            dic['Permisos'] = [permiso.to_dict() for permiso in self.permisos]
        if self.cmps_asoc:    
            dic['Cmps_asoc'] = [cmp.to_dict() for cmp in self.cmps_asoc]
        return dic


class ItemFEX:
    "Item de Factura Electrónica Exportación"
    # valores por defecto:
    pro_codigo = ""
    pro_ds = ""
    pro_qty = 0.0
    pro_umed = 1
    pro_precio_uni = 0.0
    imp_total = 0.0

    def __init__(self, codigo="", ds="", qty=1, umed=7, precio=0.00, imp_total=0.00, **kwargs):
        "Constructor" 
        self.pro_codigo = codigo
        self.pro_ds = ds
        self.pro_qty = qty
        self.pro_umed = umed
        self.pro_precio_uni = precio
        self.imp_total = imp_total or (precio*qty)

    def to_dict(self):
        "Convierte el objeto item en un diccionario serializable por xml"
        return {
           'Item': {
             'Pro_codigo': self.pro_codigo,
             'Pro_ds': self.pro_ds,
             'Pro_qty': self.pro_qty,
             'Pro_umed': self.pro_umed,
             'Pro_precio_uni': self.pro_precio_uni,
             'Pro_total_item': self.imp_total}
           }

class PermisoFEX:
    "Permiso de Factura Electrónica Exportación"
    # valores por defecto:
    id_permiso = ""
    dst_merc = 0

    def __init__(self, id_permiso="", dst_merc="",  **kwargs):
        "Constructor" 
        self.id_permiso = id_permiso
        self.dst_merc = dst_merc

    def to_dict(self):
        "Convierte el objeto permiso en un diccionario serializable por xml"
        return {
           'Permiso': {
             'Id_permiso': self.id_permiso,
             'Dst_merc': self.dst_merc,}
           }

class CmpAsocFEX:
    "Comprobante Asociado de Factura Electrónica Exportación"
    # valores por defecto:
    tipo = 0
    punto_vta = 0
    nro = 0

    def __init__(self, cbte_tipo=0, cbte_punto_vta=0, cbte_nro=0, **kwargs):
        "Constructor" 
        self.tipo = cbte_tipo
        self.punto_vta = cbte_punto_vta
        self.nro = cbte_nro
        
    def to_dict(self):
        "Convierte el objeto permiso en un diccionario serializable por xml"
        return {
           'Cmp_asoc': {
             'CBte_tipo': self.tipo,
             'Cbte_punto_vta': self.punto_vta,
             'Cbte_nro': self.nro,}
           }

def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    url = len(sys.argv)>2 and sys.argv[2].startswith("http") and sys.argv[2] or WSFEXURL

    # cliente soap del web service
    client = SoapClient(url, 
        action = SOAP_ACTION, 
        namespace = SOAP_NS,
        trace = "--trace" in sys.argv)

    # obteniendo el TA
    TA = "TA.xml"
    if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsfex")
        cms = wsaa.sign_tra(tra,"reingart.crt","reingart.key")
        ta_string = wsaa.call_wsaa(cms)
        open("TA.xml","w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    # fin TA

    CUIT = len(sys.argv)>1 and sys.argv[1] or "20267565393"

    if "--dummy" in sys.argv:
        print dummy(client)
    
    # Recuperar parámetros:
    if "--params" in sys.argv:
        import codecs, locale
        sys.stdout = codecs.getwriter('latin1')(sys.stdout); 
    
        print "=== Monedas ==="
        monedas = get_param_mon(client, token, sign, CUIT)    
        for m in monedas:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % m
        monedas = dict([(m['id'],m['ds']) for m in monedas])
        
        print "=== Tipos Comprobante ==="
        cbtes = get_param_tipo_cbte(client, token, sign, CUIT)
        for c in cbtes:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % c
        comprobantes =  dict([(c['id'],c['ds']) for c in cbtes])

        print u"=== Tipos Exportación ==="
        tipos = get_param_tipo_expo(client, token, sign, CUIT)
        for t in tipos:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % t
        tipos_expo = dict([(t['id'],t['ds']) for t in tipos])

        print "=== Idiomas ==="
        tipos = get_param_idiomas(client, token, sign, CUIT)
        for t in tipos:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % t
        idiomas = dict([(t['id'],t['ds']) for t in tipos])
           
        print "=== Unidades de medida ==="
        umedidas = get_param_umed(client, token, sign, CUIT)    
        for u in umedidas:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % u
        umeds = dict([(u['id'],u['ds']) for u in umedidas])

        print "=== INCOTERMs ==="
        incoterms = get_param_incoterms(client, token, sign, CUIT)
        for i in incoterms:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % i
        incoterms = dict([(t['id'],t['ds']) for t in incoterms])

        print "=== Pais Destino ==="
        pais = get_param_dst_pais(client, token, sign, CUIT)    
        for p in pais:
            print "||%(codigo)s||%(ds)s||" % p
        paises = dict([(p['codigo'],p['ds']) for p in pais])

        print "=== CUIT Pais Destino ==="
        pais = get_param_dst_cuit(client, token, sign, CUIT)    
        for p in pais:
            print "||%(cuit)s||%(ds)s||" % p
        cuits = dict([(p['cuit'],p['ds']) for p in pais])

        ctz = get_param_ctz(client, token, sign, CUIT, 'DOL')
        print ctz
        
        print get_param_pto_venta(client, token, sign, CUIT)
        

    else:
        monedas = {'DOL': u'D\xf3lar Estadounidense', 'PES': u'Pesos Argentinos', '010': u'Pesos Mejicanos', '011': u'Pesos Uruguayos', '012': u'Real', '014': u'Coronas Danesas', '015': u'Coronas Noruegas', '016': u'Coronas Suecas', '019': u'Yens', '018': u'D\xf3lar Canadiense', '033': u'Peso Chileno', '056': u'Forint (Hungr\xeda)', '031': u'Peso Boliviano', '036': u'Sucre Ecuatoriano', '051': u'D\xf3lar de Hong Kong', '034': u'Rand Sudafricano', '053': u'D\xf3lar de Jamaica', '057': u'Baht (Tailandia)', '043': u'Balboas Paname\xf1as', '042': u'Peso Dominicano', '052': u'D\xf3lar de Singapur', '032': u'Peso Colombiano', '035': u'Nuevo Sol Peruano', '061': u'Zloty Polaco', '060': u'Euro', '063': u'Lempira Hondure\xf1a', '062': u'Rupia Hind\xfa', '064': u'Yuan (Rep. Pop. China)', '009': u'Franco Suizo', '025': u'Dinar Yugoslavo', '002': u'D\xf3lar Libre EEUU', '027': u'Dracma Griego', '026': u'D\xf3lar Australiano', '007': u'Florines Holandeses', '023': u'Bol\xedvar Venezolano', '047': u'Riyal Saudita', '046': u'Libra Egipcia', '045': u'Dirham Marroqu\xed', '044': u'C\xf3rdoba Nicarag\xfcense', '029': u'G\xfcaran\xed', '028': u'Flor\xedn (Antillas Holandesas)', '054': u'D\xf3lar de Taiwan', '040': u'Lei Rumano', '024': u'Corona Checa', '030': u'Shekel (Israel)', '021': u'Libra Esterlina', '055': u'Quetzal Guatemalteco', '059': u'Dinar Kuwaiti'}
        comprobantes = {19: u'Facturas de Exportaci\xf3n\n', 20: u'Nota de D\xe9bito por Operaciones con el Exterior\n', 21: u'Nota de Cr\xe9dito por Operaciones con el Exterior\n'}
        tipos_expo = {1: u'Exportaci\xf3n definitiva de Bienes', 2: u'Servicios', 4: u'Otros'}
        idiomas = {1: u'Espa\xf1ol', 2: u'Ingl\xe9s', 3: u'Portugu\xe9s'}
        umeds = {0: u' ', 1: u'kilogramos', 2: u'metros', 3: u'metros cuadrados', 4: u'metros c\xfabicos', 5: u'litros', 6: u'1000 kWh', 7: u'unidades', 8: u'pares', 9: u'docenas', 10: u'quilates', 11: u'millares', 14: u'gramos', 15: u'milimetros', 16: u'mm c\xfabicos', 17: u'kil\xf3metros', 18: u'hectolitros', 20: u'cent\xedmetros', 25: u'jgo. pqt. mazo naipes', 27: u'cm c\xfabicos', 29: u'toneladas', 30: u'dam c\xfabicos', 31: u'hm c\xfabicos', 32: u'km c\xfabicos', 33: u'microgramos', 34: u'nanogramos', 35: u'picogramos', 41: u'miligramos', 47: u'mililitros', 48: u'curie', 49: u'milicurie', 50: u'microcurie', 51: u'uiacthor', 52: u'muiacthor', 53: u'kg base', 54: u'gruesa', 61: u'kg bruto', 62: u'uiactant', 63: u'muiactant', 64: u'uiactig', 65: u'muiactig', 66: u'kg activo', 67: u'gramo activo', 68: u'gramo base', 96: u'packs', 97: u'hormas', 98: u'bonificaci\xf3n', 99: u'otras unidades'}
        incoterms = {'DAF': u'DAF', 'DDP': u'DDP', 'CIF': u'CIF', 'FCA': u'FCA', 'FAS': u'FAS', 'DES': u'DES', 'CPT': u'CPT', 'EXW': u'EXW', 'CIP': u'CIP', 'DDU': u'DDU', 'FOB': u'FOB', 'DEQ': u'DEQ', 'CFR': u'CFR'}

    if "--prueba" in sys.argv:

        # recupero ultimo comprobante y id
        tipo_cbte = 19
        punto_vta = 1
        cbte_nro, cbte_fecha, events = get_last_cmp(client, token, sign, CUIT, tipo_cbte, punto_vta)
        id, events = get_last_id(client, token, sign, CUIT)

        print "last_cmp", cbte_nro, cbte_fecha
        print "last_id", id
        
        cbte_nro +=1
        id += 1

        if False: # prueba a mano
            f = {
                'Id': id,
                'Fecha_cbte': date('Ymd'),
                'Tipo_cbte': tipo_cbte, 
                'Punto_vta': punto_vta, 
                'Cbte_nro': cbte_nro,
                'Tipo_expo': 1,
                'Permiso_existente': 'N',
                'Dst_cmp': 225,
                'Cliente': 'Jose Yorugua',
                'Cuit_pais_cliente': 50000000016,
                'Domicilio_cliente': 'Montevideo, UY',
                'Id_impositivo': 'RUC 123123',
                'Moneda_Id': 'DOL',
                'Moneda_ctz': 3.85,
                'Obs_comerciales': 'Observaciones comerciales',
                'Imp_total': 60.00,
                'Obs': 'Observaciones',
                'Forma_pago': 'Taka taka',
                'Incoterms': 'FOB',
                'Idioma_cbte': 2,
                'Items': [{
                   'Item': {
                     'Pro_codigo': "kbd",
                     'Pro_ds': "Keyboard (uruguayan layout)",
                     'Pro_qty': 1,
                     'Pro_umed': 7,
                     'Pro_precio_uni': 50.000049,
                     'Pro_total_item': 50.000049}
                   },{
                   'Item': {
                     'Pro_codigo': "mice",
                     'Pro_ds': "Optical Mouse",
                     'Pro_qty': 1,
                     'Pro_umed': 7,
                     'Pro_precio_uni': 10.50,
                     'Pro_total_item': 10.50}
                   }]
                }
        else:
            # creo una factura de prueba
            f = FacturaEX()
            f.punto_vta = punto_vta
            f.cbte_nro = cbte_nro
            f.fecha_cbte = date('Ymd')
            f.tipo_expo = 1
            f.permiso_existente = 'S'
            f.dst_cmp = 203
            f.cliente = 'Joao Da Silva'
            f.cuit_pais_cliente = 50000000016
            f.domicilio_cliente = 'Rua 76 km 34.5 Alagoas'
            f.id_impositivo = 'PJ54482221-l'
            f.moneda_id = '012'
            f.moneda_ctz = 0.5
            f.obs_comerciales = 'Observaciones comerciales'
            f.obs = 'Sin observaciones'
            f.forma_pago = '30 dias'
            f.incoterms = 'FOB'
            f.idioma_cbte = 1
            # agrego los items
            it = ItemFEX(codigo='PRO1', ds=u'Producto Tipo 1 Exportacion MERCOSUR ISO 9001', 
                         qty=1, precio=125)
            f.add_item(it)
            it = ItemFEX(codigo='PRO2', ds=u'Producto Tipo 2 Exportacion MERCOSUR ISO 9001', 
                         qty=1, precio=125)
            f.add_item(it)
            permiso = PermisoFEX(id_permiso="99999AAXX999999A",dst_merc=225)
            f.add_permiso(permiso)
            permiso = PermisoFEX(id_permiso="99999AAXX999999B",dst_merc=225)
            f.add_permiso(permiso)
            if f.tipo_cbte!=19: 
                cmp_asoc = CmpAsocFEX(tipo=19, punto_vta=2, cbte_nro=1)
                f.add_cmp_asoc(cmp_asoc)
                cmp_asoc = CmpAsocFEX(tipo=19, punto_vta=2, cbte_nro=2)
                f.add_cmp_asoc(cmp_asoc)
            f = f.to_dict()
            print f

        try:
            auth, events = authorize(client, token, sign, CUIT, id=id, factura=f)
        except FEXError, fex:
            print "FEX_error:", fex.msg
            print client.xml_response
            sys.exit(1)
        cae = auth['cae']
        print "auth", auth
        print "events", events
        try:
            auth, events = get_cmp(client, token, sign, CUIT, tipo_cbte, punto_vta, cbte_nro)
        except:
            print client.xml_response
            sys.exit(1)
        print "get_cmp: auth", auth
        print "get_cmp: events", events        

    if '--ult' in sys.argv:
        print "Consultar ultimo numero:"
        tipo_cbte = int(raw_input("Tipo de comprobante: "))
        punto_vta = int(raw_input("Punto de venta: "))
        try:
            ult_cbte, fecha, events = get_last_cmp(client, token, sign, CUIT, tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            print "Fecha: ", fecha
        finally:
            print client.xml_request
            print client.xml_response

    if '--get' in sys.argv:
        print "Recuperar comprobante:"
        tipo_cbte = int(raw_input("Tipo de comprobante: "))
        punto_vta = int(raw_input("Punto de venta: "))
        cbte_nro = int(raw_input("Numero de comprobante: "))
        try:
            cbt, events = get_cmp(client, token, sign, CUIT, tipo_cbte, punto_vta, cbte_nro)
            for k,v in cbt.items():
                print "%s = %s" % (k, v)
        finally:
            print client.xml_request
            print client.xml_response

    sys.exit(0)


if __name__ == '__main__':
    main()
