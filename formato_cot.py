#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

# Based on MultipartPostHandler.py (C) 02/2006 Will Holcomb <wholcomb@gmail.com>
# Ejemplos iniciales gracias a "Matias Gieco matigro@gmail.com"

"Módulo para analizar el formato de un remito electrónico (COT)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"

import sys


registros = {
    '01': 'HEADER',
    '02': 'REMITO',
    '03': 'PRODUCTOS',
    '04': 'FOOTER',
    }

formato = {
    '01': [
        'TIPO_REGISTRO', 
        'CUIT_EMPRESA'
        ],
    '02': [
        'TIPO_REGISTRO', 
        'FECHA_EMISION',
        'CODIGO_UNICO',
        'FECHA_SALIDA_TRANSPORTE',
        'HORA_SALIDA_TRANSPORTE',
        'SUJETO_GENERADOR',
        'DESTINATARIO_CONSUMIDOR_FINAL',
        'DESTINATARIO_TIPO_DOCUMENTO',
        'DESTINATARIO_DOCUEMNTO',
        'DESTIANTARIO_CUIT',
        'DESTINATARIO_RAZON_SOCIAL',
        'DESTINATARIO_TENEDOR',
        'DESTINO_DOMICILIO_CALLE',
        'DESTINO_DOMICILIO_NUMERO',
        'DESTINO_DOMICILIO_COMPLE',
        'DESTINO_DOMICILIO_PISO',
        'DESTINO_DOMICILIO_DTO',
        'DESTINO_DOMICILIO_BARRIO',
        'DESTINO_DOMICILIO_CODIGOP',
        'DESTINO_DOMICILIO_LOCALIDAD',
        'DESTINO_DOMICILIO_PROVINCIA',
        'PROPIO_DESTINO_DOMICILIO_CODIGO',
        'ENTREGA_DOMICILIO_ORIGEN',
        'ORIGEN_CUIT',
        'ORIGEN_RAZON_SOCIAL',
        'EMISOR_TENEDOR',
        'ORIGEN_DOMICILIO_CALLE',
        'ORIGEN DOMICILIO_NUMBERO',
        'ORIGEN_DOMICILIO_COMPLE',
        'ORIGEN_DOMICILIO_PISO',
        'ORIGEN_DOMICILIO_DTO',
        'ORIGEN_DOMICILIO_BARRIO',
        'ORIGEN_DOMICILIO_CODIGOP',
        'ORIGEN_DOMICILIO_LOCALIDAD',
        'ORIGEN_DOMICILIO_PROVINCIA',
        'TRANSPORTISTA_CUIT',
        'TIPO_RECORRIDO',
        'RECORRIDO_LOCALIDAD',
        'RECORRIDO_CALLE',
        'RECORRIDO_RUTA',
        'PATENTE_VEHICULO',
        'PATENTE_ACOPLADO',
        'PRODUCTO_NO_TERM_DEV',
        'IMPORTE',
        ],
    '03': [
        'TIPO_REGISTRO',
        'CODIGO_UNICO_PRODUCTO',
        'RENTAS_CODIGO_UNIDAD_MEDIDA',
        'CANTIDAD',
        'PROPIO_CODIGO_PRODUCTO',
        'PROPIO_DESCRIPCION_PRODUCTO',
        'PROPIO_DESCRIPCION_UNIDAD_MEDIDA',
        'CANTIDAD_AJUSTADA',
        ],
    '04': [
        'TIPO_REGISTRO',
        'CANTIDAD_TOTAL_REMITOS',
        ]
    }


f = open(sys.argv[1])

for l in f:
    reg = l[0:2]
    if reg in registros:
        print "Registro: ", registros[reg]
        campos = l.strip("\r").strip("\n").split("|")
        for i, campo in enumerate(campos): 
            print " * %s: |%s|" % (formato[reg][i], campo, )
    else:
        print "registro incorrecto:", l
