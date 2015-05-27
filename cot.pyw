#!/usr/bin/python
# -*- coding: utf-8 -*-

"Aplicativo Visual (Front-end) Remito Electrónico (COT) ARBA"

from __future__ import with_statement
 
__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2013- Mariano Reingart"
__license__ = "LGPL 3.0"

import datetime
import decimal
import time
import os
import fnmatch
import shelve
import sys

# importar gui2py (atajos)

import gui          

# establecer la configuración regional por defecto:
import wx, locale
if sys.platform == "win32":
    locale.setlocale(locale.LC_ALL, 'Spanish_Argentina.1252')
elif sys.platform == "linux2":
    locale.setlocale(locale.LC_ALL, 'es_AR.utf8')
loc = wx.Locale(wx.LANGUAGE_DEFAULT, wx.LOCALE_LOAD_DEFAULT)

# importar el módulo principal de pyafipws para remito electrónico:

from cot import COT

# --- here goes your event handlers ---


# --- gui2py designer generated code starts ---

with gui.Window(name='mywin', title=u'COT: Remito Electr\xf3nico ARBA', 
                resizable=True, height='450px', left='180', top='24', 
                width='550px', bgcolor=u'#E0E0E0', fgcolor=u'#4C4C4C', 
                image='', ):
    gui.StatusBar(name='statusbar', )
    with gui.Panel(label=u'', name='panel', image='', ):
        gui.TextBox(name='usuario', left='299', top='10', width='105', 
                    value=u'20267565393', )
        gui.TextBox(name='clave', password=True, left='455', top='10', 
                    width='75', )
        gui.Line(name='line_25_556', height='3', left='24', top='390', 
                 width='499', )
        gui.Button(label=u'Salir', name='salir', left='440', top='394', 
                   width='85', onclick='import sys; sys.exit(0)', )
        gui.ComboBox(name=u'url', 
                     text=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', 
                     height='29', left='79', top='42', width='250', 
                     bgcolor=u'#FFFFFF', 
                     data_selection=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', 
                     fgcolor=u'#4C4C4C', 
                     items=[u'https://cot.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do'], 
                     selection=1, 
                     string_selection=u'http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do', )
        gui.Label(name='lblTest_273_363', height='17', left='234', top='15', 
                  width='58', text=u'Usuario:', )
        gui.Label(name='lblTest_273', height='17', left='410', top='14', 
                  width='58', text=u'Clave:', )
        gui.Gauge(name='gauge', height='18', left='20', top='365', 
                  width='507', )
        gui.Label(id=228, name='lblTest_228', height='17', left='341', 
                  top='47', width='32', text=u'Carpeta:', )
        with gui.ListView(id=213, name=u'remitos', height='74', left='20', 
                          top='180', width='510', item_count=0, sort_column=0, ):
            gui.ListColumn(name=u'nro', text=u'N\xb0 \xdanico Remito', 
                           width=250, )
            gui.ListColumn(name=u'proc', text=u'Procesado', )
        with gui.ListView(name=u'archivos', height='99', left='21', top='77', 
                          width='509', item_count=0, sort_column=2, ):
            gui.ListColumn(name=u'txt', text='Archivo TXT', width=200, )
            gui.ListColumn(name=u'xml', text='Archivo XML', )
            gui.ListColumn(name=u'cuit', text='CUIT Empresa', )
            gui.ListColumn(name=u'nro', text=u'N\xb0 Comprobante', )
            gui.ListColumn(name=u'md5', text=u'C\xf3digo Integridad', )
        with gui.ListView(id=309, name=u'errores', height='99', left='20', 
                          top='259', width='510', item_count=0, sort_column=0, ):
            gui.ListColumn(name=u'codigo', text=u'C\xf3digo', width=100, )
            gui.ListColumn(name=u'descripcion', text=u'Descripci\xf3n Error', 
                           width=400, )
        gui.TextBox(id=488, mask='date', name='fecha',  
                    left='101', top='10', width='127', enabled=False, 
                    value=datetime.date(2014, 4, 5), )
        gui.CheckBox(label=u'Fecha:', name=u'filtrar_fecha', height='24', 
                     left='22', top='11', width='73', 
                     tooltip=u'filtrar por fecha', )
        gui.Label(id=2084, name='lblTest_228_2084', height='17', left='24', 
                  top='47', width='32', text=u'URL:', )
        gui.ComboBox(id=961, name=u'carpeta', text=u'datos', height='29', 
                     left='412', top='42', width='118', bgcolor=u'#FFFFFF', 
                     data_selection=u'datos', fgcolor=u'#4C4C4C', 
                     items=[u'datos', u'procesados'], selection=0, 
                     string_selection=u'datos', )
        gui.Button(label=u'Procesar', name=u'procesar', left='20', top='394', 
                   tooltip="Presentar el remito en ARBA",
                   width='85', default=True, fgcolor=u'#4C4C4C', )
        gui.Button(label=u'Mover Procesados', name=u'mover', left='112', 
                   top='394', width='166', fgcolor=u'#4C4C4C', )

# --- gui2py designer generated code ends ---

# get a reference to the Top Level Window (used by designer / events handlers):
mywin = gui.get("mywin")
panel = mywin['panel']

# Manejo simple de claves:

passwd_db = shelve.open("passwd")

def getpass(username):
    password = passwd_db.get(str(username))
    if not password:
        password = gui.prompt(message=u"Ingrese contraseña",
                              title="Usuario: %s" % username, 
                              password=True) or ""
    return password

def setpass(username, password):
    passwd_db[str(username)] = password

def grabar_clave(evt):
    setpass(panel['usuario'].value, panel['clave'].value)

# asignar controladores 

cot = COT()

def listar_archivos(evt=None):
    # cargar listado de archivos a procesar (y su correspondiente respuesta):
    lv = panel['archivos']
    lv.clear()
    panel['remitos'].clear()
    panel['errores'].clear()
    # obtengo el fitlro de fecha (si esta habilitado):
    if panel['filtrar_fecha'].value:
        fecha = panel['fecha'].value.strftime("%Y%m%d")
    else:
        fecha = None
    carpeta = panel['carpeta'].text or "."
    for fn in os.listdir(carpeta):
        if fnmatch.fnmatch(fn, 'TB_???????????_*.txt'):
            # filtro por fecha (si esta tildado):
            # TB_20111111112_000000_20080124_000001.txt
            fecha_fn = fn[22:30]
            if fecha and fecha != fecha_fn:
                continue
            txt = fn
            xml = os.path.splitext(fn)[0] + ".xml"
            if not os.path.exists(os.path.join(carpeta, xml)):
                xml = ""
            lv.items[fn] = {'txt': txt, 'xml': xml}

def procesar_archivos(evt):
    # establezco la barra de progreso con la cantidad de archivos:
    panel['gauge'].max = len(panel['archivos'].items)
    # recorro los archivos a procesar:
    for i, item in enumerate(panel['archivos'].items):
        panel['gauge'].value = i + 1
        procesar_archivo(item, enviar=True)

def cargar_archivo(evt):
    # obtengo y proceso el archivo seleccionado:
    item = evt.target.get_selected_items()[0]
    procesar_archivo(item)

def abrir_archivo(evt):
    # obtengo y proceso el archivo seleccionado:
    item = evt.target.get_selected_items()[0]
    fn = os.path.join(panel['carpeta'].text, item['txt'])
    try:
        os.startfile(fn)
    except AttributeError:
        os.system("""gedit "%s" """ % fn)

def procesar_archivo(item, enviar=False):
    "Enviar archivo a ARBA y analizar la respuesta"
    
    # establezco credenciales:
    cuit = item['txt'][3:14]    
    cot.Usuario = panel['usuario'].value = cuit
    cot.Password = panel['clave'].value = getpass(cuit)
    cot.Conectar(panel['url'].text, trace=True)

    # obtengo la ruta al archivo de texto y xml
    carpeta = panel['carpeta'].text
    fn = os.path.join(carpeta, item['txt'])
    xml = item['xml']
    if xml:
        xml = os.path.join(carpeta, xml)
    elif not enviar:
        return

    # llamada al webservice:
    cot.PresentarRemito(fn, testing=xml)

    # grabo el xml devuelto:
    if not xml:
        xml = os.path.splitext(fn)[0] + ".xml"
        with open(xml, "w") as f:
            f.write(cot.XmlResponse)

    if cot.Excepcion and enviar:
        gui.alert(cot.Traceback, cot.Excepcion)
     
    if cot.TipoError and enviar:
        gui.alert(cot.MensajeError, "Error %s: %s" % (cot.TipoError, cot.CodigoError))

    # actualizo los datos devueltos en el listado    
    item['cuit'] = cot.CuitEmpresa
    item['nro'] = cot.NumeroComprobante
    item['md5'] = cot.CodigoIntegridad
    #assert item['txt'] == cot.NombreArchivo

    # limpio, enumero y agrego los remitos para el archivo seleccionado: 
    remitos = panel['remitos']
    item['remitos'] = []
    panel['errores'].items = []
    remitos.items = []
    i = 0
    while cot.LeerValidacionRemito():
        print "REMITO", i
        errores = []
        remito = {'nro': cot.NumeroUnico, 'proc': cot.Procesado,
                  'errores': errores}
        remitos.items[i] = remito
        item['remitos'].append(remito)
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

def filtro_fecha(evt):
    panel['fecha'].enabled = evt.target.value
    listar_archivos()


def mover_archivos(evt=None):
    carpeta = panel['carpeta'].text
    if carpeta != "datos":
        gui.alert("No se puede mover archivos de carpeta %s" % carpeta)
        
    i = 0
    print panel['archivos'].items
    for item in panel['archivos'].items:
        procesado = all([remito.get('proc', 'NO') == 'SI' 
                         for remito in item.get('remitos', [])])
        if procesado and item.get('remitos'):
            for fn in (item['txt'], item['xml']):
                fn0 = os.path.join("datos", fn)
                fn1 = os.path.join("procesados", fn)
                try:
                    os.rename(fn0, fn1)
                    i += 1
                except Exception, e:
                    gui.alert(unicode(e), "No se puede mover %s" % fn)
    gui.alert("Se movieron: %s archivos" % i)
    listar_archivos()


panel['archivos'].onitemselected = cargar_archivo 
panel['archivos'].onmousedclick = abrir_archivo
panel['remitos'].onitemselected = cargar_errores
panel['filtrar_fecha'].onclick = filtro_fecha
panel['fecha'].onchange = listar_archivos
panel['carpeta'].onchange = listar_archivos
panel['mover'].onclick = mover_archivos
panel['procesar'].onclick = procesar_archivos
panel['clave'].onchange = grabar_clave


if __name__ == "__main__":
    mywin.show()
    mywin.title = u"%s - %s" % (mywin.title, cot.Version.decode("latin1"))
    mywin['statusbar'].text = "" 
    listar_archivos()
    gui.main_loop()
    passwd_db.close()

