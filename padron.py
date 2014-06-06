#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Herramienta para procesar y consultar el Padrón Unico de Contribuyentes AFIP"

# Documentación e información adicional: 
#    http://www.sistemasagiles.com.ar/trac/wiki/PadronContribuyentesAFIP

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2014 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.02a"


import os
import shelve
import sqlite3
import urllib2
import zipfile
from email.utils import formatdate
import sys
from utils import leer, escribir, N, A, I, get_install_dir


# formato y ubicación archivo completo de la condición tributaria según RG 1817

FORMATO = [
    ("nro_doc", 11, N, ""),
    ("denominacion", 30, A, ""),
    ("imp_ganancias", 2, A,	"'NI', 'AC','EX', 'NC'"),
    ("imp_iva", 2, A, "'NI' , 'AC','EX','NA','XN','AN'"),
    ("monotributo", 2, A, "'NI', 'Codigo categoria tributaria'"),
    ("integrante_soc", 1, A, "'N' , 'S'"),
    ("empleador", 1, A, "'N', 'S'"),
    ("actividad_monotributo", 2, A, ""),
    ("tipo_doc", 2, N, "80: CUIT, 96: DNI, etc."),
    ("cat_iva", 2, N, "1: RI, 4: EX, 5: CF, 6: MT, etc"),
    ]	 

DEBUG = True

URL = "http://www.afip.gob.ar/genericos/cInscripcion/archivos/apellidoNombreDenominacion.zip"


class PadronAFIP():
    "Interfaz para consultar situación tributaria (Constancia de Inscripcion)"

    _public_methods_ = ['Buscar', 'Descargar', 'Procesar', 'Guardar',
                        'ConsultarDomicilios',
                        ]
    _public_attrs_ = ['InstallDir', 'Traceback', 'Excepcion', 'Version',
                      'cuit', 'denominacion', 'imp_ganancias', 'imp_iva',  
                      'monotributo', 'integrante_soc', 'empleador', 
                      'actividad_monotributo', 'cat_iva', 'domicilios',
                      'tipo_doc', 'nro_doc',
                     ]
    _readonly_attrs_ = _public_attrs_[3:-1]
    _reg_progid_ = "PadronAFIP"
    _reg_clsid_ = "{6206DF5E-3EEF-47E9-A532-CD81EBBAF3AA}"

    def __init__(self):
        self.db_path = os.path.join(self.InstallDir, "padron.db")
        self.Version = __version__
        # Abrir la base de datos
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

    def Descargar(self, url=URL, filename="padron.txt", proxy=None):
        "Descarga el archivo de AFIP, devuelve 200 o 304 si no fue modificado"
        proxies = {}
        if proxy:
            proxies['http'] = proxy
            proxies['https'] = proxy
            proxy_handler = urllib2.ProxyHandler(proxies)
        print "Abriendo URL %s ..." % url
        req = urllib2.Request(url)
        if os.path.exists(filename):
            http_date = formatdate(timeval=os.path.getmtime(filename), 
                                   localtime=False, usegmt=True)  
            req.add_header('If-Modified-Since', http_date)
        try:
            web = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            if e.code == 304:
                print "No modificado desde", http_date
                return 304
            else:
                raise
        # leer info del request:
        meta = web.info()
        lenght = float(meta['Content-Length'])
        date = meta['Last-Modified']
        tmp = open(filename + ".zip", "wb")
        print "Guardando"
        size = 0
        p0 = None
        while True:
            p = int(size / lenght * 100)
            if p0 is None or p>p0:
                print "Leyendo ... %0d %%" % p
                p0 = p
            data = web.read(1024*100)
            size = size + len(data)
            if not data:
                print "Descarga Terminada!"
                break
            tmp.write(data)
        print "Abriendo ZIP..."
        tmp.close()
        web.close()
        uf = open(filename + ".zip", "rb")
        zf = zipfile.ZipFile(uf)
        for fn in zf.namelist():
            print "descomprimiendo", fn
            tf = open(filename, "wb")
            tf.write(zf.read(fn))
            tf.close()
        return 200
            
    def Procesar(self, filename="padron.txt", borrar=False):
        "Analiza y crea la base de datos interna sqlite para consultas" 
        f = open(filename, "r")
        keys = [k for k, l, t, d in FORMATO]
        # conversion a planilla csv (no usado)
        if False and not os.path.exists("padron.csv"):
            csvfile = open('padron.csv', 'wb')
            import csv
            wr = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)    
            for i, l in enumerate(f):
                if i % 100000 == 0: 
                    print "Progreso: %d registros" % i
                r = leer(l, FORMATO)
                row = [r[k] for k in keys]
                wr.writerow(row)
            csvfile.close()
        f.seek(0)
        if os.path.exists(self.db_path) and borrar:
            os.remove(self.db_path)
        if True:
            db = db = sqlite3.connect(self.db_path)
            c = db.cursor()
            c.execute("CREATE TABLE padron ("
                        "tipo_doc INTEGER, "
                        "nro_doc INTEGER, "
                        "denominacion VARCHAR(30), "
                        "imp_ganancias VARCHAR(2), "
                        "imp_iva VARCHAR(2), "
                        "monotributo VARCHAR(1), "
                        "integrante_soc VARCHAR(1), "
                        "empleador VARCHAR(1), "
                        "actividad_monotributo VARCHAR(2), "
                        "cat_iva INTEGER DEFAULT NULL, "
                        "PRIMARY KEY (tipo_doc, nro_doc)"
                      ");")
            c.execute("CREATE TABLE domicilio ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "tipo_doc INTEGER, "
                        "nro_doc INTEGER, "
                        "direccion TEXT, "
                        "FOREIGN KEY (tipo_doc, nro_doc) REFERENCES padron "
                      ");")
            # importar los datos a la base sqlite
            for i, l in enumerate(f):
                if i % 10000 == 0: print i
                l = l.strip("\x00")
                r = leer(l, FORMATO)
                params = [r[k] for k in keys]
                params[-2] = 80         # agrego tipo_doc = CUIT
                params[-1] = None       # cat_iva no viene de AFIP
                placeholders = ", ".join(["?"] * len(params))
                c.execute("INSERT INTO padron VALUES (%s)" % placeholders,
                          params)
            db.commit()
            c.close()
            db.close()
        
    def Buscar(self, nro_doc, tipo_doc=80):
        "Devuelve True si fue encontrado y establece atributos con datos"
        # cuit: codigo único de identificación tributaria del contribuyente
        #       (sin guiones)
        self.cursor.execute("SELECT * FROM padron WHERE "
                            " tipo_doc=? AND nro_doc=?", [tipo_doc, nro_doc])
        row = self.cursor.fetchone()
        for key in [k for k, l, t, d in FORMATO]:
            if row:
                setattr(self, key, str(row[key]))
            else:
                setattr(self, key, '')
        if self.tipo_doc == 80:
            self.cuit = self.nro_doc
        elif self.tipo_doc == 96:
            self.dni = self.nro_doc
        return True if row else False

    def ConsultarDomicilios(self, nro_doc, tipo_doc=80, cat_iva=None):
        "Busca los domicilios, devuelve la cantidad y establece la lista"
        self.cursor.execute("SELECT direccion FROM domicilio WHERE "
                            " tipo_doc=? AND nro_doc=?", [tipo_doc, nro_doc])
        filas = self.cursor.fetchall()
        self.domicilios = [fila['direccion'] for fila in filas]
        return len(filas)

    def Guardar(self, tipo_doc, nro_doc, denominacion, cat_iva, direccion):
        "Agregar o actualizar los datos del cliente"
        if self.Buscar(nro_doc, tipo_doc):
            sql = ("UPDATE padron SET denominacion=?, cat_iva=? "
                    "WHERE tipo_doc=? AND nro_doc=?")
            params = [denominacion, cat_iva, tipo_doc, nro_doc]
        else:
            sql = ("INSERT INTO padron (tipo_doc, nro_doc, denominacion, "
                    "cat_iva) VALUES (?, ?, ?, ?)")
            params = [tipo_doc, nro_doc, denominacion, cat_iva]
        self.cursor.execute(sql, params)
        # agregar el domicilio solo si no existe:
        if direccion:
            self.cursor.execute("SELECT * FROM domicilio WHERE direccion=?",
                                [direccion])
            if not self.cursor.rowcount:
                sql = ("INSERT INTO domicilio (nro_doc, tipo_doc, direccion)"
                        "VALUES (?, ?, ?)")
                self.cursor.execute(sql, nro_doc, tipo_doc, direccion)
        self.db.commit()
        return True


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = PadronAFIP.InstallDir = get_install_dir()

if __name__ == "__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(PadronAFIP)
    else:
        padron = PadronAFIP()
        import time
        t0 = time.time()
        if "--descargar" in sys.argv:
            padron.Descargar()
        if "--procesar" in sys.argv:
            padron.Procesar(borrar='--borrar' in sys.argv)
        cuit = len(sys.argv)>1 and sys.argv[1] or "20267565393"
        # consultar un cuit:
        ok = padron.Buscar(cuit)
        if ok:
            print "Denominacion:", padron.denominacion
            print "IVA:", padron.imp_iva
            padron.ConsultarDomicilios(cuit)
            for dom in padron.domicilios:
                print dom
        t1 = time.time()
        print "tiempo", t1 -t0

