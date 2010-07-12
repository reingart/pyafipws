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
electrónico del web service WSBFE de AFIP (Bono Fiscal Electrónico)
"""

__author__ = "Mariano Reingart <mariano@nsis.com.ar>"
__copyright__ = "Copyright (C) 2009 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.13"

import sys
from php import date, SimpleXMLElement, SoapClient

WSBFEURL = "https://wswhomo.afip.gov.ar/wsbfe/service.asmx"
##WSBFEURL = "https://servicios1.afip.gov.ar/wsbfe/service.asmx"
SOAP_ACTION = 'http://ar.gov.afip.dif.bfe/'
SOAP_NS = "http://ar.gov.afip.dif.bfe/"

class BFEError(RuntimeError):
    "Clase para informar errores del WSBFE"
    def __init__(self, bfeerror):
        self.code = str(bfeerror.ErrCode)
        self.msg = unicode(bfeerror.ErrMsg)

    def __unicode__(self):
        return u"BFEError %s: %s" % (self.code, self.msg)

def get_param_mon(client, token, sign, cuit):
    "Recuperador de valores referenciales de codigos de Moneda"
    response = client.BFEGetPARAM_MON(
        auth={"Token": token, "Sign": sign, "Cuit":long(cuit)})
    
    if int(response.BFEGetPARAM_MONResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetPARAM_MONResult.BFEErr)

    mons = [] # monedas
    for m in response.BFEGetPARAM_MONResult.BFEResultGet.ClsBFEResponse_Mon:
        mon = {'id': str(m.Mon_Id), 'ds': unicode(m.Mon_Ds), 
               'vig_desde': str(m.Mon_vig_desde), 
               'vig_hasta': str(m.Mon_vig_hasta)}
        mons.append(mon)
    return mons
 
def get_param_ncm(client, token, sign, cuit):
    "Recuperador de valores referenciales de códigos de productos"
    response = client.BFEGetPARAM_NCM(
        Auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.BFEGetPARAM_NCMResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetPARAM_NCMResult.BFEErr)

    ncms = [] # productos
    for n in response.BFEGetPARAM_NCMResult.BFEResultGet.ClsBFEResponse_NCM:
        ncm = {'codigo': str(n.NCM_Codigo), 'ds': unicode(n.NCM_Ds), 
               'nota': unicode(n.NCM_Nota), 
               'vig_desde': str(n.NCM_vig_desde), 
               'vig_hasta': str(n.NCM_vig_hasta)}
        ncms.append(ncm)
    return ncms
 
def get_param_tipo_cbte(client, token, sign, cuit):
    "Recuperador de valores referenciales de códigos de Tipos de comprobante"
    response = client.BFEGetPARAM_Tipo_Cbte(
        auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.BFEGetPARAM_Tipo_CbteResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetPARAM_Tipo_CbteResult.BFEErr)

    cbtes = [] # tipos de comprobantes
    for c in response.BFEGetPARAM_Tipo_CbteResult.BFEResultGet.ClsBFEResponse_Tipo_Cbte:
        cbte = {'id': int(c.Cbte_Id), 'ds': unicode(c.Cbte_Ds), 
                'vig_desde': str(c.Cbte_vig_desde), 
                'vig_hasta': str(c.Cbte_vig_hasta)}
        cbtes.append(cbte)
    return cbtes

def get_param_tipo_iva(client, token, sign, cuit):
    "Recuperador de valores referenciales de códigos de IVA"
    response = client.BFEGetPARAM_Tipo_IVA(
        auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.BFEGetPARAM_Tipo_IVAResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetPARAM_Tipo_IVAResult.BFEErr)

    ivas= [] # tipos de iva
    for i in response.BFEGetPARAM_Tipo_IVAResult.BFEResultGet.ClsBFEResponse_Tipo_IVA:
        iva = {'id': int(i.IVA_Id), 'ds': unicode(i.IVA_Ds), 
                'vig_desde': str(i.IVA_vig_desde), 
                'vig_hasta': str(i.IVA_vig_hasta)}
        ivas.append(iva)
    return ivas

def get_param_umed(client, token, sign, cuit):
    "Recuperador de valores referenciales de Unidades de Medidas"
    response = client.BFEGetPARAM_UMed(
        auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.BFEGetPARAM_UMedResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetPARAM_UMedResult.BFEErr)

    umeds = [] # unidades de medida
    for u in response.BFEGetPARAM_UMedResult.BFEResultGet.ClsBFEResponse_UMed:
        umed = {'id': int(u.Umed_Id), 'ds': unicode(u.Umed_Ds), 
                'vig_desde': str(u.Umed_vig_desde), 
                'vig_hasta': str(u.Umed_vig_hasta)}
        umeds.append(umed)
    return umeds

def get_param_zonas(client, token, sign, cuit):
    "Recuperador de valores referenciales de Zonas"
    response = client.BFEGetPARAM_Zonas(
        auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}) 
    
    if int(response.BFEGetPARAM_ZonasResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetPARAM_ZonasResult.BFEErr)

    zonas = [] # unidades de medida
    for z in response.BFEGetPARAM_ZonasResult.BFEResultGet.ClsBFEResponse_Zon:
        zon = {'id': int(z.Zon_Id), 'ds': unicode(z.Zon_Ds), 
                'vig_desde': str(z.Zon_vig_desde), 
                'vig_hasta': str(z.Zon_vig_hasta)}
        zonas.append(zon)
    return zonas

def authorize(client, token, sign, cuit, id, factura):
    "Autorizador: recibe la factura como un dict, devuelve auth y events"
    
    # Información de la autenticación
    auth= {"Token": token, "Sign": sign, "Cuit": long(cuit)}
    # Información de la factura de ingreso
    cmp={"Id": id,}
    cmp.update(factura)

    # llamo al webservice para autorizar la factura
    response = client.BFEAuthorize(Auth=auth, Cmp=cmp)

    # hubo error?
    if int(response.BFEAuthorizeResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEAuthorizeResult.BFEErr)

    # extraigo la respuesta (auth y eventos)
    result = response.BFEAuthorizeResult.BFEResultAuth
    auth = dict(id=int(result.Id), cuit=int(result.Cuit), cae=str(result.Cae), 
               fch_cbte=str(result.Fch_cbte), resultado=str(result.Resultado),
               fch_venc_cae=str(result.Fch_venc_Cae),
               reproceso=str(result.Reproceso), obs=str(result.Obs))
    events = []
    for bfe_event in response.BFEAuthorizeResult.BFEEvents:
        events.append(dict(code=bfe_event.EventCode, msg=bfe_event.EventMsg))

    return auth, events

def get_cmp(client, token, sign, cuit, tipo_cbte, punto_vta, cbte_nro):
    "Recupera los datos completos de un comprobante ya autorizado"
    response = client.BFEGetCMP(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit)},
        Cmp={"Tipo_cbte": tipo_cbte,
             "Punto_vta": punto_vta, "Cbte_nro": cbte_nro}) 

    if int(response.BFEGetCMPResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetCMPResult.BFEErr)

    result = response.BFEGetCMPResult.BFEResultGet    
    ##print result.Id
    cbt = dict(cuit=int(result.Cuit), cae=str(result.Cae), 
               fch_cbte=str(result.Fecha_cbte_orig), 
               fch_cae=str(result.Fecha_cbte_cae),
               fch_venc_cae=str(result.Fch_venc_Cae),
               imp_total=str(result.Imp_total),
               imp_neto=str(result.Imp_neto),
               impto_liq=str(result.Impto_liq),
               obs=str(result.Obs))
    events = []
    for bfe_event in response.BFEGetCMPResult.BFEEvents:
        events.append(dict(code=bfe_event.EventCode, msg=bfe_event.EventMsg))
    return cbt, events

def get_last_cmp(client, token, sign, cuit, tipo_cbte, punto_vta):
    "Recupera el ultimos comprobante autorizado"
    response = client.BFEGetLast_CMP(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit),
              "Tipo_cbte": tipo_cbte,
              "Pto_venta": punto_vta}) 

    if int(response.BFEGetLast_CMPResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetLast_CMPResult.BFEErr)

    result = response.BFEGetLast_CMPResult.BFEResult_LastCMP    
    cbte_nro = int(result.Cbte_nro)
    try:
        cbte_fecha = str(result.Cbte_fecha)
    except AttributeError:
        cbte_fecha = ""
        
    events = []
    for bfe_event in response.BFEGetLast_CMPResult.BFEEvents:
        events.append(dict(code=bfe_event.EventCode, msg=bfe_event.EventMsg))
    return cbte_nro, cbte_fecha, events

def get_last_id(client, token, sign, cuit):
    "Recupera el ultimo ID y su fecha"
    response = client.BFEGetLast_ID(
        Auth={"Token": token, "Sign": sign, "Cuit": long(cuit)},
        ) 

    if int(response.BFEGetLast_IDResult.BFEErr.ErrCode) != 0:
        raise BFEError(response.BFEGetLast_IDResult.BFEErr)

    result = response.BFEGetLast_IDResult.BFEResultGet    
    id = int(result.Id)
    events = []
    for bfe_event in response.BFEGetLast_IDResult.BFEEvents:
        events.append(dict(code=bfe_event.EventCode, msg=bfe_event.EventMsg))
    return id, events

def dummy(client):
    "Metodo dummy para verificacion de funcionamiento"
    response = client.BFEDummy()
    result = response.BFEDummyResult
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
   
# Clases para facilitar la autorización de facturas

class FacturaBF:
    "Factura Bono Fiscal"
    # valores por defecto del encabezado de la factura
    tipo_doc = 80; nro_doc = 23111111113
    zona = 0; tipo_cbte = 1; punto_vta = 1; cbte_nro = 0; fecha_cbte = None
    imp_total = 0.0; imp_neto = 0.0; impto_liq = 0.0
    imp_tot_conc = 0.0; impto_liq_rni = 0.00; imp_op_ex = 0.00 
    imp_perc = 0.00; imp_iibb = 0.00; imp_perc_mun = 0.00; imp_internos=0.00
    imp_moneda_id = 0; imp_moneda_ctz = 1.0
    # datos del cliente (para impresion)
    nombre = ""
    domicilio = ""; localidad = ""; provincia = ""
    email = ""; telefono = ""; observaciones = ""
    categoria = ""
    items = None

    def __init__(self,**kwargs):
        self.items = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def add_item(self, item, calc=True):
        self.items.append(item)
        total = item.imp_total
        if not calc:
            return
        
        if item.iva_id==1: #'No gravado'
            self.imp_tot_conc += total
        elif item.iva_id==2: # exento
            self.imp_op_ex += total
        else:
            self.imp_neto += total
            iva = total * {3:0, 4:10.5, 5:21, 6:27}[item.iva_id] / 100
            self.impto_liq += iva
            total += iva
        self.imp_total += total
    
    def to_dict(self, completo=False):
        "Convierte el objeto factura en un diccionario serializable por xml"
        dic = {
            'Tipo_doc': self.tipo_doc, 'Nro_doc':  self.nro_doc, 
            'Zona': self.zona, 
            'Tipo_cbte': self.tipo_cbte, 'Fecha_cbte': self.fecha_cbte,
            'Punto_vta': self.punto_vta, 'Cbte_nro': self.cbte_nro,
            'Imp_total': self.imp_total, 'Imp_tot_conc': self.imp_tot_conc, 
            'Imp_neto': self.imp_neto, 'Impto_liq': self.impto_liq, 
            'Impto_liq_rni': self.impto_liq_rni, 'Imp_op_ex': self.imp_op_ex,
            'Imp_perc': self.imp_perc, 'Imp_iibb': self.imp_iibb, 
            'Imp_perc_mun': self.imp_perc_mun, 'Imp_internos': self.imp_internos,
            'Imp_moneda_Id': self.imp_moneda_id, 'Imp_moneda_ctz': self.imp_moneda_ctz,
            'Items': [{'Item': item.to_dict()} for item in self.items],
            }
        if completo:
            dic.update({'nombre': self.nombre, 'categoria': self.categoria,
                        'domicilio': self.domicilio, 'localidad': self.localidad, 'provincia': self.provincia,
                        'email': self.email, 'telefono': self.telefono, 
                        'observaciones': self.observaciones,
                        })
        return dic


class ItemBF:
    "Item de Factura Bono Fiscal"
    # valores por defecto:
    pro_codigo_ncm = ""
    pro_codigo_sec = ""
    pro_ds = ""
    pro_qty = 0.0
    pro_umed = 1
    pro_precio_uni = 0.0
    imp_bonif = 0.0
    imp_total = 0.0
    iva_id = 5

    def __init__(self, ncm="", sec="", ds="", qty=1, umed=7, precio=0.00, bonif=0.00, iva_id=5, imp_total=0.00, **kwargs):
        "Constructor" #TODO: revisar cálculo de iva y totales
        self.pro_codigo_ncm = ncm
        self.pro_codigo_sec = sec
        self.pro_ds = ds
        self.pro_qty = qty
        self.pro_umed = umed
        self.pro_precio_uni = precio
        self.imp_bonif = bonif
        self.imp_total = imp_total or (precio*qty - bonif)
        self.iva_id = iva_id

    def to_dict(self):
        "Convierte el objeto item en un diccionario serializable por xml"
        return {
            "Pro_codigo_ncm": self.pro_codigo_ncm,
            "Pro_codigo_sec": self.pro_codigo_sec,
            "Pro_ds": self.pro_ds,
            "Pro_qty": self.pro_qty,
            "Pro_umed": self.pro_umed,
            "Pro_precio_uni": self.pro_precio_uni,
            "Imp_bonif": self.imp_bonif,
            "Imp_total": self.imp_total,
            "Iva_id": self.iva_id,
            }
    
def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time
    import sys, codecs, locale
    if sys.stdout.encoding is None:
        sys.stdout = codecs.getwriter("latin1")(sys.stdout,"replace");

    url = len(sys.argv)>2 and sys.argv[2].startswith("http") and sys.argv[2] or WSBFEURL

    # cliente soap del web service
    client = SoapClient(url, 
        action = SOAP_ACTION, 
        namespace = SOAP_NS,
        trace = "--trace" in sys.argv)

    # obteniendo el TA
    TA = "TA.xml"
    if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsbfe")
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
    
        print "=== Monedas ==="
        monedas = get_param_mon(client, token, sign, CUIT)    
        for m in monedas:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % m
        monedas = dict([(m['id'],m['ds']) for m in monedas])
        
        print "=== NCM ==="
        productos = get_param_ncm(client, token, sign, CUIT)
        for p in productos:
            print "||%(codigo)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % p
        productos = dict([(m['codigo'],m['ds']) for m in productos])
        
        print "=== Tipos de Comprobante ==="
        cbtes = get_param_tipo_cbte(client, token, sign, CUIT)
        for c in cbtes:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % c
        cbtes = dict([(c['id'],c['ds']) for c in cbtes])
        
        print "=== Tipos de IVA ==="
        ivas = get_param_tipo_iva(client, token, sign, CUIT)
        for i in ivas:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % i
        ivas = dict([(i['id'],i['ds']) for i in ivas])

        print "=== Unidades de Medida ==="
        umedidas = get_param_umed(client, token, sign, CUIT)    
        for u in umedidas:
            print "||%(id)s||%(ds)s||%(vig_desde)s||%(vig_hasta)s||" % u
        umeds = dict([(u['id'],u['ds']) for u in umedidas])

        ##zonas = get_param_zonas(client, token, sign, CUIT)    
        ##print dict([(z['id'],z['ds']) for z in zonas])

    else:

        monedas = {'DOL': u'D\xf3lar Estadounidense', 'PES': u'Pesos Argentinos', '010': u'Pesos Mejicanos', '011': u'Pesos Uruguayos', '012': u'Real', '014': u'Coronas Danesas', '015': u'Coronas Noruegas', '016': u'Coronas Suecas', '019': u'Yens', '018': u'D\xf3lar Canadiense', '033': u'Peso Chileno', '056': u'Forint (Hungr\xeda)', '031': u'Peso Boliviano', '036': u'Sucre Ecuatoriano', '051': u'D\xf3lar de Hong Kong', '034': u'Rand Sudafricano', '053': u'D\xf3lar de Jamaica', '057': u'Baht (Tailandia)', '043': u'Balboas Paname\xf1as', '042': u'Peso Dominicano', '052': u'D\xf3lar de Singapur', '032': u'Peso Colombiano', '035': u'Nuevo Sol Peruano', '061': u'Zloty Polaco', '060': u'Euro', '063': u'Lempira Hondure\xf1a', '062': u'Rupia Hind\xfa', '064': u'Yuan (Rep. Pop. China)', '025': u'Dinar Yugoslavo', '002': u'D\xf3lar Libre EEUU', '027': u'Dracma Griego', '026': u'D\xf3lar Australiano', '007': u'Florines Holandeses', '023': u'Bol\xedvar Venezolano', '047': u'Riyal Saudita', '046': u'Libra Egipcia', '045': u'Dirham Marroqu\xed', '044': u'C\xf3rdoba Nicarag\xfcense', '029': u'G\xfcaran\xed', '028': u'Flor\xedn (Antillas Holandesas)', '054': u'D\xf3lar de Taiwan', '040': u'Lei Rumano', '024': u'Corona Checa', '030': u'Shekel (Israel)', '021': u'Libra Esterlina', '055': u'Quetzal Guatemalteco', '059': u'Dinar Kuwaiti'}
        comprobantes = {1: u'Factura A', 2: u'Nota de D\xe9bito A', 3: u'Nota de Cr\xe9dito A', 4: u'Recibo A', 6: u'Factura B', 7: u'Nota de D\xe9bito B', 8: u'Nota de Cr\xe9dito B', 9: u'Recibo B', 11: u'Factura C', 12: u'Nota de D\xe9bito C', 13: u'Nota de Cr\xe9dito C', 15: u'Recibo C', 51: u'Factura M', 52: u'Nota de D\xe9bito M', 53: u'Nota de Cr\xe9dito M', 54: u'Recibo M'}
        ivas = {1: u'No gravado', 2: u'Exento', 3: u'0%', 4: u'10.5%', 5: u'21%', 6: u'27%'}
        umeds = {1: u'kilogramos', 2: u'metros', 3: u'metros cuadrados', 4: u'metros c\xfabicos', 5: u'litros', 6: u'1000 kWh', 7: u'unidades', 8: u'pares', 9: u'docenas', 10: u'quilates', 11: u'millares', 14: u'gramos', 15: u'milimetros', 16: u'mm c\xfabicos', 17: u'kil\xf3metros', 18: u'hectolitros', 20: u'cent\xedmetros', 25: u'jgo. pqt. mazo naipes', 27: u'cm c\xfabicos', 29: u'toneladas', 30: u'dam c\xfabicos', 31: u'hm c\xfabicos', 32: u'km c\xfabicos', 33: u'microgramos', 34: u'nanogramos', 35: u'picogramos', 41: u'miligramos', 47: u'mililitros', 48: u'curie', 49: u'milicurie', 50: u'microcurie', 51: u'uiacthor', 52: u'muiacthor', 53: u'kg base', 54: u'gruesa', 61: u'kg bruto', 62: u'uiactant', 63: u'muiactant', 64: u'uiactig', 65: u'muiactig', 66: u'kg activo', 67: u'gramo activo', 68: u'gramo base', 96: u'packs', 97: u'hormas', 98: u'bonificaci\xf2n', 99: u'otras unidades'}

    # ncm=7308.10.00, 7308.20.00 

    if "--prueba" in sys.argv:

        # recupero ultimo comprobante y id
        tipo_cbte = 1
        punto_vta = 5
        cbte_nro, cbte_fecha, events = get_last_cmp(client, token, sign, CUIT, tipo_cbte, punto_vta)
        id, events = get_last_id(client, token, sign, CUIT)    
        
        #cbte_nro = 1
        #id = 1002 # 99000000000098

        # creo una factura de prueba
        f = FacturaBF()
        f.punto_vta = punto_vta
        f.cbte_nro = cbte_nro+1
        f.imp_moneda_id = '010'
        f.fecha_cbte = date('Ymd')
        it = ItemBF(ncm='7308.10.00', sec='', ds=u'prueba Anafe económico', qty=2.0, precio=100.0, bonif=0.0, iva_id=5)
        f.add_item(it)
        it = ItemBF(ncm='7308.20.00', sec='', ds='prueba 2', qty=4.0, precio=50.0, bonif=10.0, iva_id=5)
        f.add_item(it)
        print f.to_dict()

        try:
            # autorizar...
            auth, events = authorize(client, token, sign, CUIT, id=id+1, factura=f.to_dict())
            cae = auth['cae']
            print "auth", auth
            print "events", events
            auth, events = get_cmp(client, token, sign, CUIT, f.tipo_cbte, f.punto_vta, f.cbte_nro)
            print "get_cmp: auth", auth
            print "get_cmp: events", events        
        except:
            raise
            ##l= client.xml_request.splitlines()
            ##print l[4][1150:1200]
            ##import pdb; pdb.set_trace()

    sys.exit(0)

if __name__ == '__main__':
    main()
