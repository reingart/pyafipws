#!usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Almacenamiento de duplicados electrÃ³nicos RG1361/02"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2009 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.17"

LICENCIA = """
rg1361.py: Generador de archivos ventas para SIRED/SIAP RG1361/02
Copyright (C) 2009 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

import csv
from decimal import Decimal
import os
import sys
import traceback

C = 1 # caracter alfabetico
N = 2 # numerico
A = 3 # alfanumerico
B = 9 # blanco

CUIT = '20267565393'

categorias = {"responsable inscripto": "01", # IVA Responsable Inscripto
              "responsable no inscripto": "02", # IVA Responsable no Inscripto
              "no responsable": "03", # IVA no Responsable
              "exento": "04", # IVA Sujeto Exento
              "consumidor final": "05", # Consumidor Final
              "monotributo": "06", # Responsable Monotributo
              "no categorizado": "07", # Sujeto no Categorizado
              "importador": "08", # Importador del Exterior
              "exterior": "09", # Cliente del Exterior
              "liberado": "10", # IVA Liberado â€“ Ley NÂº 19.640
              "responsable inscripto - agente de percepciÃ³n": "11", # IVA Responsable Inscripto - Agente de Percepcion
}

codigos_operacion = { 
    "Z": "Exportaciones a la zona franca",
    "X": "Exportaciones al Exterior",
    "E": "Operaciones Exentas",
}

CAB_FAC_TIPO1 = [
    ('tipo_reg', 1, 2),
    ('fecha_cbte', 8, 2),
    ('tipo_cbte', 2, 2),
    ('ctl_fiscal', 1, 1),
    ('punto_vta', 4, 2),
    ('cbt_numero', 8, 2),
    ('cbte_nro_reg', 8, 2),
    ('cant_hojas', 3, 2),
    ('tipo_doc', 2, 2),
    ('nro_doc', 11, 2),
    ('nombre', 30, 3),
    ('imp_total', 15, 2),
    ('imp_tot_conc', 15, 2),
    ('imp_neto', 15, 2),
    ('impto_liq', 15, 2),
    ('impto_liq_rni', 15, 2),
    ('imp_op_ex', 15, 2),
    ('impto_perc', 15, 2),
    ('imp_iibb', 15, 2),
    ('impto_perc_mun', 15, 2),
    ('imp_internos', 15, 2),
    ('transporte', 15, 2),
    ('categoria', 2, 2),
    ('imp_moneda_id', 3, 3),
    ('imp_moneda_ctz', 10, 2),
    ('alicuotas_iva', 1, 2),
    ('codigo_operacion', 1, 1),
    ('cae', 14, 2),
    ('fecha_vto', 8, 2),
    ('fecha_anulacion', 8, 3),
    ]

# total
CAB_FAC_TIPO2 = [
    ('tipo_reg', 1, 2),
    ('periodo', 6, 2),
    ('relleno', 13, 9),
    ('cant_reg_tipo_1', 8, 2),
    ('relleno', 17, 9),
    ('cuit', 11, 2),
    ('relleno', 22, 9),
    ('imp_total', 15, 2),
    ('imp_tot_conc', 15, 2),
    ('imp_neto', 15, 2),
    ('impto_liq', 15, 2),
    ('impto_liq_rni', 15, 2),
    ('imp_op_ex', 15, 2),
    ('impto_perc', 15, 2),
    ('imp_iibb', 15, 2),
    ('impto_perc_mun', 15, 2),
    ('imp_internos', 15, 2),
    ('relleno', 62, 9),
    ]

DETALLE = [
    ('tipo_cbte', 2, 2),
    ('ctl_fiscal', 1, 1),
    ('fecha_cbte', 8, 2),
    ('punto_vta', 4, 2),
    ('cbt_numero', 8, 2),
    ('cbte_nro_reg', 8, 2),
    ('qty', 12, 2),
    ('pro_umed', 2, 2),
    ('pro_precio_uni', 16, 2),
    ('imp_bonif', 15, 2),
    ('imp_ajuste', 16, 2),
    ('imp_total', 16, 2),
    ('alicuota_iva', 4, 2),
    ('gravado', 1, 1),
    ('anulacion', 1, 1),
    ('diseÃ±o_libre', 75-0, 9),
    ]

VENTAS_TIPO1 = [
    ('tipo_reg', 1, 2),
    ('fecha_cbte', 8, 2),
    ('tipo_cbte', 2, 2),
    ('ctl_fiscal', 1, 1),
    ('punto_vta', 4, 2),
    ('cbt_numero', 20, 2),
    ('cbte_nro_reg', 20, 2),
    ('tipo_doc', 2, 2),
    ('nro_doc', 11, 2),
    ('nombre', 30, 3),
    ('imp_total', 15, 2),
    ('imp_tot_conc', 15, 2),
    ('imp_neto', 15, 2),
    ('alicuota_iva', 4, 2),
    ('impto_liq', 15, 2),
    ('impto_liq_rni', 15, 2),
    ('imp_op_ex', 15, 2),
    ('impto_perc', 15, 2),
    ('imp_iibb', 15, 2),
    ('impto_perc_mun', 15, 2),
    ('imp_internos', 15, 2),
    ('categoria', 2, 2),
    ('imp_moneda_id', 3, 3),
    ('imp_moneda_ctz', 10, 2),
    ('alicuotas_iva', 1, 2),
    ('codigo_operacion', 1, 1),
    ('cae', 14, 2),
    ('fecha_vto', 8, 2),
    ('fecha_anulacion', 8, 3),
    ('info_adic', 75-0, 9),
    ]

VENTAS_TIPO2 = [
    ('tipo_reg', 1, 2),
    ('periodo', 6, 2),
    ('relleno', 29, 9),
    ('cant_reg_tipo_1', 12, 2),
    ('relleno', 10, 9),
    ('cuit', 11, 2),
    ('relleno', 30, 9),
    ('imp_total', 15, 2),
    ('imp_tot_conc', 15, 2),
    ('imp_neto', 15, 2),
    ('Relleno', 4, 9),
    ('impto_liq', 15, 2),
    ('impto_liq_rni', 15, 2),
    ('imp_op_ex', 15, 2),
    ('impto_perc', 15, 2),
    ('imp_iibb', 15, 2),
    ('impto_perc_mun', 15, 2),
    ('imp_internos', 15, 2),
    ('relleno', 122, 9),
    ]
def escribir(dic, formato):
    linea = " " * sum([l for n, l, t in formato])
    comienzo = 1
    for (clave, longitud, tipo) in formato:
        if clave.capitalize() in dic:
            clave = clave.capitalize()
        valor = str(dic.get(clave,""))
        if tipo == N:
            if valor is None or valor=='None':
                valor = "0.00"
            if str(valor):
                valor = ("%%0%dd" % longitud) % int(str(valor).replace(".",""))
            else:
                valor =''
                #raise ValueError("Valor incorrecto para campo %s = %s" % (clave, valor))
        if tipo == B:
            valor = ' ' * longitud
        else:
            valor = ("%%-0%ds" % longitud) % valor
        linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
        comienzo += longitud
    return linea + "\n"


def format_as_dict(format):
    return dict([(k[0], None) for k in format])


def generar_encabezado(entrada):
    items = []
    csv_reader = csv.reader(open(entrada), dialect='excel', delimiter=",")
    for row in csv_reader:
        items.append(row)
    if len(items) < 2:
        dialog.alertDialog(self, 'El archivo no tiene datos vÃ¡lidos', 'Advertencia')
    cols = [str(it).strip() for it in items[0]]

    # armar diccionario por cada linea
    items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

    print items

    periodo = items[0]['fecha_cbte'][:6]

    out = open("CABECERA_%s.txt" % periodo, "w")
    totales = format_as_dict(CAB_FAC_TIPO2)
    totales['periodo'] = periodo
    for key in ('imp_total', 'imp_tot_conc', 'imp_neto', 'impto_liq', 'impto_liq_rni', 
                'imp_op_ex', 'impto_perc', 'imp_iibb', 'impto_perc_mun', 'imp_internos'):
        totales[key] = Decimal(0)
    
    for item in items:
        vals = format_as_dict(CAB_FAC_TIPO1)
        vals['fecha_anulacion'] = ''
        for k in cols:
            vals[k] = item[k]
            if k in totales:
                totales[k] = totales[k] + Decimal(item[k])
        vals['tipo_reg'] = '1'
        vals['ctl_fiscal'] = ' '
        vals['cbte_nro_reg'] = vals['cbt_numero']
        vals['cant_hojas'] = '01'
        vals['transporte'] = '0'
        vals['categoria'] = categorias[item['categoria'].lower()]
        if vals['imp_moneda_id'] is None:
            vals['imp_moneda_id'] = 'PES'
            vals['imp_moneda_ctz'] = '1.000'
        vals['alicuotas_iva'] = '01'
        if float(vals['impto_liq']) == 0:
            vals['codigo_operacion'] = 'E'
        else:
            vals['codigo_operacion'] = ' '
        if vals['imp_tot_conc'] is None:
            vals['imp_tot_conc'] = '0'
        s = escribir(vals, CAB_FAC_TIPO1)
        print "linea", s
        out.write(s)
        
    totales['tipo_reg'] = '2'
    totales['cant_reg_tipo_1'] = str(len(items))
    totales['cuit'] = CUIT
    s = escribir(totales, CAB_FAC_TIPO2)
    print "print totales", s
    out.write(s)
    out.close()


def generar_detalle(entrada):
    items = []
    csv_reader = csv.reader(open(entrada), dialect='excel', delimiter=",")
    for row in csv_reader:
        items.append(row)
    if len(items) < 2:
        dialog.alertDialog(self, 'El archivo no tiene datos vÃ¡lidos', 'Advertencia')
    cols = [str(it).strip() for it in items[0]]

    # armar diccionario por cada linea
    items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

    periodo = items[0]['fecha_cbte'][:6]

    out = open("DETALLE_%s.txt" % periodo, "w")
    
    for item in items:
        vals = format_as_dict(DETALLE)
        vals['qty'] = '1'
        vals['pro_umed'] = '07' # unidad
        vals['pro_precio_uni'] = item['imp_neto']
        vals['imp_bonif'] = '0.00'
        vals['imp_ajuste'] = '0.00'
        vals['imp_total'] = '0.00'
        vals['imp_tot_conc'] = '0'
        for k in cols:
            vals[k] = item[k]
        vals['tipo_reg'] = '1'
        vals['ctl_fiscal'] = ' '
        vals['cbte_nro_reg'] = vals['cbt_numero']        
        vals['anulacion'] = ' '
        vals['alicuota_iva'] = (Decimal(vals['imp_total'])/Decimal(vals['imp_neto']) - 1) * 100
        if float(vals['impto_liq']) == 0:
            vals['gravado'] = 'E'
        else:
            vals['gravado'] = 'G'

        s = escribir(vals, DETALLE)
        print "linea", s
        out.write(s)
        
    out.close()


def generar_ventas(entrada):
    items = []
    csv_reader = csv.reader(open(entrada), dialect='excel', delimiter=",")
    for row in csv_reader:
        items.append(row)
    if len(items) < 2:
        dialog.alertDialog(self, 'El archivo no tiene datos vÃ¡lidos', 'Advertencia')
    cols = [str(it).strip() for it in items[0]]

    # armar diccionario por cada linea
    items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

    periodo = items[0]['fecha_cbte'][:6]

    out = open("VENTAS_%s.txt" % periodo, "w")
    totales = format_as_dict(VENTAS_TIPO2)
    totales['periodo'] = periodo
    for key in ('imp_total', 'imp_tot_conc', 'imp_neto', 'impto_liq', 'impto_liq_rni', 
                'imp_op_ex', 'impto_perc', 'imp_iibb', 'impto_perc_mun', 'imp_internos'):
        totales[key] = Decimal(0)
    
    for item in items:
        vals = format_as_dict(VENTAS_TIPO1)
        vals['fecha_anulacion'] = ''
        for k in cols:
            vals[k] = item[k]
            if k in totales:
                totales[k] = totales[k] + Decimal(item[k])
        vals['tipo_reg'] = '1'
        vals['ctl_fiscal'] = ' '
        vals['cbte_nro_reg'] = vals['cbt_numero']
        vals['cant_hojas'] = '01'
        vals['transporte'] = '0'
        vals['categoria'] = categorias[item['categoria'].lower()]
        if vals['imp_moneda_id'] is None:
            vals['imp_moneda_id'] = 'PES'
            vals['imp_moneda_ctz'] = '1.000'

        vals['alicuota_iva'] = (Decimal(vals['imp_total'])/Decimal(vals['imp_neto']) - 1) * 100
        vals['alicuotas_iva'] = '01'
        if float(vals['impto_liq']) == 0:
            vals['codigo_operacion'] = 'E'
        else:
            vals['codigo_operacion'] = ' '
        if vals['imp_tot_conc'] is None:
            vals['imp_tot_conc'] = '0'

        s = escribir(vals, VENTAS_TIPO1)
        print "linea", s
        out.write(s)
        
    totales['tipo_reg'] = '2'
    totales['cant_reg_tipo_1'] = str(len(items))
    totales['cuit'] = CUIT
    s = escribir(totales, VENTAS_TIPO2)
    print "totales", s
    out.write(s)
    out.close()


if __name__ == '__main__':
    try:
        if hasattr(sys,"frozen") or False:
            p=os.path.dirname(os.path.abspath(sys.executable))
            os.chdir(p)
        ##sys.stdout = open("salida.txt", "a")
        if len(sys.argv)>1:
            entrada = sys.argv[1]
        else:
            entrada = 'facturas3.csv'
        
        print "Generando encabezado..."
        generar_encabezado(entrada)
        print "Generando detalle..."
        generar_detalle(entrada)
        print "Generando ventas..."
        generar_ventas(entrada)
        print "Hecho."
    except Exception, e:
        print "Error: por favor corriga los datos y vuelva a intentar:"
        print str(e)
        f = open("traceback.txt", "w+")
        import traceback
        traceback.print_exc(file=f)
        f.close()
    raw_input("presione enter para continuar...")
    ##sys.stdout.close()
