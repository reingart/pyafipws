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

"Manejo de XML simple"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008/009 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.0"

import xml.dom.minidom

class SimpleXMLElement(object):
    "Clase para Manejo simple de XMLs (simil PHP)"
    def __init__(self, text = None, elements = None, document = None):
        if text:
            self.__document = xml.dom.minidom.parseString(text)
            self.__elements = [self.__document.documentElement]
        else:
            self.__elements = elements
            self.__document = document
    def addChild(self,tag,text=None):
        element = self.__document.createElement(tag) 
        if text:
            element.appendChild(self.__document.createTextNode(str(text)))
        self.__element.appendChild(element)
        return SimpleXMLElement(
                    elements=[element],
                    document=self.__document)
    def asXML(self,filename=None):
        return self.__document.toxml('utf8')
    def __getattr__(self,tag):
        try:
            return SimpleXMLElement(
                elements=self.__elements[0].getElementsByTagName(tag),
                document=self.__document)
        except:
            raise #RuntimeError("Tag not found: %s" % tag)
    def __iter__(self):
        "Iterate over xml tags"
        try:
            for __element in self.__elements:
                yield SimpleXMLElement(
                    elements=[__element],
                    document=self.__document)
        except:
            raise #RuntimeError("Tag not found: %s" % tag)        
    def __getitem__(self,item):
        "Return xml attribute"
        return getattr(self.__element, item)
    def __contains__( self, item):
        return self.__element.getElementsByTagName(item)
    def __unicode__(self):
        return self.__element.childNodes[0].data
    def __str__(self):
        if self.__element.childNodes:
            return self.__element.childNodes[0].data.encode("utf8","ignore")
        return ''
        #raise IndexError(self.__element.toxml())
            #raise IndexError("No data:"self.__element)
    def __repr__(self):
        return repr(self.__str__())
    def __int__(self):
        return int(self.__str__())
    def __float__(self):
        return float(self.__str__())
    __element = property(lambda self: self.__elements[0])

if __name__ == "__main__":
    span = SimpleXMLElement('<span><a href="google.com">google</a><prueba><i>1</i><float>1.5</float></prueba></span>')
    print str(span.a)
    print int(span.prueba.i)
    print float(span.prueba.float)

    span = SimpleXMLElement('<span><a href="google.com">google</a><a>yahoo</a><a>hotmail</a></span>')
    for a in span.a:
        print str(a)

    span.addChild('a','altavista')
    print span.asXML()