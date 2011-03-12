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
__version__ = "1.21b"

import csv
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

from PyFPDF.ejemplos.form import Form

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
        dialog.alertDialog(self, text, u'Acerca de PyRece')

    def on_menuAyudaInstructivo_select(self, event):
        text = INSTRUCTIVO
        dialog.alertDialog(self, text, u'Instructivo de PyRece')

    def on_menuAyudaLimpiar_select(self, event):
        self.components.txtEstado.text = ""

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
            ws.Conectar("", wsdl=wsaa_url+"?wsdl", proxy=proxy_dict)
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
    
    def on_btnExaminar_mouseClick(self, event):
        filename = entrada
        wildcard = ["Archivos CSV (*.csv)|*.csv", "Archivos XML (*.xml)|*.xml"]
        if entrada.endswith("xml"):
            wildcard.sort(reverse=True)

        result = dialog.fileDialog(self, 'Abrir', '', filename, '|'.join(wildcard))
        if not result.accepted:
            return
        self.paths = result.paths

    def on_btnCargar_mouseClick(self, event):
        self.cargar()
        
    def cargar(self):
        try:
            items = []
            for fn in self.paths:
                if fn.endswith(".csv"):
                    csvfile = open(fn, "rb")
                    # deducir dialecto y delimitador
                    dialect = csv.Sniffer().sniff(csvfile.read(256), delimiters=[';',','])
                    csvfile.seek(0)
                    csv_reader = csv.reader(csvfile, dialect)
                    for row in csv_reader:
                        r = []
                        for c in row:
                            if isinstance(c, basestring):
                                c=c.strip()
                            r.append(c)
                        items.append(r)
                elif fn.endswith(".xml"):
                    import formato_xml
                    regs = formato_xml.leer(fn)
                    items.extend(formato_xml.aplanar(regs))
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

    def on_btnGrabar_mouseClick(self, event):
            filename = entrada
            wildcard = ["Archivos CSV (*.csv)|*.csv", "Archivos XML (*.xml)|*.xml"]
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
                f = open(fn,"wb")
                csv_writer = csv.writer(f, dialect='excel', delimiter=";")
                csv_writer.writerows([self.cols])
                csv_writer.writerows([[item[k] for k in self.cols] for item in self.items])
                f.close()
            else:
                import formato_xml
                regs = formato_xml.desaplanar([self.cols] + [[item[k] for k in self.cols] for item in self.items])
                formato_xml.escribir(regs, fn)                
            dialog.alertDialog(self, u'Se guardó con éxito el archivo:\n%s' % (unicode(fn),), 'Guardar')
        except Exception, e:
            self.error(u'Excepción',unicode(e))

    def on_btnAutorizar_mouseClick(self, event):
        self.verifica_ws()
        try:
            ok = procesadas = rechazadas = 0
            cols = self.cols
            items = []
            self.progreso(0)
            selected = []
            for i, kargs in self.get_selected_items():
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
                self.items[i] = kargs
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
        if not self.items: return
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
                archivo = self.generar_factura(item)
            if j != 1:
                pass # no abrir más de 1 factura
            elif sys.platform.startswith("linux"):
                os.system("evince %s" % archivo)
            else:
                os.system(archivo)
        except Exception, e:
            print e
            self.error(u'Excepción', unicode(e))

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
                    self.enviar_mail(item,archivo)
                    ok += 1
                else:
                    self.log("No se envia factura %s por no tener CAE" % item['cbt_numero'])
                    no += 1
                self.progreso(i)
            self.progreso(len(self.items))
            dialog.alertDialog(self, 'Proceso finalizado OK!\n\nEnviados: %d\nNo enviados: %d' % (ok, no), 'Envio de Email')
        except Exception, e:
            self.error(u'Excepción',unicode(e))
            
    def generar_factura(self, item):
        def fmtdate(d):
            if d is not None and str(d):
                d = str(d)
                return "%s/%s/%s" % (d[6:8], d[4:6], d[0:4]) or ''
            else:
                return ''
        def fmtimp (i):
            if i is not None and str(i):
                return ("%0.2f" % Decimal(str(i).replace(",","."))).replace(".",",")
            else:
                return ''
        def fmtcuit(c):
            if c is not None and str(c):
                c=str(c)
                return len(str(c))==11 and "%s-%s-%s" % (c[0:2], c[2:10], c[10:]) or ''
            return ''

        monedas_ds = {'DOL': u'USD: Dólar', 'PES': u'ARS: Pesos', '010': u'MXN: Pesos Mejicanos', '011': u'UYU: Pesos Uruguayos', '012': u'BRL: Real', '014': u'Coronas Danesas', '015': u'Coronas Noruegas', '016': u'Coronas Suecas', '019': u'JPY: Yens', '018': u'CAD: D\xf3lar Canadiense', '033': u'CLP: Peso Chileno', '056': u'Forint (Hungr\xeda)', '031': u'BOV: Peso Boliviano', '036': u'Sucre Ecuatoriano', '051': u'D\xf3lar de Hong Kong', '034': u'Rand Sudafricano', '053': u'D\xf3lar de Jamaica', '057': u'Baht (Tailandia)', '043': u'Balboas Paname\xf1as', '042': u'Peso Dominicano', '052': u'D\xf3lar de Singapur', '032': u'Peso Colombiano', '035': u'Nuevo Sol Peruano', '061': u'Zloty Polaco', '060': u'EUR: Euro', '063': u'Lempira Hondure\xf1a', '062': u'Rupia Hind\xfa', '064': u'Yuan (Rep. Pop. China)', '009': u'Franco Suizo', '025': u'Dinar Yugoslavo', '002': u'USD: D\xf3lar Libre EEUU', '027': u'Dracma Griego', '026': u'D\xf3lar Australiano', '007': u'Florines Holandeses', '023': u'VEB: Bol\xedvar Venezolano', '047': u'Riyal Saudita', '046': u'Libra Egipcia', '045': u'Dirham Marroqu\xed', '044': u'C\xf3rdoba Nicarag\xfcense', '029': u'G\xfcaran\xed', '028': u'Flor\xedn (Antillas Holandesas)', '054': u'D\xf3lar de Taiwan', '040': u'Lei Rumano', '024': u'Corona Checa', '030': u'Shekel (Israel)', '021': u'Libra Esterlina', '055': u'Quetzal Guatemalteco', '059': u'Dinar Kuwaiti'}

        f = Form(conf_fact.get('formato','factura.csv'), 
                 format=conf_fact.get("papel", 'A4'), 
                 orientation=conf_fact.get("orientacion", 'portrait'), )
        f.add_page()

        # establezco campos desde planilla
        for k,v in item.items():
            f.set(k,v)

        # establezco campos desde configuración
        for k,v in conf_pdf.items():
            f.set(k,v)

        numero = "%04d-%08d" % (int(item['punto_vta']), int(item['cbt_numero']))
        f.set('Numero', numero)
        f.set('Fecha', fmtdate(item['fecha_cbte']))
        f.set('Vencimiento', fmtdate(item['fecha_venc_pago']))
        
        if int(item['tipo_cbte']) in (1, 2, 3, 4, 5, 39, 60, 63):
            letra = "A"
        elif int(item['tipo_cbte']) in (6, 7, 8):
            letra = "B"
        elif int(item['tipo_cbte']) in (19, 20, 21):
            letra = "E"
        else:
            letra = "X"
            
        f.set('LETRA', letra)
        f.set('TipoCBTE', "COD.%02d" % int(item['tipo_cbte']))

        tipos = { (1, 6, 19): 'Factura', (2, 7, 20): 'Nota de Débito', 
            (3, 8, 21): 'Nota de Crédito',
            (4, 9): 'Recibo', (10,): 'Notas de Venta al contado', 
            (60, 61): 'Cuenta de Venta y Líquido producto',
            (63, 64): 'Liquidación',
            (39, 40): '???? (R.G. N° 3419)'}

        tipo = ""
        for k,v in tipos.items():
            if int(int(item['tipo_cbte'])) in k:
                tipo = v
        f.set('Comprobante.L', tipo)

        f.set('Periodo.Desde', fmtdate(item['fecha_serv_desde']))
        f.set('Periodo.Hasta', fmtdate(item['fecha_serv_hasta']))
        
        f.set('Cliente.Nombre', item['nombre'])
        f.set('Cliente.Domicilio', item['domicilio'])
        f.set('Cliente.Localidad', item['localidad'] or '')
        if 'provincia' in item:
            f.set('Cliente.Provincia', item['provincia'])
        f.set('Cliente.Telefono', item['telefono'])
        f.set('Cliente.IVA', item['categoria'])
        f.set('Cliente.CUIT', fmtcuit(item['nro_doc']))
        if 'cliente.observaciones' in item:
            f.set('Cliente.Observaciones', item['cliente.observaciones'])

        if item['moneda_id']:
            f.set('moneda_id', '')
            f.set('moneda_ds', monedas_ds.get(item['moneda_id'],''))
            if item['moneda_id']=='PES':
                for k in 'moneda_ctz.L', 'moneda_ctz':
                    f.set(k, '')
        else:
            for k in 'moneda.L', 'moneda_id', 'moneda_ds', 'moneda_ctz.L', 'moneda_ctz':
                f.set(k, '')

        if letra!='E':
            for k in 'incoterms.L', 'incoterms', 'incoterms_ds':
                f.set(k, '')

        li = 1
        for i in range(25):
            if 'codigo%d' % i in item:
                f.set('Item.Codigo%02d' % i, item['codigo%d' % i])
            if 'cantidad%d' % i in item:
                f.set('Item.Cantidad%02d' % i, item['cantidad%d' % i])
            if 'numero_despacho%d' % i in item:
                f.set('Item.Numero_Despacho%02d' % i, item['numero_despacho%d' % i])
            if 'descripcion%d' % i in item:
                f.set('Item.Descripcion%02d' % i, item['descripcion%d' % i])
            if 'importe%d' % i in item:
                f.set('Item.Importe%02d' % i, fmtimp(item['importe%d' % i]))
            if 'precio%d' % i in item:
                f.set('Item.Precio%02d' % i, fmtimp(item['precio%d' % i]))

        #if li and letra=='A':
        #    f.set('Item.Importe%02d' % li, fmtimp(item['imp_neto']))
        #elif li and letra=='B':
        #    f.set('Item.Importe%02d' % li, fmtimp(item['imp_total']))

        if 'observaciones' in item:
            f.set('Observaciones', item['observaciones'])
        
        if letra=='A':
            f.set('NETO', fmtimp(item['imp_neto']))
            f.set('IVALIQ', fmtimp(item.get('impto_liq', item.get('imp_iva'))))
            f.set('LeyendaIVA',"")
            
            for n in range(1,5):
                if 'iva_id_%s' % n in item:
                    a = {3: '0', 4: '10.5', 5: '21', 6: '27'}[item['iva_id_%s' % n]]
                    f.set('IVA%s' % a, fmtimp(item.get('iva_importe_%s' % n, 0)))
        else:
            f.set('NETO.L',"")
            f.set('IVA.L',"")
            f.set('IVA21.L',"")
            f.set('IVA10.5.L',"")
            f.set('IVA27.L',"")

        f.set('TOTAL', fmtimp(item['imp_total']))

        f.set('CAE', item['cae'])
        f.set('CAE.Vencimiento', fmtdate(item['fecha_vto']))
        if item['cae']!="NULL":
            barras = '%11s%02d%04d%s%8s' % (cuit, int(item['tipo_cbte']), int(item['punto_vta']),item['cae'], item['fecha_vto'])
            digito = digito_verificador_modulo10(barras)
            if digito:
                barras = barras + digito_verificador_modulo10(barras)
            else:
                barras = ''
        else:
            barras = ""

        f.set('CodigoBarras', barras)
        f.set('CodigoBarrasLegible', barras)

        d = os.path.join(conf_fact.get('directorio', "."), item['fecha_cbte'])
        if not os.path.isdir(d):
            os.mkdir(d)
        fs = conf_fact.get('archivo','numero').split(",")
        it = item.copy()
        it['tipo'] = tipo
        it['letra'] = letra
        it['numero'] = numero
        it['mes'] = item['fecha_cbte'][4:6]
        it['año'] = item['fecha_cbte'][0:4]
        fn = ''.join([str(it.get(ff,ff)) for ff in fs])
        archivo = os.path.join(d, "%s.pdf" % fn)
        f.render(archivo)
        return archivo
    
    def enviar_mail(self, item, archivo):
        archivo = self.generar_factura(item)
        if item['email']:
            msg = MIMEMultipart()
            msg['Subject'] = conf_mail['motivo'].replace("NUMERO",item['cbt_numero'])
            msg['From'] = conf_mail['remitente']
            msg['Reply-to'] = msg['From']
            msg['To'] = item['email']
            msg.preamble = 'Mensaje de multiples partes.\n'
            
            part = MIMEText(conf_mail['cuerpo'])
            msg.attach(part)
            
            part = MIMEApplication(open(archivo,"rb").read())
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(archivo))
            msg.attach(part)

            try:
                self.log("Enviando email: %s a %s" % (msg['Subject'], msg['To']))
                if not self.smtp:
                    self.smtp = SMTP(conf_mail['servidor'])
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
