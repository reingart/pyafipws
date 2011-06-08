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

"Módulo para manejo de Facturas Electrónicas en tablas DBF (dBase, FoxPro, Clipper et.al.)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"

from decimal import Decimal

try:
    import dbf
    dbf.encoding('cp850')
except:
    print "para soporte de DBF debe instalar dbf"
    print "     http://pypi.python.org/pypi/dbf/"
    
CHARSET = 'latin1'
DEBUG = True

# Formato de entrada/salida similar a SIAP RECE, con agregados

# definición del formato del archivo de intercambio:

from formato_txt import A, N, I, ENCABEZADO, DETALLE, TRIBUTO, IVA, CMP_ASOC, PERMISO, DATO

# agrego identificadores unicos para relacionarlos con el encabezado
DETALLE = [('id', 15, N)] + DETALLE
TRIBUTO = [('id', 15, N)] + TRIBUTO
IVA = [('id', 15, N)] + IVA
CMP_ASOC = [('id', 15, N)] + CMP_ASOC
PERMISO = [('id', 15, N)] + PERMISO
DATO = [('id', 15, N)] + DATO


def definir_campos(formato):
    "Procesar la definición de campos para DBF según el formato txt"
    claves, campos = [], []
    for fmt in formato:
        clave, longitud, tipo = fmt[0:3]
        if isinstance(longitud, tuple):
            longitud, decimales = longitud
        else:
            decimales = 2
        if longitud>250:
            tipo = "M"                  # memo!
        elif tipo == A:
            tipo = "C(%s)" % longitud   # character
        elif tipo == N:
            tipo = "N(%s,0)" % longitud # numeric
        elif tipo == I:
            tipo = "N(%s,%s)" % (longitud, decimales) # "currency"
        else:
            raise RuntimeError("Tipo desconocido: %s %s %s %s" % (tipo, clave, longitud, decimales))
        nombre =dar_nombre_campo(clave)
        campo = "%s %s" % (nombre, tipo)
        campos.append(campo)
        claves.append(nombre)
    return claves, campos


CLAVES_ESPECIALES = {
    'Dato_adicional1': "datoadic01",
    'Dato_adicional2': "datoadic02",
    'Dato_adicional3': "datoadic03",
    'Dato_adicional4': "datoadic04",
    }


def dar_nombre_campo(clave):
    "Reducir nombre de campo a 10 caracteres, sin espacios ni _, sin repetir"
    nombre = CLAVES_ESPECIALES.get(clave)
    if not nombre:
        nombre = clave.replace("_","")[:10]
    return nombre.lower()


def leer(archivos=None):
    "Leer las tablas dbf y devolver una lista de diccionarios con las facturas"
    if DEBUG: print "Leyendo DBF..."
    if archivos is None: archivos = {}
    regs = {}
    formatos = [('Encabezado', ENCABEZADO, None), 
                ('Detalle', DETALLE, 'detalles'),
                ('Iva', IVA, 'ivas'), 
                ('Tributo', TRIBUTO, 'tributos'), 
                ('Permiso', PERMISO, 'permisos'),
                ('Comprobante Asociado', CMP_ASOC, 'cmps_asocs'),
                ('Dato', DATO, 'datos'),
                ]
    for nombre, formato, subclave in formatos:
        filename = archivos.get(nombre.lower(), "%s.dbf" % nombre[:8])
        if DEBUG: print "leyendo tabla", nombre, filename
        tabla = dbf.Table(filename)
        for reg in tabla:
            r = {}
            d = reg.scatter_fields() 
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                nombre = dar_nombre_campo(clave)
                v = d[nombre]
                r[clave] = v
            # agrego 
            if formato==ENCABEZADO:
                r.update({
                    'detalles': [],
                    'ivas': [],
                    'tributos': [],
                    'permisos': [],
                    'cmps_asocs': [],
                    'datos': [],
                    })
                regs[r['id']] = r
            else:
                regs[r['id']][subclave].append(r) 
                
    return regs


def escribir(regs, archivos=None):
    "Grabar en talbas dbf la lista de diccionarios con la factura"
    if DEBUG: print "Creando DBF..."
    if not archivos: filenames = {}
    
    for reg in regs:
        formatos = [('Encabezado', ENCABEZADO, [reg]), 
                    ('Detalle', DETALLE, reg.get('detalles', [])), 
                    ('Iva', IVA, reg.get('ivas', [])), 
                    ('Tributo', TRIBUTO, reg.get('tributos', [])),
                    ('Permiso', PERMISO, reg.get('permisos', [])), 
                    ('Comprobante Asociado', CMP_ASOC, reg.get('cbtes_asoc', [])),
                    ('Dato', DATO, reg.get('datos', [])), 
                    ]
        for nombre, formato, l in formatos:
            claves, campos = definir_campos(formato)
            filename = archivos.get(nombre.lower(), "%s.dbf" % nombre[:8])
            if DEBUG: print "leyendo tabla", nombre, filename
            tabla = dbf.Table(filename, campos)

            for d in l:
                r = {}
                for fmt in formato:
                    clave, longitud, tipo = fmt[0:3]
                    if clave=='id':
                        v = reg['id']
                    else:
                        v = d.get(clave, None)
                    if DEBUG: print clave,v, tipo
                    if v is None and tipo == A:
                        v = ''
                    if (v is None or v=='') and tipo in (I, N):
                        v = 0
                    if tipo == A:
                        if isinstance(v, str):
                            v = unicode(v,'latin1', 'ignore')
                        else:
                            v = str(v)
                    r[dar_nombre_campo(clave)] = v
                registro = tabla.append(r)
            tabla.close()


def ayuda():
    "Imprimir ayuda con las tablas DBF y definición de campos"
    print "=== Formato DBF: ==="
    tipos_registro =  [
        ('Encabezado', ENCABEZADO),
        ('Detalle Item', DETALLE),
        ('Iva', IVA), 
        ('Tributo', TRIBUTO), 
        ('Comprobante Asociado', CMP_ASOC),
        ('Permisos', PERMISO),
        ('Datos', DATO),
        ]
    for msg, formato in tipos_registro:
        filename =  "%s.dbf" % msg.lower()[:8]
        print "==== %s (%s) ====" % (msg, filename)
        claves, campos = definir_campos(formato)
        for campo in campos:
            print " * Campo: %s" % (campo,)


if __name__ == "__main__":
    ayuda()