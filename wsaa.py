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

"""Módulo para obtener un ticket de autorización del web service WSAA de AFIP
Basado en wsaa-client.php de Gerardo Fisanotti - DvSHyS/DiOPIN/AFIP - 13-apr-07
Definir WSDL, CERT, PRIVATEKEY, PASSPHRASE, SERVICE, WSAAURL
Devuelve TA.xml (ticket de autorización de WSAA)
"""

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "2.0"

import email,os,sys
from php import date
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy
from M2Crypto import BIO, Rand, SMIME, SSL

# Constantes (si se usa el script de linea de comandos)
WSDL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"  # El WSDL correspondiente al WSAA 
CERT = "homo.crt"        # El certificado X.509 obtenido de Seg. Inf.
PRIVATEKEY = "homo.key"  # La clave privada del certificado CERT
PASSPHRASE = "xxxxxxx"  # La contraseña para firmar (si hay)
SERVICE = "wsfe"        # El nombre del web service al que se le pide el TA

# WSAAURL: la URL para acceder al WSAA, verificar http/https y wsaa/wsaahomo
#WSAAURL = "https://wsaa.afip.gov.ar/ws/services/LoginCms" # PRODUCCION!!!
WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" # homologacion (pruebas)
SOAP_ACTION = 'http://ar.gov.afip.dif.facturaelectronica/' # Revisar WSDL
SOAP_NS = "http://wsaa.view.sua.dvadac.desein.afip.gov"     # Revisar WSDL 

# Verificación del web server remoto (opcional?) igual no se usa
REMCN = "wsaahomo.afip.gov.ar" # WSAA homologacion CN (CommonName)
REMCACERT = "AFIPcerthomo.crt" # WSAA homologacion CA Cert

HOMO = True

# No debería ser necesario modificar nada despues de esta linea

def create_tra(service=SERVICE,ttl=2400):
    "Crear un Ticket de Requerimiento de Acceso (TRA)"
    tra = SimpleXMLElement(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<loginTicketRequest version="1.0">'
        '</loginTicketRequest>')
    tra.add_child('header')
    # El source es opcional. Si falta, toma la firma (recomendado).
    #tra.header.addChild('source','subject=...')
    #tra.header.addChild('destination','cn=wsaahomo,o=afip,c=ar,serialNumber=CUIT 33693450239')
    tra.header.add_child('uniqueId',date('U'))
    tra.header.add_child('generationTime',date('c',date('U')-ttl))
    tra.header.add_child('expirationTime',date('c',date('U')+ttl))
    tra.add_child('service',service)
    return tra.as_xml()

def sign_tra(tra,cert=CERT,privatekey=PRIVATEKEY):
    "Firmar PKCS#7 el TRA y devolver CMS (recortando los headers SMIME)"

    # Firmar el texto (tra)
    buf = BIO.MemoryBuffer(tra)             # Crear un buffer desde el texto
    #Rand.load_file('randpool.dat', -1)     # Alimentar el PRNG
    s = SMIME.SMIME()                       # Instanciar un SMIME
    if privatekey.startswith("-----BEGIN RSA PRIVATE KEY-----"):
        key_bio = BIO.MemoryBuffer(privatekey)
        crt_bio = BIO.MemoryBuffer(cert)
        s.load_key_bio(key_bio, crt_bio)        # Cargar certificados (buffer)
    elif os.path.exists(privatekey) and os.path.exists(cert):
        s.load_key(privatekey, cert)            # Cargar certificados (archivo)
    else:
        raise RuntimeError("Archivos no encontrados: %s, %s" % (privatekey, cert))
    p7 = s.sign(buf,0)                      # Firmar el buffer
    out = BIO.MemoryBuffer()                # Crear un buffer para la salida 
    s.write(out, p7)                        # Generar p7 en formato mail
    #Rand.save_file('randpool.dat')         # Guardar el estado del PRNG's

    # extraer el cuerpo del mensaje (parte firmada)
    msg = email.message_from_string(out.read())
    for part in msg.walk():
        filename = part.get_filename()
        if filename == "smime.p7m":                 # es la parte firmada?
            return part.get_payload(decode=False)   # devolver CMS

def call_wsaa(cms, location = WSAAURL, proxy=None, trace=False):
    "Llamar web service con CMS para obtener ticket de autorización (TA)"

    # creo la nueva clase
    wsaa = WSAA()
    try:
        wsdl = location + "?wsdl"
        wsaa.Conectar(proxy=proxy, wsdl=wsdl, cache="")
        ta = wsaa.LoginCMS(cms)
        return ta or ''
    except:
        raise


class WSAA:
    "Interfase para el WebService de Autenticación y Autorización"
    _public_methods_ = ['CreateTRA', 'SignTRA', 'CallWSAA', 'LoginCMS', 'Conectar']
    _public_attrs_ = ['Token', 'Sign', 'Version', 
                      'XmlRequest', 'XmlResponse', 
                      'InstallDir', 'Traceback', 'Excepcion',
                      'SoapFault',
                    ]
    _readonly_attrs_ = _public_attrs_
    _reg_progid_ = "WSAA"
    _reg_clsid_ = "{6268820C-8900-4AE9-8A2D-F0A1EBD4CAC5}"
    
    def __init__(self):
        self.Token = self.Sign = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        if not hasattr(sys, "frozen"): 
            basepath = __file__
        elif sys.frozen=='dll':
            import win32api
            basepath = win32api.GetModuleFileName(sys.frozendllhandle)
        else:
            basepath = sys.executable
        self.InstallDir = os.path.dirname(os.path.abspath(basepath))
        self.Excepcion = self.Traceback = ""

    def Conectar(self, cache=None, wsdl=None, proxy=""):
        # cliente soap del web service
        proxy_dict = parse_proxy(proxy)
        if HOMO or not wsdl:
            wsdl = WSDL
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        self.client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            trace = "--trace" in sys.argv)
        return True

    def CreateTRA(self, service="wsfe", ttl=2400):
        "Crear un Ticket de Requerimiento de Acceso (TRA)"
        return create_tra(service,ttl)

    def SignTRA(self, tra, cert, privatekey):
        "Firmar el TRA y devolver CMS"
        return sign_tra(str(tra),cert.encode('latin1'),privatekey.encode('latin1'))

    def LoginCMS(self, cms):
        "Obtener ticket de autorización (TA)"
        try:
            self.Excepcion = self.Traceback = ""
            self.Token = self.Sign = ""
            results = self.client.loginCms(in0=str(cms))
            ta_xml = results['loginCmsReturn']
            ta = SimpleXMLElement(ta_xml)
            self.Token = str(ta.credentials.token)
            self.Sign = str(ta.credentials.sign)
            return ta_xml
        except SoapFault,e:
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
        except Exception, e:
            import traceback
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = u"%s" % (e)
        finally:
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
            
    def CallWSAA(self, cms, url="", proxy=None):
        "Obtener ticket de autorización (TA) -version retrocompatible-"
        self.Conectar("", url+"?wsdl", proxy)
        ta_xml = self.LoginCMS(cms)
        if not ta_xml:
            raise RuntimeError(self.excepcion)

if __name__=="__main__":

    if '--register' in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSAA)

    else:
    
        # Leer argumentos desde la linea de comando (si no viene tomar default)
        cert = len(sys.argv)>1 and sys.argv[1] or CERT
        privatekey = len(sys.argv)>2 and sys.argv[2] or PRIVATEKEY
        service = len(sys.argv)>3 and sys.argv[3] or "wsfe"
        ttl = len(sys.argv)>4 and not sys.argv[4].startswith("--") and int(sys.argv[4]) or 2400
        url = len(sys.argv)>5 and sys.argv[5].startswith("http") and sys.argv[5] or WSAAURL

        print "Usando CERT=%s PRIVATEKEY=%s URL=%s SERVICE=%s TTL=%s" % (cert,privatekey,url,service, ttl)

        if '--proxy' in sys.argv:
            proxy = parse_proxy(sys.argv[sys.argv.index("--proxy")+1])
            print "Usando PROXY:", proxy
        else:
            proxy = None

        for filename in (cert,privatekey):
            if not os.access(filename,os.R_OK):
                sys.exit("Imposible abrir %s\n" % filename)
        print "Creando TRA..."
        tra = create_tra(service,ttl)
        if '--trace' in sys.argv:
            print "-" * 78
            print tra
            print "-" * 78
        #open("TRA.xml","w").write(tra)
        print "Frimando TRA..."
        cms = sign_tra(tra,cert,privatekey)
        #open("TRA.tmp","w").write(cms)
        #cms = open("TRA.tmp").read()
        print "Llamando WSAA..."
        try:
            ta = call_wsaa(cms,url, trace='--trace' in sys.argv, proxy=proxy)
        except SoapFault,e:
            sys.exit("Falla SOAP: %s\n%s\n" % (e.faultcode,e.faultstring))
        if ta=='':
            sys.exit("No se generó TA.xml\n")
        try:
            open("TA.xml","w").write(ta)
            print "El archivo TA.xml se ha generado correctamente."
        except:
            sys.exit("Error escribiendo TA.xml\n")
