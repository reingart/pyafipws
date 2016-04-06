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

"Almacenamiento de duplicados electrónicos RG1361/02 y RG1579/03 AFIP"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2009-2015 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.22d"

LICENCIA = """
sired.py: Generador de archivos ventas para SIRED/SIAP RG1361/02 RG1579/03
(Sistema Resúmen Electrónico de Datos / Almacenamiento de Duplicados)
Copyright (C) 2009-2015 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

import csv
import datetime
from decimal import Decimal
import os
import sys
import unicodedata
import sqlite3
import traceback

from utils import leer, escribir, C, N, A, I, B, get_install_dir

CUIT = '20267565393'

# ESPECIFICACIONES TECNICAS - ANEXO II RESOLUCION GENERAL N°1361
# http://www.afip.gov.ar/afip/resol136102_Anexo_II.html

categorias = {"responsable inscripto": "01", # IVA Responsable Inscripto
              "responsable no inscripto": "02", # IVA Responsable no Inscripto
              "no responsable": "03", # IVA no Responsable
              "exento": "04", # IVA Sujeto Exento
              "consumidor final": "05", # Consumidor Final
              "monotributo": "06", # Responsable Monotributo
              "responsable monotributo": "06", # Responsable Monotributo
              "no categorizado": "07", # Sujeto no Categorizado
              "importador": "08", # Importador del Exterior
              "exterior": "09", # Cliente del Exterior
              "liberado": "10", # IVA Liberado Ley Nº 19.640
              "responsable inscripto - agente de percepción": "11", # IVA Responsable Inscripto - Agente de Percepcion
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

# Regimen de informacion de compras y ventas

from rg3685 import REGINFO_CV_VENTAS_CBTE, REGINFO_CV_VENTAS_CBTE_ALICUOTA

def format_as_dict(format):
    return dict([(k[0], None) for k in format])


def leer_planilla(entrada, sep=','):
    "Convierte una planilla CSV a una lista de diccionarios [{'col': celda}]"
    
    items = []
    csv_reader = csv.reader(open(entrada), dialect='excel', delimiter=sep)
    for row in csv_reader:
        items.append(row)
    if len(items) < 2:
        raise RuntimeError('El archivo no tiene filas validos')
    if len(items[0]) < 2:
        raise RuntimeError('El archivo no tiene columnas (usar %s de separador)' % sep)
    cols = [str(it).strip() for it in items[0]]

    # armar diccionario por cada linea
    items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

    return items


def leer_json(entrada="sired.json"):
    "Carga los datos en formato JSON [{'col': celda}]"
        
    import json
    items = json.load(open(entrada))

    return items


def grabar_json(salida="sired.json"):
    "Guarda los datos en formato JSON"
    
    import json
    json.dump(items, open(salida, "w"), sort_keys=True, indent=4)


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
            if k in totales and k in IMPORTES:
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
        out.write(s)
        
    totales['tipo_reg'] = '2'
    totales['cant_reg_tipo_1'] = str(len(items))
    totales['cuit'] = CUIT
    s = escribir(totales, CAB_FAC_TIPO2)
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
            if 'iva_id' in it and it['iva_id']:
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
                if float(item.get('impto_liq', item.get('imp_iva', 0))) == 0:
                    vals['gravado'] = 'E'
                else:
                    vals['gravado'] = 'G'
            # diseño libre: código de barras y descripción:
            vals['codigo'] = it.get('codigo', '')
            vals['ds'] = it.get('ds', '')
            s = escribir(vals, DETALLE)
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
                if float(item.get('impto_liq', item.get('imp_iva', 0))) == 0:
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
            out.write(s)
        
    totales['tipo_reg'] = '2'
    totales['cant_reg_tipo_1'] = str(len(items))
    totales['cuit'] = CUIT
    s = escribir(totales, VENTAS_TIPO2)
    out.write(s)
    out.close()


class SIRED():
    "Componente para Sistema Resúmen Electrónico de Datos RG1361/02 RG1579/03"

    _public_methods_ = ['CrearBD', 
                        'CrearFactura', 
                        'AgregarDetalleItem', 'AgregarIva', 'AgregarTributo', 
                        'AgregarCmpAsoc', 'AgregarPermiso',
                        'AgregarDato',
                        'GuardarFactura', 'ObtenerFactura',
                        ]
    _public_attrs_ = ['InstallDir', 'Traceback', 'Excepcion', 'Version',
                     ]
    _readonly_attrs_ = _public_attrs_
    _reg_progid_ = "SIRED"
    _reg_clsid_ = "{3DC74AD5-939F-42AB-8381-FCA7AF783C77}"

    def __init__(self):
        self.db_path = os.path.join(self.InstallDir, "sired.db")
        self.Version = __version__
        # Abrir la base de datos
        crear = not os.path.exists(self.db_path)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        if crear:
            from formatos.formato_txt import ENCABEZADO, DETALLE, TRIBUTO, IVA, CMP_ASOC, PERMISO, DATO
            from formatos.formato_sql import esquema_sql
            tipos_registro =  [
                ('encabezado', ENCABEZADO),
                ('detalle', DETALLE),
                ('tributo', TRIBUTO), 
                ('iva', IVA), 
                ('cmp_asoc', CMP_ASOC),
                ('permiso', PERMISO),
                ('dato', DATO),
                ]
            for sql in esquema_sql(tipos_registro):
                self.cursor.execute(sql)

    def CrearFactura(self, concepto=1, tipo_doc=80, nro_doc="", tipo_cbte=1, punto_vta=0,
            cbte_nro=0, imp_total=0.00, imp_tot_conc=0.00, imp_neto=0.00,
            imp_iva=0.00, imp_trib=0.00, imp_op_ex=0.00, fecha_cbte="", fecha_venc_pago="", 
            fecha_serv_desde=None, fecha_serv_hasta=None, 
            moneda_id="PES", moneda_ctz="1.0000", cae="", fch_venc_cae="", id_impositivo='',
            nombre_cliente="", domicilio_cliente="", pais_dst_cmp=None,
            obs_comerciales="", obs_generales="", forma_pago="", incoterms="", 
            idioma_cbte=7, motivos_obs="", descuento=0.0, email="",
            **kwargs
            ):
        "Creo un objeto factura (internamente)"
        fact = {'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbte_nro': cbte_nro, 
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto, 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'nombre_cliente': nombre_cliente,
                'domicilio_cliente': domicilio_cliente,
                'pais_dst_cmp': pais_dst_cmp,
                'obs_comerciales': obs_comerciales,
                'obs_generales': obs_generales,
                'id_impositivo': id_impositivo,
                'forma_pago': forma_pago, 'incoterms': incoterms,
                'cae': cae, 'fecha_vto': fch_venc_cae,
                'motivos_obs': motivos_obs,
                'descuento': descuento,
                'email': email,
                'cbtes_asoc': [],
                'tributos': [],
                'ivas': [],
                'permisos': [],
                'detalles': [],
                'datos': [],
            }
        if fecha_serv_desde: fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fecha_serv_hasta'] = fecha_serv_hasta
        self.factura = fact
        return True

    def EstablecerParametro(self, parametro, valor):
        "Modifico un parametro general a la factura (internamente)"
        self.factura[parametro] = valor
        return True

    def AgregarDato(self, campo, valor, pagina='T'):
        "Agrego un dato a la factura (internamente)"
        self.factura["datos"].append({'campo': campo, 'valor': valor, 'pagina': pagina})
        return True

    def AgregarDetalleItem(self, u_mtx, cod_mtx, codigo, ds, qty, umed, precio, 
                    bonif, iva_id, imp_iva, importe, despacho, 
                    dato_a=None, dato_b=None, dato_c=None, dato_d=None, dato_e=None):
        "Agrego un item a una factura (internamente)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        item = {
                'u_mtx': u_mtx,
                'cod_mtx': cod_mtx,
                'codigo': codigo,                
                'ds': ds,
                'qty': qty,
                'umed': umed,
                'precio': precio,
                'bonif': bonif,
                'iva_id': iva_id,
                'imp_iva': imp_iva,
                'importe': importe,
                'despacho': despacho,
                'dato_a': dato_a,
                'dato_b': dato_b,
                'dato_c': dato_c,
                'dato_d': dato_d,
                'dato_e': dato_e,
                }
        self.factura['detalles'].append(item)
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwarg):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'cbte_tipo': tipo, 'cbte_punto_vta': pto_vta, 'cbte_nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, tributo_id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg):
        "Agrego un tributo a una factura (interna)"
        tributo = { 'tributo_id': tributo_id, 'desc': desc, 'base_imp': base_imp, 
                    'alic': alic, 'importe': importe}
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, iva_id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = { 'iva_id': iva_id, 'base_imp': base_imp, 'importe': importe }
        self.factura['ivas'].append(iva)
        return True
    
    def GuardarFactura(self):
        from formatos.formato_sql import escribir
        escribir([self.factura], self.db)
        return self.factura['id']

    def ActualizarFactura(self, id_factura):
        from formatos.formato_sql import modificar
        self.factura["id"] = id_factura
        modificar(self.factura, self.db)
        return True

    def ObtenerFactura(self, id_factura=None):
        from formatos.formato_sql import leer, max_id
        if not id_factura:
            id_factura = max_id(self.db) 
        facts = list(leer(self.db, ids=[id_factura]))
        if facts:
            self.factura = facts[0]
        return True

    def Consultar(self, **kwargs):
        from formatos.formato_sql import leer
        return leer(self.db, **kwargs)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = SIRED.InstallDir = get_install_dir()

if __name__ == '__main__':
    try:
        if hasattr(sys,"frozen") or False:
            p=os.path.dirname(os.path.abspath(sys.executable))
            os.chdir(p)
        ##sys.stdout = open("salida.txt", "a")
        entrada = {}
        for i, k in enumerate(('encabezados', 'detalles', 'ivas', 'tributos')):
            if len(sys.argv) > i+1:
                filename = sys.argv[i+1]
                if not filename.startswith("--") and os.path.exists(filename):
                    entrada[k] = filename
        if not entrada:
            entrada['encabezado'] = 'facturas3.csv'

        if '--prueba' in sys.argv:
            sired = SIRED()
            
            # creo una factura de ejemplo
            tipo_cbte = 2
            punto_vta = 4000
            fecha = datetime.datetime.now().strftime("%Y%m%d")
            concepto = 3
            tipo_doc = 80; nro_doc = "30000000007"
            cbte_nro = 12345678
            imp_total = "122.00"; imp_tot_conc = "3.00"
            imp_neto = "100.00"; imp_iva = "21.00"
            imp_trib = "1.00"; imp_op_ex = "2.00"; imp_subtotal = "100.00"
            fecha_cbte = fecha; fecha_venc_pago = fecha
            # Fechas del período del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = fecha; fecha_serv_hasta = fecha
            moneda_id = 'PES'; moneda_ctz = '1.000'
            obs_generales = "Observaciones Generales, texto libre"
            obs_comerciales = "Observaciones Comerciales, texto libre"

            nombre_cliente = 'Joao Da Silva'
            domicilio_cliente = 'Rua 76 km 34.5 Alagoas'
            pais_dst_cmp = 16
            id_impositivo = 'PJ54482221-l'
            moneda_id = '012'
            moneda_ctz = 0.5
            forma_pago = '30 dias'
            incoterms = 'FOB'
            idioma_cbte = 1
            motivo = "11"

            cae = None
            fch_venc_cae = None
            
            sired.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                cbte_nro, imp_total, imp_tot_conc, imp_neto,
                imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
                fecha_serv_desde, fecha_serv_hasta, 
                moneda_id, moneda_ctz, cae, fch_venc_cae, id_impositivo,
                nombre_cliente, domicilio_cliente, pais_dst_cmp, 
                obs_comerciales, obs_generales, forma_pago, incoterms, 
                idioma_cbte, motivo)
            
            tipo = 91
            pto_vta = 2
            nro = 1234
            sired.AgregarCmpAsoc(tipo, pto_vta, nro)
            tipo = 5
            pto_vta = 2
            nro = 1234
            sired.AgregarCmpAsoc(tipo, pto_vta, nro)
            
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            sired.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_imp = 100
            importe = 21
            sired.AgregarIva(iva_id, base_imp, importe)
            
            u_mtx = 123456
            cod_mtx = 1234567890123
            codigo = "P0001"
            ds = "Descripcion del producto P0001\n" + "Lorem ipsum sit amet " * 10
            qty = 1.00
            umed = 7
            precio = 100.00
            bonif = 0.00
            iva_id = 5
            imp_iva = 21.00
            importe = 121.00
            despacho = u'Nº 123456'
            sired.AgregarDetalleItem(u_mtx, cod_mtx, codigo, ds, qty, umed, 
                    precio, bonif, iva_id, imp_iva, importe, despacho)

            sired.AgregarDato("prueba", "1234")
            print "Prueba!"
            id_factura = sired.GuardarFactura()
            fact = sired.factura.copy()
            ok = sired.ObtenerFactura(id_factura)
            f = sired.factura
            
            # verificar que los datos se hayan grabado y leido correctamente:
            difs = []
            def cmp_dict(d1, d2, prefijo=None):
                global difs
                if difs is None:
                    difs = []
                for k in set(d1.keys() + d2.keys()):
                    if k in d1 and k in d2:
                        if isinstance(d1[k], list):
                            for i, (v1, v2) in enumerate(zip(d1[k], d2[k])):
                                cmp_dict(v1, v2, (k, i))
                        else:
                            if isinstance(d1[k], Decimal) or isinstance(d2[k], Decimal):
                                d1[k] = float(d1[k])
                                d2[k] = float(d2[k])
                            if isinstance(d1[k], long) or isinstance(d2[k], long):
                                d1[k] = long(d1[k])
                                d2[k] = long(d2[k])
                            if d1[k] != d2[k]:
                                difs.append(("Dif", prefijo, k, d1[k], d2[k]))
            cmp_dict(fact, f)
            for dif in difs:
                print dif
                
            sired.EstablecerParametro("cae", "61123022925855")
            sired.EstablecerParametro("fch_venc_cae", "20110320")
            sired.EstablecerParametro("motivo_obs", "")
            ok = sired.ActualizarFactura(id_factura)
            ok = sired.ObtenerFactura(id_factura)
            assert sired.factura["cae"] == "61123022925855"

            sys.exit(0)

        if '--leer' in sys.argv:
            if '--completar_padron' in sys.argv:
                from padron import PadronAFIP
                padron = PadronAFIP()
                padron.Conectar(trace="--trace" in sys.argv)
                from formatos import formato_txt
                formato = formato_txt.ENCABEZADO
                categorias_iva = dict([(int(v), k) for k, v in categorias.items()])

            else:
                formato = VENTAS_TIPO1
             
            claves = [clave for clave, pos, leng in formato if clave not in ('tipo','info_adic')]
            csv = csv.DictWriter(open("ventas.csv","wb"), claves, extrasaction='ignore')
            csv.writerow(dict([(k, k) for k in claves]))
            f = open("VENTAS.txt")
            for linea in f:
                if str(linea[0])=='2':
                    datos = leer(linea, REGINFO_CV_VENTAS_CBTE)

                    if '--completar_padron' in sys.argv:
                        cuit = datos['nro_doc']
                        print "Consultando AFIP online...", cuit,
                        ok = padron.Consultar(cuit)
                        print padron.direccion, padron.provincia
                        datos["nombre_cliente"] = padron.denominacion.encode("latin1")
                        datos["domicilio_cliente"] = padron.direccion.encode("latin1")
                        datos["localidad_cliente"] = "%s (CP %s) " % (
                                                        padron.localidad.encode("latin1"), 
                                                        padron.cod_postal.encode("latin1")) 
                        datos["provincia_cliente"] = padron.provincia.encode("latin1")
                        datos['cbte_nro'] = datos['cbt_numero_desde']
                        #datos['id_impositivo'] = categorias_iva[int(datos['categoria'])]
                    csv.writerow(datos)
            f.close()
        else:
            # cargar datos desde planillas CSV separadas o JSON:
            if entrada['encabezados'].lower().endswith("csv"):
                facturas = items = leer_planilla(entrada['encabezados'], ";")

                # pre-procesar:
                for factura in facturas:
                    for k, v in factura.items():
                        # decodificar strings (evitar problemas unicode)
                        if isinstance(v, basestring):
                            if isinstance(v, str):
                                v = v.decode("latin1", "ignore")
                            factura[k] = unicodedata.normalize('NFKD', v).encode('ASCII', 'ignore')
                            print k,factura[k]
                        # convertir tipos de datos desde los strings del CSV
                        if k.startswith("imp"):
                            factura[k] = float(v)
                        if k in ('cbt_desde', 'cbt_hasta', 'concepto', 
                                 'punto_vta', 'tipo_cbte', 'tipo_doc', 
                                 'nro_doc', 'cbt_numero'):
                            factura[k] = int(v)

                    alicuotas = {3:0, 4: 10.5, 5: 21., 6: 27}
                    ivas = {}
                    imp_iva = 0.00

                    ruta = os.path.dirname(entrada['encabezados'])
                    prefijos = ("%(tipo_cbte)02d%(cbt_numero)08d",
                               "%(tipo_cbte)02d%(cbt_numero)06d",
                               "%(tipo_cbte)02d%(punto_vta)04d%(cbt_numero)08d",
                               )
                    for prefijo in prefijos:
                        fn = os.path.join(ruta, "%s.csv" % (prefijo % factura))
                        print "Detalle: ", fn
                        if os.path.exists(fn):
                            det = fn
                            print "encontrado!"
                            break
                    else:
                        if 'detalles' in entrada:
                            det = entrada['detalles']
                        else:
                            det = None

                    if det:
                        detalles = leer_planilla(det, ";")

                    for det in detalles:
                        iva_id = det.get('iva_id', 5)
                        if isinstance(det.get('ds'), str):
                            det['ds'] = det['ds'].decode("latin1", "ignore")
                        if 'ds' in det:
                            det['ds'] = unicodedata.normalize('NFKD', det['ds']).encode('ASCII', 'ignore')
                        print det
                        if iva_id:
                            iva_id = int(iva_id)
                            if iva_id not in ivas:
                                ivas[iva_id] = {"base_imp": 0, "importe": 0, "iva_id": iva_id}

                            importe = det.get('importe', det.get('total'))
                            if importe:
                                iva = det.get('imp_iva', None)
                                importe = round(float(importe.replace(",", ".")), 2)
                                if not iva is None:
                                    iva = round(float(iva.replace(",", ".")), 2)
                                # si el iva es incorrecto o no está, liquidar:                                
                                if not iva and iva_id > 3:
                                    # extraer IVA incluido factura B:
                                    if factura["tipo_cbte"] in (6, 7, 8):
                                        neto = round(importe / ((100 + alicuotas[iva_id]) / 100.), 2)
                                        iva = importe - neto
                                    else:
                                        neto = importe
                                        iva = round(neto * alicuotas[iva_id] /100., 2)
                                    print "importe iva calc:", importe, iva
                                else:
                                    neto = importe
                                    # descontar IVA incluido factura B:
                                    if factura["tipo_cbte"] in (6, 7, 8):
                                        neto = neto - iva
                                imp_iva += iva
                                ivas[iva_id]['importe'] += iva
                                ivas[iva_id]['base_imp'] += neto
                                det['imp_iva'] = iva

                    # rearmar estructuras internas:
                    factura['detalles'] = detalles
                    factura['ivas'] = ivas.values()
                    factura['datos'] = []
                    factura['tributos'] = []
                    if 'imp_iva' not in factura or factura['imp_iva'] == "":
                        print "debe agregar el IVA total en el encabezado..."
                        factura['imp_iva'] = imp_iva
                    if 'cbt_numero' in factura:
                        factura['cbt_desde'] = factura['cbt_numero']
                        factura['cbt_hasta'] = factura['cbt_numero']
                    if 'nombre' in factura:
                        factura['nombre_cliente'] = factura['nombre']
                        factura['domicilio_cliente'] = factura['domicilio']
                    factura['cbte_nro'] = factura['cbt_desde']
                    if not 'concepto' in factura:
                        factura['concepto'] = 1

                    # limpio campos que no correspondan (productos vs servicios):
                    if factura['concepto'] == 1:
                        factura['fecha_venc_pago'] = None

            elif entrada['encabezados'].lower().endswith('.json'):
                items = leer_json(entrada['encabezados'])

                
            print "Generando encabezado..."
            generar_encabezado(items)
            print "Generando detalle..."
            generar_detalle(items)
            print "Generando ventas..."
            generar_ventas(items)
            if '--json' in sys.argv:
                grabar_json()

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
    if '--debug' in sys.argv:
        raw_input("presione enter para continuar...")
    ##sys.stdout.close()
