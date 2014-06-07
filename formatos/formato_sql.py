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

"Módulo para manejo de archivos SQL"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2014 Mariano Reingart"
__license__ = "GPL 3.0"

from decimal import Decimal

DEBUG = False

def esquema_sql(tipos_registro, conf={}):
    from formato_txt import A, N, I
    
    for tabla, formato in tipos_registro:
        sql = []
        sql.append("CREATE TABLE %s (" % tabla)
        if tabla!='encabezado':
            # agrego id como fk
            id = [('id', 15, N)]
        else:
            id = []
        for (clave, longitud, tipo) in id+formato:
            clave_orig = clave
            if conf:
                if tabla == 'encabezado':
                    clave = conf["encabezado"].get(clave, clave)
                if tabla == 'detalle':
                    clave = conf["detalle"].get(clave, clave)
                if tabla == 'iva':
                    clave = conf["iva"].get(clave, clave)
                if tabla == 'tributo':
                    clave = conf["tributo"].get(clave, clave)
                if tabla == 'cmp_asoc':
                    clave = conf["cmp_asoc"].get(clave, clave)
                if tabla == 'permiso':
                    clave = conf["permiso"].get(clave, clave)
            if isinstance(longitud, (tuple, list)):
                longitud, decimales = longitud
            else:
                decimales = 2
            sql.append ("    %s %s %s%s%s" % (
                clave, 
                {N: 'INTEGER', I: 'NUMERIC', A: 'VARCHAR'}[tipo], 
                {I: "(%s, %s)" % (longitud, decimales), A: '(%s)' % longitud, N: ''}[tipo],
                clave == 'id' and (tabla=='encabezado' and " PRIMARY KEY" or " FOREING KEY encabezado") or "",
                formato[-1][0]!=clave_orig and "," or ""))
        sql.append(")")
        sql.append(";")
        if DEBUG: print '\n'.join(sql)
        yield '\n'.join(sql)    


def ayuda():
    print "Formato:"
    from formato_txt import ENCABEZADO, DETALLE, TRIBUTO, IVA, CMP_ASOC, DATO
    tipos_registro =  [
        ('encabezado', ENCABEZADO),
        ('detalle', DETALLE),
        ('tributo', TRIBUTO), 
        ('iva', IVA), 
        ('cmp_asoc', CMP_ASOC),
        ('dato', DATO),
        ]
    print "Esquema:"
    for sql in esquema_sql(tipos_registro):
        print sql


if __name__ == "__main__":
    ayuda()
