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

"Módulo para generar códigos QR"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.02e"

import base64
import json
import os
import sys
import traceback

import qrcode


TEST_QR_DATA = """
eyJ2ZXIiOjEsImZlY2hhIjoiMjAyMC0xMC0xMyIsImN1aXQiOjMwMDAwMDAwMDA3LCJwdG9WdGEiOj
EwLCJ0aXBvQ21wIjoxLCJucm9DbXAiOjk0LCJpbXBvcnRlIjoxMjEwMCwibW9uZWRhIjoiRE9MIiwi
Y3R6Ijo2NSwidGlwb0RvY1JlYyI6ODAsIm5yb0RvY1JlYyI6MjAwMDAwMDAwMDEsInRpcG9Db2RBdX
QiOiJFIiwiY29kQXV0Ijo3MDQxNzA1NDM2NzQ3Nn0=""".replace("\n", "")


class PyQR:
    "Interfaz para generar Codigo QR de Factura Electrónica"
    _public_methods_ = ['GenerarImagen',
                        ]
    _public_attrs_ = ['Version', 'Excepcion', 'Traceback', "URL", "Archivo",
                      'qr_ver', 'box_size', 'border', 'error_correction',
                     ]

    _reg_progid_ = "PyQR"
    _reg_clsid_ = "{}"

    URL = "https://www.afip.gob.ar/fe/qr/?p=%s"
    Archivo = "qr.png"

    # qrencode default parameters:
    qr_ver = 1
    box_size = 10
    border = 4
    error_correction = qrcode.constants.ERROR_CORRECT_L

    def __init__(self):
        self.Version = __version__
        self.Exception = self.Traceback = ""

    def GenerarImagen(self, ver=1,
                      fecha="2020-10-13",
                      cuit=30000000007,
                      pto_vta=10, tipo_cmp=1, nro_cmp=94,
                      importe=12100, moneda="PES", ctz=1.000,
                      tipo_doc_rec=80, nro_doc_rec=20000000001,
                      tipo_cod_aut="E", cod_aut=70417054367476,
                      ):
        "Generar una imágen con el código QR"
        # basado en: https://www.afip.gob.ar/fe/qr/especificaciones.asp
        datos_cmp = {
            "ver": ver, "fecha": fecha, "cuit": cuit,
            "ptoVta": pto_vta, "tipoCmp": tipo_cmp, "nroCmp": nro_cmp,
            "importe": importe, "moneda": moneda, "ctz": ctz,
            "tipoDocRec": tipo_doc_rec, "nroDocRec": nro_doc_rec,
            "tipoCodAut": tipo_cod_aut, "codAut": cod_aut}

        # convertir a representación json y codificar en base64:
        datos_cmp_json = json.dumps(datos_cmp)
        url = self.URL % (base64.b64encode(datos_cmp_json))

        qr = qrcode.QRCode(
            version=self.qr_ver,
            error_correction=self.error_correction,
            box_size=self.box_size,
            border=self.border,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img.save(self.Archivo, "PNG")
        return url


if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(PyQR)
    elif "/Automate" in sys.argv:
        try:
            # MS seems to like /automate to run the class factories.
            import win32com.server.localserver
            win32com.server.localserver.serve([PyQR._reg_clsid_])
        except Exception:
            raise
    elif "py2exe" in sys.argv:
        from distutils.core import setup
        from nsis import build_installer, Target
        import py2exe
        import glob
        VCREDIST = (
            ".", glob.glob(r'c:\Program Files\Mercurial\mfc*.*') +
                 glob.glob(r'c:\Program Files\Mercurial\Microsoft.VC90.CRT.manifest'),
            )
        setup(
            name="PyQR",
            version=__version__,
            description="Interfaz PyAfipWs QR %s",
            long_description=__doc__,
            author="Mariano Reingart",
            author_email="reingart@gmail.com",
            url="http://www.sistemasagiles.com.ar",
            license="GNU LGPL v3",
            com_server = [
                {'modules': 'pyqr', 'create_exe': True, 'create_dll': True},
                ],
            console=[Target(module=sys.modules[__name__], script='pyqr.py', dest_base="pyqr_cli")],
            windows=[Target(module=sys.modules[__name__], script="pyqr.py", dest_base="pyqr_win")],
            options={
                'py2exe': {
                'includes': [],
                'optimize': 2,
                'excludes': ["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui","distutils.core","py2exe","nsis"],
                #'skip_archive': True,
            }},
            data_files = [VCREDIST, (".", ["licencia.txt"]),],
            cmdclass = {"py2exe": build_installer}
        )
    else:

        pyqr = PyQR()

        if '--datos' in sys.argv:
            args = sys.argv[sys.argv.index("--barras")+1:]
            (ver, fecha, cuit, pto_vta, tipo_cmp, nro_cmp, importe, moneda, ctz,
            tipo_doc_rec, nro_doc_rec, tipo_cod_aut, cod_aut) = args
        else:
            ver = 1
            fecha = "2020-10-13"
            cuit = 30000000007
            pto_vta = 10
            tipo_cmp = 1
            nro_cmp = 94
            importe = 12100
            moneda = "DOL"
            ctz = 65.000
            tipo_doc_rec = 80
            nro_doc_rec = 20000000001
            tipo_cod_aut = "E"
            cod_aut = 70417054367476

        if '--archivo' in sys.argv:
            pyqr.Archivo = sys.argv[sys.argv.index("--archivo")+1]

        print "datos:", (ver, fecha, cuit, pto_vta, tipo_cmp, nro_cmp,
                         importe, moneda, ctz, tipo_doc_rec, nro_doc_rec,
                         tipo_cod_aut, cod_aut)
        print "archivo", pyqr.Archivo

        url = pyqr.GenerarImagen(ver, fecha, cuit, pto_vta, tipo_cmp, nro_cmp,
                                importe, moneda, ctz, tipo_doc_rec, nro_doc_rec,
                                tipo_cod_aut, cod_aut)

        print "url generada:", url

        if "--prueba" in sys.argv:
            qr_data_test = json.loads(base64.b64decode(TEST_QR_DATA))
            qr_data_gen = json.loads(base64.b64decode(url[33:]))
            assert url.startswith("https://www.afip.gob.ar/fe/qr/?p=")
            assert qr_data_test == qr_data_gen, "Diff: %r != %r" % (qr_data_test, qr_data_gen)
            print "QR data ok:", qr_data_gen


        if not '--mostrar' in sys.argv:
            pass
        elif sys.platform=="linux2":
            os.system("eog ""%s""" % pyqr.Archivo)
        else:
            os.startfile(pyqr.archivo)
