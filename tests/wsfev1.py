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

"Pruebas para WSFEv1 de AFIP (Factura Electrónica Mercado Interno sin detalle)"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"

import unittest
import os, time, sys
from decimal import Decimal
import datetime

sys.path.append("/home/reingart")        # TODO: proper packaging

from pyafipws.wsfev1 import WSFEv1
from pyafipws.wsaa import WSAA

WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
CUIT = 20267565393
CERT = "/home/reingart/pyafipws/reingart.crt"
PRIVATEKEY = "/home/reingart/pyafipws/reingart.key"
CACERT = "/home/reingart/pyafipws/afip_root_desa_ca.crt"
CACHE = "/home/reingart/pyafipws/cache"

# Autenticación:
wsaa = WSAA()
tra = wsaa.CreateTRA(service="wsfe")
cms = wsaa.SignTRA(tra, CERT, PRIVATEKEY)
wsaa.Conectar()
wsaa.LoginCMS(cms)


class TestFE(unittest.TestCase):

    def setUp(self):
        sys.argv.append("--trace")                  # TODO: use logging
        self.wsfev1 = wsfev1 = WSFEv1()
        wsfev1.Cuit = CUIT
        wsfev1.Token = wsaa.Token
        wsfev1.Sign = wsaa.Sign 
        wsfev1.Conectar(CACHE, WSDL)
    
    def atest_dummy(self):
        print wsfev1.client.help("dummy")
        wsfev1.Dummy()
        print "AppServerStatus", wsfev1.AppServerStatus
        print "DbServerStatus", wsfev1.DbServerStatus
        print "AuthServerStatus", wsfev1.AuthServerStatus
    
    def test_autorizar_comprobante(self, tipo_cbte=1, cbte_nro=None, servicios=True):
        "Prueba de autorización de un comprobante (obtención de CAE)"
        wsfev1 = self.wsfev1
        
        # datos generales del comprobante:
        punto_vta = 4000
        if not cbte_nro:
            # si no me especifícan nro de comprobante, busco el próximo
            cbte_nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)
            cbte_nro = long(cbte_nro) + 1
        fecha = datetime.datetime.now().strftime("%Y%m%d")
        tipo_doc = 80; nro_doc = "30000000007" ##"30500010912" # CUIT BNA
        cbt_desde = cbte_nro; cbt_hasta = cbt_desde
        imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
        imp_trib = "1.00"; imp_op_ex = "0.00"; imp_iva = "21.00"
        fecha_cbte = fecha
        # Fechas del período del servicio facturado (solo si concepto = 1?)
        if servicios:
            concepto = 3
            fecha_venc_pago = fecha
            fecha_serv_desde = fecha; fecha_serv_hasta = fecha
        else:
            concepto = 1
            fecha_venc_pago = fecha_serv_desde = fecha_serv_hasta = None
        moneda_id = 'PES'; moneda_ctz = '1.000'
        obs = "Observaciones Comerciales, libre"

        wsfev1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde, fecha_serv_hasta, #--
            moneda_id, moneda_ctz)
        
        # agrego un comprobante asociado (solo notas de crédito / débito)
        if tipo_cbte in (2, 3):
            tipo = 1
            pv = 2
            nro = 1234
            wsfev1.AgregarCmpAsoc(tipo, pv, nro)
        
        # agrego otros tributos:
        tributo_id = 99
        desc = 'Impuesto Municipal Matanza'
        base_imp = "100.00"
        alic = "1.00"
        importe = "1.00"
        wsfev1.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

        # agrego el subtotal por tasa de IVA:
        iva_id = 5 # 21%
        base_im = 100
        importe = 21
        wsfev1.AgregarIva(iva_id, base_imp, importe)
        
        # llamo al websevice para obtener el CAE:
        wsfev1.CAESolicitar()
        
        self.assertEqual(wsfev1.Resultado, "A")    # Aprobado!
        self.assertIsInstance(wsfev1.CAE, basestring)
        self.assertEqual(len(wsfev1.CAE), len("63363178822329")) 
        self.assertEqual(len(wsfev1.Vencimiento), len("20130907")) 
        wsfev1.AnalizarXml("XmlResponse")
        # observación "... no se encuentra registrado en los padrones de AFIP.":
        self.assertEqual(wsfev1.ObtenerTagXml('Obs', 0, 'Code'), '10017')
        

    def test_consulta(self):
        "Prueba de obtener los datos de un comprobante autorizado"
        wsfev1 = self.wsfev1        
        # autorizo un comprobante:
        tipo_cbte = 1
        self.test_autorizar_comprobante(tipo_cbte)
        # obtengo datos para comprobar
        cae = wsfev1.CAE
        wsfev1.AnalizarXml("XmlRequest")
        imp_total = float(wsfev1.ObtenerTagXml('ImpTotal'))
        concepto = int(wsfev1.ObtenerTagXml('Concepto'))
        punto_vta = wsfev1.PuntoVenta
        cbte_nro = wsfev1.CbteNro
        
        # llamo al webservice para consultar y validar manualmente el CAE:        
        wsfev1.CompConsultar(tipo_cbte, punto_vta, cbte_nro)
        
        self.assertEqual(wsfev1.CAE, cae) 
        self.assertEqual(wsfev1.CbteNro, cbte_nro) 
        self.assertEqual(wsfev1.ImpTotal, imp_total)

        wsfev1.AnalizarXml("XmlResponse")
        self.assertEqual(wsfev1.ObtenerTagXml('CodAutorizacion'), str(wsfev1.CAE))
        self.assertEqual(wsfev1.ObtenerTagXml('Concepto'), str(concepto))


    def test_reproceso_servicios(self):
        "Prueba de reproceso de un comprobante (recupero de CAE por consulta)"
        wsfev1 = self.wsfev1
        # obtengo el próximo número de comprobante
        tipo_cbte = 1
        punto_vta = 4000
        nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)
        cbte_nro = long(nro) + 1
        # obtengo CAE
        wsfev1.Reprocesar = True
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro)
        self.assertEqual(wsfev1.Reproceso, "")
        # intento reprocesar:
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro)
        self.assertEqual(wsfev1.Reproceso, "S")

    def test_reproceso_productos(self):
        "Prueba de reproceso de un comprobante (recupero de CAE por consulta)"
        wsfev1 = self.wsfev1
        # obtengo el próximo número de comprobante
        tipo_cbte = 1
        punto_vta = 4000
        nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)
        cbte_nro = long(nro) + 1
        # obtengo CAE
        wsfev1.Reprocesar = True
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsfev1.Reproceso, "")
        # intento reprocesar:
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsfev1.Reproceso, "S")

    def test_reproceso_nota_debito(self):
        "Prueba de reproceso de un comprobante (recupero de CAE por consulta)"
        # N/D con comprobantes asociados
        wsfev1 = self.wsfev1
        # obtengo el próximo número de comprobante
        tipo_cbte = 2
        punto_vta = 4000
        nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)
        cbte_nro = long(nro) + 1
        # obtengo CAE
        wsfev1.Reprocesar = True
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsfev1.Reproceso, "")
        # intento reprocesar:
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsfev1.Reproceso, "S")
        
        
if __name__ == '__main__':
    unittest.main()

