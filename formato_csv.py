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

"Módulo para manejo de archivos CSV (planillas de cálculo)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"

import csv
from decimal import Decimal


def leer(fn="entrada.csv", delimiter=";"):
    "Analiza un archivo CSV y devuelve un diccionario (aplanado)"
    items = []
    csvfile = open(fn, "rb")
    # deducir dialecto y delimitador
    try:
        dialect = csv.Sniffer().sniff(csvfile.read(256), delimiters=[';',','])
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter=delimiter
    csvfile.seek(0)
    csv_reader = csv.reader(csvfile, dialect)
    for row in csv_reader:
        r = []
        for c in row:
            if isinstance(c, basestring):
                c=c.strip()
            r.append(c)
        items.append(r)
    return items
    # TODO: return desaplanar(items)

    
def aplanar(regs):
    "Convierte una estructura python en planilla CSV (PyRece)"
    
    from formato_xml import MAP_ENC
    
    filas = []
    for reg in regs:
        fila = {}
        for k in MAP_ENC:
            fila[k] = reg.get(k)

        fila['forma_pago']=reg['forma_pago']
        
        # por compatibilidad con pyrece:
        if reg.get('cbte_nro'):
            fila['cbt_numero']=reg['cbte_nro']

        for i, det in enumerate(reg['detalles']):
            li = i+1
            fila.update({
                    'codigo%s' % li: det['codigo'],
                    'descripcion%s' % li: det['ds'],
                    'umed%s' % li: det.get('umed'),
                    'cantidad%s' % li: det['qty'],
                    'precio%s' % li: det.get('precio'),
                    'importe%s' % li: det['importe'],
                    'iva_id%s' % li: det.get('iva_id'),
                    'imp_iva%s' % li: det.get('imp_iva'),
                    'numero_despacho%s' % li: det.get('numero_despacho'),
                    })
        for i, iva in enumerate(reg['ivas']):
            li = i+1
            fila.update({
                    'iva_id_%s' % li: iva['iva_id'],
                    'iva_base_imp_%s' % li: iva['base_imp'],
                    'iva_importe_%s' % li: iva['importe'],
                    })
        for i, tributo in enumerate(reg['tributos']):
            li = i+1
            fila.update({
                    'tributo_id_%s' % li: tributo['tributo_id'],
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
        "obs_generales", "obs_comerciales",
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

    from formato_xml import MAP_ENC

    def max_li(colname): 
        l = [int(k[len(colname):])+1 for k in filas[0] if k.startswith(colname)]
        if l:
            tmp = max(l)
        if l and tmp:
            ##print "max_li(%s)=%s" % (colname, tmp)
            return tmp
        else:
            return 0

    regs = []
    for fila in filas[1:]:
        dic = dict([(filas[0][i], v) for i, v in enumerate(fila)])
        reg = {}

        # por compatibilidad con pyrece:
        reg['cbte_nro'] = dic['cbt_numero']

        for k in MAP_ENC:
            if k in dic:
                reg[k] = dic.pop(k)
            
        reg['detalles'] = [{
                'codigo': ('codigo%s' % li) in dic and dic.pop('codigo%s' % li),
                'ds': ('descripcion%s' % li) in dic and dic.pop('descripcion%s' % li),
                'umed': ('umed%s' % li) in dic and dic.pop('umed%s' % li),
                'qty': ('cantidad%s' % li) in dic and dic.pop('cantidad%s' % li),
                'precio': ('precio%s' % li) in dic and dic.pop('precio%s' % li),
                'importe': ('importe%s' % li) in dic and dic.pop('importe%s' % li),
                'iva_id': ('iva_id%s' % li) in dic and dic.pop('iva_id%s' % li),
                'imp_iva': ('imp_iva%s' % li) in dic and dic.pop('imp_iva%s'% li),                                               
                'numero_despacho': ('numero_despacho%s' % li) in dic and dic.pop('numero_despacho%s'% li),
                } for li in xrange(1, max_li("cantidad")) 
                  if dic['cantidad%s' % li] is not None]
                
        reg['tributos'] = [{
                'tributo_id': dic.pop('tributo_id_%s'  % li),
                'desc': dic.pop('tributo_desc_%s'  % li),
                'base_imp': dic.pop('tributo_base_imp_%s'  % li),
                'alic': dic.pop('tributo_alic_%s'  % li),
                'importe': dic.pop('tributo_importe_%s'  % li),
                } for li in xrange(1, max_li("tributo_id_"))
                  if dic['tributo_id_%s'  % li]]

        reg['ivas'] = [{
                'iva_id': dic.pop('iva_id_%s'  % li),
                'base_imp': dic.pop('iva_base_imp_%s'  % li),
                'importe': dic.pop('iva_importe_%s'  % li),
                } for li in xrange(1, max_li("iva_id_"))
                  if dic['iva_id_%s'  % li]]
                
        reg['forma_pago'] = dic.pop('forma_pago')

        # agrego campos adicionales:
        reg['datos'] = [{
                'campo': campo, 
                'valor': valor, 
                'pagina': '',
                } for campo, valor in dic.items()
                ]


        regs.append(reg)

    return regs


def escribir(filas, fn="salida.csv", delimiter=";"):
    "Dado una lista de comprobantes (diccionarios), aplana y escribe"
    f = open(fn,"wb")
    csv_writer = csv.writer(f, dialect='excel', delimiter=";")
    # TODO: filas = aplanar(regs)
    csv_writer.writerows(filas)
    f.close()

    
# pruebas básicas
if __name__ == '__main__':
    ##import pdb; pdb.set_trace()
    filas = leer("facturas-wsfev1-bis.csv")
    regs1 = desaplanar(filas)
    print filas
    filas1 = aplanar(regs1)   
    print filas1
    print filas1 == filas
    escribir(filas1, "facturas-wsfev1-bis-sal.csv")
