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

"Módulo para manejo de archivos XML simil Facturador-Plus (RCEL)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"

from pysimplesoap.simplexml import SimpleXMLElement
from decimal import Decimal

# Formato de entrada/salida similar al Facturador Plus, con agregados
XML_FORMAT = {
    'comprobantes': [{
        'comprobante': {
            'tipo': int,
            'ptovta': int,
            'numero': int,
            'cuitemisor': long,
            'fechaemision': str,
            'idioma': int,
            'concepto': int,
            'moneda': str,
            'tipocambio': Decimal,
            'tipodocreceptor': int,
            'nrodocreceptor': long,
            'receptor': str,
            'domicilioreceptor': str,
            'localidadreceptor': str,
            'provinciareceptor': str,
            'telefonoreceptor': str,
            'idimpositivoreceptor': str,
            'emailgeneral': str,
            
            'numero_cliente': str,
            'numero_orden_compra': str,
            'condicion_frente_iva': str,
            'numero_cotizacion': str,
            'numero_remito': str,

            'ape': str,
            'incoterms': str,
            'detalleincoterms': str,
            'destinocmp': int,
            
            'importetotal': Decimal,
            
            'importetotalconcepto': Decimal,
            'importeneto': Decimal,
            'importeiva': Decimal,
            'importetributos': Decimal,
            'importeopex': Decimal,

            'formaspago': [{
                'formapago': {
                    'codigo': str,
                    'descripcion': str,
                    }
                }],
            
            'otrosdatoscomerciales': str,
            
            'detalles': [{
                'detalle': {
                    'cod': str,
                    'desc': str,
                    'unimed': str,
                    'cant': float,
                    'preciounit': Decimal,
                    'importe': Decimal,
                    'tasaiva': int,
                    'aliciva': Decimal,
                    'importeiva': Decimal,
                    
                    'ncm': str,
                    'sec': str,
                    'bonificacion': str,
                    'importe': str,
                    
                    #'desctributo': str,
                    #'alictributo': Decimal,
                    #'importetributo': Decimal,
                    
                    'numero_despacho': str,
                    
                    },
                }],
            
            'tributos': [{
                'tributo': {
                    'id': int,
                    'desc': str,
                    'baseimp': Decimal,
                    'alic': Decimal,
                    'importe': Decimal,
                    }
                }],

            'ivas': [{
                'iva': {
                    'id': int,
                    'baseimp': Decimal,
                    'importe': Decimal,
                    },
                }],
            
            'permisosdestinos': [{
                'permisodestino': {
                    'permisoemb': str,
                    'permisoemb': str,
                    'destino': int,
                    },
                }],
                
            'cmpasociados': [{
                'cmpasociado': {
                    'tipoasoc': int,
                    'ptovtaasoc': int,
                    'nroasoc': int,
                    },
                }],
                
            'otrosdatosgenerales': str,

            'fechaservdesde': str,
            'fechaservhasta': str,
            'fechavencpago': str,

            'resultado': str,
            'cae': long,
            'fecha_vto': str, 
            'reproceso': str,
            'motivo': str,
            'errores': str,
            
            'id': str,

            },
        }],
    }

# Mapeo de nombres internos ws vs facturador-plus (encabezado)
MAP_ENC = {
    "tipo_cbte": 'tipo',
    "punto_vta": 'ptovta',
    "cbt_numero": 'numero',
    "cuit": 'cuitemisor',
    "fecha_cbte": 'fechaemision',
    "idioma": 'idioma',
    "concepto": 'concepto',
    "moneda_id": 'moneda',
    "moneda_ctz": 'tipocambio',
    "tipo_doc": 'tipodocreceptor',
    "nro_doc": 'nrodocreceptor',
    "nombre_cliente": 'receptor',
    "domicilio_cliente": 'domicilioreceptor',
    "telefono_cliente": 'telefonoreceptor',
    "localidad_cliente": 'localidadreceptor',
    "provincia_cliente": 'provinciareceptor',
    "id_impositivo": 'idimpositivoreceptor',

    "email": 'emailgeneral',

    'numero_cliente': 'numero_cliente',
    'numero_orden_compra': 'numero_orden_compra',
    'condicion_frente_iva': 'condicion_frente_iva',
    'numero_cotizacion': 'numero_cotizacion',
    'numero_remito': 'numero_remito',

    "imp_total": 'importetotal',
    "imp_tot_conc": 'importetotalconcepto',
    "imp_neto": 'importeneto',
    "imp_iva": 'importeiva',
    "imp_trib": 'importetributos',
    "imp_op_ex": 'importeopex',

    "fecha_serv_desde": 'fechaservdesde',
    "fecha_serv_hasta": 'fechaservhasta',
    "fecha_venc_pago": 'fechavencpago',

    "obs_generales": "otrosdatosgenerales",
    "obs_comerciales": "otrosdatoscomerciales",
    
    "resultado": 'resultado',
    "cae": 'cae',
    "fecha_vto": 'fecha_vto', 
    "reproceso": 'reproceso',
    "motivo": 'motivo',
    #'errores',
    "id": 'id',
    }

# Mapeo de nombres internos ws vs facturador-plus (detalle)
MAP_DET = {
    'codigo': 'cod',
    'ds': 'desc',
    'umed': 'unimed',
    'qty': 'cant',
    'precio': 'preciounit',
    'importe': 'importe',
    'iva_id':'tasaiva',
    'imp_iva': 'importeiva',
    'ncm': 'ncm',
    'sec': 'sec',
    'bonif': 'bonificacion',
    
    'despacho': 'numero_despacho',
    }


# Mapeo de nombres internos ws vs facturador-plus (ivas)
MAP_IVA = {
    'iva_id': 'id',
    'base_imp': 'baseimp',
    'importe': 'importe',
    }

# Mapeo de nombres ws vs facturador-plus (ivas)
MAP_TRIB = {
    'tributo_id': 'id',
    'base_imp': 'baseimp',
    'desc': 'desc',
    'alic': 'alic',
    'importe': 'importe',
    }


# Esqueleto XML básico simil facturador-plus
XML_BASE = """\
<?xml version="1.0" encoding="UTF-8"?>
<comprobantes/>
"""

def mapear(new, old, MAP, swap=False):
    try:
        for k, v in MAP.items():
            if swap:
                k, v = v, k
            new[k] = old.get(v)
        return new
    except:
        print new, old, MAP
        raise

def leer(fn="entrada.xml"):
    "Analiza un archivo XML y devuelve un diccionario"
    xml = open(fn,"rb").read()
    return desserializar(xml)

def desserializar(xml):
    "Analiza un XML y devuelve un diccionario"
    xml = SimpleXMLElement(xml)

    dic = xml.unmarshall(XML_FORMAT, strict=True)
    
    regs = []

    for dic_comprobante in dic['comprobantes']:
        reg = {
            'detalles': [],
            'ivas': [],
            'tributos': [],
            'permisos': [],
            'cmps_asocs': [],
            }
        comp = dic_comprobante['comprobante']
        mapear(reg, comp, MAP_ENC)
        reg['forma_pago']= ''.join([d['formapago']['descripcion'] for d in comp['formaspago']])


        for detalles in comp['detalles']:
            det = detalles['detalle']
            reg['detalles'].append(mapear({}, det, MAP_DET))
            
        for ivas in comp['ivas']:
            iva = ivas['iva']
            reg['ivas'].append(mapear({}, iva, MAP_IVA))

        for tributos in comp['tributos']:
            tributo = tributos['tributo']
            reg['tributos'].append(mapear({}, tributo, MAP_TRIB))

        regs.append(reg)
    return regs

    
def escribir(regs, fn="salida.xml"):
    "Dado una lista de comprobantes (diccionarios), convierte y escribe"
    xml = serializar(regs)
    open(fn, "wb").write(xml)

def serializar(regs):
    "Dado una lista de comprobantes (diccionarios), convierte a xml"
    xml = SimpleXMLElement(XML_BASE)

    comprobantes = []
    for reg in regs:
        dic = {}
        for k, v in MAP_ENC.items():
            dic[v] = reg[k]
                
        dic.update({
                'detalles': [{
                    'detalle': mapear({}, det, MAP_DET, swap=True),
                    } for det in reg['detalles']],                
                'tributos': [{
                    'tributo': mapear({}, trib, MAP_TRIB, swap=True),
                    } for trib in reg['tributos']],
                'ivas': [{
                    'iva': mapear({}, iva, MAP_IVA, swap=True),
                    } for iva in reg['ivas']],
                'formaspago': [{
                'formapago': {
                    'codigo': '',
                    'descripcion': reg['forma_pago'],
                    }}]
                })
        comprobantes.append(dic)

    for comprobante in comprobantes:
        xml.marshall("comprobante", comprobante)
    return xml.as_xml()

# pruebas básicas
if __name__ == '__main__':
    regs = leer("prueba_entrada.xml")
    regs[0]['cae']='1'*15
    import pprint
    pprint.pprint(regs[0])
    escribir(regs, 'prueba_salida.xml')
