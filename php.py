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

"Módulo con funciones y objetos para compatibilidad con PHP"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.0"

import datetime, sys, time
import xml.dom.minidom
import httplib2
from simplexml import SimpleXMLElement
from soap import SoapFault, SoapClient, parse_proxy

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


