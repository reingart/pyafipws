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

"Módulo para manejo de archivos JSON"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"

from decimal import Decimal

try:
    import json
except ImportError:
    try:
        import simplejson as json 
    except:
        print "para soporte de JSON debe instalar simplejson"

        
def leer(fn="entrada.json"):
    "Analiza un archivo JSON y devuelve un diccionario (confia en que el json este ok)"
    items = []
    jsonfile = open(fn, "rb")
    regs = json.load(jsonfile)
    return regs

    
def escribir(filas, fn="salida.json"):
    "Dado una lista de comprobantes (diccionarios), escribe JSON"
    import codecs
    jsonfile = codecs.open(fn, "w")
    json.dump(filas, jsonfile, sort_keys=True, indent=4, encoding="utf-8",)
    jsonfile.close()

    
