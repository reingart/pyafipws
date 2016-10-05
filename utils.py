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

import datetime
import functools
import inspect
import locale
import socket
import sys
import os
import stat
import time
import traceback
import warnings
from cStringIO import StringIO
from decimal import Decimal
from urllib import urlencode
import unicodedata
import mimetools, mimetypes
from HTMLParser import HTMLParser
from Cookie import SimpleCookie
from ConfigParser import SafeConfigParser

from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper

try:
    import json
except ImportError:
    try:
        import simplejson as json 
    except:
        print "para soporte de JSON debe instalar simplejson"
        json = None

try:
    import httplib2
    # corregir temas de negociacion de SSL en algunas versiones de ubuntu:
    import platform
    dist, ver, nick = platform.linux_distribution() if sys.version > (2, 6) else ("", "", "")
    from pysimplesoap.client import SoapClient
    monkey_patch = httplib2._ssl_wrap_socket.__module__ != "httplib2"
    if dist == 'Ubuntu' and ver == '14.04' and not monkey_patch:
        import ssl
        def _ssl_wrap_socket(sock, key_file, cert_file,
                             disable_validation, ca_certs):
            if disable_validation:
                cert_reqs = ssl.CERT_NONE
            else:
                cert_reqs = ssl.CERT_REQUIRED
            return ssl.wrap_socket(sock, keyfile=key_file, certfile=cert_file,
                           cert_reqs=cert_reqs, ca_certs=ca_certs,
                           ssl_version=ssl.PROTOCOL_SSLv3)
        httplib2._ssl_wrap_socket = _ssl_wrap_socket

except:
    print "para soporte de WebClient debe instalar httplib2"


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
    "Decorador para inicializar y capturar errores (version para webservices)"
    @functools.wraps(func)
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Errores = []           # listas de str para lenguajes legados
            self.Observaciones = []
            self.errores = []           # listas de dict para usar en python
            self.observaciones = []
            self.Eventos = []
            self.Traceback = self.Excepcion = ""
            self.ErrCode = self.ErrMsg = self.Obs = ""
            # limpio variables especificas del webservice:
            self.inicializar()
            # actualizo los parámetros
            kwargs.update(self.params_in)
            # limpio los parámetros
            self.params_in = {}
            self.params_out = {}
            # llamo a la función (con reintentos)
            retry = self.reintentos + 1
            while retry:
                try:
                    retry -= 1
                    return func(self, *args, **kwargs)
                except socket.error, e:
                    if e[0] not in (10054, 10053):
                        # solo reintentar si el error es de conexión
                        # (10054, 'Connection reset by peer')
                        # (10053, 'Software caused connection abort')
                        raise
                    else:
                        if DEBUG: print e, "Reintentando..."
                        self.log(exception_info().get("msg", ""))

        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            if self.LanzarExcepciones:
                raise
        except Exception, e:
            ex = exception_info()
            self.Traceback = ex.get("tb", "")
            try:
                self.Excepcion = ex.get("msg", "")
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


def inicializar_y_capturar_excepciones_simple(func):
    "Decorador para inicializar y capturar errores (versión básica indep.)"
    @functools.wraps(func)
    def capturar_errores_wrapper(self, *args, **kwargs):
        self.inicializar()
        try:
            return func(self, *args, **kwargs)
        except:
            ex = exception_info()
            self.Excepcion = ex['name']
            self.Traceback = ex['msg']
            if self.LanzarExcepciones:
                raise
            else:
                return False
    return capturar_errores_wrapper


class BaseWS:
    "Infraestructura basica para interfaces webservices de AFIP"

    def __init__(self, reintentos=1):
        self.reintentos = reintentos
        self.xml = self.client = self.Log = None
        self.params_in = {}
        self.inicializar()
        self.Token = self.Sign = ""
        self.LanzarExcepciones = True
    
    def inicializar(self):
        self.Excepcion = self.Traceback = ""
        self.XmlRequest = self.XmlResponse = ""

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30, soap_server=None):
        "Conectar cliente soap del web service"
        try:
            # analizar transporte y servidor proxy:
            if wrapper:
                Http = set_http_wrapper(wrapper)
                self.Version = self.Version + " " + Http._wrapper_version
            if isinstance(proxy, dict):
                proxy_dict = proxy
            else:
                proxy_dict = parse_proxy(proxy)
                self.log("Proxy Dict: %s" % str(proxy_dict))
            if self.HOMO or not wsdl:
                wsdl = self.WSDL
            # agregar sufijo para descargar descripción del servicio ?WSDL o ?wsdl
            if not wsdl.endswith(self.WSDL[-5:]) and wsdl.startswith("http"):
                wsdl += self.WSDL[-5:]
            if not cache or self.HOMO:
                # use 'cache' from installation base directory 
                cache = os.path.join(self.InstallDir, 'cache')
            # deshabilitar verificación cert. servidor si es nulo falso vacio
            if not cacert:
                cacert = None
            elif cacert is True:
                # usar certificados predeterminados que vienen en la biblioteca
                cacert = os.path.join(httplib2.__path__[0], 'cacerts.txt')
            elif cacert.startswith("-----BEGIN CERTIFICATE-----"):
                pass
            else:
                if not os.path.exists(cacert): 
                    self.log("Buscando CACERT en conf...")
                    cacert = os.path.join(self.InstallDir, "conf", os.path.basename(cacert))
                if cacert and not os.path.exists(cacert):
                    self.log("No se encuentra CACERT: %s" % str(cacert))
                    warnings.warn("No se encuentra CACERT: %s" % str(cacert))
                    cacert = None   # wrong version, certificates not found...
                    raise RuntimeError("Error de configuracion CACERT ver DebugLog")
                    return False
                    
            self.log("Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict))
            # analizar espacio de nombres (axis vs .net):
            ns = 'ser' if self.WSDL[-5:] == "?wsdl" else None
            self.client = SoapClient(
                wsdl = wsdl,        
                cache = cache,
                proxy = proxy_dict,
                cacert = cacert,
                timeout = timeout,
                ns = ns, soap_server = soap_server, 
                trace = "--trace" in sys.argv)
            self.cache = cache  # utilizado por WSLPG y WSAA (Ticket de Acceso)
            self.wsdl = wsdl    # utilizado por TrazaMed (para corregir el location)
            # corrijo ubicación del servidor (puerto http 80 en el WSDL AFIP)
            for service in self.client.services.values():
                for port  in service['ports'].values():
                    location = port['location']
                    if location and location.startswith("http://"):
                        warnings.warn("Corrigiendo WSDL ... %s" % location)
                        location = location.replace("http://", "https://").replace(":80", ":443")
                        port['location'] = location
            return True
        except:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            if self.LanzarExcepciones:
                raise
            return False

    def log(self, msg):
        "Dejar mensaje en bitacora de depuración (método interno)"
        if not isinstance(msg, unicode):
            msg = unicode(msg, 'utf8', 'ignore')
        if not self.Log:
            self.Log = StringIO()
        self.Log.write(msg)
        self.Log.write('\n\r')
        if DEBUG:
            warnings.warn(msg)

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
        "Cargar un archivo de pruebas con la respuesta simulada (depuración)"
        # si el parametro es un nombre de archivo, cargar el contenido:
        if os.path.exists(xml):
            xml = open(xml).read()
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

    @inicializar_y_capturar_excepciones
    def SetTicketAcceso(self, ta_string):
        "Establecer el token y sign desde un ticket de acceso XML"
        if ta_string:
            ta = SimpleXMLElement(ta_string)
            self.Token = str(ta.credentials.token)
            self.Sign = str(ta.credentials.sign)
            return True
        else:
            raise RuntimeError("Ticket de Acceso vacio!")

    def SetParametro(self, clave, valor):
        "Establece un parámetro de entrada (a usarse en llamada posterior)"
        # útil para parámetros de entrada (por ej. VFP9 no soporta más de 27)
        self.params_in[str(clave)] = valor
        return True

    def GetParametro(self, clave, clave1=None, clave2=None, clave3=None, clave4=None):
        "Devuelve un parámetro de salida (establecido por llamada anterior)"
        # útil para parámetros de salida (por ej. campos de TransaccionPlainWS)
        valor = self.params_out.get(clave)
        # busco datos "anidados" (listas / diccionarios)
        for clave in (clave1, clave2, clave3, clave4):
            if clave is not None and valor is not None:
                if isinstance(clave1, basestring) and clave.isdigit():
                    clave = int(clave)
                try:
                    valor = valor[clave]
                except (KeyError, IndexError):
                    valor = None
        if valor is not None:
            if isinstance(valor, basestring):
                return valor
            else:
                return str(valor)
        else:
            return ""

    def LeerError(self):
        "Recorro los errores devueltos y devuelvo el primero si existe"
        
        if self.Errores:
            # extraigo el primer item
            er = self.Errores.pop(0)
            return er
        else:
            return ""


class WebClient:
    "Minimal webservice client to do POST request with multipart encoded FORM data"

    def __init__(self, location, enctype="multipart/form-data", trace=False,
                       cacert=None, timeout=30):
        kwargs = {}
        if httplib2.__version__ >= '0.3.0':
                kwargs['timeout'] = timeout
        if httplib2.__version__ >= '0.7.0':
                kwargs['disable_ssl_certificate_validation'] = cacert is None
                kwargs['ca_certs'] = cacert
        self.http = httplib2.Http(**kwargs)
        self.trace = trace
        self.location = location
        self.enctype = enctype
        self.cookies = None
        self.method = "POST"
        self.referer = None

    def multipart_encode(self, vars):
        "Enconde form data (vars dict)"
        boundary = mimetools.choose_boundary()
        buf = StringIO()
        for key, value in vars.items():
            if not isinstance(value, file):
                buf.write('--%s\r\n' % boundary)
                buf.write('Content-Disposition: form-data; name="%s"' % key)
                buf.write('\r\n\r\n' + value + '\r\n')
            else:
                fd = value
                file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
                filename = os.path.basename(fd.name)
                contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                buf.write('--%s\r\n' % boundary)
                buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
                buf.write('Content-Type: %s\r\n' % contenttype)
                # buffer += 'Content-Length: %s\r\n' % file_size
                fd.seek(0)
                buf.write('\r\n' + fd.read() + '\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf

    def __call__(self, *args, **vars):
        "Perform a GET/POST request and return the response"

        location = self.location
        if isinstance(location, unicode):
            location = location.encode("utf8")
        # extend the base URI with additional components
        if args:
            location += "/".join(args)
        if self.method == "GET":
            location += "?%s" % urlencode(vars)
            
        # prepare the request content suitable to be sent to the server:
        if self.enctype == "multipart/form-data":
            boundary, body = self.multipart_encode(vars)
            content_type = '%s; boundary=%s' % (self.enctype, boundary)
        elif self.enctype == "application/x-www-form-urlencoded":
            body = urlencode(vars)
            content_type = self.enctype
        else:
            body = None
            
        # add headers according method, cookies, etc.:
        headers={}        
        if self.method == "POST":
            headers.update({
                'Content-type': content_type,
                'Content-length': str(len(body)),
                })
        if self.cookies:
            headers['Cookie'] = self.cookies.output(attrs=(), header="", sep=";")
        if self.referer:
            headers['Referer'] = self.referer

        if self.trace:
            print "-"*80
            print "%s %s" % (self.method, location)
            print '\n'.join(["%s: %s" % (k,v) for k,v in headers.items()])
            print "\n%s" % body
        
        # send the request to the server and store the result:
        response, content = self.http.request(
            location, self.method, body=body, headers=headers )
        self.response = response
        self.content = content

        if self.trace: 
            print 
            print '\n'.join(["%s: %s" % (k,v) for k,v in response.items()])
            print content
            print "="*80

        # Parse and store the cookies (if any)
        if "set-cookie" in self.response:
            if not self.cookies:
                self.cookies = SimpleCookie()
            self.cookies.load(self.response["set-cookie"])

        return content


class AttrDict(dict):
    "Custom Dict to hold attributes and items"


class HTMLFormParser(HTMLParser):
    "Convert HTML form into custom named-tuple dicts"
    
    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.forms = {}
        
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'name' in attrs:
            name = attrs['name']
        elif 'id' in attrs:
            name = attrs['id']
        else:
            name = None
        if tag == 'form':
            form = AttrDict()
            for k, v in attrs.items():
                setattr(form, "_%s" % k, v)
            self.form = self.forms[name or len(self.forms)] = form
        elif tag == 'input':
            self.form[name or len(self.form)] = attrs.get('value')


# Funciones para manejo de archivos de texto de campos de ancho fijo:


def leer(linea, formato, expandir_fechas=False):
    "Analiza una linea de texto dado un formato, devuelve un diccionario"
    dic = {}
    comienzo = 1
    for fmt in formato:    
        clave, longitud, tipo = fmt[0:3]
        dec = (len(fmt)>3 and isinstance(fmt[3], int)) and fmt[3] or 2
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        try:
            if chr(8) in valor or chr(127) in valor or chr(255) in valor:
                valor = None        # nulo
            elif tipo == N:
                if valor:
                    valor = long(valor)
                else:
                    valor = 0
            elif tipo == I:
                if valor:
                    try:
                        if '.' in valor:
                                valor = float(valor)
                        else:
                            valor = valor.strip(" ")
                            valor = float(("%%s.%%0%sd" % dec) % (long(valor[:-dec] or '0'), int(valor[-dec:] or '0')))
                    except ValueError:
                        raise ValueError("Campo invalido: %s = '%s'" % (clave, valor))
                else:
                    valor = 0.00
            elif expandir_fechas and clave.lower().startswith("fec") and longitud <= 8:
                if valor:
                    valor = "%s-%s-%s" % (valor[0:4], valor[4:6], valor[6:8])
                else:
                    valor = None
            else:
                valor = valor.decode("ascii","ignore")
            dic[clave] = valor
            comienzo += longitud
        except Exception, e:
            raise ValueError("Error al leer campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return dic


def escribir(dic, formato, contraer_fechas=False):
    "Genera una cadena dado un formato y un diccionario de claves/valores"
    linea = " " * sum([fmt[1] for fmt in formato])
    comienzo = 1
    for fmt in formato:
        clave, longitud, tipo = fmt[0:3]
        try:
            dec = (len(fmt)>3 and isinstance(fmt[3], int)) and fmt[3] or 2
            if clave.capitalize() in dic:
                clave = clave.capitalize()
            s = dic.get(clave,"")
            if isinstance(s, unicode):
                s = s.encode("latin1")
            if s is None:
                valor = ""
            else:
                valor = str(s)
            # reemplazo saltos de linea por tabulaci{on vertical
            valor = valor.replace("\n\r", "\v").replace("\n", "\v").replace("\r", "\v")
            if tipo == N and valor and valor!="NULL":
                valor = ("%%0%dd" % longitud) % long(valor)
            elif tipo == I and valor:
                valor = ("%%0%d.%df" % (longitud+1, dec) % float(valor)).replace(".", "")
            elif contraer_fechas and clave.lower().startswith("fec") and longitud <= 8 and valor:
                valor = valor.replace("-", "")
            else:
                valor = ("%%-0%ds" % longitud) % valor
            linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
            comienzo += longitud
        except Exception, e:
            warnings.warn("Error al escribir campo %s pos %s val '%s': %s" % (
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
                if longitud >= 18:
                    longitud = 17
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
            if agrega or not tabla:
                if DEBUG: print "Agregando !!!", r
                registro = tabla.append(r)
            else:
                if DEBUG: print "Actualizando ", r
                reg = tabla.current()
                for k, v in reg.scatter_fields().items():
                    if k not in r:
                        r[k] = v
                if DEBUG: print "Actualizando ", r
                reg.write_record(**r)
                # mover de registro para no actualizar siempre el primero:
                if not tabla.eof() and len(l) > 1:
                    if DEBUG: print "Moviendo al próximo registro ", tabla.record_number
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
        # normalizo a float para poder comparar numericamente:
        if isinstance(v, (Decimal, int, long)):
            v = float(v)
        if isinstance(res_dict.get(k), (Decimal, int, long)):
            res_dict[k] = float(res_dict[k])
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
        elif isinstance(v, float) or isinstance(res_dict.get(k), float):
            # comparar numericamente
            if float(res_dict.get(k)) != float(v):
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


def norm(x, encoding="latin1"):
    "Convertir acentos codificados en ISO 8859-1 u otro, a ASCII regular"
    if not isinstance(x, basestring):
        x = unicode(x)
    elif isinstance(x, str):
        x = x.decode(encoding, 'ignore')
    return unicodedata.normalize('NFKD', x).encode('ASCII', 'ignore')


def date(fmt=None,timestamp=None):
    "Manejo de fechas (simil PHP)"
    if fmt=='U': # return timestamp
        t = datetime.datetime.now()
        return int(time.mktime(t.timetuple()))
    if fmt=='c': # return isoformat 
        d = datetime.datetime.fromtimestamp(timestamp)
        return d.isoformat()
    if fmt=='Ymd':
        d = datetime.datetime.now()
        return d.strftime("%Y%m%d")


def get_install_dir():
    if not hasattr(sys, "frozen"): 
        basepath = __file__
    elif sys.frozen=='dll':
        import win32api
        basepath = win32api.GetModuleFileName(sys.frozendllhandle)
    else:
        basepath = sys.executable

    if hasattr(sys, "frozen"): 
        # we are running as py2exe-packed executable
        import pythoncom
        pythoncom.frozen = 1
        sys.argv[0] = sys.executable

    return os.path.dirname(os.path.abspath(basepath))

        
def abrir_conf(config_file, debug=False):
    "Abrir el archivo de configuración (usar primer parámetro como ruta)"
    # en principio, usar el nombre de archivo predeterminado
    # si se pasa el archivo de configuración por parámetro, confirmar que exista
    # y descartar que sea una opción
    if len(sys.argv)>1:
        if os.path.splitext(sys.argv[1])[1].lower() == ".ini":
            config_file = sys.argv.pop(1)
    if not os.path.exists(config_file) or not os.path.isfile(config_file):
        warnings.warn("Archivo de configuracion %s invalido" % config_file)

    if debug: print "CONFIG_FILE:", config_file
    
    config = SafeConfigParser()
    config.read(config_file)

    return config


if __name__ == "__main__":
    print get_install_dir()
    try:
        1/0
    except:
        ex = exception_info()
        print ex
        assert ex['name'] == "ZeroDivisionError"
        assert ex['lineno'] == 73
        assert ex['tb']


