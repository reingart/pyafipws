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


def configurar(schema):
    tablas = {}
    campos = {}
    if not schema:
        for tabla in "encabezado", "detalle", "cmp_asoc", "permiso", "tributo", "iva":
            tablas[tabla] = tabla
            campos[tabla] = {"id": "id"}
    return tablas, campos

def ejecutar(cur, sql, params=None):
    print sql, params
    if params is None:
        return cur.execute(sql)
    else:
        return cur.execute(sql, params)


def max_id(db, schema={}):
    cur = db.cursor()
    tablas, campos = configurar(schema)
    query = ("SELECT MAX(%%(id)s) FROM %(encabezado)s" % tablas) % campos["encabezado"]
    if DEBUG: print "ejecutando",query
    ret = None
    try:
        ejecutar(cur, query)
        for row in cur:
            ret = row[0]
        if not ret:
            ret = 0
        print "MAX_ID = ", ret
        return ret
    finally:
        cur.close()


def escribir(facts, db, schema={}, commit=True):
    from formato_txt import ENCABEZADO, DETALLE, TRIBUTO, IVA, CMP_ASOC, PERMISO, DATO
    tablas, campos = configurar(schema)
    cur = db.cursor()
    try:
        for dic in facts:
            if not 'id' in dic:
                dic['id'] = max_id(db, schema={}) + 1
            query = "INSERT INTO %(encabezado)s (%%s) VALUES (%%s)" % tablas
            fields = ','.join([campos["encabezado"].get(k, k) for k,t,n in ENCABEZADO if k in dic])
            values = ','.join(['?' for k,t,n in ENCABEZADO if k in dic])
            if DEBUG: print "Ejecutando2: %s %s" % (query % (fields, values), [dic[k] for k,t,n in ENCABEZADO if k in dic])
            ejecutar(cur, query % (fields, values), [dic[k] for k,t,n in ENCABEZADO if k in dic])
            query = ("INSERT INTO %(detalle)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % tablas) % campos["detalle"]
            for item in dic['detalles']:
                fields = ','.join([campos["detalle"].get(k, k) for k,t,n in DETALLE if k in item])
                values = ','.join(['?' for k,t,n in DETALLE if k in item])
                if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in DETALLE if k in item])
                ejecutar(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in DETALLE if k in item])
            if 'cbtes_asoc' in dic and tablas["cmp_asoc"]: 
                query = ("INSERT INTO %(cmp_asoc)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % tablas) % campos["cmp_asoc"]
                for item in dic['cbtes_asoc']:
                    fields = ','.join([campos["cmp_asoc"].get(k, k) for k,t,n in CMP_ASOC if k in item])
                    values = ','.join(['?' for k,t,n in CMP_ASOC if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in CMP_ASOC if k in item])
                    ejecutar(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in CMP_ASOC if k in item])
            if 'permisos' in dic: 
                query = ("INSERT INTO %(permiso)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % tablas) % campos["permiso"]
                for item in dic['permisos']:
                    fields = ','.join([campos["permiso"].get(k, k) for k,t,n in PERMISO if k in item])
                    values = ','.join(['?' for k,t,n in PERMISO if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in PERMISO if k in item])
                    ejecutar(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in PERMISO if k in item])
            if 'tributos' in dic: 
                query = ("INSERT INTO %(tributo)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % tablas) % campos["tributo"]
                for item in dic['tributos']:
                    fields = ','.join([campos["tributo"].get(k, k) for k,t,n in TRIBUTO if k in item])
                    values = ','.join(['?' for k,t,n in TRIBUTO if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in TRIBUTO if k in item])
                    ejecutar(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in TRIBUTO if k in item])
            if 'ivas' in dic: 
                query = ("INSERT INTO %(iva)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % tablas) % campos["iva"]
                for item in dic['ivas']:
                    fields = ','.join([campos["iva"].get(k, k) for k,t,n in IVA if k in item])
                    values = ','.join(['?' for k,t,n in IVA if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in IVA if k in item])
                    ejecutar(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in IVA if k in item])
        if commit:
            db.commit()
    finally:
        pass



def ayuda():
    print "-- Formato:"
    from formato_txt import ENCABEZADO, DETALLE, TRIBUTO, IVA, CMP_ASOC, DATO
    tipos_registro =  [
        ('encabezado', ENCABEZADO),
        ('detalle', DETALLE),
        ('tributo', TRIBUTO), 
        ('iva', IVA), 
        ('cmp_asoc', CMP_ASOC),
        ('dato', DATO),
        ]
    print "-- Esquema:"
    for sql in esquema_sql(tipos_registro):
        print sql


if __name__ == "__main__":
    ayuda()
