#!usr/bin/python
# -*- coding: latin1 -*-
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
__version__ = "1.18"

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

from utils import leer, escribir

C = 1 # caracter alfabetico
N = 2 # numerico
A = 3 # alfanumerico
I = 4 # importes
B = 9 # blanco

CUIT = '20267565393'

# ESPECIFICACIONES TECNICAS - ANEXO II RESOLUCION GENERAL N°1361
# http://www.afip.gov.ar/afip/resol136102_Anexo_II.html

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
    ('tipo_reg', 1, N),
    ('fecha_cbte', 8, N),
    ('tipo_cbte', 2, N),
    ('ctl_fiscal', 1, C),
    ('punto_vta', 4, N),
    ('cbt_numero', 8, N),
    ('cbte_nro_reg', 8, N),
    ('cant_hojas', 3, N),
    ('tipo_doc', 2, N),
    ('nro_doc', 11, N),
    ('nombre', 30, A),
    ('imp_total', 15, I),
    ('imp_tot_conc', 15, I),
    ('imp_neto', 15, I),
    ('impto_liq', 15, I),
    ('impto_liq_rni', 15, I),
    ('imp_op_ex', 15, I),
    ('impto_perc', 15, I),
    ('imp_iibb', 15, I),
    ('impto_perc_mun', 15, I),
    ('imp_internos', 15, I),
    ('transporte', 15, I),
    ('categoria', 2, N),
    ('imp_moneda_id', 3, A),
    ('imp_moneda_ctz', 10, I),
    ('alicuotas_iva', 1, N),
    ('codigo_operacion', 1, C),
    ('cae', 14, N),
    ('fecha_vto', 8, N),
    ('fecha_anulacion', 8, A),
    ]

# campos especiales del encabezado:
IMPORTES = ('imp_total', 'imp_tot_conc', 'imp_neto', 'impto_liq', 
            'impto_liq_rni', 'imp_op_ex', 'impto_perc', 'imp_iibb', 
            'impto_perc_mun', 'imp_internos')

# total
CAB_FAC_TIPO2 = [
    ('tipo_reg', 1, N),
    ('periodo', 6, N),
    ('relleno', 13, B),
    ('cant_reg_tipo_1', 8, N),
    ('relleno', 17, B),
    ('cuit', 11, N),
    ('relleno', 22, B),
    ('imp_total', 15, I),
    ('imp_tot_conc', 15, I),
    ('imp_neto', 15, I),
    ('impto_liq', 15, I),
    ('impto_liq_rni', 15, I),
    ('imp_op_ex', 15, I),
    ('impto_perc', 15, I),
    ('imp_iibb', 15, I),
    ('impto_perc_mun', 15, I),
    ('imp_internos', 15, I),
    ('relleno', 62, B),
    ]

DETALLE = [
    ('tipo_cbte', 2, N),
    ('ctl_fiscal', 1, C),
    ('fecha_cbte', 8, N),
    ('punto_vta', 4, N),
    ('cbt_numero', 8, N),
    ('cbte_nro_reg', 8, N),
    ('qty', 12, I),
    ('pro_umed', 2, N),
    ('pro_precio_uni', 16, I),
    ('imp_bonif', 15, I),
    ('imp_ajuste', 16, I),
    ('imp_total', 16, I),
    ('alicuota_iva', 4, I),
    ('gravado', 1, C),
    ('anulacion', 1, C),
    ('codigo', 50, A),
    ('ds', 150, A),
    ]

VENTAS_TIPO1 = [
    ('tipo_reg', 1, N),
    ('fecha_cbte', 8, N),
    ('tipo_cbte', 2, N),
    ('ctl_fiscal', 1, C),
    ('punto_vta', 4, N),
    ('cbt_numero', 20, N),
    ('cbte_nro_reg', 20, N),
    ('tipo_doc', 2, N),
    ('nro_doc', 11, N),
    ('nombre', 30, A),
    ('imp_total', 15, I),
    ('imp_tot_conc', 15, I),
    ('imp_neto', 15, I),
    ('alicuota_iva', 4, I),
    ('impto_liq', 15, I),
    ('impto_liq_rni', 15, I),
    ('imp_op_ex', 15, I),
    ('impto_perc', 15, I),
    ('imp_iibb', 15, I),
    ('impto_perc_mun', 15, I),
    ('imp_internos', 15, I),
    ('categoria', 2, N),
    ('imp_moneda_id', 3, A),
    ('imp_moneda_ctz', 10, I),
    ('alicuotas_iva', 1, N),
    ('codigo_operacion', 1, C),
    ('cae', 14, N),
    ('fecha_vto', 8, N),
    ('fecha_anulacion', 8, A),
    ('info_adic', 75-0, B),
    ]

VENTAS_TIPO2 = [
    ('tipo_reg', 1, N),
    ('periodo', 6, N),
    ('relleno', 29, B),
    ('cant_reg_tipo_1', 12, N),
    ('relleno', 10, B),
    ('cuit', 11, N),
    ('relleno', 30, B),
    ('imp_total', 15, I),
    ('imp_tot_conc', 15, I),
    ('imp_neto', 15, I),
    ('Relleno', 4, B),
    ('impto_liq', 15, I),
    ('impto_liq_rni', 15, I),
    ('imp_op_ex', 15, I),
    ('impto_perc', 15, I),
    ('imp_iibb', 15, I),
    ('impto_perc_mun', 15, I),
    ('imp_internos', 15, I),
    ('relleno', 122, B),
    ]


def format_as_dict(format):
    return dict([(k[0], None) for k in format])


def leer_planilla(entrada):
    "Convierte una planilla CSV a una lista de diccionarios [{'col': celda}]"
    
    items = []
    csv_reader = csv.reader(open(entrada), dialect='excel', delimiter=",")
    for row in csv_reader:
        items.append(row)
    if len(items) < 2:
        dialog.alertDialog(self, 'El archivo no tiene datos vÃ¡lidos', 'Advertencia')
    cols = [str(it).strip() for it in items[0]]

    # armar diccionario por cada linea
    items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

    return items


def leer_json(entrada):
    "Carga los datos de json [{'col': celda}]"
        
    import json
    items = json.load(open(entrada))

    return items


def grabar_json(salida):
    "Guarda los datos json"
    
    import json
    json.dump(items, open("rg1361.json", "w"), sort_keys=True, indent=4)


def generar_encabezado(items):
    "Crear archivo de cabecera de facturas emitidas"

    periodo = items[0]['fecha_cbte'][:6]

    out = open("CABECERA_%s.txt" % periodo, "w")
    totales = format_as_dict(CAB_FAC_TIPO2)
    totales['periodo'] = periodo
    for key in IMPORTES:
        totales[key] = Decimal(0)
    
    for item in items:
        vals = format_as_dict(CAB_FAC_TIPO1)
        vals['fecha_anulacion'] = ''
        for k in item.keys():
            vals[k] = item[k]
            if k in totales:
                totales[k] = totales[k] + Decimal(item[k])
        vals['tipo_reg'] = '1'
        vals['ctl_fiscal'] = item.get('ctl_fiscal', ' ')  # C para controlador
        vals['cbte_nro_reg'] = vals['cbt_numero']
        vals['cant_hojas'] = '01'
        vals['transporte'] = '0'
        vals['categoria'] = categorias[item['categoria'].lower()]
        if vals['imp_moneda_id'] is None:
            vals['imp_moneda_id'] = 'PES'
            vals['imp_moneda_ctz'] = '1.000'
        vals['alicuotas_iva'] = max(len(item.get('ivas', [])), 1)
        if vals['codigo_operacion'] is None:
            if int(item['tipo_cbte']) in (19, 20, 21):
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


def generar_detalle(items):
    "Crear archivo de detalle de facturas emitidas"
    
    periodo = items[0]['fecha_cbte'][:6]

    out = open("DETALLE_%s.txt" % periodo, "w")
    
    # recorro las facturas y detalles de artículos vendidos:
    for item in items:
        for it in item.get('detalles', [{}]):
            vals = format_as_dict(DETALLE)
            # datos generales de la factura:
            vals['tipo_reg'] = '1'
            for k in ('tipo_cbte', 'fecha_cbte', 'punto_vta', 'cbt_numero'):
                vals[k] = item[k]
            vals['cbte_nro_reg'] = item['cbt_numero']  # no hay varias hojas
            vals['ctl_fiscal'] = item.get('ctl_fiscal', ' ')  # C para controlador
            vals['anulacion'] = item.get('anulacion', ' ')
            # datos del artículo:
            vals['qty'] = it.get('qty', '1')  # cantidad
            vals['pro_umed'] = it.get('umed', '07')  # unidad de medida
            vals['pro_precio_uni'] = it.get('precio', item['imp_neto'])
            vals['imp_bonif'] = it.get('bonif', '0.00')
            vals['imp_ajuste'] = it.get('ajuste', '0.00')
            vals['imp_total'] = it.get('importe', '0.00')
            # iva
            if 'iva_id' in it:
                # mapear alicuota de iva según código usado en MTX
                iva_id = int(it['iva_id'])
                if iva_id in (1, 2):
                    alicuota = None
                else:
                    alicuota = {3: "0.00", 4: "10.5", 5: "21", 6: "27"}[iva_id]
                if alicuota is None:
                    vals['gravado'] = 'E'
                else:
                    vals['gravado'] = 'G'
                vals['alicuota_iva'] = alicuota or '0.00'
            else:
                # tomar datos generales:
                vals['alicuota_iva'] = (Decimal(item['imp_total'])/Decimal(item['imp_neto']) - 1) * 100
                if float(item['impto_liq']) == 0:
                    vals['gravado'] = 'E'
                else:
                    vals['gravado'] = 'G'
            # diseño libre: código de barras y descripción:
            vals['codigo'] = it.get('codigo', '')
            vals['ds'] = it.get('ds', '')
            s = escribir(vals, DETALLE)
            print "linea", s
            out.write(s)
        
    out.close()


def generar_ventas(items):
    "Crear archivos de ventas (registros tipo 1 y tipo 2 totales)"
    
    periodo = items[0]['fecha_cbte'][:6]

    out = open("VENTAS_%s.txt" % periodo, "w")
    totales = format_as_dict(VENTAS_TIPO2)
    totales['periodo'] = periodo
    for key in IMPORTES:
        totales[key] = Decimal(0)
    
    # recorro las facturas e itero sobre los subtotales por alicuota de IVA:
    for item in items:
        ivas = item.get("ivas", [{}])
        for i, iva in enumerate(ivas):
            vals = format_as_dict(VENTAS_TIPO1)
            # datos generales de la factura:
            vals['tipo_reg'] = '1'
            # copio los campos que no varían para las distintas alicuotas de IVA
            for k, l, t in VENTAS_TIPO1[1:10] + VENTAS_TIPO1[21:30]:
                vals[k] = item.get(k)
            vals['fecha_anulacion'] = ''
            vals['ctl_fiscal'] = item.get('ctl_fiscal', ' ')  # C para controlador
            vals['anulacion'] = item.get('anulacion', ' ')
            vals['cbte_nro_reg'] = item['cbt_numero']
            vals['cant_hojas'] = '01'
            vals['transporte'] = '0'
            vals['categoria'] = categorias[item['categoria'].lower()]
            if vals['imp_moneda_id'] is None:
                vals['imp_moneda_id'] = 'PES'
                vals['imp_moneda_ctz'] = '1.000'
            # subtotales por alícuota de IVA
            if 'iva_id' in iva:
                # mapear alicuota de iva según código usado en MTX
                iva_id = int(iva['iva_id'])
                if iva_id == 1:
                    vals['imp_tot_conc'] = iva['base_imp']
                    alicuota = None
                elif iva_id == 2:
                    vals['imp_op_ex'] = iva['base_imp']
                    alicuota = None
                else:
                    alicuota = {3: "0.00", 4: "10.5", 5: "21", 6: "27"}[iva_id]
                    vals['imp_neto'] = iva['base_imp']
                    vals['impto_liq'] = iva['importe']
                vals['alicuota_iva'] = alicuota or '0.00'
            else:
                # tomar datos generales: 
                vals['alicuota_iva'] = (Decimal(item['imp_total'])/Decimal(item['imp_neto']) - 1) * 100
                vals['alicuotas_iva'] = '01'
                if float(item['impto_liq']) == 0:
                    vals['codigo_operacion'] = 'E'
                else:
                    vals['codigo_operacion'] = ' '
                if vals['imp_tot_conc'] is None:
                    vals['imp_tot_conc'] = '0'

            # acumulo los totales para el registro tipo 2
            for k in IMPORTES:
                totales[k] = totales[k] + Decimal(vals[k] or 0)

            # otros impuestos (TODO: recorrer tributos) solo ultimo registro:
            if len(ivas) == i-1:
                for k in ('impto_perc', 'imp_iibb', 'impto_perc_mun', 'imp_internos'):
                    if k in item:
                        vals[k] = item[k]
                        totales[k] = totales[k] + Decimal(vals[k] or 0)

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

        if '--leer' in sys.argv:
            claves = [clave for clave, pos, leng in VENTAS_TIPO1 if clave not in ('tipo','info_adic')]
            csv = csv.DictWriter(open("ventas.csv","wb"), claves, extrasaction='ignore')
            csv.writerow(dict([(k, k) for k in claves]))
            f = open("VENTAS.txt")
            for linea in f:
                if str(linea[0])=='1':
                    datos = leer(linea, VENTAS_TIPO1)
                    csv.writerow(datos)
            f.close()
        else:
            if '--json' in sys.argv:
                items = leer_json(entrada)
            else:
                items = leer_planilla(entrada)
            print "Generando encabezado..."
            generar_encabezado(items)
            print "Generando detalle..."
            generar_detalle(items)
            print "Generando ventas..."
            generar_ventas(items)
            if '--json' in sys.argv:
                grabar_json(entrada)
        print "Hecho."
    except Exception, e:
        if '--debug' in sys.argv:
            raise
        print "Error: por favor corriga los datos y vuelva a intentar:"
        print str(e)
        f = open("traceback.txt", "w+")
        import traceback
        traceback.print_exc(file=f)
        f.close()
    raw_input("presione enter para continuar...")
    ##sys.stdout.close()
