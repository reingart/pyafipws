#!/usr/bin/python
# -*- coding: utf8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Módulo con funciones auxiliares para el manejo de errores y temas comunes"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"

import inspect
import socket
import sys
import os
import traceback
from cStringIO import StringIO

from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper

try:
    import dbf
except ImportError:
    print "para soporte de DBF debe instalar dbf 0.88.019 o superior"

try:
    import json
except ImportError:
    try:
        import simplejson as json 
    except:
        print "para soporte de JSON debe instalar simplejson"
        json = None


DEBUG = False


# Funciones para manejo de errores:


def exception_info(current_filename=None, index=-1):
    "Analizar el traceback y armar un dict con la info amigable user-friendly"
    # guardo el traceback original (por si hay una excepción):
    info = sys.exc_info() #         exc_type, exc_value, exc_traceback
    # importante: no usar unpacking porque puede causar memory leak
    if not current_filename:
        # genero un call stack para ver quien me llamó y limitar la traza: 
        # advertencia: esto es necesario ya que en py2exe no tengo __file__ 
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            f = sys.exc_info()[2].tb_frame.f_back
        current_filename = os.path.normpath(os.path.abspath(f.f_code.co_filename))

    # extraer la última traza del archivo solicitado:
    # (útil para no alargar demasiado la traza con lineas de las librerías)
    ret = {'filename': "", 'lineno': 0, 'function_name': "", 'code': ""}
    try:
        for (filename, lineno, fn, text) in traceback.extract_tb(info[2]):
            if os.path.normpath(os.path.abspath(filename)) == current_filename:
                ret = {'filename': filename, 'lineno': lineno, 
                       'function_name': fn, 'code': text}
            else:
                print filename
    except Exception, e:
        pass
    # obtengo el mensaje de excepcion tal cual lo formatea python:
    # (para evitar errores de encoding)
    try:
        ret['msg'] = traceback.format_exception_only(*info[0:2])[0]
    except: 
        ret['msg'] = '<no disponible>'
    # obtener el nombre de la excepcion (ej. "NameError")
    try:
        ret['name'] = info[0].__name__
    except:
        ret['name'] = 'Exception'
    # obtener la traza formateada como string:
    try:
        tb = traceback.format_exception(*info)
        ret['tb'] = ''.join(tb)
    except:
        ret['tb'] = ""
    return ret


def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Errores = []
            self.Observaciones = []
            self.Eventos = []
            self.Traceback = self.Excepcion = ""
            self.ErrCode = ""
            self.ErrMsg = ""
            # limpio variables especificas del webservice:
            self.inicializar()

            # llamo a la función (con reintentos)
            retry = self.reintentos
            while retry:
                try:
                    retry -= 1
                    return func(self, *args, **kwargs)
                except socket.error, e:
                    if e[0] != 10054:
                        # solo reintentar si el error es de conexión
                        # (10054, 'Connection reset by peer')
                        raise

        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            if self.LanzarExcepciones:
                raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            if self.LanzarExcepciones:
                raise
            else:
                self.ErrMsg = self.Excepcion
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class BaseWS:
    "Infraestructura basica para interfaces webservices de AFIP"

    def __init__(self, reintentos=1):
        self.reintentos = reintentos
        self.xml = self.client = self.Log = None
        self.inicializar()
    
    def inicializar(self):
        self.Token = self.Sign = None
        self.Excepcion = self.Traceback = ""
        self.LanzarExcepciones = True
        self.XmlRequest = self.XmlResponse = ""

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30):
        "Conectar cliente soap del web service"
        # analizar transporte y servidor proxy:
        if wrapper:
            Http = set_http_wrapper(wrapper)
            self.Version = self.Version + " " + Http._wrapper_version
        if isinstance(proxy, dict):
            proxy_dict = proxy
        else:
            proxy_dict = parse_proxy(proxy)
        if self.HOMO or not wsdl:
            wsdl = self.WSDL
        # agregar sufijo para descargar descripción del servicio ?WSDL o ?wsdl
        if not wsdl.endswith(self.WSDL[-5:]) and wsdl.startswith("http"):
            wsdl += self.WSDL[-5:]
        if not cache or self.HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        self.log("Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict))
        # analizar espacio de nombres (axis vs .net):
        ns = 'ser' if self.WSDL[-5:] == "?wsdl" else None
        self.client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            cacert = cacert,
            timeout = timeout,
            ns = ns,
            trace = "--trace" in sys.argv)
        return True

    def log(self, msg):
        "Dejar mensaje en bitacora de depuración (método interno)"
        if not isinstance(msg, unicode):
            msg = unicode(msg, 'utf8', 'ignore')
        if not self.Log:
            self.Log = StringIO()
        self.Log.write(msg)
        self.Log.write('\n\r')

    def DebugLog(self):
        "Devolver y limpiar la bitácora de depuración"
        if self.Log:
            msg = self.Log.getvalue()
            # limpiar log
            self.Log.close()
            self.Log = None
        else:
            msg = u''
        return msg    

    def LoadTestXML(self, xml):
        class DummyHTTP:
            def __init__(self, xml_response):
                self.xml_response = xml_response
            def request(self, location, method, body, headers):
                return {}, self.xml_response
        self.client.http = DummyHTTP(xml)

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto el ticket de acceso)"
        try:
            if not xml or xml=='XmlResponse':
                xml = self.XmlResponse 
            elif xml=='XmlRequest':
                xml = self.XmlRequest 
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception, e:
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

    def ObtenerTagXml(self, *tags):
        "Busca en el Xml analizado y devuelve el tag solicitado"
        # convierto el xml a un objeto
        try:
            if self.xml:
                xml = self.xml
                # por cada tag, lo busco segun su nombre o posición
                for tag in tags:
                    xml = xml(tag) # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]

    def SetParametros(self, cuit, token, sign):
        "Establece un parámetro general"
        self.Token = token
        self.Sign = sign
        self.Cuit = cuit
        return True

    def SetTicketAcceso(self, ta_string):
        "Establecer el token y sign desde un ticket de acceso XML"
        ta = SimpleXMLElement(ta_string)
        self.Token = str(ta.credentials.token)
        self.Sign = str(ta.credentials.sign)
        return True

# Funciones para manejo de archivos de texto de campos de ancho fijo:


def leer(linea, formato):
    "Analiza una linea de texto dado un formato, devuelve un diccionario"
    dic = {}
    comienzo = 1
    for fmt in formato:    
        clave, longitud, tipo = fmt[0:3]
        dec = len(fmt)>3 and fmt[3] or 2
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        try:
            if chr(8) in valor or chr(127) in valor or chr(255) in valor:
                valor = None        # nulo
            elif tipo == N:
                if valor:
                    valor = int(valor)
                else:
                    valor = 0
            elif tipo == I:
                if valor:
                    try:
                        valor = valor.strip(" ")
                        valor = float(("%%s.%%0%sd" % dec) % (int(valor[:-dec] or '0'), int(valor[-dec:] or '0')))
                    except ValueError:
                        raise ValueError("Campo invalido: %s = '%s'" % (clave, valor))
                else:
                    valor = 0.00
            else:
                valor = valor.decode("ascii","ignore")
            dic[clave] = valor
            comienzo += longitud
        except Exception, e:
            raise ValueError("Error al leer campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return dic


def escribir(dic, formato):
    "Genera una cadena dado un formato y un diccionario de claves/valores"
    linea = " " * sum([fmt[1] for fmt in formato])
    comienzo = 1
    for fmt in formato:
        clave, longitud, tipo = fmt[0:3]
        try:
            dec = len(fmt)>3 and fmt[3] or 2
            if clave.capitalize() in dic:
                clave = clave.capitalize()
            s = dic.get(clave,"")
            if isinstance(s, unicode):
                s = s.encode("latin1")
            if s is None:
                valor = ""
            else:
                valor = str(s)
            if tipo == N and valor and valor!="NULL":
                valor = ("%%0%dd" % longitud) % int(valor)
            elif tipo == I and valor:
                valor = ("%%0%dd" % longitud) % int(float(valor)*(10**dec))
            else:
                valor = ("%%-0%ds" % longitud) % valor
            linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
            comienzo += longitud
        except Exception, e:
            raise ValueError("Error al escribir campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return linea + "\n"


# Tipos de datos (código RG1361)


N = 'Numerico'      # 2
A = 'Alfanumerico'  # 3
I = 'Importe'       # 4
C = A               # 1 (caracter alfabetico)
B = A               # 9 (blanco)


# Funciones para manejo de tablas en DBF


def guardar_dbf(formatos, agrega=False, conf_dbf=None):
    import dbf
    if DEBUG: print "Creando DBF..."

    tablas = {}
    for nombre, formato, l in formatos:
        campos = []
        claves = []
        filename = conf_dbf.get(nombre.lower(), "%s.dbf" % nombre[:8])
        if DEBUG: print "=== tabla %s (%s) ===" %  (nombre, filename)
        for fmt in formato:
            clave, longitud, tipo = fmt[0:3]
            dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
            if longitud>250:
                tipo = "M" # memo!
            elif tipo == A:
                tipo = "C(%s)" % longitud 
            elif tipo == N:
                if longitud >= 18:
                    longitud = 17
                tipo = "N(%s,0)" % longitud 
            elif tipo == I:
                if longitud - 2 <= dec:
                    longitud += longitud - dec + 1      # ajusto long. decimales 
                tipo = "N(%s,%s)" % (longitud, dec)
            clave_dbf = dar_nombre_campo_dbf(clave, claves)
            campo = "%s %s" % (clave_dbf, tipo)
            if DEBUG: print " * %s : %s" %  (campo, clave)
            campos.append(campo)
            claves.append(clave_dbf)
        if DEBUG: print "leyendo tabla", nombre, filename
        if agrega:
            tabla = dbf.Table(filename, campos)
        else:
            tabla = dbf.Table(filename)

        for d in l:
            # si no es un diccionario, ignorar ya que seguramente va en otra 
            # tabla (por ej. retenciones tiene su propio formato)
            if isinstance(d, basestring):
                continue
            r = {}
            claves = []
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                if agrega or clave in d:
                    v = d.get(clave, None)
                    if DEBUG: print clave,v, tipo
                    if v is None and tipo == A:
                        v = ''
                    if (v is None or v=='') and tipo in (I, N):
                        v = 0
                    if tipo == A:
                        if isinstance(v, unicode):
                            v = v.encode("ascii", "replace")
                        if isinstance(v, str):
                            v = v.decode("ascii", "replace").encode("ascii", "replace")
                        if not isinstance(v, basestring):
                            v = str(v)
                        if len(v) > longitud:
                            v = v[:longitud]  # recorto el string para que quepa
                    clave_dbf = dar_nombre_campo_dbf(clave, claves)
                    claves.append(clave_dbf)
                    r[clave_dbf] = v
            # agregar si lo solicitaron o si la tabla no tiene registros:
            if agrega or (tabla.eof() and tabla.bof()):
                print "Agregando !!!", r
                registro = tabla.append(r)
            else:
                print "Actualizando ", r
                reg = tabla.current()
                for k, v in reg.scatter_fields().items():
                    if k not in r:
                        r[k] = v
                print "Actualizando ", r
                reg.write_record(**r)
                # mover de registro para no actualizar siempre el primero:
                if not tabla.eof() and len(l) > 1:
                    print "Moviendo al próximo registro ", tabla.record_number
                    tabla.next()
        tabla.close()


def leer_dbf(formatos, conf_dbf):
    import dbf
    if DEBUG: print "Leyendo DBF..."
    
    for nombre, formato, ld in formatos:
        filename = conf_dbf.get(nombre.lower(), "%s.dbf" % nombre[:8])
        if DEBUG: print "leyendo tabla", nombre, filename
        if not os.path.exists(filename):
            continue
        tabla = dbf.Table(filename)
        for reg in tabla:
            r = {}
            d = reg.scatter_fields() 
            claves = []
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                #import pdb; pdb.set_trace()
                clave_dbf = dar_nombre_campo_dbf(clave, claves)
                claves.append(clave_dbf)
                v = d.get(clave_dbf)
                r[clave] = v
            if isinstance(ld, dict):
                ld.update(r)
            else:
                ld.append(r)    


def dar_nombre_campo_dbf(clave, claves):
    "Reducir nombre de campo a 10 caracteres, sin espacios ni _, sin repetir"
    # achico el nombre del campo para que quepa en la tabla:
    nombre = clave.replace("_","")[:10]
    # si el campo esta repetido, le agrego un número
    i = 0
    while nombre in claves:
        i += 1    
        nombre = nombre[:9] + str(i)
    return nombre.lower()


def verifica(ver_list, res_dict, difs):
    "Verificar que dos diccionarios sean iguales, actualiza lista diferencias"
    for k, v in ver_list.items():
        if isinstance(v, list):
            # verifico que ambas listas tengan la misma cantidad de elementos:
            if v and not k in res_dict and v:
                difs.append("falta tag %s: %s %s" % (k, repr(v), repr(res_dict.get(k))))
            elif len(res_dict.get(k, []))!=len(v or []):
                difs.append("tag %s len !=: %s %s" % (k, repr(v), repr(res_dict.get(k))))
            else:
                # ordeno las listas para poder compararlas si vienen mezcladas
                rl = sorted(res_dict.get(k, []))
                # comparo los elementos uno a uno:
                for i, vl in enumerate(sorted(v)):
                    verifica(vl, rl[i], difs)
        elif isinstance(v, dict):
            # comparo recursivamente los elementos:
            verifica(v, res_dict.get(k, {}), difs)
        elif res_dict.get(k) is None or v is None:
            # alguno de los dos es nulo, verifico si ambos lo son o faltan
            if v=="":
                v = None
            r = res_dict.get(k)
            if r=="":
                r = None
            if not (r is None and v is None):
                difs.append("%s: nil %s!=%s" % (k, repr(v), repr(r)))
        elif type(res_dict.get(k)) == type(v):
            # tipos iguales, los comparo directamente
            if res_dict.get(k) != v:
                difs.append("%s: %s!=%s" % (k, repr(v), repr(res_dict.get(k))))                 
        elif unicode(res_dict.get(k)) != unicode(v):
            # tipos diferentes, comparo la representación  
            difs.append("%s: str %s!=%s" % (k, repr(v), repr(res_dict.get(k))))
        else:
            pass
            #print "%s: %s==%s" % (k, repr(v), repr(res_dict[k]))


def safe_console():
    if True or sys.stdout.encoding is None:
        class SafeWriter:
            def __init__(self, target):
                self.target = target
                self.encoding = 'utf-8'
                self.errors = 'replace'
                self.encode_to = 'latin-1'
            def write(self, s):
                self.target.write(self.intercept(s))        
            def flush(self):
                self.target.flush()
            def intercept(self, s):
                if not isinstance(s, unicode):
                    s = s.decode(self.encode_to, self.errors)
                return s.encode(self.encoding, self.errors)

        sys.stdout = SafeWriter(sys.stdout)
        #sys.stderr = SafeWriter(sys.stderr)
        print "Encodign in %s" % locale.getpreferredencoding()    


if __name__ == "__main__":
    try:
        1/0
    except:
        ex = exception_info()
        print ex
        assert ex['name'] == "ZeroDivisionError"
        assert ex['lineno'] == 73
        assert ex['tb']

