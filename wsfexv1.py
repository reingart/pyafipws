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

"""Módulo para obtener código de autorización de impresión o 
electrónico del web service WSFEXv1 de AFIP (Factura Electrónica Exportación V1)
"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "0.01a"

import sys
import traceback

HOMO = True


class WSFEXv1:
    "Interfaz para el WebService de Factura Electrónica Exportación Versión 1"
    _public_methods_ = ['CrearFactura', 'AgregarItem', 'Authorize', 'GetCMP',
                        'AgregarPermiso', 'AgregarCmpAsoc',
                        'GetParamMon', 'GetParamTipoCbte', 'GetParamTipoExpo', 
                        'GetParamIdiomas', 'GetParamUMed', 'GetParamIncoterms', 
                        'GetParamDstPais','GetParamDstCUIT',
                        'GetParamCtz',
                        'Dummy', 'Conectar', 'GetLastCMP', 'GetLastID' ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Obs', 'Reproceso',
        'CAE','Vencimiento', 'Eventos', 'ErrCode', 'ErrMsg',
        'Excepcion', 'LanzarExcepciones', 'Traceback',
        'CbteNro', 'FechaCbte', 'ImpTotal']
        
    _reg_progid_ = "WSFEXv1"
    _reg_clsid_ = "{CE73DA43-86F4-413E-99CD-6468CBFF20B4}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.factura = None
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.ErrCode = self.ErrMsg = None
        self.LanzarExcepciones = True
        self.Traceback = self.Excepcion = ""

    def Conectar(self, cache="", url="", proxy="", httplib="", cacert=""):
        "Establecer la conexión a los servidores de la AFIP"
        return True
        
    def CrearFactura(self, tipo_cbte=19, punto_vta=1, cbte_nro=0, fecha_cbte=None,
            imp_total=0.0, tipo_expo=1, permiso_existente="N", dst_cmp=None,
            cliente="", cuit_pais_cliente="", domicilio_cliente="",
            id_impositivo="", moneda_id="PES", moneda_ctz=1.0,
            obs_comerciales="", obs="", forma_pago="", incoterms="", incoterms_ds="",
            idioma_cbte=7):
        "Creo un objeto factura (interna)"
        return True
    
    def AgregarItem(self, codigo, ds, qty, umed, precio, bonificacion, imp_total):
        "Agrego un item a una factura (interna)"
        # Nota: no se calcula total (debe venir calculado!)
        return True
       
    def AgregarPermiso(self, id_permiso, dst_merc):
        "Agrego un permiso a una factura (interna)"
        return True

    def AgregarCmpAsoc(self, cbte_tipo=19, cbte_punto_vta=0, cbte_nro=0, cbte_cuit=None):
        "Agrego un comprobante asociado a una factura (interna)"
        return True

    def Authorize(self, id):
        "Autoriza la factura cargada en memoria"
        try:
            # Resultado: A: Aceptado, R: Rechazado
            self.Resultado = auth['resultado']
            # Obs:
            self.Obs = auth['obs'].strip(" ")
            self.Reproceso = auth['reproceso']
            self.CAE = auth['cae']
            self.CbteNro  = auth['cbte_nro']
            vto = str(auth['fch_venc_cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]
            return self.CAE
        except wsfex.FEXError, e:
            self.ErrCode = unicode(e.code)
            self.ErrMsg = unicode(e.msg)
            if self.LanzarExcepciones:
                raise COMException(scode = vbObjectError + int(e.code),
                                   desc=unicode(e.msg), source="WebService")
        except SoapFault,e:
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            if self.LanzarExcepciones:
                raiseSoapError(e)
        except Exception, e:
            if self.LanzarExcepciones:
                raisePythonException(e)
            else:
                ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
                self.Traceback = ''.join(ex)
                try:
                    self.Excepcion = u"%s" % (e)
                except:
                    pass

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])
        return True

    def GetCMP(self, tipo_cbte, punto_vta, cbte_nro):
        "Recuperar los datos completos de un comprobante ya autorizado"
        try:
            # Obs, cae y fecha cae
            self.Obs = cbt['obs'].strip(" ")
            self.CAE = cbt['cae']
            vto = str(cbt['fch_venc_cae'])
            self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]
            return self.CAE
        except wsfex.FEXError, e:
            self.ErrCode = unicode(e.code)
            self.ErrMsg = unicode(e.msg)
        finally:
            # guardo datos de depuración
            self.XmlRequest = self.client.xml_request
            self.XmlResponse = self.client.xml_response
    
    def GetLastCMP(self, tipo_cbte, punto_vta):
        "Recuperar último número de comprobante emitido"
        return cbte_nro
            
    def GetLastID(self):
        "Recuperar último número de transacción (ID)"
        return id

if __name__ == "__main__":
    # Crear objeto interface Web Service de Factura Electrónica de Exportación
    wsfexv1 = WSFEXv1()
    # Setear token y sing de autorización (pasos previos)
    ##wsfexv1.Token = wsaa.Token
    ##wsfexv1.Sign = wsaa.Sign

    # CUIT del emisor (debe estar registrado en la AFIP)
    wsfexv1.Cuit = "20267565393"

    # Conectar al Servicio Web de Facturación (homologación)
    ok = wsfexv1.Conectar("","http://wswhomo.afip.gov.ar/WSFEXv1/service.asmx")

    if "--prueba" in sys.argv:
        try:
            # Establezco los valores de la factura a autorizar:
            tipo_cbte = 19 # FC Expo (ver tabla de parámetros)
            punto_vta = 7
            # Obtengo el último número de comprobante y le agrego 1
            cbte_nro = int(wsfexv1.GetLastCMP(tipo_cbte, punto_vta)) + 1
            fecha = datetime.datetime.now().strftime("%Y%m%d")
            tipo_expo = 1 # tipo de exportación (ver tabla de parámetros)
            permiso_existente = "N"
            dst_cmp = 203 # país destino
            cliente = "Joao Da Silva"
            cuit_pais_cliente = "50000000016"
            domicilio_cliente = "Rua 76 km 34.5 Alagoas"
            id_impositivo = "PJ54482221-l"
            moneda_id = "012" # para reales, "DOL" o "PES" (ver tabla de parámetros)
            moneda_ctz = 0.5
            obs_comerciales = "Observaciones comerciales"
            obs = "Sin observaciones"
            forma_pago = "30 dias"
            incoterms = "FOB" # (ver tabla de parámetros)
            incoterms_ds = "Flete a Bordo" 
            idioma_cbte = 1 # (ver tabla de parámetros)
            imp_total = "250.00"
            
            # Creo una factura (internamente, no se llama al WebService):
            ok = wsfexv1.CrearFactura(tipo_cbte, punto_vta, cbte_nro, fecha_cbte, 
                    imp_total, tipo_expo, permiso_existente, dst_cmp, 
                    cliente, cuit_pais_cliente, domicilio_cliente, 
                    id_impositivo, moneda_id, moneda_ctz, 
                    obs_comerciales, obs, forma_pago, incoterms, incoterms_ds,
                    idioma_cbte)
            
            
            # Agrego un item:
            codigo = "PRO1"
            ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
            qty = 2
            precio = "150.00"
            umed = 1 # Ver tabla de parámetros (unidades de medida)
            bonif = "50.00"
            imp_total = "250.00" # importe total final del artículo
            # lo agrego a la factura (internamente, no se llama al WebService):
            ok = wsfexv1.AgregarItem(codigo, ds, qty, umed, precio, bonif, imp_total)

            # Agrego un permiso (ver manual para el desarrollador)
            id = "99999AAXX999999A"
            dst = 225 # país destino de la mercaderia
            ok = wsfexv1.AgregarPermiso(id, dst)

            # Agrego un comprobante asociado (solo para N/C o N/D)
            if tipo_cbte in (20,21): 
                cbteasoc_tipo = 19
                cbteasoc_pto_vta = 2
                cbteasoc_nro = 1234
                cbteasoc_cuit = 20111111111
                wsfexv1.AgregarCmpAsoc(cbteasoc_tipo, cbteasoc_pto_vta, cbteasoc_nro, cbteasoc_cuit)
                
            ##id = "99000000000100" # número propio de transacción
            # obtengo el último ID y le adiciono 1 
            # (advertencia: evitar overflow y almacenar!)
            id = int(wsfexv1.GetLastID()) + 1

            # Llamo al WebService de Autorización para obtener el CAE
            cae = wsfev1.Authorize(id)

            print "Resultado", wsfexv1.Resultado
            print "CAE", wsfexv1.CAE
            print "Vencimiento", wsfexv1.Vencimiento
                        
            wsfexv1.GetCMP(tipo_cbte, punto_vta, cbte_nro)
            print "CAE consulta", wsfexv1.CAE, wsfexv1.CAE==cae 
            print "NRO consulta", wsfexv1.CbteNro, wsfexv1.CbteNro==cbte_nro 
            print "TOTAL consulta", wsfexv1.ImpTotal, wsfexv1.ImpTotal==imp_total

        except:
            print wsfexv1.XmlRequest        
            print wsfexv1.XmlResponse        
            print wsfexv1.ErrCode
            print wsfexv1.ErrMsg
            print wsfexv1.Excepcion
            print wsfexv1.Traceback


            
