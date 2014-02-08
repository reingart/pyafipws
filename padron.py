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

"Herramienta para procesar y consultar el Padrón Unico de Contribuyentes de AFIP"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2014 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"


import os
import shelve
import sqlite3
import urllib2
import zipfile
from email.utils import formatdate
import sys
from utils import leer, escribir, N, A, I, get_install_dir


FORMATO = [
    ("cuit", 11, N, ""),
    ("denominacion", 30, A, ""),
    ("imp_ganancias", 2, A,	"'NI', 'AC','EX', 'NC'"),
    ("imp_iva", 2, A, "'NI' , 'AC','EX','NA','XN','AN'"),
    ("monotributo", 2, A, "'NI', 'Codigo categoria tributaria'"),
    ("integrante_soc", 1, A, "'N' , 'S'"),
    ("empleador", 1, A, "'N', 'S'"),
    ("actividad_monotributo", 2, A, ""),
    ]	 

DEBUG = True

URL = "http://www.afip.gob.ar/genericos/cInscripcion/archivos/apellidoNombreDenominacion.zip"


class PadronAFIP():
    "Interfaz para el WebService de Constatación de Comprobantes"

    _public_methods_ = ['Buscar', 'Descargar', 'Procesar',                    
                        ]
    _public_attrs_ = ['InstallDir', 'Traceback', 'Excepcion', 'Version',
                      'cuit', 'denominacion', 'imp_ganancias', 'imp_iva',  
                      'monotributo', 'integrante_soc', 'empleador', 
                      'actividad_monotributo']
    _readonly_attrs_ = _public_attrs_[3:-1]
    _reg_progid_ = "PadronAFIP"
    _reg_clsid_ = "{6206DF5E-3EEF-47E9-A532-CD81EBBAF3AA}"

    def __init__(self):
        self.db_path = os.path.join(self.InstallDir, "padron.db")
        self.Version = __version__

    def Descargar(self, url=URL, filename="padron.txt", proxy=None):
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
            
    def Procesar(self, filename="padron.txt"):
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
        os.remove(self.db_path)
        if not os.path.exists(self.db_path):
            db = sqlite3.connect(self.db_path)
            c = db.cursor()
            c.execute("CREATE TABLE padron ("
                        "cuit INTEGER PRIMARY KEY, "
                        "denominacion VARCHAR(30), "
                        "imp_ganancias VARCHAR(2), "
                        "imp_iva VARCHAR(2), "
                        "monotributo VARCHAR(1), "
                        "integrante_soc VARCHAR(1), "
                        "empleador VARCHAR(1), "
                        "actividad_monotributo VARCHAR(2)"
                      ");")
            # importar los datos a la base sqlite
            for i, l in enumerate(f):
                if i % 10000 == 0: print i
                r = leer(l, FORMATO)
                params = [r[k] for k in keys]
                c.execute("INSERT INTO padron VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          params)
            db.commit()
            c.close()
            db.close()
        
    def Buscar(self, cuit):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute("SELECT * FROM padron WHERE cuit=?", [cuit])
        row = c.fetchone()
        for key in [k for k, l, t, d in FORMATO]:
            if row:
                setattr(self, key, str(row[key]))
            else:
                setattr(self, key, '')
        c.close()
        db.close()
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
            padron.Procesar()
        cuit = len(sys.argv)>1 and sys.argv[1] or "20267565393"
        # consultar un cuit:
        ok = padron.Buscar(cuit)
        if ok:
            print "Denominacion:", padron.denominacion
            print "IVA:", padron.imp_iva
        t1 = time.time()
        print "tiempo", t1 -t0

