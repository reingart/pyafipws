#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WsARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Módulo para autenticar en servidor idp de ARBA"

__license__ = "LGPL 3.0"
__version__ = "1.00b"

import sys, time
import json, os
import utils
from utils import WebClient

HOMO = False

URL = "https://idp.test.arba.gov.ar/realms/ARBA/protocol/openid-connect/token" # Homologación
# URL = "https://idp.arba.gov.ar/realms/ARBA/protocol/openid-connect/token" # Producción


class WSIDP:
    "Interfaz para el servicio de Autenticación del servidor IDP de Arba"

    _public_methods_ = [
        "ObtenerToken"
    ]

    _public_attrs_ = [
        'Token', 'Version', 'HttpCode', 'Traceback', 'InstallDir',
        'Request', 'Response', 'Excepcion', 'Url'
    ]

    _reg_progid_ = "WSIDP"
    _reg_clsid_ = "{819aa21d-070a-4a8c-9438-2f331dda57b9}"

    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def __init__(self):
        self.Token = None
        self.InstallDir = INSTALL_DIR
        self.url = URL
        self.hora_obtenido = 0
        self.duracion = 280
        self.client = WebClient(location=self.url, 
                            enctype="application/x-www-form-urlencoded")
        self.LanzarExcepciones = False
        self.inicializar()
        
    def inicializar(self):
        self.HttpCode = 0
        self.Traceback = ""
        self.Excepcion = ""
        self.Request = ""
        self.Response = ""

    @utils.inicializar_y_capturar_excepciones_basico
    def ObtenerToken(self, cuit, cit, client_id, secret, url=None):
        "Metodo de Autenticación en servidor IDP de Arba"

        base = getattr(self, 'InstallDir', INSTALL_DIR)

        cache_dir = os.path.join(base, "cache")
        cache_path = os.path.join(
            cache_dir,
            "wsidp_token_%s.json" % cuit
        )

        try:
            os.makedirs(cache_dir)
        except OSError:
            pass
        if HOMO:
            self.url = URL
        elif url:
            self.url = url

        self.client.location = self.url

        # intentar leer el token en el archivo
        ahora = time.time()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                # verificar que access_token no sea none ni vacío
                token_en_disco = cache_data.get('access_token')
                if token_en_disco and cache_data.get('expires_at', 0) > (ahora + 20):
                    self.Token = token_en_disco
                    self.Request = self.Response = "Token Reutilizado, no hay llamada"
                    return self.Token
            except (IOError, ValueError):
                pass

        payload = {
            'client_id': str(client_id),
            'client_secret': str(secret),
            'username': str(cuit),
            'password': str(cit),
            'grant_type': 'password',
            'scope': 'openid'
        }

        self.client.method = "POST"
        content = self.client("", **payload)

        self.HttpCode = self.client.response.status
        self.Response = content
        self.Request = self.client.request
        self.Traceback = self.client.trace
        if 200 <= self.HttpCode < 300:
            datos = json.loads(content)
            temp_token = datos.get('access_token')
            
            if temp_token:
                self.Token = temp_token
                self.hora_obtenido = time.time()
                expires_in = datos.get('expires_in', 300)
                # guardar token en el archivo
                try:
                    with open(cache_path, 'w') as f:
                        json.dump({
                            'access_token': self.Token,
                            'expires_at': self.hora_obtenido + expires_in
                        }, f)
                except:
                    pass
                return self.Token
        else:
            try:
                err_json = json.loads(content)
                msg = err_json.get('error_description') or err_json.get('error') or content
                self.Traceback = self.client.trace
            except:
                self.Traceback = self.client.trace
                msg = content
            raise Exception("Error IDP: (%s): %s" % (self.HttpCode, msg))

# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"):
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))

if __name__ == "__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSIDP)
        sys.exit(0)

    trace_active = "--trace" in sys.argv
    cuit = sys.argv[1]
    cit = sys.argv[2]
    client_id = sys.argv[3]
    secret = sys.argv[4]
    idp = WSIDP()
    if "--help" in sys.argv or len(sys.argv) < 5:
        print "--- Uso: python wsidp.py <cuit> <cit> <client_id> <secret> [--prod] (sin --prod = testing) ---"
    else:
        if "--prod" not in sys.argv or HOMO:
            token = idp.ObtenerToken(cuit, cit, client_id, secret, url=URL)
        else:
            token = idp.ObtenerToken(cuit, cit, client_id, secret,
                                     url="https://idp.arba.gov.ar/realms/ARBA/protocol/openid-connect/token")
        if token:
            print "--- Token ---\n", token, "\n--- Token ---"
        else:
            trace_active = True
        if trace_active:
            print "----- DEBUG WSIDP -----"
            print ">> URL:", idp.url
            print ">> Request:", idp.Request
            print ">> Error:", idp.Response
            print ">> Code:", idp.HttpCode
            print ">> Traceback:", idp.Traceback
            