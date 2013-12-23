#!/usr/bin/python
# -*- coding: utf-8 -*-

"Aplicativo Visual (Front-end) Remito Electrónico (COT) ARBA"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2013- Mariano Reingart"
__license__ = "LGPL 3.0"

import datetime
import decimal
import time
import os
import fnmatch

# establecer la configuración regional por defecto:
import locale
locale.setlocale(locale.LC_ALL, "")

# importar gui2py (atajos)

import gui          

# importar el módulo principal de pyafipws para remito electrónico:

from cot import COT

# --- here goes your event handlers ---


# --- gui2py designer generated code starts ---

gui.Window(name='mywin', title=u'COT: Remito Electr\xf3nico ARBA', 
           resizable=True, height='423px', left='180', top='24', 
           width='389px', bgcolor=u'#E0E0E0', fgcolor=u'#4C4C4C')
gui.TextBox(name='txtTest', left='100', top='10', width='105', parent='mywin', 
            value=u'20267565393', )
gui.TextBox(id=329, name='txtTest_329', password=True, left='300', top='10', 
            width='75', parent='mywin', value=u'24567', )
gui.Line(name='line_25_556', height='3', left='24', top='390', width='349', 
         parent='mywin', )
gui.Button(label=u'click me!', name=u'btnAutorizar', left='110', top='394', 
           width='85', default=True, fgcolor=u'#4C4C4C', parent='mywin', )
gui.Button(label=u'Quit', name='btnClose', left='210', top='394', width='85', 
           parent='mywin', onclick='exit()', )
gui.ComboBox(name=u'url', 
             text=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', 
             height='29', left='100', top='36', width='277', 
             bgcolor=u'#FFFFFF', 
             data_selection=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', 
             fgcolor=u'#4C4C4C', 
             items=[u'https://cot.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do'], 
             parent='mywin', selection=1, 
             string_selection=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', )
gui.Label(name='lblTest_273_363', height='17', left='28', top='15', 
          width='58', parent='mywin', text=u'Usuario:', )
gui.Label(name='lblTest_273', height='17', left='243', top='14', width='58', 
          parent='mywin', text=u'Clave:', )
gui.Gauge(name='gauge', height='18', left='15', top='360', width='367', 
          parent='mywin', )
gui.StatusBar(name='statusbar', parent='mywin', )
gui.Label(id=228, name='lblTest_228', height='17', left='30', top='41', 
          width='32', parent='mywin', text=u'URL:', )
gui.ListView(id=213, name=u'remitos', height='74', left='20', top='171', 
             width='356', bgcolor=u'#FFFFFF', fgcolor=u'#3C3C3C', 
             item_count=0, parent='mywin', sort_column=0, 
             onitemselected="print ('sel %s' % event.target.get_selected_items())", )
gui.ListColumn(name=u'nro', text=u'N\xb0 \xdanico', width=250, 
               parent=u'remitos', )
gui.ListColumn(name=u'proc', text=u'Procesado', parent=u'remitos', )
gui.ListView(name=u'archivos', height='99', left='21', top='70', width='356', 
             bgcolor=u'#FFFFFF', fgcolor=u'#3C3C3C', item_count=0, 
             parent='mywin', sort_column=1, 
             onitemselected="print ('sel %s' % event.target.get_selected_items())", )
gui.ListColumn(name=u'txt', text='Archivo TXT', width=200, parent=u'archivos', )
gui.ListColumn(name=u'xml', text='Archivo XML', parent=u'archivos', )
gui.ListView(id=309, name=u'errores', height='99', left='20', top='250', 
             width='356', bgcolor=u'#FFFFFF', fgcolor=u'#3C3C3C', 
             item_count=0, parent='mywin', sort_column=-1, 
             onitemselected="print ('sel %s' % event.target.get_selected_items())", )
gui.ListColumn(name=u'codigo', text=u'C\xf3digo', width=100, 
               parent=u'errores', )
gui.ListColumn(name=u'descripcion', text=u'Descripci\xf3n', parent=u'errores', )

# --- gui2py designer generated code ends ---

# get a reference to the Top Level Window (used by designer / events handlers):
mywin = gui.get("mywin")

# cargar listado de archivos a procesar (y su correspondiente respuesta):
lv = mywin['archivos']
for fn in os.listdir("."):
    if fnmatch.fnmatch(fn, 'TB_???????????_*.txt'):
        txt = fn
        xml = os.path.splitext(fn)[0] + ".xml"
        if not os.path.exists(xml):
            xml = ""
        lv.items[fn] = {'txt': txt, 'xml': xml}        

# asignar controladores 

cot = COT()

cot.Usuario = ""
cot.Password = ""
cot.Conectar("", trace=True)

def cargar_archivo(evt):
    item = evt.target.get_selected_items()[0]
    lv = mywin['remitos']
    print item
    cot.PresentarRemito(item['txt'], testing=item['xml'])
    print cot.Excepcion, cot.Traceback
    print "CUIT Empresa:", cot.CuitEmpresa
    print "Numero Comprobante:", cot.NumeroComprobante
    print "Nombre Archivo:", cot.NombreArchivo
    print "Codigo Integridad:", cot.CodigoIntegridad

    while cot.LeerValidacionRemito():
        print "Numero Unico:", cot.NumeroUnico
        print "Procesado:", cot.Procesado
        while cot.LeerErrorValidacion():
            print "Error Validacion:", "|", cot.CodigoError, "|", cot.MensajeError

lv.onitemselected = cargar_archivo 

if __name__ == "__main__":
    mywin.show()
    mywin.title = "%s - %s" % (mywin.title, cot.Version)
    mywin['statusbar'].text = "" 
    gui.main_loop()
