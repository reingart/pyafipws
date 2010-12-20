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
                    'importeiva': Decimal,
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


def leer(fn="entrada.xml"):
    "Analiza un archivo XML y devuelve un diccionario"
    xml = SimpleXMLElement(open(fn,"rb").read())

    dic = xml.unmarshall(XML_FORMAT)
    
    cols_e = ["id","nombre","domicilio","localidad","telefono","categoria","email",
            "tipo_cbte","punto_vta","cbt_numero","fecha_cbte",
            "tipo_doc","nro_doc","moneda_id","moneda_ctz",
            "imp_neto","imp_iva","imp_trib","imp_op_ex","imp_tot_conc","imp_total",
            "concepto","fecha_venc_pago","fecha_serv_desde","fecha_serv_hasta",
            "cae","fecha_vto","resultado","motivo","reproceso",
            ]

    cols_d = [] # detalle
    cols_i = [] # "iva_id_1","iva_base_imp_1","iva_importe_1",
    cols_t = [] # "tributo_id_1","tributo_desc_1","tributo_base_imp_1","tributo_alic_1","tributo_importe_1",

    filas = []
    for dic_comprobante in dic['comprobantes']:
        fila = {}
        comp = dic_comprobante['comprobante']
        for k, v in MAP_ENC.items():
            fila[k] = comp[v]
            for i, detalles in enumerate(comp['detalles']):
                li = i+1
                det = detalles['detalle']
                fila.update({
                        'codigo%s' % li: det['cod'],
                        'descripcion%s' % li: det['desc'],
                        'umed%s' % li: det.get('unimed'),
                        'cantidad%s' % li: det['cant'],
                        'precio%s' % li: det.get('preciounit'),
                        'importe%s' % li: det['importe'],
                        'iva_id%s' % li: det.get('tasaiva'),
                        'imp_iva%s' % li: det.get('importeiva'),
                        })
            for i, ivas in enumerate(comp['ivas']):
                li = i+1
                iva = ivas['iva']
                fila.update({
                        'iva_id_%s' % li: iva['id'],
                        'iva_base_imp_%s' % li: iva['baseimp'],
                            'iva_importe_%s' % li: iva['importe'],
                        })
            for i, tributos in enumerate(comp['tributos']):
                li = i+1
                tributo = tributos['tributo']
                fila.update({
                        'tributo_id_%s' % li: tributo['id'],
                        'tributo_base_imp_%s' % li: tributo['baseimp'],
                        'tributo_desc_%s' % li: det['desc'],
                        'tributo_alic_%s' % li: tributo['alic'],
                        'tributo_importe_%s' % li: tributo['importe'],
                        })
        filas.append(fila)
    return filas


def escribir(filas, fn="salida.xml"):
    "Dado una lista de comprobantes (diccionarios), convierte y escribe"
    xml = SimpleXMLElement(XML_BASE)

    def max_li(colname): 
        tmp = max([k for k in fila if k.startswith(colname)])
        if max_li:
            return int(tmp[len(colname):])+1
        else:
            return 0

    comprobantes = []
    for fila in filas:
        dic = {}
        for k, v in MAP_ENC.items():
            dic[v] = fila[k]

        dic.update({
                
                'detalles': [{
                    'detalle': {
                        'cod': fila['codigo%s' % li],
                        'desc': fila['descripcion%s' % li],
                        'unimed': fila['umed%s' % li],
                        'cant': fila['cantidad%s' % li],
                        'preciounit': fila['precio%s' % li],
                        'importe': fila['importe%s' % li],
                        'tasaiva': fila['iva_id%s' % li],
                        'importeiva': fila['imp_iva%s'% li],                                               
                        },
                    } for li in xrange(1, max_li("cantidad"))],
                
                'tributos': [{
                    'tributo': {
                        'id': fila['tributo_id_%s'  % li],
                        'desc': fila['tributo_desc_%s'  % li],
                        'baseimp': fila['tributo_base_imp_%s'  % li],
                        'alic': fila['tributo_alic_%s'  % li],
                        'importe': fila['tributo_importe_%s'  % li],
                        },
                    } for li in xrange(1, max_li("tributo_id_"))],

                'ivas': [{
                    'iva': {
                        'id': fila['iva_id_%s'  % li],
                        'baseimp': fila['iva_base_imp_%s'  % li],
                        'importe': fila['iva_importe_%s'  % li],
                        },
                    } for li in xrange(1, max_li("iva_id_"))],
                })
        comprobantes.append(dic)

    xml.marshall("comprobante", comprobantes)
    open(fn,"wb").write(xml.as_xml())

# pruebas básicas
if __name__ == '__main__':
    d = leer()
    d[0]['cae']='0'*15
    escribir(d)