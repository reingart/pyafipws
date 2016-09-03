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
__copyright__ = "Copyright (C) 2014-2016 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.07b"


import csv
import json
import os
import shelve
import sqlite3
import urllib2
import zipfile
from email.utils import formatdate
import sys
from utils import leer, escribir, N, A, I, get_install_dir, safe_console, \
                  inicializar_y_capturar_excepciones_simple, WebClient, norm


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
    ("email", 250, A, ""),    
    ]	 

# Mapeos constantes:

PROVINCIAS = {0: 'CIUDAD AUTONOMA BUENOS AIRES', 1: 'BUENOS AIRES', 
    2: 'CATAMARCA', 3: 'CORDOBA', 4: 'CORRIENTES', 5: 'ENTRE RIOS', 6: 'JUJUY',
    7: 'MENDOZA', 8: 'LA RIOJA', 9: 'SALTA', 10: 'SAN JUAN', 11: 'SAN LUIS', 
    12: 'SANTA FE', 13: 'SANTIAGO DEL ESTERO', 14: 'TUCUMAN', 16: 'CHACO', 
    17: 'CHUBUT', 18: 'FORMOSA', 19: 'MISIONES', 20: 'NEUQUEN', 21: 'LA PAMPA',
    22: 'RIO NEGRO', 23: 'SANTA CRUZ', 24: 'TIERRA DEL FUEGO'}

TIPO_CLAVE = {'CUIT': 80, 'CUIL': 86, 'CDI': 86, 'DNI': 96, 'Otro': 99}

DEBUG = True

URL = "http://www.afip.gob.ar/genericos/cInscripcion/archivos/apellidoNombreDenominacion.zip"
URL_API = "https://soa.afip.gob.ar/"


class PadronAFIP():
    "Interfaz para consultar situación tributaria (Constancia de Inscripcion)"

    _public_methods_ = ['Buscar', 'Descargar', 'Procesar', 'Guardar',
                        'ConsultarDomicilios', 'Consultar', 'Conectar',
                        'DescargarConstancia', 'MostrarPDF', 
                        "ObtenerTablaParametros",
                        ]
    _public_attrs_ = ['InstallDir', 'Traceback', 'Excepcion', 'Version',
                      'cuit', 'dni', 'denominacion', 'imp_ganancias', 'imp_iva',  
                      'monotributo', 'integrante_soc', 'empleador', 
                      'actividad_monotributo', 'cat_iva', 'domicilios',
                      'tipo_doc', 'nro_doc', 'LanzarExcepciones',
                      'tipo_persona', 'estado', 'impuestos', 'actividades',
                      'direccion', 'localidad', 'provincia', 'cod_postal',
                      'data', 'response',
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
        self.LanzarExcepciones = False
        self.inicializar()
        self.client = None
    
    def inicializar(self):
        self.Excepcion = self.Traceback = ""
        self.cuit = self.dni = 0
        self.tipo_persona = ""                      # FISICA o JURIDICA
        self.tipo_doc = 0
        self.estado = ""                            # ACTIVO
        self.denominacion = ""
        self.direccion = self.localidad = self.provincia = self.cod_postal = ""
        self.domicilios = []
        self.impuestos = []
        self.actividades = []
        self.imp_iva = self.empleador = self.integrante_soc = self.cat_iva = ""
        self.monotributo = self.actividad_monotributo = "" 
        self.data = {}
        self.response = ""

    @inicializar_y_capturar_excepciones_simple
    def Conectar(self, url=URL_API, proxy="", wrapper=None, cacert=None, trace=False):
        self.client = WebClient(location=url, trace=trace, cacert=cacert)
        self.client.method = "GET"       # metodo RESTful predeterminado 
        self.client.enctype = None       # no enviar body
        return True

    @inicializar_y_capturar_excepciones_simple
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
            
    @inicializar_y_capturar_excepciones_simple
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
                        "nro_doc INTEGER, "
                        "denominacion VARCHAR(30), "
                        "imp_ganancias VARCHAR(2), "
                        "imp_iva VARCHAR(2), "
                        "monotributo VARCHAR(1), "
                        "integrante_soc VARCHAR(1), "
                        "empleador VARCHAR(1), "
                        "actividad_monotributo VARCHAR(2), "
                        "tipo_doc INTEGER, "
                        "cat_iva INTEGER DEFAULT NULL, "
                        "email VARCHAR(250), "
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
                params[8] = 80          # agrego tipo_doc = CUIT
                params[9] = None        # cat_iva no viene de AFIP
                placeholders = ", ".join(["?"] * len(params))
                c.execute("INSERT INTO padron VALUES (%s)" % placeholders,
                          params)
            db.commit()
            c.close()
            db.close()
        
    @inicializar_y_capturar_excepciones_simple
    def Buscar(self, nro_doc, tipo_doc=80):
        "Devuelve True si fue encontrado y establece atributos con datos"
        # cuit: codigo único de identificación tributaria del contribuyente
        #       (sin guiones)
        self.cursor.execute("SELECT * FROM padron WHERE "
                            " tipo_doc=? AND nro_doc=?", [tipo_doc, nro_doc])
        row = self.cursor.fetchone()
        for key in [k for k, l, t, d in FORMATO]:
            if row:
                val = row[key]
                if not isinstance(val, basestring):
                    val = str(row[key])
                setattr(self, key, val)
            else:
                setattr(self, key, '')
        if self.tipo_doc == 80:
            self.cuit = self.nro_doc
        elif self.tipo_doc == 96:
            self.dni = self.nro_doc
        # determinar categoría de IVA (tentativa)
        try:
            cat_iva = int(self.cat_iva)
        except ValueError:
            cat_iva = None
        if cat_iva:
            pass
        elif self.imp_iva in ('AC', 'S'):
            self.cat_iva = 1  # RI
        elif self.imp_iva == 'EX':
            self.cat_iva = 4  # EX
        elif self.monotributo:
            self.cat_iva = 6  # MT
        else:
            self.cat_iva = 5  # CF
        return True if row else False

    @inicializar_y_capturar_excepciones_simple
    def ConsultarDomicilios(self, nro_doc, tipo_doc=80, cat_iva=None):
        "Busca los domicilios, devuelve la cantidad y establece la lista"
        self.cursor.execute("SELECT direccion FROM domicilio WHERE "
                            " tipo_doc=? AND nro_doc=? ORDER BY id ", 
                            [tipo_doc, nro_doc])
        filas = self.cursor.fetchall()
        self.domicilios = [fila['direccion'] for fila in filas]
        return len(filas)

    @inicializar_y_capturar_excepciones_simple
    def Guardar(self, tipo_doc, nro_doc, denominacion, cat_iva, direccion, email):
        "Agregar o actualizar los datos del cliente"
        if self.Buscar(nro_doc, tipo_doc):
            sql = ("UPDATE padron SET denominacion=?, cat_iva=?, email=? "
                    "WHERE tipo_doc=? AND nro_doc=?")
            params = [denominacion, cat_iva, email, tipo_doc, nro_doc]
        else:
            sql = ("INSERT INTO padron (tipo_doc, nro_doc, denominacion, "
                    "cat_iva, email) VALUES (?, ?, ?, ?, ?)")
            params = [tipo_doc, nro_doc, denominacion, cat_iva, email]
        self.cursor.execute(sql, params)
        # agregar el domicilio solo si no existe:
        if direccion:
            self.cursor.execute("SELECT * FROM domicilio WHERE direccion=? "
                                "AND tipo_doc=? AND nro_doc=?", 
                                [direccion, tipo_doc, nro_doc])
            if self.cursor.rowcount < 0:
                sql = ("INSERT INTO domicilio (nro_doc, tipo_doc, direccion)"
                        "VALUES (?, ?, ?)")
                self.cursor.execute(sql, [nro_doc, tipo_doc, direccion])
        self.db.commit()
        return True

    @inicializar_y_capturar_excepciones_simple
    def Consultar(self, nro_doc):
        "Llama a la API pública de AFIP para obtener los datos de una persona"
        if not self.client:
            self.Conectar()
        self.response = self.client("sr-padron", "v2", "persona", str(nro_doc))
        result = json.loads(self.response)
        if result['success']:
            data = result['data']
            # extraigo datos generales del contribuyente:
            self.cuit = data["idPersona"]
            self.tipo_persona = data["tipoPersona"]
            self.tipo_doc = TIPO_CLAVE.get(data["tipoClave"])
            self.dni = data.get("numeroDocumento")
            self.estado = data.get("estadoClave")
            self.denominacion = data.get("nombre")
            # analizo el domicilio
            domicilio = data.get("domicilioFiscal")
            if domicilio:
                self.direccion = domicilio.get("direccion", "")
                self.localidad = domicilio.get("localidad", "")  # no usado en CABA
                self.provincia = PROVINCIAS.get(domicilio.get("idProvincia"), "")
                self.cod_postal = domicilio.get("codPostal")
            else:
                self.direccion = self.localidad = self.provincia = ""
                self.cod_postal = ""
            # retrocompatibilidad:
            self.domicilios = ["%s - %s (%s) - %s" % (
                                    self.direccion, self.localidad, 
                                    self.cod_postal, self.provincia,) ]
            # analizo impuestos:
            self.impuestos = data.get("impuestos", [])
            self.actividades = data.get("actividades", [])
            if 32 in self.impuestos:
                self.imp_iva = "EX"
            elif 33 in self.impuestos:
                self.imp_iva = "NI"
            elif 34 in self.impuestos:
                self.imp_iva = "NA"
            else:
                self.imp_iva = "S" if 30 in self.impuestos else "N"
            mt = data.get("categoriasMonotributo", {})
            self.monotributo = "S" if mt else "N"
            self.actividad_monotributo = "" # TODO: mt[0].get("idCategoria")
            self.integrante_soc = ""
            self.empleador = "S" if 301 in self.impuestos else "N"
            self.cat_iva = ""
            self.data = data
        else:
            error = result['error']
            self.Excepcion = error['mensaje']
        return True


    @inicializar_y_capturar_excepciones_simple
    def DescargarConstancia(self, nro_doc, filename="constancia.pdf"):
        "Llama a la API para descargar una constancia de inscripcion (PDF)"
        if not self.client:
            self.Conectar()
        self.response = self.client("sr-padron", "v1", "constancia", str(nro_doc))
        if self.response.startswith("{"):
            result = json.loads(self.response)
            assert not result["success"]
            self.Excepcion = result['error']['mensaje']
            return False
        else:
            with open(filename, "wb") as f:
                f.write(self.response)
            return True

    @inicializar_y_capturar_excepciones_simple
    def MostrarPDF(self, archivo, imprimir=False):
        if sys.platform.startswith(("linux2", 'java')):
            os.system("evince ""%s""" % archivo)
        else:
            operation = imprimir and "print" or ""
            os.startfile(archivo, operation)
        return True

    @inicializar_y_capturar_excepciones_simple
    def ObtenerTablaParametros(self, tipo_recurso, sep="||"):
        "Devuelve un array de elementos que tienen id y descripción"        
        if not self.client:
            self.Conectar()
        self.response = self.client("parametros", "v1", tipo_recurso)
        result = json.loads(self.response)
        ret = {}
        if result['success']:
            data = result['data']
            # armo un diccionario con los datos devueltos:
            key = [k for k in data[0].keys() if k.startswith("id")][0]
            val = [k for k in data[0].keys() if k.startswith("desc")][0]
            for it in data:
                ret[it[key]] = it[val]
            self.data = data
        else:
            error = result['error']
            self.Excepcion = error['mensaje']
        if sep:
            return ["%s%%s%s%%s%s" % (sep, sep, sep) % it for it in sorted(ret.items())]
        else:
            return ret
        


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = PadronAFIP.InstallDir = get_install_dir()

if __name__ == "__main__":

    safe_console()

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(PadronAFIP)
    else:
        padron = PadronAFIP()
        padron.LanzarExcepciones = True
        import time
        t0 = time.time()
        if "--descargar" in sys.argv:
            padron.Descargar()
        if "--procesar" in sys.argv:
            padron.Procesar(borrar='--borrar' in sys.argv)
        if "--parametros" in sys.argv:
            import codecs, locale, traceback
            if sys.stdout.encoding is None:
                sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
                sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");
            print "=== Impuestos ==="
            print u'\n'.join(padron.ObtenerTablaParametros("impuestos"))
            print "=== Conceptos ==="
            print u'\n'.join(padron.ObtenerTablaParametros("conceptos"))
            print "=== Actividades ==="
            print u'\n'.join(padron.ObtenerTablaParametros("actividades"))
            print "=== Caracterizaciones ==="
            print u'\n'.join(padron.ObtenerTablaParametros("caracterizaciones"))
            print "=== Categorias Monotributo ==="
            print u'\n'.join(padron.ObtenerTablaParametros("categoriasMonotributo"))
            print "=== Categorias Autonomos ==="
            print u'\n'.join(padron.ObtenerTablaParametros("categoriasAutonomo"))

        if '--csv' in sys.argv:
            csv_reader = csv.reader(open("entrada.csv", "rU"), 
                                    dialect='excel', delimiter=",")
            csv_writer = csv.writer(open("salida.csv", "w"), 
                                    dialect='excel', delimiter=",")
            encabezado = next(csv_reader)
            columnas = ["cuit", "denominacion", "estado", "direccion",
                        "localidad", "provincia", "cod_postal",
                        "impuestos", "actividades", "imp_iva", 
                        "monotributo", "actividad_monotributo", 
                        "empleador", "imp_ganancias", "integrante_soc"]
            csv_writer.writerow(columnas)
            
            for fila in csv_reader:
                cuit = (fila[0] if fila else "").replace("-", "")
                if cuit.isdigit():
                    if '--online' in sys.argv:
                        padron.Conectar(trace="--trace" in sys.argv)
                        print "Consultando AFIP online...", cuit,
                        ok = padron.Consultar(cuit)
                    else:
                        print "Consultando AFIP local...", cuit,
                        ok = padron.Buscar(cuit)
                    print 'ok' if ok else "error", padron.Excepcion
                    # domicilio posiblemente esté en Latin1, normalizar
                    csv_writer.writerow([norm(getattr(padron, campo, ""))
                                         for campo in columnas])
        else:
            cuit = len(sys.argv)>1 and sys.argv[1] or "20267565393"
            # consultar un cuit:
            if '--online' in sys.argv:
                padron.Conectar(trace="--trace" in sys.argv)
                print "Consultando AFIP online...",
                ok = padron.Consultar(cuit)
                print 'ok' if ok else "error", padron.Excepcion
                print "Denominacion:", padron.denominacion
                print "CUIT:", padron.cuit 
                print "Tipo:", padron.tipo_persona, padron.tipo_doc, padron.dni
                print "Estado:", padron.estado
                print "Direccion:", padron.direccion
                print "Localidad:", padron.localidad
                print "Provincia:", padron.provincia
                print "Codigo Postal:", padron.cod_postal
                print "Impuestos:", padron.impuestos
                print "Actividades:", padron.actividades
                print "IVA", padron.imp_iva
                print "MT", padron.monotributo, padron.actividad_monotributo
                print "Empleador", padron.empleador
            elif '--constancia' in sys.argv:
                filename = sys.argv[2]
                print "Descargando constancia AFIP online...", cuit, filename
                ok = padron.DescargarConstancia(cuit, filename)
                print 'ok' if ok else "error", padron.Excepcion
                if '--mostrar' in sys.argv:
                    padron.MostrarPDF(archivo=filename,
                                     imprimir='--imprimir' in sys.argv)
            else:
                ok = padron.Buscar(cuit)
                if ok:
                    print "Denominacion:", padron.denominacion
                    print "IVA:", padron.imp_iva
                    print "Ganancias:", padron.imp_ganancias
                    print "Monotributo:", padron.monotributo
                    print "Integrante Soc.:", padron.integrante_soc
                    print "Empleador", padron.empleador
                    print "Actividad Monotributo:", padron.actividad_monotributo
                    print "Categoria IVA:", padron.cat_iva
                    padron.ConsultarDomicilios(cuit)
                    for dom in padron.domicilios:
                        print dom
                else:
                    print padron.Excepcion
                    print padron.Traceback
        t1 = time.time()
        if '--trace' in sys.argv:
            print "tiempo", t1 -t0

