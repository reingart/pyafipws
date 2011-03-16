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
    "nombre": 'receptor',
    "domicilio": 'domicilioreceptor',
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

    "resultado": 'resultado',
    "cae": 'cae',
    "fecha_vto": 'fecha_vto', 
    "reproceso": 'reproceso',
    "motivo": 'motivo',
    #'errores',
    }

# Mapeo de nombres internos ws vs facturador-plus (detalle)
MAP_DET = {
    'codigo': 'cod',
    'ds': 'desc',
    'umed': 'unimed',
    'qty': 'cant',
    'precio': 'preciounit',
    'imp_total': 'importe',
    'iva_id':'tasaiva',
    'imp_iva': 'importeiva',
    'ncm': 'ncm',
    'sec': 'sec',
    'bonif': 'bonificacion',
    
    'numero_despacho': 'numero_despacho',
    }


# Mapeo de nombres internos ws vs facturador-plus (ivas)
MAP_IVA = {
    'id': 'id',
    'base_imp': 'baseimp',
    'importe': 'importe',
    }

# Mapeo de nombres ws vs facturador-plus (ivas)
MAP_TRIB = {
    'id': 'id',
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
    xml = SimpleXMLElement(open(fn,"rb").read())

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
        reg['formas_pago']= [d['formapago'] for d in comp['formaspago']]


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


def aplanar(regs):
    "Convierte una estructura python en planilla CSV (PyRece)"
    
    filas = []
    for reg in regs:
        fila = {}
        for k in MAP_ENC:
            fila[k] = reg[k]

        fila['forma_pago']=reg['formas_pago'][0]['descripcion']


        for i, det in enumerate(reg['detalles']):
            li = i+1
            fila.update({
                    'codigo%s' % li: det['codigo'],
                    'descripcion%s' % li: det['ds'],
                    'umed%s' % li: det.get('umed'),
                    'cantidad%s' % li: det['qty'],
                    'precio%s' % li: det.get('precio'),
                    'importe%s' % li: det['imp_total'],
                    'iva_id%s' % li: det.get('iva_id'),
                    'imp_iva%s' % li: det.get('imp_iva'),
                    'numero_despacho%s' % li: det.get('numero_despacho'),
                    })
        for i, iva in enumerate(reg['ivas']):
            li = i+1
            fila.update({
                    'iva_id_%s' % li: iva['id'],
                    'iva_base_imp_%s' % li: iva['base_imp'],
                        'iva_importe_%s' % li: iva['importe'],
                    })
        for i, tributo in enumerate(reg['tributos']):
            li = i+1
            fila.update({
                    'tributo_id_%s' % li: tributo['id'],
                    'tributo_base_imp_%s' % li: tributo['base_imp'],
                    'tributo_desc_%s' % li: tributo['desc'],
                    'tributo_alic_%s' % li: tributo['alic'],
                    'tributo_importe_%s' % li: tributo['importe'],
                    })
        filas.append(fila)
    
    
    cols = ["id",
        "tipo_cbte","punto_vta","cbt_numero","fecha_cbte",
        "tipo_doc","nro_doc","moneda_id","moneda_ctz",
        "imp_neto","imp_iva","imp_trib","imp_op_ex","imp_tot_conc","imp_total",
        "concepto","fecha_venc_pago","fecha_serv_desde","fecha_serv_hasta",
        "cae","fecha_vto","resultado","motivo","reproceso",
        "nombre","domicilio","localidad","telefono","categoria","email",
        'numero_cliente', 'numero_orden_compra', 'condicion_frente_iva',
        'numero_cotizacion', 'numero_remito',
        ]

    # filtro y ordeno las columnas
    l = [k for f in filas for k in f.keys()]
    s = set(l) - set(cols)
    cols = cols + list(s)
 
    ret = [cols]
    for fila in filas:
        ret.append([fila.get(k) for k in cols])
        
    return ret


def desaplanar(filas):
    "Dado una planilla, conviertir en estructura python"

    def max_li(colname): 
        tmp = max([k for k in filas[0] if k.startswith(colname)])
        if max_li:
            return int(tmp[len(colname):])+1
        else:
            return 0

    regs = []
    for fila in filas[1:]:
        dic = dict([(filas[0][i], v) for i, v in enumerate(fila)])
        reg = {}
        for k in MAP_ENC:
            reg[k] = dic[k]

        reg['detalles'] = [{
                'codigo': dic['codigo%s' % li],
                'ds': dic['descripcion%s' % li],
                'umed': dic['umed%s' % li],
                'qty': dic['cantidad%s' % li],
                'precio': dic['precio%s' % li],
                'imp_total': dic['importe%s' % li],
                'iva_id': dic['iva_id%s' % li],
                'imp_iva': dic['imp_iva%s'% li],                                               
                'numero_despacho': dic['numero_despacho%s'% li],
                } for li in xrange(1, max_li("cantidad"))]
                
        reg['tributos'] = [{
                'id': dic['tributo_id_%s'  % li],
                'desc': dic['tributo_desc_%s'  % li],
                'base_imp': dic['tributo_base_imp_%s'  % li],
                'alic': dic['tributo_alic_%s'  % li],
                'importe': dic['tributo_importe_%s'  % li],
                } for li in xrange(1, max_li("tributo_id_"))]

        reg['ivas'] = [{
                'id': dic['iva_id_%s'  % li],
                'baseimp': dic['iva_base_imp_%s'  % li],
                'importe': dic['iva_importe_%s'  % li],
                } for li in xrange(1, max_li("iva_id_"))]
                
        reg['formas_pago']=[{'descripcion': dic['forma_pago']}]
        regs.append(reg)

    return regs


def escribir(regs, fn="salida.xml"):
    "Dado una lista de comprobantes (diccionarios), convierte y escribe"
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
                    'descripcion': reg['formas_pago'][0]['descripcion'],
                    }}]
                })
        comprobantes.append({'comprobante':dic})

    xml.marshall("comprobante", comprobantes)
    open(fn,"wb").write(xml.as_xml())

# pruebas básicas
if __name__ == '__main__':
    regs = leer("")
    regs[0]['cae']='1'*15
    filas = aplanar(regs)   
    print filas
    reg1 = desaplanar(filas)
    print reg1
    print reg1 == regs
    escribir(reg1)
