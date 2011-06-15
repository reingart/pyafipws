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

"Módulo para generar códigos de barra en Entrelazado 2 de 5 (I25)"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.02a"

import os
import sys
import traceback
import Image, ImageFont, ImageDraw


class PyI25:
    "Interfaz para generar PDF de Factura Electrónica"
    _public_methods_ = ['GenerarImagen', 
                        'DigitoVerificadorModulo10'
                        ]
    _public_attrs_ = ['Version', 'Excepcion', 'Traceback']
        
    _reg_progid_ = "PyI25"
    _reg_clsid_ = "{5E6989E8-F658-49FB-8C39-97C74BC67650}"


    def __init__(self):
        self.Version = __version__
        self.Exception = self.Traceback = ""
            
    def GenerarImagen(self, codigo, archivo="barras.png", 
                      basewidth=3, width=None, height=30, extension = "PNG"):
        "Generar una imágen con el código de barras Interleaved 2 of 5"
        # basado de:
        #  * http://www.fpdf.org/en/script/script67.php
        #  * http://code.activestate.com/recipes/426069/

        wide = basewidth
        narrow = basewidth / 3

        # códigos ancho/angostos (wide/narrow) para los dígitos
        bars = ("nnwwn", "wnnnw", "nwnnw", "wwnnn", "nnwnw", "wnwnn", "nwwnn", 
                "nnnww", "wnnwn", "nwnwn", "nn", "wn")

        # agregar un 0 al principio si el número de dígitos es impar
        if len(codigo) % 2:
            codigo = "0" + codigo

        if not width:
            width = (len(codigo) * 3) * basewidth + (10 * narrow)
            print width
            #width = 380
        # crear una nueva imágen
        im = Image.new("1",(width, height))

        # agregar códigos de inicio y final
        codigo = "::" + codigo.lower() + ";:" # A y Z en el original

        # crear un drawer
        draw = ImageDraw.Draw(im)

        # limpiar la imágen
        draw.rectangle(((0, 0), (im.size[0], im.size[1])), fill=256)

        xpos = 0    
        # dibujar los códigos de barras
        for i in range(0,len(codigo),2):
            # obtener el próximo par de dígitos
            bar = ord(codigo[i]) - ord("0")
            space = ord(codigo[i + 1]) - ord("0")
            # crear la sequencia barras (1er dígito=barras, 2do=espacios)
            seq = ""
            for s in range(len(bars[bar])):
                seq = seq + bars[bar][s] + bars[space][s]

            for s in range(len(seq)):
                if seq[s] == "n":
                    width = narrow
                else:
                    width = wide

                # dibujar barras impares (las pares son espacios)
                if not s % 2:
                    draw.rectangle(((xpos,0),(xpos+width-1,height)),fill=0)
                xpos = xpos + width 
       
        im.save(archivo, extension.upper())
        return True 

    def DigitoVerificadorModulo10(self, codigo):
        "Rutina para el cálculo del dígito verificador 'módulo 10'"
        # http://www.consejo.org.ar/Bib_elect/diciembre04_CT/documentos/rafip1702.htm
        # Etapa 1: comenzar desde la izquierda, sumar todos los caracteres ubicados en las posiciones impares.
        codigo = codigo.strip()
        if not codigo or not codigo.isdigit():
            return ''
        etapa1 = sum([int(c) for i,c in enumerate(codigo) if not i%2])
        # Etapa 2: multiplicar la suma obtenida en la etapa 1 por el número 3
        etapa2 = etapa1 * 3
        # Etapa 3: comenzar desde la izquierda, sumar todos los caracteres que están ubicados en las posiciones pares.
        etapa3 = sum([int(c) for i,c in enumerate(codigo) if i%2])
        # Etapa 4: sumar los resultados obtenidos en las etapas 2 y 3.
        etapa4 = etapa2 + etapa3
        # Etapa 5: buscar el menor número que sumado al resultado obtenido en la etapa 4 dé un número múltiplo de 10. Este será el valor del dígito verificador del módulo 10.
        digito = 10 - (etapa4 - (int(etapa4 / 10) * 10))
        if digito == 10:
            digito = 0
        return str(digito)



if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(PyI25)
    elif "py2exe" in sys.argv:
        from distutils.core import setup
        from nsis import build_installer, Target
        import py2exe
        setup( 
            name="PyI25",
            version=__version__,
            description="Interfaz PyAfipWs I25 %s",
            long_description=__doc__,
            author="Mariano Reingart",
            author_email="reingart@gmail.com",
            url="http://www.sistemasagiles.com.ar",
            license="GNU GPL v3",
            com_server = ['pyi25'],
            console=[],
            options={ 
                'py2exe': {
                'includes': [],
                'optimize': 2,
                'excludes': ["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui","distutils.core","py2exe","nsis"],
                #'skip_archive': True,
            }},
            data_files = [(".", ["licencia.txt"]),],
            cmdclass = {"py2exe": build_installer}
        )
    else:
        
        pyi25 = PyI25()

        if '--barras' in sys.argv:
            barras = sys.argv[sys.argv.index("--barras")+1]
        else:
            cuit = 20267565393
            tipo_cbte = 2
            punto_vta = 4001
            cae = 61203034739042
            fch_venc_cae = 20110529
        
            # codigo de barras de ejemplo:
            barras = '%11s%02d%04d%s%8s' % (cuit, tipo_cbte, punto_vta, cae, fch_venc_cae)

        if not '--noverificador' in sys.argv:
            barras = barras + pyi25.DigitoVerificadorModulo10(barras)

        if '--archivo' in sys.argv:
            archivo = sys.argv[sys.argv.index("--archivo")+1]
        else:
            archivo="prueba-cae-i25.png"
        
        print "barras", barras
        print "archivo", archivo
        pyi25.GenerarImagen(barras, archivo)

        if not '--mostrar' in sys.argv:
            pass
        elif sys.platform=="linux2":
            os.system("eog ""%s""" % archivo)
        else:
            os.startfile(archivo)
