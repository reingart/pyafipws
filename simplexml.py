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


DEBUG = False


class SimpleXMLElement(object):
    "Clase para Manejo simple de XMLs (simil PHP)"
    def __init__(self, text = None, elements = None, document = None, namespace = None, prefix=None):
        self.__ns = namespace
        self.__prefix = prefix
        if text:
            try:
                self.__document = xml.dom.minidom.parseString(text)
            except:
                if DEBUG: print text
                raise
            self.__elements = [self.__document.documentElement]
        else:
            self.__elements = elements
            self.__document = document
    def addChild(self,tag,text=None,ns=True):
        if not ns or not self.__ns:
            if DEBUG: print "adding %s ns %s %s" % (tag, self.__ns,ns)
            element = self.__document.createElement(tag)
        else:
            if DEBUG: print "adding %s ns %s %s" % (tag, self.__ns,ns)
            element = self.__document.createElementNS(self.__ns, "%s:%s" % (self.__prefix, tag))
        if text:
            if isinstance(text, unicode):
                element.appendChild(self.__document.createTextNode(text))
            else:
                element.appendChild(self.__document.createTextNode(str(text)))
        self.__element.appendChild(element)
        return SimpleXMLElement(
                    elements=[element],
                    document=self.__document,
                    namespace=self.__ns,
                    prefix=self.__prefix)
    def asXML(self,filename=None):
        return self.__document.toxml('UTF-8')
    def __getattr__(self,tag):
        try:
            if self.__ns:
                if DEBUG: print "searching %s by ns=%s" % (tag,self.__ns)
                elements = self.__elements[0].getElementsByTagNameNS(self.__ns, tag)
            if not self.__ns or not elements:
                if DEBUG: print "searching %s " % (tag)
                elements = self.__elements[0].getElementsByTagName(tag)
            if not elements:
                if DEBUG: print self.__elements[0].toxml()
                raise AttributeError("Sin elementos")
            return SimpleXMLElement(
                elements=elements,
                document=self.__document,
                namespace=self.__ns,
                prefix=self.__prefix)
        except AttributeError, e:
            raise AttributeError("Tag not found: %s (%s)" % (tag, str(e)))
    def __iter__(self):
        "Iterate over xml tags"
        try:
            for __element in self.__elements:
                yield SimpleXMLElement(
                    elements=[__element],
                    document=self.__document,
                    namespace=self.__ns,
                    prefix=self.__prefix)
        except:
            raise
    def __getitem__(self,item):
        "Return xml attribute"
        return getattr(self.__element, item)
    def __contains__( self, item):
        return self.__element.getElementsByTagName(item)
    def __unicode__(self):
        return self.__element.childNodes[0].data
    def __str__(self):
        if self.__element.childNodes:
            rc = ""
            for node in self.__element.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc = rc + node.data.encode("utf8","ignore")
            return rc
        return ''
    def __repr__(self):
        return repr(self.__str__())
    def __int__(self):
        return int(self.__str__())
    def __float__(self):
        try:
            return float(self.__str__())
        except:
            raise IndexError(self.__element.toxml())    
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