#!usr/bin/python
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

"Aplicativo AdHoc Para generación de Facturas Electrónicas"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2009 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.23e"

from datetime import datetime
from decimal import Decimal
import os
import sys
import wx
from PythonCard import dialog, model
import traceback
from ConfigParser import SafeConfigParser
import wsaa, wsfe, wsfev1
from php import SimpleXMLElement, SoapClient, SoapFault, date
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP

#from PyFPDF.ejemplos.form import Form
from pyfepdf import FEPDF

# Formatos de archivos:
import formato_xml
import formato_csv
import formato_dbf
import formato_txt
import formato_json

HOMO = False
DEBUG = '--debug' in sys.argv
CONFIG_FILE = "rece.ini"

ACERCA_DE = u"""
PyRece: Aplicativo AdHoc para generar Facturas Electrónicas
Copyright (C) 2008/2009/2010/2011 Mariano Reingart reingart@gmail.com

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

def digito_verificador_modulo10(codigo):
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

    
class PyRece(model.Background):

    def on_initialize(self, event):
        self.cols = []
        self.items = []
        self.paths = [entrada]
        self.token = self.sign = ""
        self.smtp = None
        self.webservice = None
        if entrada and os.path.exists(entrada):
            self.cargar()
        
        self.components.cboWebservice.stringSelection = "wsfev1"
        self.on_cboWebservice_select(event)
        
        self.tipos = {
            1:u"Factura A",
            2:u"Notas de Débito A",
            3:u"Notas de Crédito A",
            4:u"Recibos A",
            5:u"Notas de Venta al contado A",
            6:u"Facturas B",
            7:u"Notas de Débito B",
            8:u"uNotas de Crédito B",
            9:u"uRecibos B",
            10:u"Notas de Venta al contado B",
            39:u"Otros comprobantes A que cumplan con la R.G. N° 3419",
            40:u"Otros comprobantes B que cumplan con la R.G. N° 3419",
            60:u"Cuenta de Venta y Líquido producto A",
            61:u"Cuenta de Venta y Líquido producto B",
            63:u"Liquidación A",
            64:u"Liquidación B"}

        
        # deshabilito ordenar
        self.components.lvwListado.GetColumnSorter = lambda: lambda x,y: 0

    def set_cols(self, cols):
        self.__cols = cols
        self.components.lvwListado.columnHeadings = [col.replace("_"," ").title() for col in cols]
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
        itemidx = -1
        itemidx = self.components.lvwListado.GetNextItem(itemidx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
        while itemidx >= 0:
            yield itemidx, self.__items[itemidx]
            itemidx = self.components.lvwListado.GetNextItem(itemidx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)

    def set_selected_items(self, selected):
        for itemidx in selected:
            self.components.lvwListado.Select(itemidx, on=True)

    def set_paths(self, paths):
        self.__paths = paths
        self.components.txtArchivo.text = ', '.join([fn for fn in paths])
    def get_paths(self):
        return self.__paths
    paths = property(get_paths, set_paths)
        
    def log(self, msg):
        if not isinstance(msg, unicode):
            msg = unicode(msg, "latin1","ignore")
        self.components.txtEstado.text = msg + u"\n" + self.components.txtEstado.text
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
        dialog.alertDialog(self, text, 'Error %s' % code)

    def verifica_ws(self):
        if not self.ws:
            dialog.alertDialog(self, "Debe seleccionar el webservice a utilizar!", 'Advertencia')
            raise RuntimeError()
        if not self.token or not self.sign:
            dialog.alertDialog(self, "Debe autenticarse con AFIP!", 'Advertencia')
            raise RuntimeError()

    def on_btnMarcarTodo_mouseClick(self, event):
        for i in range(len(self.__items)):
            self.components.lvwListado.SetSelection(i)

    def on_menuConsultasDummy_select(self, event):
        self.verifica_ws()
        try:
            if self.webservice=="wsfe":
                results = self.client.FEDummy()
                msg = "AppServ %s\nDbServer %s\nAuthServer %s" % (
                    results.appserver, results.dbserver, results.authserver)
                location = self.ws.client.location
            elif  self.webservice=="wsfev1":
                self.ws.Dummy()
                msg = "AppServ %s\nDbServer %s\nAuthServer %s" % (
                    self.ws.AppServerStatus, self.ws.DbServerStatus, self.ws.AuthServerStatus)
                location = self.ws.client.location
                    
            dialog.alertDialog(self, msg, location)
        except Exception, e:
            self.error(u'Excepción',unicode(str(e),"latin1","ignore"))

    def on_menuConsultasLastCBTE_select(self, event):
        self.verifica_ws()
        result = dialog.singleChoiceDialog(self, "Tipo de comprobante",
            u"Consulta Último Nro. Comprobante", 
                [v for k,v in sorted([(k,v) for k,v in self.tipos.items()])])
        if not result.accepted:
            return
        tipocbte = [k for k,v in self.tipos.items() if v==result.selection][0]
        result = dialog.textEntryDialog(self, u"Punto de venta",
            u"Consulta Último Nro. Comprobante", '2')
        if not result.accepted:
            return
        ptovta = result.text

        try:
            if self.webservice=="wsfe":
                ultcmp = wsfe.recuperar_last_cmp(self.client, self.token, self.sign, 
                    cuit, ptovta, tipocbte)
            elif  self.webservice=="wsfev1":
                ultcmp = "%s (wsfev1)" % self.ws.CompUltimoAutorizado(tipocbte, ptovta) 
                    
            dialog.alertDialog(self, u"Último comprobante: %s\n" 
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

    def on_menuConsultasGetCAE_select(self, event):
        self.verifica_ws()
        result = dialog.singleChoiceDialog(self, "Tipo de comprobante",
            u"Consulta Comprobante", 
                [v for k,v in sorted([(k,v) for k,v in self.tipos.items()])])
        if not result.accepted:
            return
        tipocbte = [k for k,v in self.tipos.items() if v==result.selection][0]
        result = dialog.textEntryDialog(self, u"Punto de venta",
            u"Consulta Comprobante", '2')
        if not result.accepted:
            return
        ptovta = result.text
        result = dialog.textEntryDialog(self, u"Nº de comprobante",
            u"Consulta Comprobante", '2')
        if not result.accepted:
            return
        nrocbte = result.text

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
                    
            dialog.alertDialog(self, u"CAE: %s\n" 
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


    def on_menuConsultasLastID_select(self, event):
        self.verifica_ws()
        try:
            ultnro = wsfe.ultnro(self.client, self.token, self.sign, cuit)
            dialog.alertDialog(self, u"Último ID (máximo): %s" % (ultnro), 
                u'Consulta Último ID')
        except SoapFault,e:
            self.log(self.client.xml_request)
            self.log(self.client.xml_response)
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except wsfe.WSFEError,e:
            self.error(e.code, e.msg.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(e))


    def on_menuAyudaAcercaDe_select(self, event):
        text = ACERCA_DE
        dialog.alertDialog(self, text, u'Acerca de PyRece Versión %s' % __version__)

    def on_menuAyudaInstructivo_select(self, event):
        text = INSTRUCTIVO
        dialog.alertDialog(self, text, u'Instructivo de PyRece')

    def on_menuAyudaLimpiar_select(self, event):
        self.components.txtEstado.text = ""

    def on_menuAyudaMensajesXML_select(self, event):
        self.verifica_ws()
        self.components.txtEstado.text = u"XmlRequest:\n%s\n\nXmlResponse:\n%s" % (
            self.ws.xml_request, self.ws.xml_response)
        self.size = (592, 517)

    def on_menuAyudaVerEstado_select(self, event):
        if self.size[1]<517:
            self.size = (592, 517)
        else:
            self.size = (592, 265)
    
    def on_menuAyudaVerConfiguracion_select(self, event):
        self.components.txtEstado.text = open(CONFIG_FILE).read()
        self.size = (592, 517)
        
    def on_cboWebservice_select(self, event):
        self.webservice = self.components.cboWebservice.stringSelection
        self.ws = None
        self.token = None
        self.sign = None
        
        if self.webservice == "wsfe":
            self.client = SoapClient(wsfe_url, action=wsfe.SOAP_ACTION, namespace=wsfe.SOAP_NS,
                        trace=False, exceptions=True)
        elif self.webservice == "wsfev1":
            self.ws = wsfev1.WSFEv1()

    def on_btnAutenticar_mouseClick(self, event):
        try:

            if self.webservice in ('wsfe', ):
                service = "wsfe"
            elif self.webservice in ('wsfev1', ):
                self.log("Conectando WSFEv1... " + wsfev1_url)
                self.ws.Conectar("",wsfev1_url, proxy_dict)
                self.ws.Cuit = cuit
                service = "wsfe"
            elif self.webservice in ('wsfex', ):
                service = "wsfex"
            else:
                dialog.alertDialog(self, 'Debe seleccionar servicio web!', 'Advertencia')
                return

            self.log("Creando TRA %s ..." % service)
            ws = wsaa.WSAA()
            tra = ws.CreateTRA(service)
            self.log("Frimando TRA (CMS) con %s %s..." % (str(cert),str(privatekey)))
            cms = ws.SignTRA(str(tra),str(cert),str(privatekey))
            self.log("Llamando a WSAA... " + wsaa_url)
            ws.Conectar("", wsdl=wsaa_url, proxy=proxy_dict)
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
            if self.webservice == "wsfev1":
                self.ws.Token = self.token
                self.ws.Sign = self.sign

            if xml:
                dialog.alertDialog(self, 'Autenticado OK!', 'Advertencia')
            else:
                dialog.alertDialog(self, u'Respuesta: %s' % ws.XmlResponse, u'No se pudo autenticar: %s' % ws.Excepcion)
        except SoapFault,e:
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(e))
    
    def examinar(self):
        filename = entrada
        wildcard = ["Archivos CSV (*.csv)|*.csv", "Archivos XML (*.xml)|*.xml", 
                        "Archivos TXT (*.txt)|*.txt", "Archivos DBF (*.dbf)|*.dbf",
                        "Archivos JSON (*.json)|*.json",
                        ]
        if entrada.endswith("xml"):
            wildcard.sort(reverse=True)

        result = dialog.fileDialog(self, 'Abrir', '', filename, '|'.join(wildcard))
        if not result.accepted:
            return
        self.paths = result.paths

    def on_menuArchivoAbrir_select(self, event):
        self.examinar()
        self.cargar()

    def on_menuArchivoCargar_select(self, event):
        self.cargar()
        
    def cargar(self):
        try:
            items = []
            for fn in self.paths:
                if fn.lower().endswith(".csv"):
                    filas = formato_csv.leer(fn)
                    items.extend(filas)
                elif fn.lower().endswith(".xml"):
                    regs = formato_xml.leer(fn)
                    items.extend(formato_csv.aplanar(regs))
                elif fn.lower().endswith(".txt"):
                    regs = formato_txt.leer(fn)
                    items.extend(formato_csv.aplanar(regs))
                elif fn.lower().endswith(".dbf"):
                    reg = formato_dbf.leer({'Encabezado': fn})
                    items.extend(formato_csv.aplanar(reg.values()))
                elif fn.lower().endswith(".json"):
                    regs = formato_json.leer(fn)
                    items.extend(formato_csv.aplanar(regs))
                else:
                    self.error(u'Formato de archivo desconocido: %s' % unicode(fn))
            if len(items) < 2:
                dialog.alertDialog(self, u'El archivo no tiene datos válidos', 'Advertencia')
            cols = items and [str(it).strip() for it in items[0]] or []
            if DEBUG: print "Cols",cols
            # armar diccionario por cada linea
            items = [dict([(cols[i],v) for i,v in enumerate(item)]) for item in items[1:]]
            self.cols = cols
            self.items = items
        except Exception,e:
                self.error(u'Excepción',unicode(e))

    def on_menuArchivoGuardar_select(self, event):
            filename = entrada
            wildcard = ["Archivos CSV (*.csv)|*.csv", "Archivos XML (*.xml)|*.xml", 
                        "Archivos TXT (*.txt)|*.txt", "Archivos DBF (*.dbf)|*.dbf",
                        "Archivos JSON (*.json)|*.json",
                        ]
            if entrada.endswith("xml"):
                wildcard.sort(reverse=True)
            if self.paths:
                path = self.paths[0]
            else:
                path = salida
            result = dialog.saveFileDialog(self, title='Guardar', filename=path, 
                wildcard='|'.join(wildcard))
            if not result.accepted:
                return
            fn = result.paths[0]
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
            if fn.endswith(".csv"):
                formato_csv.escribir([self.cols] + [[item[k] for k in self.cols] for item in self.items], fn)
            else:
                regs = formato_csv.desaplanar([self.cols] + [[item[k] for k in self.cols] for item in self.items])
                if fn.endswith(".xml"):
                    formato_xml.escribir(regs, fn)
                elif fn.endswith(".txt"):
                    formato_txt.escribir(regs, fn)
                elif fn.endswith(".dbf"):
                    formato_dbf.escribir(regs, {'Encabezado': fn})
                elif fn.endswith(".json"):
                    formato_json.escribir(regs, fn)
                else:
                    self.error(u'Formato de archivo desconocido: %s' % unicode(fn))
            dialog.alertDialog(self, u'Se guardó con éxito el archivo:\n%s' % (unicode(fn),), 'Guardar')
        except Exception, e:
            self.error(u'Excepción',unicode(e))

    def on_menuArchivoDiseniador_select(self, event):
        # TODO: no funciona porque PythonCard aparentemente no importa el mismo namespace de wx
        from pyfpdf_hg.designer import AppFrame
        frame = AppFrame()
        frame.Show(1)

    def on_btnAutorizar_mouseClick(self, event):
        self.verifica_ws()
        try:
            ok = procesadas = rechazadas = 0
            cols = self.cols
            items = []
            self.progreso(0)
            selected = []
            for i, item in self.get_selected_items():
                kargs = item.copy()
                selected.append(i)
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
                        dialog.alertDialog(self, self.ws.ErrMsg, "Error AFIP")
                    if self.ws.Obs and self.ws.Obs!='00':
                        dialog.alertDialog(self, self.ws.Obs, u"Observación AFIP")
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
            self.progreso(len(self.items))
            dialog.alertDialog(self, u'Proceso finalizado, procesadas %d\n\n'
                    'Aceptadas: %d\n'
                    'Rechazadas: %d' % (procesadas, ok, rechazadas), 
                    u'Autorización')
            self.grabar()
        except (SoapFault, wsfev1.SoapFault),e:
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

    def on_btnAutorizarLote_mouseClick(self, event):
        self.verifica_ws()
        if not self.items or self.webservice != 'wsfe': return
        try:
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
                'id': None,
            }
            importes = {
                'imp_total': Decimal(0),
                'imp_tot_conc': Decimal(0),
                'imp_neto': Decimal(0),
                'impto_liq':Decimal(0),
                'impto_liq_rni': Decimal(0),
                'imp_op_ex': Decimal(0),
            }
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
                    if key in importes:
                        importes[key] = importes[key] + Decimal(str(item[key]).replace(",","."))
                
            kargs = {'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta}
            kargs.update({'tipo_doc': 99, 'nro_doc':  '0'})
            kargs.update(datos)
            kargs.update(importes)
            if kargs['fecha_serv_desde'] and kargs['fecha_serv_hasta']:
                kargs['presta_serv'] = 1
            else:
                kargs['presta_serv'] = 0
                del kargs['fecha_serv_desde'] 
                del kargs['fecha_serv_hasta']
            
            if 'id' not in kargs or kargs['id'] == "":
                id = long(kargs['cbt_desde'])
                id += (int(kargs['tipo_cbte'])*10**4 + int(kargs['punto_vta']))*10**8
                kargs['id'] = id
            
            if DEBUG:
                self.log('\n'.join(["%s='%s'" % (k,v) for k,v in kargs.items()]))
            
            if dialog.messageDialog(self, "Confirma Lote:\n"
                "Tipo: %(tipo_cbte)s Desde: %(cbt_desde)s Hasta %(cbt_hasta)s\n"
                "Neto: %(imp_neto)s IVA: %(impto_liq)s Total: %(imp_total)s" 
                % kargs, "Autorizar lote:").accepted:
                ret = wsfe.aut(self.client, self.token, self.sign, cuit, **kargs)
                kargs.update(ret)
            
                for i, item in self.get_selected_items():
                    for key in ret:
                        item[key] = ret[key]
                    item['id'] = kargs['id']
                    
                self.log("ID: %s CAE: %s Motivo: %s Reproceso: %s" % (kargs['id'], kargs['cae'], kargs['motivo'],kargs['reproceso']))
                if kargs['resultado'] == "R":
                    rechazadas += 1
                elif kargs['resultado'] == "A":
                    ok += 1

                self.items = self.items # refrescar, ver de corregir
                self.progreso(len(self.items))
                dialog.alertDialog(self, 'Proceso finalizado OK!\n\nAceptadas: %d\nRechazadas: %d' % (ok, rechazadas), 'Autorización')
                self.grabar()
        except SoapFault,e:
            self.log(self.client.xml_request)
            self.log(self.client.xml_response)
            self.error(e.faultcode, e.faultstring.encode("ascii","ignore"))
        except wsfe.WSFEError,e:
            self.error(e.code, e.msg.encode("ascii","ignore"))
        except Exception, e:
            self.error(u'Excepción',unicode(e))

    def on_btnPrevisualizar_mouseClick(self, event):
        try:
            j = 0
            for i, item in self.get_selected_items():
                j += 1
                archivo = self.generar_factura(item,  mostrar=(j==1))
        except Exception, e:
            print e
            self.error(u'Excepción', unicode(str(e), 'latin1', 'ignore'))

    def on_btnGenerar_mouseClick(self, event):
        for item in self.items:
            archivo = self.generar_factura(item)

    def on_btnEnviar_mouseClick(self, event):
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
            dialog.alertDialog(self, 'Proceso finalizado OK!\n\nEnviados: %d\nNo enviados: %d' % (ok, no), 'Envio de Email')
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
            fn = ''.join([str(it.get(ff,ff)) for ff in fs])
            fn = fn.decode('latin1').encode('ascii', 'replace').replace('?','_')
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
            print "Error al cargar datos desde el archivo: ",CONFIG_FILE
        else:
            print "No se encuentra el archivo: ",CONFIG_FILE
        sys.exit(1)
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSFE','CUIT')
    if config.has_option('WSFE','ENTRADA'):
        entrada = config.get('WSFE','ENTRADA')
    else:
        entrada = "" #"facturas-wsfev1.csv"
    if config.has_option('WSFE','SALIDA'):
        salida = config.get('WSFE','SALIDA')
    else:
        salida = "resultado.csv"
    
    if config.has_section('FACTURA'):
        conf_fact = dict(config.items('FACTURA'))
    else:
        conf_fact = {}
    
    conf_pdf = dict(config.items('PDF'))
    conf_mail = dict(config.items('MAIL'))
      
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

    if config.has_section('PROXY'):
        proxy_dict = dict(("proxy_%s" % k,v) for k,v in config.items('PROXY'))
        proxy_dict['proxy_port'] = int(proxy_dict['proxy_port'])
    else:
        proxy_dict = {}

    app = model.Application(PyRece)
    app.MainLoop()
