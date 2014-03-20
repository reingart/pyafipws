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

with gui.Window(name='mywin', title=u'COT: Remito Electr\xf3nico ARBA', 
                resizable=True, height='428px', left='180', top='24', 
                width='550px', bgcolor=u'#E0E0E0', fgcolor=u'#4C4C4C', 
                image='', ):
    gui.StatusBar(name='statusbar', )
    with gui.Panel(name='panel', ):
        gui.TextBox(name='txtTest', left='100', top='10', width='105', 
                    value=u'20267565393', )
        gui.TextBox(id=329, name='txtTest_329', password=True, left='300', 
                    top='10', width='75', value=u'24567', )
        gui.Line(name='line_25_556', height='3', left='24', top='390', 
                 width='499', )
        gui.Button(label=u'Procesar', name=u'procesar', left='187', top='394', 
                   width='85', default=True, fgcolor=u'#4C4C4C', )
        gui.Button(label=u'Salir', name='salir', left='287', top='394', 
                   width='85', onclick='exit()', )
        gui.ComboBox(name=u'url', 
                     text=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', 
                     height='29', left='100', top='36', width='426', 
                     bgcolor=u'#FFFFFF', 
                     data_selection=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', 
                     fgcolor=u'#4C4C4C', 
                     items=[u'https://cot.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do'], 
                     selection=1, 
                     string_selection=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', )
        gui.Label(name='lblTest_273_363', height='17', left='28', top='15', 
                  width='58', text=u'Usuario:', )
        gui.Label(name='lblTest_273', height='17', left='243', top='14', 
                  width='58', text=u'Clave:', )
        gui.Gauge(name='gauge', height='18', left='20', top='360', width='507', )
        gui.Label(id=228, name='lblTest_228', height='17', left='30', top='41', 
                  width='32', text=u'URL:', )
        with gui.ListView(id=213, name=u'remitos', height='74', left='20', 
                          top='171', width='510', bgcolor=u'#FFFFFF', 
                          fgcolor=u'#3C3C3C', item_count=0, sort_column=0, ):
            gui.ListColumn(name=u'nro', text=u'N\xb0 \xdanico Remito', width=250, )
            gui.ListColumn(name=u'proc', text=u'Procesado', )
        with gui.ListView(name=u'archivos', height='99', left='21', top='70', 
                          width='509', bgcolor=u'#FFFFFF', fgcolor=u'#3C3C3C', 
                          item_count=2, sort_column=2, ):
            gui.ListColumn(name=u'txt', text='Archivo TXT', width=200, )
            gui.ListColumn(name=u'xml', text='Archivo XML', )
            gui.ListColumn(name=u'cuit', text='CUIT Empresa', )
            gui.ListColumn(name=u'nro', text=u'N\xb0 Comprobante', )
            gui.ListColumn(name=u'md5', text=u'C\xf3digo Integridad', )
        with gui.ListView(id=309, name=u'errores', height='99', left='20', 
                          top='250', width='510', bgcolor=u'#FFFFFF', 
                          fgcolor=u'#3C3C3C', item_count=0, sort_column=-1, ):
            gui.ListColumn(name=u'codigo', text=u'C\xf3digo', width=100, )
            gui.ListColumn(name=u'descripcion', text=u'Descripci\xf3n Error', 
                           width=400, )

# --- gui2py designer generated code ends ---

# get a reference to the Top Level Window (used by designer / events handlers):
mywin = gui.get("mywin")
panel = mywin['panel']

# cargar listado de archivos a procesar (y su correspondiente respuesta):
lv = panel['archivos']
for fn in os.listdir("datos"):
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
    # obtengo y proceso el archivo seleccionado:
    item = evt.target.get_selected_items()[0]
    cot.PresentarRemito(os.path.join("datos", item['txt']), testing=item['xml'])

    print cot.Excepcion, cot.Traceback
    # actualizo los datos devueltos en el listado    
    item['cuit'] = cot.CuitEmpresa
    item['nro'] = cot.NumeroComprobante
    item['md5'] = cot.CodigoIntegridad
    #assert item['txt'] == cot.NombreArchivo

    # limpio, enumero y agrego los remitos para el archivo seleccionado: 
    remitos = panel['remitos']
    panel['errores'].items = []
    remitos.items = []
    i = 0
    while cot.LeerValidacionRemito():
        print "REMITO", i
        errores = []
        remitos.items[i] = {'nro': cot.NumeroUnico, 'proc': cot.Procesado,
                            'errores': errores}
        i += 1
        while cot.LeerErrorValidacion():
            print "Error Validacion:", "|", cot.CodigoError, "|", cot.MensajeError
            errores.append({'codigo': cot.CodigoError,
                            'descripcion': cot.MensajeError})

def cargar_errores(evt):
    # obtengo el remito seleccionado:
    item = evt.target.get_selected_items()[0]
    # limpio, enumero y agrego los errores para el remito seleccionado: 
    errores = panel['errores']
    errores.items = []
    for i, error in enumerate(item['errores']):
        print i, error
        errores.items[i] = error

panel['archivos'].onitemselected = cargar_archivo 
panel['remitos'].onitemselected = cargar_errores

if __name__ == "__main__":
    mywin.show()
    mywin.title = u"%s - %s" % (mywin.title, cot.Version.decode("latin1"))
    mywin['statusbar'].text = "" 
    gui.main_loop()
