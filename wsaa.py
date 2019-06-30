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
__copyright__ = "Copyright (C) 2008-2019 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "2.11c"

import hashlib
import datetime
import email
import os
import sys
import time
import traceback
import warnings
import unicodedata
from pysimplesoap.client import SimpleXMLElement
from .utils import (inicializar_y_capturar_excepciones, BaseWS, get_install_dir,
                    exception_info, safe_console, date)

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


try:
    from M2Crypto import BIO, Rand, SMIME, SSL
except ImportError:
    ex = exception_info()
    warnings.warn("No es posible importar M2Crypto (OpenSSL)")
    warnings.warn(ex['msg'])            # revisar instalación y DLLs de OpenSSL
    BIO = Rand = SMIME = SSL = None
    # utilizar alternativa (ejecutar proceso por separado)
    from subprocess import Popen, PIPE
    from base64 import b64encode
    from tempfile import NamedTemporaryFile

# Constantes (si se usa el script de linea de comandos)
WSDL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"  # El WSDL correspondiente al WSAA
CERT = "reingart.crt"        # El certificado X.509 obtenido de Seg. Inf.
PRIVATEKEY = "reingart.key"  # La clave privada del certificado CERT
PASSPHRASE = "xxxxxxx"  # La contraseña para firmar (si hay)
SERVICE = "wsfe"        # El nombre del web service al que se le pide el TA

# WSAAURL: la URL para acceder al WSAA, verificar http/https y wsaa/wsaahomo
# WSAAURL = "https://wsaa.afip.gov.ar/ws/services/LoginCms" # PRODUCCION!!!
WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"  # homologacion (pruebas)
SOAP_ACTION = 'http://ar.gov.afip.dif.facturaelectronica/'  # Revisar WSDL
SOAP_NS = "http://wsaa.view.sua.dvadac.desein.afip.gov"     # Revisar WSDL

# Verificación del web server remoto, necesario para verificar canal seguro
CACERT = "conf/afip_ca_info.crt"  # WSAA CA Cert (Autoridades de Confiaza)

HOMO = False
TYPELIB = False
DEFAULT_TTL = 60 * 60 * 5       # five hours
DEBUG = False

# No debería ser necesario modificar nada despues de esta linea


def create_tra(service=SERVICE, ttl=2400):
    "Crear un Ticket de Requerimiento de Acceso (TRA)"
    tra = SimpleXMLElement(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<loginTicketRequest version="1.0">'
        '</loginTicketRequest>')
    tra.add_child('header')
    # El source es opcional. Si falta, toma la firma (recomendado).
    # tra.header.addChild('source','subject=...')
    # tra.header.addChild('destination','cn=wsaahomo,o=afip,c=ar,serialNumber=CUIT 33693450239')
    tra.header.add_child('uniqueId', str(date('U')))
    tra.header.add_child('generationTime', str(date('c', date('U') - ttl)))
    tra.header.add_child('expirationTime', str(date('c', date('U') + ttl)))
    tra.add_child('service', service)
    return tra.as_xml()


def sign_tra(tra, cert=CERT, privatekey=PRIVATEKEY, passphrase=""):
    "Firmar PKCS#7 el TRA y devolver CMS (recortando los headers SMIME)"

    if BIO:
        # Firmar el texto (tra) usando m2crypto (openssl bindings para python)
        buf = BIO.MemoryBuffer(tra)             # Crear un buffer desde el texto
        # Rand.load_file('randpool.dat', -1)     # Alimentar el PRNG
        s = SMIME.SMIME()                       # Instanciar un SMIME
        # soporte de contraseña de encriptación (clave privada, opcional)
        callback = lambda *args, **kwarg: passphrase
        # Cargar clave privada y certificado
        if not privatekey.startswith("-----BEGIN RSA PRIVATE KEY-----"):
            # leer contenido desde archivo (evitar problemas Applink / MSVCRT)
            if os.path.exists(privatekey) and os.path.exists(cert):
                privatekey = open(privatekey).read()
                cert = open(cert).read()
            else:
                raise RuntimeError("Archivos no encontrados: %s, %s" % (privatekey, cert))
        # crear buffers en memoria de la clave privada y certificado:
        key_bio = BIO.MemoryBuffer(privatekey.encode('utf8'))
        crt_bio = BIO.MemoryBuffer(cert.encode('utf8'))
        s.load_key_bio(key_bio, crt_bio, callback)  # (desde buffer)
        p7 = s.sign(buf, 0)                      # Firmar el buffer
        out = BIO.MemoryBuffer()                # Crear un buffer para la salida
        s.write(out, p7)                        # Generar p7 en formato mail
        # Rand.save_file('randpool.dat')         # Guardar el estado del PRNG's

        # extraer el cuerpo del mensaje (parte firmada)
        msg = email.message_from_string(out.read().decode('utf8'))
        for part in msg.walk():
            filename = part.get_filename()
            if filename == "smime.p7m":                 # es la parte firmada?
                return part.get_payload(decode=False)   # devolver CMS
    else:
        # Firmar el texto (tra) usando OPENSSL directamente
        try:
            if sys.platform.startswith("linux"):
                openssl = "openssl"
            else:
                if sys.maxsize <= 2**32:
                    openssl = r"c:\OpenSSL-Win32\bin\openssl.exe"
                else:
                    openssl = r"c:\OpenSSL-Win64\bin\openssl.exe"
            # NOTE: workaround if certificate is not already stored in a file
            # SECURITY WARNING: the private key will be exposed a bit in /tmp
            #                   (in theory only for the current user)
            if cert.startswith("-----BEGIN CERTIFICATE-----"):
                cert_f = NamedTemporaryFile()
                cert_f.write(cert.encode('utf-8'))
                cert_f.flush()
                cert = cert_f.name
            else:
                cert_f = None
            if privatekey.startswith("-----BEGIN RSA PRIVATE KEY-----"):
                key_f = NamedTemporaryFile()
                key_f.write(privatekey.encode('utf-8'))
                key_f.flush()
                privatekey = key_f.name
            else:
                key_f = None
            try:
                out = Popen([openssl, "smime", "-sign",
                             "-signer", cert, "-inkey", privatekey,
                             "-outform", "DER", "-nodetach"],
                            stdin=PIPE, stdout=PIPE,
                            stderr=PIPE).communicate(tra)[0]
            finally:
                # close temp files to delete them (just in case):
                if cert_f:
                    cert_f.close()
                if key_f:
                    key_f.close()
            return b64encode(out).decode("utf8")
        except OSError as e:
            if e.errno == 2:
                warnings.warn("El ejecutable de OpenSSL no esta disponible en el PATH")
            raise


def call_wsaa(cms, location=WSAAURL, proxy=None, trace=False, cacert=None):
    "Llamar web service con CMS para obtener ticket de autorización (TA)"

    # creo la nueva clase
    wsaa = WSAA()
    try:
        wsaa.Conectar(proxy=proxy, wsdl=location, cache="", cacert=cacert)
        ta = wsaa.LoginCMS(cms)
        if not ta:
            raise RuntimeError(wsaa.Excepcion)
        else:
            return ta
    except BaseException:
        raise


class WSAA(BaseWS):
    "Interfaz para el WebService de Autenticación y Autorización"
    _public_methods_ = ['CreateTRA', 'SignTRA', 'CallWSAA', 'LoginCMS', 'Conectar',
                        'AnalizarXml', 'ObtenerTagXml', 'Expirado', 'Autenticar',
                        'DebugLog', 'AnalizarCertificado',
                        'CrearClavePrivada', 'CrearPedidoCertificado',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'ExpirationTime', 'Version',
                      'XmlRequest', 'XmlResponse',
                      'InstallDir', 'Traceback', 'Excepcion',
                      'Identidad', 'Caducidad', 'Emisor', 'CertX509',
                      'SoapFault', 'LanzarExcepciones',
                      ]
    _readonly_attrs_ = _public_attrs_[:-1]
    _reg_progid_ = "WSAA"
    _reg_clsid_ = "{6268820C-8900-4AE9-8A2D-F0A1EBD4CAC5}"

    if TYPELIB:
        _typelib_guid_ = '{30E9C94B-7385-4534-9A80-DF50FD169253}'
        _typelib_version_ = 2, 11
        _com_interfaces_ = ['IWSAA']

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    @inicializar_y_capturar_excepciones
    def CreateTRA(self, service="wsfe", ttl=2400):
        "Crear un Ticket de Requerimiento de Acceso (TRA)"
        return create_tra(service, ttl)

    @inicializar_y_capturar_excepciones
    def AnalizarCertificado(self, crt, binary=False):
        "Carga un certificado digital y extrae los campos más importantes"

        if binary:
            cert = x509.load_pem_x509_certificate(crt, default_backend())
        else:
            if not crt.startswith("-----BEGIN CERTIFICATE-----"):
                crt = open(crt).read()
                if isinstance(crt, str):
                    crt = crt.encode('utf-8')
            cert = x509.load_pem_x509_certificate(crt, default_backend())
        if cert:
            self.Identidad = cert.subject
            self.Caducidad = cert.not_valid_after
            self.Emisor = cert.issuer
            self.CertX509 = cert
        return True

    @inicializar_y_capturar_excepciones
    def CrearClavePrivada(self, filename="privada.key", key_length=4096,
                          pub_exponent=0x10001, passphrase=""):
        "Crea una clave privada (private key)"
        # create the RSA key pair (and save the result to a file):
        rsa_key = rsa.generate_private_key(pub_exponent, key_length, backend=default_backend())

        if passphrase:
            passp = passphrase.encode('utf-8')
            # encryption AES-256-CBC
            cypher = serialization.BestAvailableEncryption(passp)
        else:
            cypher = serialization.NoEncryption()

        with open(filename, "wb") as f:
            f.write(rsa_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=cypher,
            ))

        self.rsa_key = rsa_key
        return True

    @inicializar_y_capturar_excepciones
    def CrearPedidoCertificado(self, cuit="", empresa="", nombre="pyafipws",
                               filename="empresa.csr"):
        "Crear un certificate signing request (X509 CSR)"
        # create the certificate signing request (CSR):
        self.x509_req = x509.CertificateSigningRequestBuilder()

        # normalizar encoding (reemplazar acentos, eñe, etc.)
        if isinstance(empresa, str):
            empresa = unicodedata.normalize('NFKD', empresa).encode('ASCII', 'ignore')
        if isinstance(nombre, str):
            nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore')

        # subjet: C=AR/O=[empresa]/CN=[nombre]/serialNumber=CUIT [nro_cuit]
        # sign the request with the previously created key (CrearClavePrivada)
        csrs = self.x509_req.subject_name(x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, 'AR'),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, '{}'.format(empresa)),
                x509.NameAttribute(NameOID.COMMON_NAME, '{}'.format(nombre)),
                x509.NameAttribute(NameOID.SERIAL_NUMBER, 'CUIT {}'.format(cuit)),
                ])).sign(self.rsa_key, hashes.SHA256(), default_backend())

        # save the CSR result to a file:
        with open(filename, "wb") as f:
            f.write(csrs.public_bytes(serialization.Encoding.PEM))

        return True

    @inicializar_y_capturar_excepciones
    def SignTRA(self, tra, cert, privatekey, passphrase=""):
        "Firmar el TRA y devolver CMS"
        return sign_tra(tra, cert, privatekey, passphrase)

    @inicializar_y_capturar_excepciones
    def LoginCMS(self, cms):
        "Obtener ticket de autorización (TA)"
        results = self.client.loginCms(in0=str(cms))
        ta_xml = results['loginCmsReturn']  # .encode("utf-8")
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

    def Autenticar(self, service, crt, key, wsdl=None, proxy=None, wrapper=None, cacert=None, cache=None, debug=False):
        "Método unificado para obtener el ticket de acceso (cacheado)"

        self.LanzarExcepciones = True
        try:
            # sanity check: verificar las credenciales
            for filename in (crt, key):
                if not os.access(filename, os.R_OK):
                    raise RuntimeError("Imposible abrir %s\n" % filename)
            # creo el nombre para el archivo del TA (según credenciales y ws)
            ta_src = (service + crt + key).encode("utf8")
            fn = "TA-%s.xml" % hashlib.md5(ta_src).hexdigest()
            if cache:
                fn = os.path.join(cache, fn)
            else:
                fn = os.path.join(self.InstallDir, "cache", fn)

            # leer el ticket de acceso (si fue previamente solicitado)
            if not os.path.exists(fn) or os.path.getsize(fn) == 0 or \
               os.path.getmtime(fn) + (DEFAULT_TTL) < time.time():
                # ticket de acceso (TA) vencido, crear un nuevo req. (TRA)
                if DEBUG:
                    print("Creando TRA...")
                tra = self.CreateTRA(service=service, ttl=DEFAULT_TTL)
                # firmarlo criptográficamente
                if DEBUG:
                    print("Firmando TRA...")
                cms = self.SignTRA(tra, crt, key)
                # concectar con el servicio web:
                if DEBUG:
                    print("Conectando a WSAA...")
                ok = self.Conectar(cache, wsdl, proxy, wrapper, cacert)
                if not ok or self.Excepcion:
                    raise RuntimeError("Fallo la conexión: %s" % self.Excepcion)
                # llamar al método remoto para solicitar el TA
                if DEBUG:
                    print("Llamando WSAA...")
                ta = self.LoginCMS(cms)
                if not ta:
                    raise RuntimeError("Ticket de acceso vacio: %s" % WSAA.Excepcion)
                # grabar el ticket de acceso para poder reutilizarlo luego
                if DEBUG:
                    print("Grabando TA en %s..." % fn)
                try:
                    open(fn, "w").write(ta)
                except IOError as e:
                    self.Excepcion = "Imposible grabar ticket de accesso: %s" % fn
            else:
                # leer el ticket de acceso del archivo en cache
                if DEBUG:
                    print("Leyendo TA de %s..." % fn)
                ta = open(fn, "r").read()
            # analizar el ticket de acceso y extraer los datos relevantes
            self.AnalizarXml(xml=ta)
            self.Token = self.ObtenerTagXml("token")
            self.Sign = self.ObtenerTagXml("sign")
        except BaseException:
            ta = ""
            if not self.Excepcion:
                # avoid encoding problem when reporting exceptions to the user:
                self.Excepcion = traceback.format_exception_only(sys.exc_info()[0],
                                                                 sys.exc_info()[1])[0]
                self.Traceback = ""
            if DEBUG or debug:
                raise
        return ta


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSAA.InstallDir = get_install_dir()


if __name__ == "__main__":

    safe_console()

    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        if TYPELIB:
            if '--register' in sys.argv:
                tlb = os.path.abspath(os.path.join(INSTALL_DIR, "typelib", "wsaa.tlb"))
                print("Registering %s" % (tlb,))
                tli = pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif '--unregister' in sys.argv:
                k = WSAA
                pythoncom.UnRegisterTypeLib(k._typelib_guid_,
                                            k._typelib_version_[0],
                                            k._typelib_version_[1],
                                            0,
                                            pythoncom.SYS_WIN32)
                print("Unregistered typelib")
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSAA)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        # win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([WSAA._reg_clsid_])
    elif "--crear_pedido_cert" in sys.argv:
        # instanciar el helper y revisar los parámetros
        wsaa = WSAA()
        args = [arg for arg in sys.argv if not arg.startswith("--")]
        # obtengo el CUIT y lo normalizo:
        cuit = len(args) > 1 and args[1] or input("Ingrese un CUIT: ")
        cuit = ''.join([c for c in cuit if c.isdigit()])
        nombre = len(args) > 2 and args[2] or "PyAfipWs"
        # consultar el padrón online de AFIP si no se especificó razón social:
        empresa = len(args) > 3 and args[3] or ""
        if not empresa:
            from .padron import PadronAFIP
            padron = PadronAFIP()
            ok = padron.Consultar(cuit)
            if ok and padron.denominacion:
                print("Denominación según AFIP:", padron.denominacion)
                empresa = padron.denominacion
            else:
                print("CUIT %s no encontrado: %s..." % (cuit, padron.Excepcion))
                empresa = input("Empresa: ")
        # longitud de la clave (2048 predeterminada a partir de 8/2016)
        key_length = len(args) > 4 and args[4] or ""
        try:
            key_length = int(key_length)
        except ValueError:
            key_length = 2048
        # generar los archivos (con fecha para no pisarlo)
        ts = datetime.datetime.now().strftime("%Y%m%d%M%S")
        clave_privada = "clave_privada_%s_%s.key" % (cuit, ts)
        pedido_cert = "pedido_cert_%s_%s.csr" % (cuit, ts)
        print("Longitud clave %s (bits)" % key_length)
        wsaa.CrearClavePrivada(clave_privada, key_length)
        wsaa.CrearPedidoCertificado(cuit, empresa, nombre, pedido_cert)
        print("Se crearon los archivos:")
        print(clave_privada)
        print(pedido_cert)
        # convertir a terminación de linea windows y abrir con bloc de notas
        if sys.platform == "win32":
            txt = open(pedido_cert + ".txt", "w")
            for linea in open(pedido_cert, "r"):
                txt.write("{}".format(linea))
            txt.close()
            os.startfile(pedido_cert + ".txt")
    else:

        # Leer argumentos desde la linea de comando (si no viene tomar default)
        args = [arg for arg in sys.argv if arg.startswith("--")]
        argv = [arg for arg in sys.argv if not arg.startswith("--")]
        crt = len(argv) > 1 and argv[1] or CERT
        key = len(argv) > 2 and argv[2] or PRIVATEKEY
        service = len(argv) > 3 and argv[3] or "wsfe"
        ttl = len(argv) > 4 and int(argv[4]) or 36000
        url = len(argv) > 5 and argv[5] or WSAAURL
        wrapper = len(argv) > 6 and argv[6] or None
        cacert = len(argv) > 7 and argv[7] or CACERT
        DEBUG = "--debug" in args or DEBUG

        print("Usando CRT=%s KEY=%s URL=%s SERVICE=%s TTL=%s" % (crt, key, url, service, ttl), file=sys.stderr)

        # creo el objeto para comunicarme con el ws
        wsaa = WSAA()
        wsaa.LanzarExcepciones = True

        print("WSAA Version %s %s" % (WSAA.Version, HOMO), file=sys.stderr)

        if '--proxy' in args:
            proxy = sys.argv[sys.argv.index("--proxy") + 1]
            print("Usando PROXY:", proxy, file=sys.stderr)
        else:
            proxy = None

        if '--analizar' in sys.argv:
            wsaa.AnalizarCertificado(crt)
            print(wsaa.Identidad)
            print(wsaa.Caducidad)
            print(wsaa.Emisor)
            print(wsaa.CertX509)

        ta = wsaa.Autenticar(service, crt, key, url, proxy, wrapper, cacert)
        if not ta:
            if DEBUG:
                print(wsaa.Traceback, file=sys.stderr)
            sys.exit("Excepcion: %s" % wsaa.Excepcion)

        else:
            print(ta)

        if wsaa.Excepcion:
            print(wsaa.Excepcion, file=sys.stderr)

        if DEBUG:
            print("Source:", wsaa.ObtenerTagXml('source'))
            print("UniqueID Time:", wsaa.ObtenerTagXml('uniqueId'))
            print("Generation Time:", wsaa.ObtenerTagXml('generationTime'))
            print("Expiration Time:", wsaa.ObtenerTagXml('expirationTime'))
            print("Expiro?", wsaa.Expirado())
