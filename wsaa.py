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

"Módulo para obtener un ticket de autorización del web service WSAA de AFIP"

# Basado en wsaa-client.php de Gerardo Fisanotti - DvSHyS/DiOPIN/AFIP - 13-apr-07
# Definir WSDL, CERT, PRIVATEKEY, PASSPHRASE, SERVICE, WSAAURL
# Devuelve TA.xml (ticket de autorización de WSAA)

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008-2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "2.06a"

import datetime,email,os,sys,traceback
from php import date
from pysimplesoap.client import SimpleXMLElement
from utils import inicializar_y_capturar_excepciones, BaseWS
try:
    from M2Crypto import BIO, Rand, SMIME, SSL
except ImportError:
    BIO = Rand = SMIME = SSL = None
    from subprocess import Popen, PIPE
    from base64 import b64encode

# Constantes (si se usa el script de linea de comandos)
WSDL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"  # El WSDL correspondiente al WSAA 
CERT = "reingart.crt"        # El certificado X.509 obtenido de Seg. Inf.
PRIVATEKEY = "reingart.key"  # La clave privada del certificado CERT
PASSPHRASE = "xxxxxxx"  # La contraseña para firmar (si hay)
SERVICE = "wsfe"        # El nombre del web service al que se le pide el TA

# WSAAURL: la URL para acceder al WSAA, verificar http/https y wsaa/wsaahomo
#WSAAURL = "https://wsaa.afip.gov.ar/ws/services/LoginCms" # PRODUCCION!!!
WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" # homologacion (pruebas)
SOAP_ACTION = 'http://ar.gov.afip.dif.facturaelectronica/' # Revisar WSDL
SOAP_NS = "http://wsaa.view.sua.dvadac.desein.afip.gov"     # Revisar WSDL 

# Verificación del web server remoto
CACERT = "afip_ca_info.crt" # WSAA CA Cert

HOMO = False
TYPELIB = False

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

    if BIO:
        # Firmar el texto (tra) usando m2crypto (openssl bindings para python)
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
    else:
        # Firmar el texto (tra) usando OPENSSL directamente
        out = Popen(["openssl", "smime", "-sign", 
                     "-signer", cert, "-inkey", privatekey,
                     "-outform","DER", "-nodetach"], 
                    stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(tra)[0]
        return b64encode(out)

                
def call_wsaa(cms, location = WSAAURL, proxy=None, trace=False):
    "Llamar web service con CMS para obtener ticket de autorización (TA)"

    # creo la nueva clase
    wsaa = WSAA()
    try:
        wsaa.Conectar(proxy=proxy, wsdl=location, cache="")
        ta = wsaa.LoginCMS(cms)
        if not ta:
            raise RuntimeError(wsaa.Excepcion)
        else:
            return ta
    except:
        raise


class WSAA(BaseWS):
    "Interfaz para el WebService de Autenticación y Autorización"
    _public_methods_ = ['CreateTRA', 'SignTRA', 'CallWSAA', 'LoginCMS', 'Conectar',
                        'AnalizarXml', 'ObtenerTagXml', 'Expirado',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'ExpirationTime', 'Version', 
                      'XmlRequest', 'XmlResponse', 
                      'InstallDir', 'Traceback', 'Excepcion',
                      'SoapFault', 'LanzarExcepciones',
                    ]
    _readonly_attrs_ = _public_attrs_[:-1]
    _reg_progid_ = "WSAA"
    _reg_clsid_ = "{6268820C-8900-4AE9-8A2D-F0A1EBD4CAC5}"

    if TYPELIB:
        _typelib_guid_ = '{30E9C94B-7385-4534-9A80-DF50FD169253}'
        _typelib_version_ = 2, 4
        _com_interfaces_ = ['IWSAA']

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    
    @inicializar_y_capturar_excepciones
    def CreateTRA(self, service="wsfe", ttl=2400):
        "Crear un Ticket de Requerimiento de Acceso (TRA)"
        return create_tra(service,ttl)
        
    @inicializar_y_capturar_excepciones
    def SignTRA(self, tra, cert, privatekey):
        "Firmar el TRA y devolver CMS"
        return sign_tra(str(tra),cert.encode('latin1'),privatekey.encode('latin1'))

    @inicializar_y_capturar_excepciones
    def LoginCMS(self, cms):
        "Obtener ticket de autorización (TA)"
        results = self.client.loginCms(in0=str(cms))
        ta_xml = results['loginCmsReturn'].encode("utf-8")
        self.xml = ta = SimpleXMLElement(ta_xml)
        self.Token = str(ta.credentials.token)
        self.Sign = str(ta.credentials.sign)
        self.ExpirationTime = str(ta.header.expirationTime)
        return ta_xml
            
    def CallWSAA(self, cms, url="", proxy=None):
        "Obtener ticket de autorización (TA) -version retrocompatible-"
        self.Conectar("", url, proxy)
        ta_xml = self.LoginCMS(cms)
        if not ta_xml:
            raise RuntimeError(self.Excepcion)
        return ta_xml

    @inicializar_y_capturar_excepciones
    def Expirado(self, fecha=None):
        "Comprueba la fecha de expiración, devuelve si ha expirado"
        if not fecha:
            fecha = self.ObtenerTagXml('expirationTime')
        now = datetime.datetime.now()
        d = datetime.datetime.strptime(fecha[:19], '%Y-%m-%dT%H:%M:%S')
        return now > d
        
        
# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = WSAA.InstallDir = os.path.dirname(os.path.abspath(basepath))

if hasattr(sys, 'frozen'):
    # we are running as py2exe-packed executable
    import pythoncom
    pythoncom.frozen = 1
    sys.argv[0] = sys.executable

if __name__=="__main__":
    
    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        if TYPELIB: 
            if '--register' in sys.argv:
                tlb = os.path.abspath(os.path.join(INSTALL_DIR, "wsaa.tlb"))
                print "Registering %s" % (tlb,)
                tli=pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif '--unregister' in sys.argv:
                k = WSAA
                pythoncom.UnRegisterTypeLib(k._typelib_guid_, 
                                            k._typelib_version_[0], 
                                            k._typelib_version_[1], 
                                            0, 
                                            pythoncom.SYS_WIN32)
                print "Unregistered typelib"
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSAA)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([WSAA._reg_clsid_])
    else:
        
        # Leer argumentos desde la linea de comando (si no viene tomar default)
        args = [arg for arg in sys.argv if arg.startswith("--")]
        argv = [arg for arg in sys.argv if not arg.startswith("--")]
        cert = len(argv)>1 and argv[1] or CERT
        privatekey = len(argv)>2 and argv[2] or PRIVATEKEY
        service = len(argv)>3 and argv[3] or "wsfe"
        ttl = len(argv)>4 and int(argv[4]) or 36000
        url = len(argv)>5 and argv[5] or WSAAURL
        wrapper = len(argv)>6 and argv[6] or None
        cacert = len(argv)>7 and argv[7] or CACERT

        print "Usando CERT=%s PRIVATEKEY=%s URL=%s SERVICE=%s TTL=%s" % (cert,privatekey,url,service, ttl)

        # creo el objeto para comunicarme con el ws
        wsaa = WSAA()
        wsaa.LanzarExcepciones = True
        
        if '--proxy' in args:
            proxy = parse_proxy(sys.argv[sys.argv.index("--proxy")+1])
            print "Usando PROXY:", proxy
        else:
            proxy = None

        for filename in (cert,privatekey):
            if not os.access(filename,os.R_OK):
                sys.exit("Imposible abrir %s\n" % filename)
        print "Creando TRA..."
        tra = create_tra(service,ttl)
        if '--trace' in args:
            print "-" * 78
            print tra
            print "-" * 78
        #open("TRA.xml","w").write(tra)
        print "Frimando TRA..."
        cms = sign_tra(tra,cert,privatekey)
        #open("TRA.tmp","w").write(cms)
        #cms = open("TRA.tmp").read()
        print "Conectando a WSAA"
        wrapper = wrapper # "pycurl" o "httplib2" o "urrlib2"
        cacert = cacert # "geotrust.crt" o "thawte.crt"
        wsaa.Conectar("", url, proxy, wrapper, cacert)
        print wsaa.Version
        if wrapper!='pycurl' or not cacert: 
            print "NO SE VERIFICA CERTIFICADO CA!"
        else:
            print "Verificando CA: ", cacert
        print "Llamando WSAA..."
        ta = wsaa.LoginCMS(cms)
        if wsaa.Excepcion:
            sys.exit("Falla SOAP: %s\n" % wsaa.Excepcion)
        if ta=='':
            sys.exit("No se generó TA.xml\n")
        try:
            if ta is not None:
                open("TA.xml","w").write(ta)
                print "El archivo TA.xml se ha generado correctamente."
        except Exception, e:
            if "--debug" in args:
                raise
            else:
                sys.exit("Error escribiendo TA.xml: %s\n")

        if "--debug" in args:
            print "Source:", wsaa.ObtenerTagXml('source')
            print "UniqueID Time:", wsaa.ObtenerTagXml('uniqueId')
            print "Generation Time:", wsaa.ObtenerTagXml('generationTime')
            print "Expiration Time:", wsaa.ObtenerTagXml('expirationTime')
            print "Expiro?", wsaa.Expirado()
            ##import time; time.sleep(10)
            ##print "Expiro?", wsaa.Expirado()
