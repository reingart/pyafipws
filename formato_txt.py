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

"Módulo para manejo de archivos TXT simil SIAP-RECE (Cobol et. al.)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"

from decimal import Decimal

CHARSET = 'latin1'

# Formato de entrada/salida similar a SIAP RECE, con agregados

# definición del formato del archivo de intercambio:
N = 'Numerico'
A = 'Alfanumerico'
I = 'Importe'

ENCABEZADO = [
    ('tipo_reg', 1, N), # 0: encabezado
    ('webservice', 6, A), # wsfe, wsbfe, wsfex, wsfev1
    ('fecha_cbte', 8, A),
    ('tipo_cbte', 2, N), ('punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ('tipo_expo', 1, N), # 1:bienes, 2:servicios,... 
    ('permiso_existente', 1, A), # S/N/
    ('pais_dst_cmp', 3, N), # 203
    ('nombre_cliente', 200, A), # 'Joao Da Silva'
    ('tipo_doc', 2, N),
    ('nro_doc', 11, N), # cuit_pais_cliente 50000000016
    ('domicilio_cliente', 300, A), # 'Rua 76 km 34.5 Alagoas'
    ('id_impositivo', 50, A), # 'PJ54482221-l'    
    ('imp_total', (15,3), I), 
    ('imp_tot_conc', (15,3), I),
    ('imp_neto', (15,3), I), ('impto_liq', (15,3), I),
    ('impto_liq_nri', (15,3), I), ('imp_op_ex', (15,3), I),
    ('impto_perc', 15, I), ('imp_iibb', (15,3), I),
    ('impto_perc_mun', (15,3), I), ('imp_internos', (15,3), I),
    ('imp_trib', (15,3), I),
    ('moneda_id', 3, A),
    ('moneda_ctz', (10,6), I), #10,6
    ('obs_comerciales', 1000, A),
    ('obs_generales', 1000, A),
    ('forma_pago', 50, A),
    ('incoterms', 3, A),
    ('incoterms_ds', 20, A),
    ('idioma_cbte', 1, A),
    ('zona', 5, A),
    ('fecha_venc_pago', 8,A),
    ('presta_serv', 1, N),
    ('fecha_serv_desde', 8, A),
    ('fecha_serv_hasta', 8, A),
    ('cae', 14, N), ('fecha_vto_cae', 8, A),
    ('resultado', 1, A), 
    ('reproceso', 1, A),
    ('motivo', 1000, A),
    ('id', 15, N),
    ('telefono_cliente', 50, A),
    ('localidad_cliente', 50, A),
    ('provincia_cliente', 50, A),
    ('formato_id', 10, N),
    ('email', 100, A),
    ('pdf', 100, A),
    ('err_code', 6, A),
    ('err_msg', 1000, A),
    ('Dato_adicional1', 30, A),
    ('Dato_adicional2', 30, A),
    ('Dato_adicional3', 30, A),
    ('Dato_adicional4', 30, A),
    ]

DETALLE = [
    ('tipo_reg', 1, N), # 1: detalle item
    ('codigo', 30, A),
    ('qty', (12,2), I),
    ('umed', 2, N),
    ('precio', (12,3), I),
    ('importe', (14,3), I),
    ('iva_id', 5, N),
    ('ds', 4000, A),
    ('ncm', 15, A),
    ('sec', 15, A),
    ('bonif', 15, I),
    ]

PERMISO = [
    ('tipo_reg', 1, N), # 2: permiso
    ('id_permiso', 16, A),
    ('dst_merc', 3, N),
    ]

CMP_ASOC = [
    ('tipo_reg', 1, N), # 3: comprobante asociado
    ('cbte_tipo', 3, N), ('cbte_punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ]

IVA = [
    ('tipo_reg', 1, N), # 4: alícuotas de iva
    ('iva_id', 5, N),
    ('base_imp', (15, 3), I), 
    ('importe', (15, 3), I), 
    ]

TRIBUTO = [
    ('tipo_reg', 1, N), # 5: tributos
    ('tributo_id', 5, N),
    ('desc', 100, A),
    ('base_imp', (15, 3), I), 
    ('alic', 15, I), 
    ('importe', (15, 3), I), 
    ]

DATO = [
    ('tipo_reg', 1, N), # 9: datos adicionales
    ('campo', 30, A),
    ('valor', 1000, A),
    ]
    
def leer_linea_txt(linea, formato):
    dic = {}
    comienzo = 1
    for (clave, longitud, tipo) in formato:    
        if isinstance(longitud, tuple):
            longitud, decimales = longitud
        else:
            decimales = 2
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        try:
            if tipo == N:
                if valor:
                    valor = int(valor)
                else:
                    valor = None
            elif tipo == I:
                if valor:
                    try:
                        valor = valor.strip(" ")
                        if '.' in valor:
                            valor = float(valor)
                        else:
                            valor = float(("%%s.%%0%sd" % decimales) % (int(valor[:-decimales] or '0'), int(valor[-decimales:] or '0')))
                    except ValueError:
                        raise ValueError("Campo invalido: %s = '%s'" % (clave, valor))
                else:
                    valor = None
            elif tipo == A:
                valor = valor.replace("\v","\n") # reemplazo salto de linea
            dic[clave] = valor
            comienzo += longitud
        except Exception, e:
            raise ValueError("Error al leer campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return dic

def leer(fn="entrada.txt"):
    "Analiza un archivo TXT y devuelve un diccionario"
    f_entrada = open(fn,"r")
    try:
        regs = []
        reg = None
        for linea in f_entrada:
            linea = unicode(linea, CHARSET)
            if str(linea[0])=='0':
                encabezado = leer_linea_txt(linea, ENCABEZADO)
                reg = encabezado
                reg.update({
                    'cbtes_asoc': [],
                    'tributos': [],
                    'ivas': [],
                    'permisos': [],
                    'detalles': [],
                    'datos': [],
                })
                regs.append(reg)
            elif str(linea[0])=='1':
                detalle = leer_linea_txt(linea, DETALLE)
                detalle['id'] = encabezado['id']
                reg['detalles'].append(detalle)
            elif str(linea[0])=='2':
                permiso = leer_linea_txt(linea, PERMISO)
                permiso['id'] = encabezado['id']
                reg['permisos'].append(permiso)
            elif str(linea[0])=='3':
                cbtasoc = leer_linea_txt(linea, CMP_ASOC)
                cbtasoc['id'] = encabezado['id']
                reg['cbtasocs'].append(cbtasoc)
            elif str(linea[0])=='4':
                iva = leer_linea_txt(linea, IVA)
                iva['id'] = encabezado['id']
                reg['ivas'].append(iva)
            elif str(linea[0])=='5':
                tributo = leer_linea_txt(linea, TRIBUTO)
                tributo['id'] = encabezado['id']
                reg['tributos'].append(tributo)
            elif str(linea[0])=='9':
                dato = leer_linea_txt(linea, DATO)
                dato['id'] = encabezado['id']
                reg['datos'].append(dato)
                print dato
            else:
                print "Tipo de registro incorrecto:", linea[0]
    finally:
        f_entrada.close()

    return regs

def ayuda():
    print "Formato:"
    tipos_registro =  [
        ('Encabezado', ENCABEZADO),
        ('Detalle Item', DETALLE),
        ('Tributo', TRIBUTO), 
        ('Iva', IVA), 
        ('Comprobante Asociado', CMP_ASOC),
        ('Datos Adicionales', DATO),
        ]
    for msg, formato in tipos_registro:
        comienzo = 1
        print "== %s ==" % msg
        for fmt in formato:
            clave, longitud, tipo = fmt[0:3]
            if isinstance(longitud, tuple):
                longitud, decimales = longitud
            else:
                decimales = 2
            print " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                clave, comienzo, longitud, tipo, decimales)
            comienzo += longitud

if __name__ == "__main__":
    ayuda()