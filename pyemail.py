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

"Módulo para enviar correos electrónicos"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.06f"

import os
import sys
import traceback

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import sys, os
import smtplib
from ConfigParser import SafeConfigParser


DEBUG = False


class PyEmail:
    "Interfaz para enviar correos de Factura Electrónica"
    _public_methods_ = ['Conectar', 'Crear', 'Enviar',
                        'AgregarDestinatario', 'Adjuntar', 
                        'AgregarCC', 'AgregarBCC',
                        ]
    _public_attrs_ = [
                    'Motivo', 'Remitente', 'Destinatarios', 'ResponderA',
                    'MensajeHTML', 'MensajeTexto',
                    'Version', 'Excepcion', 'Traceback',
                    ]
        
    _reg_progid_ = "PyEmail"
    _reg_clsid_ = "{2BEF3037-BF38-41AA-84A3-6F109D543FC9}"


    def __init__(self):
        self.Version = __version__
        self.Excepcion = self.Traceback = ""
        self.Motivo = self.Destinatario = self.ResponderA = ""
        self.MensajeHTML = MensajeTexto = None
        self.adjuntos = []
        self.BCC = []
        self.CC = []

    def Conectar(self, servidor, usuario=None, clave=None, puerto=25):
        "Iniciar conexión al servidor de correo electronico"
        try:
            # convertir el nro de puerto a entero porque puede ser string:
            puerto = int(puerto)
            if puerto != 465:
                self.smtp = smtplib.SMTP(servidor, puerto)
            else:
                # creo una conexión segura (SSL, no disponible en Python<2.6):
                self.smtp = smtplib.SMTP_SSL(servidor, puerto)
            if DEBUG:
                self.smtp.set_debuglevel(1)
            self.smtp.ehlo()
            if puerto == 587:
                # inicio una sesión segura (TLS)
                self.smtp.starttls()
            if usuario and clave:
                # convertir a string (hmac necesita string "bytes")
                if isinstance(usuario, unicode):
                    usuario = usuario.encode("utf8")
                if isinstance(clave, unicode):
                    clave = clave.encode("utf8")
                self.smtp.login(usuario, clave)
            return True
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

    def Crear(self, remitente="", motivo=""):
        "Inicializa un mensaje de correo"
        self.Remitente = remitente
        self.Motivo = motivo
        self.Destinatarios = []
        self.adjuntos = []
        return True

    def AgregarDestinatario(self, destinatario):
        "Agrega una dirección de correo de destino"
        self.Destinatarios.append(destinatario)
        return True
        
    def AgregarCC(self, destinatario):
        "Agrega una dirección de correo de destino (copia carbónica)"
        self.CC.append(destinatario)
        return True

    def AgregarBCC(self, destinatario):
        "Agrega una dirección de correo de destino (copia carbónica invisible)"
        self.BCC.append(destinatario)
        return True

    def Adjuntar(self, archivo):
        "Agrega un archivo para ser enviado como adjunto"
        self.adjuntos.append(archivo)
        return True
        
    def Enviar(self, remitente="", motivo="", destinatario="", mensaje="", archivo=None):
        "Generar un correo multiparte y enviarlo"
        try:
            to = ([destinatario] if destinatario 
                  else self.Destinatarios)
            
            msg = MIMEMultipart('related')
            msg['Subject'] = motivo or self.Motivo
            msg['From'] = remitente or self.Remitente
            msg['Reply-to'] = remitente or self.ResponderA
            msg['To'] = ', '.join(to)
            if self.CC:
                msg['CC'] = u", ".join(self.CC)
                to += self.CC
            if self.BCC:
                to += self.BCC

            msg.preamble = 'Mensaje de multiples partes.\n'
            
            if mensaje:
                text = mensaje
                html = None
            else:
                text = self.MensajeTexto
                html = self.MensajeHTML
            
            if html:
                alt = MIMEMultipart('alternative')
                msg.attach(alt)
                part = MIMEText(text, 'text')
                alt.attach(part)
                part = MIMEText(html, 'html')
                alt.attach(part)
            else:
                part = MIMEText(text)
                msg.attach(part)
            
            if archivo:
                self.adjuntos.append(archivo)

            for archivo in self.adjuntos:
                part = MIMEApplication(open(archivo,"rb").read())
                part.add_header('Content-Disposition', 'attachment', 
                                    filename=os.path.basename(archivo))
                msg.attach(part)

            #print "Enviando email: %s a %s" % (msg['Subject'], msg['To'])
            self.smtp.sendmail(msg['From'], to, msg.as_string())

            return True
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

    def Salir(self):
        "Termino la conexión al servidor de correo electronico"
        try:
            self.smtp.quit()
            return True
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

            
if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(PyEmail)
    elif "py2exe" in sys.argv:
        from distutils.core import setup
        from nsis import build_installer, Target
        import py2exe
        setup( 
            name="PyEmail",
            version=__version__,
            description="Interfaz PyAfipWs Email %s",
            long_description=__doc__,
            author="Mariano Reingart",
            author_email="reingart@gmail.com",
            url="http://www.sistemasagiles.com.ar",
            license="GNU GPL v3",
            com_server = ['pyemail'],
            console=[],
            options={ 
                'py2exe': {
                'includes': ['email.generator', 'email.iterators', 'email.message', 'email.utils'],
                'optimize': 2,
                'excludes': ["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui","distutils.core","py2exe","nsis"],
                #'skip_archive': True,
            }},
            data_files = [(".", ["licencia.txt"]),],
            cmdclass = {"py2exe": build_installer}
        )
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([PyEmail._reg_clsid_])
    elif "/prueba" in sys.argv:
        pyemail = PyEmail()
        import getpass
        usuario = raw_input("usuario:")
        clave = getpass.getpass("clave:")
        ok = pyemail.Conectar("smtp.gmail.com", "reingart", clave, 587)
        print "login ok?", ok, pyemail.Excepcion
        print pyemail.Traceback
        ok = pyemail.Enviar(usuario, "prueba", usuario, "prueba!", None)
        print "mail enviado?", ok, pyemail.Excepcion
        ok = pyemail.Salir()
    else:        
        config = SafeConfigParser()
        config.read("rece.ini")

        if '/debug'in sys.argv:
            DEBUG = True
            print "VERSION", __version__
            sys.argv.remove("/debug")

        if len(sys.argv)<3:
            print "Parámetros: motivo destinatario [mensaje] [archivo]"
            sys.exit(1)

        conf_mail = dict(config.items('MAIL'))
        motivo = sys.argv[1]
        destinatario = sys.argv[2]
        mensaje = len(sys.argv)>3 and sys.argv[3] or conf_mail['cuerpo']
        archivo = len(sys.argv)>4 and sys.argv[4] or None
        
        print "Motivo: ", motivo
        print "Destinatario: ", destinatario
        print "Mensaje: ", mensaje
        print "Archivo: ", archivo
        
        pyemail = PyEmail()
        ok = pyemail.Conectar(conf_mail['servidor'], 
                              conf_mail['usuario'], conf_mail['clave'],
                              conf_mail.get('puerto', 25))
        if ok:
            pyemail.Enviar(conf_mail['remitente'], 
                           motivo, destinatario, mensaje, archivo)
        else:
            print pyemail.Traceback
