#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
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
__version__ = "1.0"

import email,os,sys
from php import date, SimpleXMLElement, SoapClient, SoapFault, parse_proxy
from M2Crypto import BIO, Rand, SMIME, SSL

# Constantes (si se usa el script de linea de comandos)
WSDL = "wsaa.wsdl"      # El WSDL correspondiente al WSAA (no se usa)
CERT = "homo.crt"        # El certificado X.509 obtenido de Seg. Inf.
PRIVATEKEY = "homo.key"  # La clave privada del certificado CERT
PASSPHRASE = "xxxxxxx"  # La contraseña para firmar (si hay)
SERVICE = "wsfe"        # El nombre del web service al que se le pide el TA

# WSAAURL: la URL para acceder al WSAA, verificar http/https y wsaa/wsaahomo
#WSAAURL = "https://wsaa.afip.gov.ar/ws/services/LoginCms" # PRODUCCION!!!
WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" # homologacion (pruebas)
SOAP_ACTION = 'http://ar.gov.afip.dif.facturaelectronica/' # Revisar WSDL
SOAP_NS = "http://ar.gov.afip.dif.facturaelectronica/"     # Revisar WSDL 

# Verificación del web server remoto (opcional?) igual no se usa
REMCN = "wsaahomo.afip.gov.ar" # WSAA homologacion CN (CommonName)
REMCACERT = "AFIPcerthomo.crt" # WSAA homologacion CA Cert

# No debería ser necesario modificar nada despues de esta linea

def create_tra(service=SERVICE,ttl=2400):
    "Crear un Ticket de Requerimiento de Acceso (TRA)"
    tra = SimpleXMLElement(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<loginTicketRequest version="1.0">'
        '</loginTicketRequest>')
    tra.addChild('header')
    # El source es opcional. Si falta, toma la firma (recomendado).
    #tra.header.addChild('source','subject=...')
    #tra.header.addChild('destination','cn=wsaahomo,o=afip,c=ar,serialNumber=CUIT 33693450239')
    tra.header.addChild('uniqueId',date('U'))
    tra.header.addChild('generationTime',date('c',date('U')-ttl))
    tra.header.addChild('expirationTime',date('c',date('U')+ttl))
    tra.addChild('service',service)
    return tra.asXML()

def sign_tra(tra,cert=CERT,privatekey=PRIVATEKEY):
    "Firmar PKCS#7 el TRA y devolver CMS (recortando los headers SMIME)"

    # Firmar el texto (tra)
    buf = BIO.MemoryBuffer(tra)             # Crear un buffer desde el texto
    #Rand.load_file('randpool.dat', -1)     # Alimentar el PRNG
    s = SMIME.SMIME()                       # Instanciar un SMIME
    s.load_key(privatekey, cert)            # Cargar certificados
    p7 = s.sign(buf,0)                      # Firmar el buffer
    out = BIO.MemoryBuffer()                # Crear un buffer para la salida 
    s.write(out, p7, buf)                   # Generar p7 en formato mail
    #Rand.save_file('randpool.dat')         # Guardar el estado del PRNG's

    # extraer el cuerpo del mensaje (parte firmada)
    msg = email.message_from_string(out.read())
    for part in msg.walk():
        filename = part.get_filename()
        if filename == "smime.p7s":                 # es la parte firmada?
            return part.get_payload(decode=False)   # devolver CMS

def call_wsaa(cms, location = WSAAURL, proxy=None, trace=False):
    "Llamar web service con CMS para obtener ticket de autorización (TA)"
  
    # cliente soap del web service
    client = SoapClient(location = location , 
        action = SOAP_ACTION,
        namespace = SOAP_NS,
        cert = REMCACERT,  # certificado remoto (revisar)
        trace = trace,     # imprimir mensajes de depuración
        exceptions = True, # lanzar Fallas Soap
        proxy = proxy,      # datos del servidor proxy (opcional)
        )
        

    try:
        results = client.loginCms(in0=cms)
        return str(results.loginCmsReturn)
    except:
        #print client.xml_request
        #print client.xml_response
        raise


if __name__=="__main__":

    # Leer argumentos desde la linea de comando (si no viene tomar default)
    cert = len(sys.argv)>1 and sys.argv[1] or CERT
    privatekey = len(sys.argv)>2 and sys.argv[2] or PRIVATEKEY
    url = len(sys.argv)>3 and sys.argv[3] or WSAAURL
    service = len(sys.argv)>4 and sys.argv[4] or "wsfe"
    ttl = len(sys.argv)>5 and int(sys.argv[5]) or 2400

    print "Usando CERT=%s PRIVATEKEY=%s URL=%s SERVICE=%s TTL=%s" % (cert,privatekey,url,service, ttl)

    for filename in (cert,privatekey):
        if not os.access(filename,os.R_OK):
            sys.exit("Imposible abrir %s\n" % filename)
    print "Creando TRA..."
    tra = create_tra(service,ttl)
    #open("TRA.xml","w").write(tra)
    print "Frimando TRA..."
    cms = sign_tra(tra,cert,privatekey)
    #open("TRA.tmp","w").write(cms)
    #cms = open("TRA.tmp").read()
    print "Llamando WSAA..."
    try:
        ta = call_wsaa(cms,url, trace='trace' in sys.argv) #parse_proxy("localhost:81")
    except SoapFault,e:
        sys.exit("Falla SOAP: %s\n%s\n" % (e.faultcode,e.faultstring))
    try:
        open("TA.xml","w").write(ta)
        print "El archivo TA.xml se ha generado correctamente."
    except:
        sys.exit("Error escribiendo TA.xml\n")
