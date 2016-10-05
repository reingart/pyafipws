#!usr/bin/python
# -*- coding: utf-8-*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Aplicativo AdHoc Para generación de Facturas Electrónicas"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2009-2015 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.27g"

from datetime import datetime
from decimal import Decimal, getcontext, ROUND_DOWN
import os
import sys
import wx
import gui
import unicodedata
import traceback
from ConfigParser import SafeConfigParser
import wsaa, wsfe, wsfev1, wsfexv1
from utils import SimpleXMLElement, SoapClient, SoapFault, date
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP

#from PyFPDF.ejemplos.form import Form
from pyfepdf import FEPDF

# Formatos de archivos:
from formatos import formato_xml, formato_csv, formato_dbf, formato_txt, formato_json

HOMO = False
DEBUG = '--debug' in sys.argv
CONFIG_FILE = "rece.ini"

ACERCA_DE = u"""
PyRece: Aplicativo AdHoc para generar Facturas Electrónicas
Copyright (C) 2008-2015 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional y descargas ver:
http://www.sistemasagiles.com.ar/
"""

INSTRUCTIVO = U"""
Forma de uso:

 * Examinar: para buscar el archivo a procesar (opcional)
 * Cargar: para leer los datos del archivo de facturas a procesar 
 * Autenticar: para iniciar la sesión en los servidores de AFIP (obligatorio antes de autorizar)
 * Marcar Todo: para seleccionar todas las facturas
 * Autorizar: para autorizar las facturas seleccionadas, completando el CAE y demás datos
 * Autorizar Lote: para autorizar en un solo lote las facturas seleccionadas
 * Grabar: para almacenar los datos procesados en el archivo de facturas 
 * Previsualizar: para ver por pantalla la factura seleccionadas
 * Enviar: para envia por correo electrónico las facturas seleccionadas

Para solicitar soporte comercial, escriba a pyrece@sistemasagiles.com.ar
"""

    
class PyRece(gui.Controller):

    def on_load(self, event):
        self.cols = []
        self.items = []
        self.paths = [entrada]
        self.token = self.sign = ""
        self.smtp = None
        self.webservice = None
        if entrada and os.path.exists(entrada):
            self.cargar()
        
        self.components.cboWebservice.value = DEFAULT_WEBSERVICE
        self.on_cboWebservice_click(event)
        
        self.tipos = {
            1:u"Factura A",
            2:u"Notas de Débito A",
            3:u"Notas de Crédito A",
            4:u"Recibos A",
            5:u"Notas de Venta al contado A",
            6:u"Facturas B",
            7:u"Notas de Débito B",
            8:u"Notas de Crédito B",
            9:u"Recibos B",
            10:u"Notas de Venta al contado B",
            19:u"Facturas de Exportación",
            20:u"Nota de Débito por Operaciones con el Exterior",
            21:u"Nota de Crédito por Operaciones con el Exterior",
            39:u"Otros comprobantes A que cumplan con la R.G. N° 3419",
            40:u"Otros comprobantes B que cumplan con la R.G. N° 3419",
            60:u"Cuenta de Venta y Líquido producto A",
            61:u"Cuenta de Venta y Líquido producto B",
            63:u"Liquidación A",
            64:u"Liquidación B",
            11:u"Factura C",
            12:u"Nota de Débito C",
            13:u"Nota de Crédito C",
            15:u"Recibo C",
            }

        self.component.bgcolor = "light gray"
        # deshabilito ordenar
        ##self.components.lvwListado.GetColumnSorter = lambda: lambda x,y: 0

    def set_cols(self, cols):
        self.__cols = cols
        lv = self.components.lvwListado
        # remove old columns:
        lv.clear_all()
        # insert new columns
        for col in cols:
            ch = gui.ListColumn(lv, name=col, text=col.replace("_"," ").title(), align="left")
    def get_cols(self):
        return self.__cols
    cols = property(get_cols, set_cols)

    def set_items(self, items):
        cols = self.cols
        self.__items = items
        def convert_str(value):
            if value is None:
                return ''
            elif isinstance(value, str):
                return unicode(value,'latin1')
            elif isinstance(value, unicode):
                return value
            else:
                return str(value)
        self.components.lvwListado.items = [[convert_str(item[col]) for col in cols] for item in items]
        wx.SafeYield()
    def get_items(self):
        return self.__items
    items = property(get_items, set_items)

    def get_selected_items(self):
        for it in self.components.lvwListado.get_selected_items():
            yield it.index, it

    def set_selected_items(self, selected):
        for it in selected:
            it.selected = True

    def set_paths(self, paths):
        self.__paths = paths
        self.components.txtArchivo.value = ', '.join([fn for fn in paths])
    def get_paths(self):
        return self.__paths
    paths = property(get_paths, set_paths)
        
    def log(self, msg):
        if not isinstance(msg, unicode):
            msg = unicode(msg, "latin1","ignore")
        print "LOG", msg
        self.components.txtEstado.value = msg + u"\n" + self.components.txtEstado.value
        wx.SafeYield()
        f = None
        try:
            f = open("pyrece.log","a")
            f.write("%s: " % (datetime.now(), ))
            f.write(msg.encode("ascii", "ignore"))
            f.write("\n\r")
        except Exception, e:
            print e
        finally:
            if f:
                f.close()
                
    def progreso(self, value):
        if self.items:
            per = (value+1)/float(len(self.items))*100
            self.components.pbProgreso.value = per
            wx.SafeYield()

    def error(self, code, text):
        ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
        self.log(''.join(ex))
        gui.alert(text, 'Error %s' % code)

    def verifica_ws(self):
        if not self.ws:
            gui.alert("Debe seleccionar el webservice a utilizar!", 'Advertencia')
            raise RuntimeError()
        if not self.token or not self.sign:
            gui.alert("Debe autenticarse con AFIP!", 'Advertencia')
            raise RuntimeError()
        self.ws.Dummy()

    def on_btnMarcarTodo_click(self, event):
        for it in self.components.lvwListado.items:
            it.selected = True

    def on_menu_consultas_dummy_click(self, event):
        ##self.verifica_ws()
        try:
            if self.webservice=="wsfe":
                results = self.client.FEDummy()
                msg = "AppServ %s\nDbServer %s\nAuthServer %s" % (
                    results.appserver, results.dbserver, results.authserver)
                location = self.ws.client.location
            elif self.webservice in ("wsfev1", "wsfexv1"):
                self.ws.Dummy()
                msg = "AppServ %s\nDbServer %s\nAuthServer %s" % (
                    self.ws.AppServerStatus, self.ws.DbServerStatus, self.ws.AuthServerStatus)
                location = self.ws.client.location
            else:
                msg = "%s no soportado" % self.webservice
                location = ""
            gui.alert(msg, location)
        except Exception, e:
            self.error(u'Excepción',unicode(str(e),"latin1","ignore"))

    def on_menu_consultas_lastCBTE_click(self, event):
        ##self.verifica_ws()
        options = [v for k,v in sorted([(k,v) for k,v in self.tipos.items()])]
        result = gui.single_choice(options, "Tipo de comprobante",
                                   u"Consulta Último Nro. Comprobante", 
                )
        if not result:
            return
        tipocbte = [k for k,v in self.tipos.items() if v==result][0]
        result = gui.prompt(u"Punto de venta",
            u"Consulta Último Nro. Comprobante", '2')
        if not result:
            return
        ptovta = result

        try:
            if self.webservice=="wsfe":
                ultcmp = wsfe.recuperar_last_cmp(self.client, self.token, self.sign, 
                    cuit, ptovta, tipocbte)
            elif  self.webservice=="wsfev1":
                ultcmp = "%s (wsfev1)" % self.ws.CompUltimoAutorizado(tipocbte, ptovta) 
            elif  self.webservice=="wsfexv1":
                ultcmp = "%s (wsfexv1)" % self.ws.GetLastCMP(tipocbte, ptovta) 
            
            gui.alert(u"Último comprobante: %s\n" 
                u"Tipo: %s (%s)\nPunto de Venta: %s" % (ultcmp, self.tipos[tipocbte], 
                    tipocbte, ptovta), u'Consulta Último Nro. Comprobante')
        except SoapFault,e:
            self.log(self.client.xml_request)
            self.log(self.client.xml_response)
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except wsfe.WSFEError,e:
            self.error(e.code, e.msg.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(str(e),"latin1","ignore"))

    def on_menu_consultas_getCAE_click(self, event):
        self.verifica_ws()
        options = [v for k,v in sorted([(k,v) for k,v in self.tipos.items()])]
        result = gui.single_choice(options, "Tipo de comprobante",
            u"Consulta Comprobante", 
                )
        if not result:
            return
        tipocbte = [k for k,v in self.tipos.items() if v==result][0]
        result = gui.prompt(u"Punto de venta",
            u"Consulta Comprobante", '2')
        if not result:
            return
        ptovta = result
        result = gui.prompt(u"Nº de comprobante",
            u"Consulta Comprobante", '2')
        if not result:
            return
        nrocbte = result

        try:
            if self.webservice=="wsfe":
                cae = 'no soportado'
            elif  self.webservice=="wsfev1":
                cae = "%s (wsfev1)" % self.ws.CompConsultar(tipocbte, ptovta, nrocbte)
                self.log('CAE: %s' % self.ws.CAE)
                self.log('FechaCbte: %s' % self.ws.FechaCbte)
                self.log('PuntoVenta: %s' % self.ws.PuntoVenta)
                self.log('CbteNro: %s' % self.ws.CbteNro)
                self.log('ImpTotal: %s' % self.ws.ImpTotal)
                self.log('ImpNeto: %s' % self.ws.ImpNeto)
                self.log('ImptoLiq: %s' % self.ws.ImptoLiq)
                self.log('EmisionTipo: %s' % self.ws.EmisionTipo)
            elif  self.webservice=="wsfexv1":
                cae = "%s (wsfexv1)" % self.ws.GetCMP(tipocbte, ptovta, nrocbte)
                self.log('CAE: %s' % self.ws.CAE)
                self.log('FechaCbte: %s' % self.ws.FechaCbte)
                self.log('PuntoVenta: %s' % self.ws.PuntoVenta)
                self.log('CbteNro: %s' % self.ws.CbteNro)
                self.log('ImpTotal: %s' % self.ws.ImpTotal)
                    
            gui.alert(u"CAE: %s\n" 
                u"Tipo: %s (%s)\nPunto de Venta: %s\nNumero: %s\nFecha: %s" % (
                    cae, self.tipos[tipocbte],
                    tipocbte, ptovta, nrocbte, self.ws.FechaCbte), 
                    u'Consulta Comprobante')

        except SoapFault,e:
            self.log(self.client.xml_request)
            self.log(self.client.xml_response)
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except wsfe.WSFEError,e:
            self.error(e.code, e.msg.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(str(e),"latin1","ignore"))


    def on_menu_consultas_lastID_click(self, event):
        ##self.verifica_ws()
        try:
            if self.webservice=="wsfe":
                ultnro = wsfe.ultnro(self.client, self.token, self.sign, cuit)
                print "ultnro", ultnro
                print self.client.xml_response
            elif self.webservice=="wsfexv1":
                ultnro = self.ws.GetLastID()
            else: 
                ultnro = None
            gui.alert(u"Último ID (máximo): %s" % (ultnro), 
                u'Consulta Último ID')
        except SoapFault,e:
            self.log(self.client.xml_request)
            self.log(self.client.xml_response)
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except wsfe.WSFEError,e:
            self.error(e.code, e.msg.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(e))


    def on_menu_ayuda_acercade_click(self, event):
        text = ACERCA_DE
        gui.alert(text, u'Acerca de PyRece Versión %s' % __version__)

    def on_menu_ayuda_instructivo_click(self, event):
        text = INSTRUCTIVO
        gui.alert(text, u'Instructivo de PyRece')

    def on_menu_ayuda_limpiar_click(self, event):
        self.components.txtEstado.value = ""

    def on_menu_ayuda_mensajesXML_click(self, event):
        self.verifica_ws()
        self.components.txtEstado.value = u"XmlRequest:\n%s\n\nXmlResponse:\n%s" % (
            self.ws.xml_request, self.ws.xml_response)
        self.component.size = (592, 517)

    def on_menu_ayuda_estado_click(self, event):
        if self.component.size[1]<517:
            self.component.size = (592, 517)
        else:
            self.component.size = (592, 265)
    
    def on_menu_ayuda_configuracion_click(self, event):
        self.components.txtEstado.value = open(CONFIG_FILE).read()
        self.component.size = (592, 517)
        
    def on_cboWebservice_click(self, event):
        self.webservice = self.components.cboWebservice.value
        self.ws = None
        self.token = None
        self.sign = None
        
        if self.webservice == "wsfe":
            self.client = SoapClient(wsfe_url, action=wsfe.SOAP_ACTION, namespace=wsfe.SOAP_NS,
                        trace=False, exceptions=True)
        elif self.webservice == "wsfev1":
            self.ws = wsfev1.WSFEv1()
        elif self.webservice == "wsfexv1":
            self.ws = wsfexv1.WSFEXv1()

    def on_btnAutenticar_click(self, event):
        try:
            if self.webservice in ('wsfe', ):
                service = "wsfe"
            elif self.webservice in ('wsfev1', ):
                self.log("Conectando WSFEv1... " + wsfev1_url)
                self.ws.Conectar("",wsfev1_url, proxy_dict, timeout=60, cacert=CACERT, wrapper=WRAPPER)
                self.ws.Cuit = cuit
                service = "wsfe"
            elif self.webservice in ('wsfex', 'wsfexv1'):
                self.log("Conectando WSFEXv1... " + wsfexv1_url)
                self.ws.Conectar("",wsfexv1_url, proxy_dict, cacert=CACERT, wrapper=WRAPPER)
                self.ws.Cuit = cuit
                service = "wsfex"
            else:
                gui.alert('Debe seleccionar servicio web!', 'Advertencia')
                return

            self.log("Creando TRA %s ..." % service)
            ws = wsaa.WSAA()
            tra = ws.CreateTRA(service)
            self.log("Frimando TRA (CMS) con %s %s..." % (str(cert),str(privatekey)))
            cms = ws.SignTRA(str(tra),str(cert),str(privatekey))
            self.log("Llamando a WSAA... " + wsaa_url)
            ws.Conectar("", wsdl=wsaa_url, proxy=proxy_dict, cacert=CACERT, wrapper=WRAPPER)
            self.log("Proxy: %s" % proxy_dict)
            xml = ws.LoginCMS(str(cms))
            self.log("Procesando respuesta...")
            if xml:
                self.token = ws.Token
                self.sign = ws.Sign
            if DEBUG:
                self.log("Token: %s" % self.token)
                self.log("Sign: %s" % self.sign)
            elif self.token and self.sign:
                self.log("Token: %s... OK" % self.token[:10])
                self.log("Sign: %s... OK" % self.sign[:10])
            if self.webservice in ("wsfev1", "wsfexv1"):
                self.ws.Token = self.token
                self.ws.Sign = self.sign

            if xml:
                gui.alert('Autenticado OK!', 'Advertencia')
            else:
                gui.alert(u'Respuesta: %s' % ws.XmlResponse, u'No se pudo autenticar: %s' % ws.Excepcion)
        except SoapFault,e:
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(e))
    
    def examinar(self):
        filename = entrada
        wildcard = ["Planillas Excel (*.xlsx)|*.xlsx", 
                    "Archivos CSV (*.csv)|*.csv", 
                    "Archivos XML (*.xml)|*.xml", 
                    "Archivos TXT (*.txt)|*.txt", 
                    "Archivos DBF (*.dbf)|*.dbf",
                    "Archivos JSON (*.json)|*.json",
                   ]
        if entrada.endswith("xml"):
            wildcard.sort(reverse=True)

        result = gui.open_file('Abrir', 'datos', filename, '|'.join(wildcard))
        if not result:
            return
        self.paths = [result]

    def on_menu_archivo_abrir_click(self, event):
        self.examinar()
        self.cargar()

    def on_menu_archivo_cargar_click(self, event):
        self.cargar()
        
    def cargar(self):
        try:
            items = []
            for fn in self.paths:
                if fn.lower().endswith(".csv") or fn.lower().endswith(".xlsx"):
                    filas = formato_csv.leer(fn)
                    items.extend(filas)
                elif fn.lower().endswith(".xml"):
                    regs = formato_xml.leer(fn)
                    items.extend(formato_csv.aplanar(regs))
                elif fn.lower().endswith(".txt"):
                    regs = formato_txt.leer(fn)
                    items.extend(formato_csv.aplanar(regs))
                elif fn.lower().endswith(".dbf"):
                    reg = formato_dbf.leer(conf_dbf, carpeta=os.path.dirname(fn))
                    items.extend(formato_csv.aplanar(reg.values()))
                elif fn.lower().endswith(".json"):
                    regs = formato_json.leer(fn)
                    items.extend(formato_csv.aplanar(regs))
                else:
                    self.error(u'Formato de archivo desconocido: %s', unicode(fn))
            if len(items) < 2:
                gui.alert(u'El archivo no tiene datos válidos', 'Advertencia')
            # extraer los nombres de columnas (ignorar vacios de XLSX)
            cols = items and [str(it).strip() for it in items[0] if it] or []
            if DEBUG: print "Cols",cols
            # armar diccionario por cada linea
            items = [dict([(col,item[i]) for i, col in enumerate(cols)]) 
                                for item in items[1:]]
            self.cols = cols
            self.items = items
        except Exception,e:
                self.error(u'Excepción',unicode(e))
                ##raise

    def on_menu_archivo_guardar_click(self, event):
            filename = entrada
            wildcard = ["Archivos CSV (*.csv)|*.csv", "Archivos XML (*.xml)|*.xml", 
                        "Archivos TXT (*.txt)|*.txt", "Archivos DBF (*.dbf)|*.dbf",
                        "Archivos JSON (*.json)|*.json",
                        "Planillas Excel (*.xlsx)|*.xlsx",
                        ]
            if entrada.endswith("xml"):
                wildcard.sort(reverse=True)
            if self.paths:
                path = self.paths[0]
            else:
                path = salida
            result = gui.save_file(title='Guardar', filename=path, 
                wildcard='|'.join(wildcard))
            if not result:
                return
            fn = result[0]
            self.grabar(fn)
            

    def grabar(self, fn=None):
        try:
            if fn is None and salida:
                if salida.startswith("-") and self.paths:
                    fn = os.path.splitext(self.paths[0])[0] + salida
                else:
                    fn = salida
            elif not fn:
                raise RuntimeError("Debe indicar un nombre de archivo para grabar")
            if fn.lower().endswith(".csv") or fn.lower().endswith(".xlsx"):
                formato_csv.escribir([self.cols] + [[item[k] for k in self.cols] for item in self.items], fn)
            else:
                regs = formato_csv.desaplanar([self.cols] + [[item[k] for k in self.cols] for item in self.items])
                if fn.endswith(".xml"):
                    formato_xml.escribir(regs, fn)
                elif fn.endswith(".txt"):
                    formato_txt.escribir(regs, fn)
                elif fn.endswith(".dbf"):
                    formato_dbf.escribir(regs, conf_dbf, carpeta=os.path.dirname(fn))
                elif fn.endswith(".json"):
                    formato_json.escribir(regs, fn)
                else:
                    self.error(u'Formato de archivo desconocido', unicode(fn))
            gui.alert(u'Se guardó con éxito el archivo:\n%s' % (unicode(fn),), 'Guardar')
        except Exception, e:
            self.error(u'Excepción',unicode(e))

    def on_btnAutorizar_click(self, event):
        self.verifica_ws()
        try:
            ok = procesadas = rechazadas = 0
            cols = self.cols
            items = []
            self.progreso(0)
            selected = []
            for i, item in self.get_selected_items():
                kargs = item.copy()
                selected.append(item)
                kargs['cbt_desde'] = kargs['cbt_hasta'] = kargs ['cbt_numero']
                for key in kargs:
                    if isinstance(kargs[key], basestring):
                        kargs[key] = kargs[key].replace(",",".")
                if self.webservice == 'wsfe':
                    if 'id' not in kargs or kargs['id'] == "":
                        id = long(kargs['cbt_desde'])
                        id += (int(kargs['tipo_cbte'])*10**4 + int(kargs['punto_vta']))*10**8
                        kargs['id'] = id
                    if DEBUG:
                        self.log('\n'.join(["%s='%s'" % (k,v) for k,v in kargs.items()]))
                    if not cuit in kargs:
                        kargs['cuit'] = cuit
                    ret = wsfe.aut(self.client, self.token, self.sign, **kargs)
                    kargs.update(ret)
                    del kargs['cbt_desde'] 
                    del kargs['cbt_hasta']
                elif self.webservice == 'wsfev1':
                    encabezado = {}
                    for k in ('concepto', 'tipo_doc', 'nro_doc', 'tipo_cbte', 'punto_vta',
                              'cbt_desde', 'cbt_hasta', 'imp_total', 'imp_tot_conc', 'imp_neto',
                              'imp_iva', 'imp_trib', 'imp_op_ex', 'fecha_cbte', 
                              'moneda_id', 'moneda_ctz'):
                        encabezado[k] = kargs[k]
                            
                    for k in ('fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta'):
                        if k in kargs:
                            encabezado[k] = kargs.get(k)
                    
                    self.ws.CrearFactura(**encabezado)
                    
                    for l in range(1,1000):
                        k = 'tributo_%%s_%s' % l
                        if (k % 'id') in kargs:
                            id = kargs[k % 'id']
                            desc = kargs[k % 'desc']
                            base_imp = kargs[k % 'base_imp']
                            alic = kargs[k % 'alic']
                            importe = kargs[k % 'importe']
                            if id:
                                self.ws.AgregarTributo(id, desc, base_imp, alic, importe)
                        else:
                            break

                    for l in range(1,1000):
                        k = 'iva_%%s_%s' % l
                        if (k % 'id') in kargs:
                            id = kargs[k % 'id']
                            base_imp = kargs[k % 'base_imp']
                            importe = kargs[k % 'importe']
                            if id:
                                self.ws.AgregarIva(id, base_imp, importe)
                        else:
                            break
                        
                    for l in range(1,1000):
                        k = 'cbte_asoc_%%s_%s' % l
                        if (k % 'tipo') in kargs:
                            tipo = kargs[k % 'tipo']
                            pto_vta = kargs[k % 'pto_vta']
                            nro = kargs[k % 'nro']
                            if id:
                                self.ws.AgregarCmpAsoc(tipo, pto_vta, nro)
                        else:
                            break
                
                    if DEBUG:
                        self.log('\n'.join(["%s='%s'" % (k,v) for k,v in self.ws.factura.items()]))

                    cae = self.ws.CAESolicitar()
                    kargs.update({
                        'cae': self.ws.CAE,
                        'fecha_vto': self.ws.Vencimiento,
                        'resultado': self.ws.Resultado,
                        'motivo': self.ws.Obs,
                        'reproceso': self.ws.Reproceso,
                        'err_code': self.ws.ErrCode.encode("latin1"),
                        'err_msg': self.ws.ErrMsg.encode("latin1"),
                        })
                    if self.ws.ErrMsg:
                        gui.alert(self.ws.ErrMsg, "Error AFIP")
                    if self.ws.Obs and self.ws.Obs!='00':
                        gui.alert(self.ws.Obs, u"Observación AFIP")

                elif self.webservice == 'wsfexv1':
                    kargs['cbte_nro'] = kargs ['cbt_numero']
                    kargs['permiso_existente'] = kargs['permiso_existente'] or ""
                    encabezado = {}
                    for k in ('tipo_cbte', 'punto_vta', 'cbte_nro', 'fecha_cbte',
                              'imp_total', 'tipo_expo', 'permiso_existente', 'pais_dst_cmp',
                              'nombre_cliente', 'cuit_pais_cliente', 'domicilio_cliente',
                              'id_impositivo', 'moneda_id', 'moneda_ctz',
                              'obs_comerciales', 'obs_generales', 'forma_pago', 'incoterms', 
                              'idioma_cbte', 'incoterms_ds'):
                        encabezado[k] = kargs.get(k)
                    
                    self.ws.CrearFactura(**encabezado)
                    
                    for l in range(1,1000):
                        k = 'codigo%s' % l
                        if k in kargs:
                            codigo = kargs['codigo%s' % l]
                            ds = kargs['descripcion%s' % l]
                            qty = kargs['cantidad%s' % l]
                            umed = kargs['umed%s' % l]
                            precio = kargs['precio%s' % l]
                            importe = kargs['importe%s' % l]
                            bonif = kargs.get('bonif%s' % l)
                            self.ws.AgregarItem(codigo, ds, qty, umed, precio, importe, bonif)
                        else:
                            break
                        
                    for l in range(1,1000):
                        k = 'cbte_asoc_%%s_%s' % l
                        if (k % 'tipo') in kargs:
                            tipo = kargs[k % 'tipo']
                            pto_vta = kargs[k % 'pto_vta']
                            nro = kargs[k % 'nro']
                            if id:
                                self.ws.AgregarCmpAsoc(tipo, pto_vta, nro)
                        else:
                            break
                
                    if DEBUG:
                        self.log('\n'.join(["%s='%s'" % (k,v) for k,v in self.ws.factura.items()]))

                    cae = self.ws.Authorize(kargs['id'])
                    kargs.update({
                        'cae': self.ws.CAE,
                        'fecha_vto': self.ws.Vencimiento,
                        'resultado': self.ws.Resultado,
                        'motivo': self.ws.Obs,
                        'reproceso': self.ws.Reproceso,
                        'err_code': self.ws.ErrCode.encode("latin1"),
                        'err_msg': self.ws.ErrMsg.encode("latin1"),
                        })
                    if self.ws.ErrMsg:
                        gui.alert(self.ws.ErrMsg, "Error AFIP")
                    if self.ws.Obs and self.ws.Obs!='00':
                        gui.alert(self.ws.Obs, u"Observación AFIP")
                        
                # actuaizo la factura
                for k in ('cae', 'fecha_vto', 'resultado', 'motivo', 'reproceso', 'err_code', 'err_msg'):
                    if kargs.get(k):
                        item[k] = kargs[k]
                self.items[i] = item
                self.log(u"ID: %s CAE: %s Motivo: %s Reproceso: %s" % (kargs['id'], kargs['cae'], kargs['motivo'],kargs['reproceso']))
                procesadas += 1
                if kargs['resultado'] == "R":
                    rechazadas += 1
                elif kargs['resultado'] == "A":
                    ok += 1
                self.progreso(i)
            self.items = self.items 
            self.set_selected_items(selected)
            self.progreso(len(self.items) - 1)
            gui.alert(u'Proceso finalizado, procesadas %d\n\n'
                    'Aceptadas: %d\n'
                    'Rechazadas: %d' % (procesadas, ok, rechazadas), 
                    u'Autorización')
            self.grabar()
        except SoapFault, e:
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except wsfe.WSFEError,e:
            self.error(e.code, e.msg.encode("ascii","ignore"))
        except KeyError, e:
            self.error("Error",u'Campo obligatorio no encontrado: %s' % e)
        except Exception, e:
            self.error(u'Excepción',unicode(e))
        finally:
            if DEBUG:
                if self.webservice == 'wsfev1' and DEBUG:
                    print self.ws.XmlRequest
                    print self.ws.XmlResponse

    def on_btnAutorizarLote_click(self, event):
        self.verifica_ws()
        if not self.items: return
        try:
            #getcontext().prec = 2
            ok = 0
            rechazadas = 0
            cols = self.cols
            items = []
            self.progreso(0)
            cbt_desde = cbt_hasta = None
            datos = {
                'tipo_cbte': None,
                'punto_vta': None,
                'fecha_cbte': None,
                'fecha_venc_pago': None,
                'fecha_cbte': None,
                'fecha_venc_pago': None,
                'fecha_serv_desde': None,
                'fecha_serv_hasta': None,
                'moneda_id': None,
                'moneda_ctz': None,
                'id': None,
            }
            importes = {
                'imp_total': Decimal(0),
                'imp_tot_conc': Decimal(0),
                'imp_neto': Decimal(0),
                'imp_iva':Decimal(0),
                'imp_op_ex': Decimal(0),
                'imp_trib': Decimal(0),
            }
            for l in range(1,5):
                k = 'iva_%%s_%s' % l
                datos[k % 'id'] = None
                importes[k % 'base_imp'] = Decimal(0)
                importes[k % 'importe'] = Decimal(0)

            for l in range(1,10):
                k = 'tributo_%%s_%s' % l
                datos[k % 'id'] = None
                datos[k % 'desc'] = None
                importes[k % 'base_imp'] = Decimal(0)
                datos[k % 'alic'] = None
                importes[k % 'importe'] = Decimal(0)

            for i, item in self.get_selected_items():
                if cbt_desde is None or int(item['cbt_numero']) < cbt_desde:
                    cbt_desde = int(item['cbt_numero'])
                if cbt_hasta is None or int(item['cbt_numero']) > cbt_hasta:
                    cbt_hasta = int(item['cbt_numero'])
                for key in item:
                    if key in datos:
                        if datos[key] is None:
                            datos[key] = item[key]
                        elif datos[key] != item[key]:
                            raise RuntimeError(u"%s tiene valores distintos en el lote!" % key)
                    if key in importes and item[key]:
                        importes[key] = importes[key] + Decimal("%.2f" % float(str(item[key].replace(",","."))))
                
            kargs = {'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta}
            kargs.update({'tipo_doc': 99, 'nro_doc':  '0'})
            kargs.update(datos)
            kargs.update(importes)
            if kargs['fecha_serv_desde'] and kargs['fecha_serv_hasta']:
                kargs['presta_serv'] = 1
                kargs['concepto'] = 2
            else:
                kargs['presta_serv'] = 0
                kargs['concepto'] = 1
                del kargs['fecha_serv_desde'] 
                del kargs['fecha_serv_hasta']
            
            for key, val in importes.items():
                importes[key] = val.quantize(Decimal('.01'), rounding=ROUND_DOWN)
                
            if 'id' not in kargs or kargs['id'] == "":
                id = long(kargs['cbt_desde'])
                id += (int(kargs['tipo_cbte'])*10**4 + int(kargs['punto_vta']))*10**8
                kargs['id'] = id
            
            if DEBUG:
                self.log('\n'.join(["%s='%s'" % (k,v) for k,v in kargs.items()]))
            if '--test' in sys.argv:
                kargs['cbt_desde'] = 777
                kargs['fecha_cbte'] = '20110802'
                kargs['fecha_venc_pago'] = '20110831'

            if gui.confirm("Confirma Lote:\n"
                "Tipo: %(tipo_cbte)s Desde: %(cbt_desde)s Hasta %(cbt_hasta)s\n"
                "Neto: %(imp_neto)s IVA: %(imp_iva)s Trib.: %(imp_trib)s Total: %(imp_total)s" 
                % kargs, "Autorizar lote:"):

                if self.webservice == 'wsfev1':
                    encabezado = {}
                    for k in ('concepto', 'tipo_doc', 'nro_doc', 'tipo_cbte', 'punto_vta',
                              'cbt_desde', 'cbt_hasta', 'imp_total', 'imp_tot_conc', 'imp_neto',
                              'imp_iva', 'imp_trib', 'imp_op_ex', 'fecha_cbte', 
                              'moneda_id', 'moneda_ctz'):
                        encabezado[k] = kargs[k]
                            
                    for k in ('fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta'):
                        if k in kargs:
                            encabezado[k] = kargs.get(k)
                    
                    self.ws.CrearFactura(**encabezado)
                    for l in range(1,1000):
                        k = 'iva_%%s_%s' % l
                        if (k % 'id') in kargs:
                            id = kargs[k % 'id']
                            base_imp = kargs[k % 'base_imp']
                            importe = kargs[k % 'importe']
                            if id:
                                self.ws.AgregarIva(id, base_imp, importe)
                        else:
                            break

                    for l in range(1,1000):
                        k = 'tributo_%%s_%s' % l
                        if (k % 'id') in kargs:
                            id = kargs[k % 'id']
                            desc = kargs[k % 'desc']
                            base_imp = kargs[k % 'base_imp']
                            alic = kargs[k % 'alic']
                            importe = kargs[k % 'importe']
                            if id:
                                self.ws.AgregarTributo(id, desc, base_imp, alic, importe)
                        else:
                            break

                    if DEBUG:
                        self.log('\n'.join(["%s='%s'" % (k,v) for k,v in self.ws.factura.items()]))

                    cae = self.ws.CAESolicitar()
                    kargs.update({
                        'cae': self.ws.CAE,
                        'fecha_vto': self.ws.Vencimiento,
                        'resultado': self.ws.Resultado,
                        'motivo': self.ws.Obs,
                        'reproceso': self.ws.Reproceso,
                        'err_code': self.ws.ErrCode.encode("latin1"),
                        'err_msg': self.ws.ErrMsg.encode("latin1"),
                        })
                    if self.ws.ErrMsg:
                        gui.alert(self.ws.ErrMsg, "Error AFIP")
                    if self.ws.Obs and self.ws.Obs!='00':
                        gui.alert(self.ws.Obs, u"Observación AFIP")
            
                for i, item in self.get_selected_items():
                    for key in ('id', 'cae', 'fecha_vto', 'resultado', 'motivo', 'reproceso', 'err_code', 'err_msg'):
                        item[key] = kargs[key]
                    
                self.log("ID: %s CAE: %s Motivo: %s Reproceso: %s" % (kargs['id'], kargs['cae'], kargs['motivo'],kargs['reproceso']))
                if kargs['resultado'] == "R":
                    rechazadas += 1
                elif kargs['resultado'] == "A":
                    ok += 1

                self.items = self.items # refrescar, ver de corregir
                self.progreso(len(self.items))
                gui.alert('Proceso finalizado OK!\n\nAceptadas: %d\nRechazadas: %d' % (ok, rechazadas), 'Autorización')
                self.grabar()
        except SoapFault,e:
            self.log(self.client.xml_request)
            self.log(self.client.xml_response)
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except wsfe.WSFEError,e:
            self.error(e.code, e.msg.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(e))

    def on_btnPrevisualizar_click(self, event):
        try:
            j = 0
            for i, item in self.get_selected_items():
                j += 1
                archivo = self.generar_factura(item,  mostrar=(j==1))
        except Exception, e:
            print e
            self.error(u'Excepción', unicode(str(e), 'latin1', 'ignore'))

    def on_btnEnviar_click(self, event):
        try:
            ok = no = 0
            self.progreso(0)
            for i, item in self.get_selected_items():
                if not item['cae'] in ("", "NULL"):
                    archivo = self.generar_factura(item)
                    if item.get('email'):
                        self.enviar_mail(item,archivo)
                        ok += 1
                    else:
                        no += 1
                        self.log("No se envia factura %s por no tener EMAIL" % item['cbt_numero'])
                else:
                    self.log("No se envia factura %s por no tener CAE" % item['cbt_numero'])
                    no += 1
                self.progreso(i)
            self.progreso(len(self.items))
            gui.alert('Proceso finalizado OK!\n\nEnviados: %d\nNo enviados: %d' % (ok, no), 'Envio de Email')
        except Exception, e:
            self.error(u'Excepción',unicode(e))
            
    def generar_factura(self, fila, mostrar=False):
        
        fepdf = FEPDF()
        fact = formato_csv.desaplanar([self.cols] + [[item[k] for k in self.cols] for item in [fila]])[0]
        fact['cbte_nro'] = fact['cbt_numero']
        fact['items'] = fact['detalles']

        for d in fact['datos']:
            fepdf.AgregarDato(d['campo'], d['valor'], d['pagina'])
            # por compatiblidad, completo campos anteriores
            if d['campo'] not in fact and d['valor']:
                fact[d['campo']] = d['valor']
                
        fepdf.factura = fact
        # cargo el formato CSV por defecto (factura.csv)
        fepdf.CargarFormato(conf_fact.get("formato", "factura.csv"))

        # establezco formatos (cantidad de decimales) según configuración:
        fepdf.FmtCantidad = conf_fact.get("fmt_cantidad", "0.2")
        fepdf.FmtPrecio = conf_fact.get("fmt_precio", "0.2")
        
        # datos fijos:
        fepdf.CUIT = cuit  # CUIT del emisor para código de barras
        for k, v in conf_pdf.items():
            fepdf.AgregarDato(k, v)

        fepdf.CrearPlantilla(papel=conf_fact.get("papel", "legal"), 
                             orientacion=conf_fact.get("orientacion", "portrait"))
        fepdf.ProcesarPlantilla(num_copias=int(conf_fact.get("copias", 1)),
                                lineas_max=int(conf_fact.get("lineas_max", 24)),
                                qty_pos=conf_fact.get("cant_pos") or 'izq')
        
        salida = conf_fact.get("salida", "")
        fact = fepdf.factura
        if salida:
            pass
        elif 'pdf' in fact and fact['pdf']:
            salida = fact['pdf']
        else:
            # genero el nombre de archivo según datos de factura
            d = conf_fact.get('directorio', ".")
            clave_subdir = conf_fact.get('subdirectorio','fecha_cbte')
            if clave_subdir:
                d = os.path.join(d, item[clave_subdir])
            if not os.path.isdir(d):
                os.mkdir(d)
            fs = conf_fact.get('archivo','numero').split(",")
            it = item.copy()
            tipo_fact, letra_fact, numero_fact = fact['_fmt_fact']
            it['tipo'] = tipo_fact.replace(" ", "_")
            it['letra'] = letra_fact
            it['numero'] = numero_fact
            it['mes'] = item['fecha_cbte'][4:6]
            it['año'] = item['fecha_cbte'][0:4]
            # remover acentos, ñ del nombre de archivo (vía unicode):
            fn = u''.join([unicode(it.get(ff,ff)) for ff in fs])
            fn = unicodedata.normalize('NFKD', fn).encode('ASCII', 'ignore') 
            salida = os.path.join(d, "%s.pdf" % fn)
        fepdf.GenerarPDF(archivo=salida)
        if mostrar:
            fepdf.MostrarPDF(archivo=salida,imprimir='--imprimir' in sys.argv)

        return salida
        
    def enviar_mail(self, item, archivo):
        archivo = self.generar_factura(item)
        if item['email']:
            msg = MIMEMultipart()
            msg['Subject'] = conf_mail['motivo'].replace("NUMERO",str(item['cbt_numero']))
            msg['From'] = conf_mail['remitente']
            msg['Reply-to'] = msg['From']
            msg['To'] = item['email']
            msg.preamble = 'Mensaje de multiples partes.\n'
            if not 'html' in conf_mail:
                part = MIMEText(conf_mail['cuerpo'])
                msg.attach(part)
            else:
                alt = MIMEMultipart('alternative')
                msg.attach(alt)
                text = MIMEText(conf_mail['cuerpo'])
                alt.attach(text)
                # We reference the image in the IMG SRC attribute by the ID we give it below
                html = MIMEText(conf_mail['html'], 'html')
                alt.attach(html)
            part = MIMEApplication(open(archivo,"rb").read())
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(archivo))
            msg.attach(part)

            try:
                self.log("Enviando email: %s a %s" % (msg['Subject'], msg['To']))
                if not self.smtp:
                    self.smtp = SMTP(conf_mail['servidor'], conf_mail.get('puerto', 25))
                    if conf_mail['usuario'] and conf_mail['clave']:
                        self.smtp.ehlo()
                        self.smtp.login(conf_mail['usuario'], conf_mail['clave'])
                self.smtp.sendmail(msg['From'], msg['To'], msg.as_string())
            except Exception,e:
                self.error(u'Excepción',unicode(e))
            
        
if __name__ == '__main__':

    if len(sys.argv)>1 and not sys.argv[1].startswith("-"):
        CONFIG_FILE = sys.argv[1]
    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    if not len(config.sections()):
        if os.path.exists(CONFIG_FILE):
            gui.alert(u"Error al cargar archivo de configuración: %s" % 
                        CONFIG_FILE, "PyRece: Imposible Continuar")
        else:
            gui.alert(u"No se encuentra archivo de configuración: %s" % 
                        CONFIG_FILE, "PyRece: Imposible Continuar")
        sys.exit(1)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSFEv1','CUIT')
    if config.has_option('WSFEv1','ENTRADA'):
        entrada = config.get('WSFEv1','ENTRADA')
    else:
        entrada = ""
    if not os.path.exists(entrada):
        entrada = "facturas.csv"
    if config.has_option('WSFEv1','SALIDA'):
        salida = config.get('WSFEv1','SALIDA')
    else:
        salida = "resultado.csv"
    
    if config.has_section('FACTURA'):
        conf_fact = dict(config.items('FACTURA'))
    else:
        conf_fact = {}
    
    conf_pdf = dict(config.items('PDF'))
    conf_mail = dict(config.items('MAIL'))

    if config.has_section('DBF'):
        conf_dbf = dict(config.items('DBF'))
    else:
        conf_dbf = {}

      
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = wsaa.WSAAURL
    if config.has_option('WSFE','URL') and not HOMO:
        wsfe_url = config.get('WSFE','URL')
    else:
        wsfe_url = wsfe.WSFEURL

    if config.has_option('WSFEv1','URL') and not HOMO:
        wsfev1_url = config.get('WSFEv1','URL')
    else:
        wsfev1_url = wsfev1.WSDL

    if config.has_option('WSFEXv1','URL') and not HOMO:
        wsfexv1_url = config.get('WSFEXv1','URL')
    else:
        wsfexv1_url = wsfexv1.WSDL

    CACERT = config.has_option('WSAA', 'CACERT') and config.get('WSAA', 'CACERT') or None
    WRAPPER = config.has_option('WSAA', 'WRAPPER') and config.get('WSAA', 'WRAPPER') or None

    DEFAULT_WEBSERVICE = "wsfev1"
    if config.has_section('PYRECE'):
        DEFAULT_WEBSERVICE = config.get('PYRECE','WEBSERVICE')

    if config.has_section('PROXY'):
        proxy_dict = dict(("proxy_%s" % k,v) for k,v in config.items('PROXY'))
        proxy_dict['proxy_port'] = int(proxy_dict['proxy_port'])
    else:
        proxy_dict = {}
       
    c = PyRece()
    gui.main_loop()
