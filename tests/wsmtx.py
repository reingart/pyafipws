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

"Pruebas para WSMTX de AFIP (Factura Electrónica Mercado Interno con detalle)"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"

import unittest
import os, time, sys
from decimal import Decimal
import datetime

sys.path.append("/home/reingart")        # TODO: proper packaging

from pyafipws.wsmtx import WSMTXCA
from pyafipws.wsaa import WSAA

WSDL="https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"
CUIT = 20267565393
CERT = "/home/reingart/pyafipws/reingart.crt"
PRIVATEKEY = "/home/reingart/pyafipws/reingart.key"
CACERT = "/home/reingart/pyafipws/afip_root_desa_ca.crt"
CACHE = "/home/reingart/pyafipws/cache"

# Autenticación:
wsaa = WSAA()
tra = wsaa.CreateTRA(service="wsmtxca")
cms = wsaa.SignTRA(tra, CERT, PRIVATEKEY)
wsaa.Conectar()
wsaa.LoginCMS(cms)


class TestMTX(unittest.TestCase):

    def setUp(self):
        sys.argv.append("--trace")                  # TODO: use logging
        self.wsmtxca = wsmtxca = WSMTXCA()
        wsmtxca.Cuit = CUIT
        wsmtxca.Token = wsaa.Token
        wsmtxca.Sign = wsaa.Sign 
        wsmtxca.Conectar(CACHE, WSDL)
    
    def atest_dummy(self):
        print wsmtxca.client.help("dummy")
        wsmtxca.Dummy()
        print "AppServerStatus", wsmtxca.AppServerStatus
        print "DbServerStatus", wsmtxca.DbServerStatus
        print "AuthServerStatus", wsmtxca.AuthServerStatus
    
    def test_autorizar_comprobante(self, tipo_cbte=1, cbte_nro=None, servicios=True, tributos=True):
        "Prueba de autorización de un comprobante (obtención de CAE)"
        wsmtxca = self.wsmtxca
        
        # datos generales del comprobante:
        punto_vta = 4000
        if not cbte_nro:
            # si no me especifícan nro de comprobante, busco el próximo
            cbte_nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            cbte_nro = long(cbte_nro) + 1
        fecha = datetime.datetime.now().strftime("%Y-%m-%d")
        tipo_doc = 80; nro_doc = "30000000007"
        cbt_desde = cbte_nro; cbt_hasta = cbt_desde
        imp_tot_conc = "0.00" 
        imp_neto = "100.00"
        if tributos:
            imp_total = "123.00"
            imp_trib = "2.00"
        else:
            imp_total = "121.00"
            imp_trib = "0.00"        
        imp_op_ex = "0.00"; 
        imp_subtotal = "100.00"
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

        wsmtxca.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde, fecha_serv_hasta, #--
            moneda_id, moneda_ctz, obs)
        
        # agrego un comprobante asociado (solo notas de crédito / débito)
        if tipo_cbte in (2, 3):
            tipo = 1
            pv = 2
            nro = 1234
            wsmtxca.AgregarCmpAsoc(tipo, pv, nro)
        
        if tributos:
            # agrego otros tributos:
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            wsmtxca.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            # agrego otros tributos:
            tributo_id = 1
            desc = 'Impuestos Internos'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            wsmtxca.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

        # agrego el subtotal por tasa de IVA:
        iva_id = 5 # 21%
        base_imp = "100.00"
        importe = 21
        wsmtxca.AgregarIva(iva_id, base_imp, importe)
        
        # agrego un artículo:
        u_mtx = 123456
        cod_mtx = 1234567890123
        codigo = "P0001"
        ds = "Descripcion del producto P0001"
        qty = 2.00
        umed = 7
        precio = 100.00
        bonif = 0.00
        iva_id = 5
        imp_iva = 42.00
        imp_subtotal = 242.00
        wsmtxca.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif, 
                    iva_id, imp_iva, imp_subtotal)
        
        # agrego bonificación general
        wsmtxca.AgregarItem(None, None, None, 'bonificacion', 0, 99, 1, None, 
                    5, -21, -121)
        
        # llamo al websevice para obtener el CAE:
        wsmtxca.AutorizarComprobante()
        
        self.assertEqual(wsmtxca.Resultado, "A")    # Aprobado!
        self.assertIsInstance(wsmtxca.CAE, basestring)
        self.assertEqual(len(wsmtxca.CAE), len("63363178822329")) 
        self.assertEqual(len(wsmtxca.Vencimiento), len("2013-09-07")) 
        
        cae = wsmtxca.CAE

        # llamo al webservice para consultar y validar manualmente el CAE:        
        wsmtxca.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)
        
        self.assertEqual(wsmtxca.CAE, cae) 
        self.assertEqual(wsmtxca.CbteNro, cbte_nro) 
        self.assertEqual(wsmtxca.ImpTotal, imp_total)

        wsmtxca.AnalizarXml("XmlResponse")
        self.assertEqual(wsmtxca.ObtenerTagXml('codigoAutorizacion'), str(wsmtxca.CAE))
        self.assertEqual(wsmtxca.ObtenerTagXml('codigoConcepto'), str(concepto))
        self.assertEqual(wsmtxca.ObtenerTagXml('arrayItems', 0, 'item', 'unidadesMtx'), '123456')


    def test_reproceso_servicios(self):
        "Prueba de reproceso de un comprobante (recupero de CAE por consulta)"
        wsmtxca = self.wsmtxca
        # obtengo el próximo número de comprobante
        tipo_cbte = 1
        punto_vta = 4000
        nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
        cbte_nro = long(nro) + 1
        # obtengo CAE
        wsmtxca.Reprocesar = True
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro)
        self.assertEqual(wsmtxca.Reproceso, "")
        # intento reprocesar:
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro)
        self.assertEqual(wsmtxca.Reproceso, "S")

    def test_reproceso_productos(self):
        "Prueba de reproceso de un comprobante (recupero de CAE por consulta)"
        wsmtxca = self.wsmtxca
        # obtengo el próximo número de comprobante
        tipo_cbte = 1
        punto_vta = 4000
        nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
        cbte_nro = long(nro) + 1
        # obtengo CAE
        wsmtxca.Reprocesar = True
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsmtxca.Reproceso, "")
        # intento reprocesar:
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsmtxca.Reproceso, "S")

    def test_reproceso_nota_debito(self):
        "Prueba de reproceso de un comprobante (recupero de CAE por consulta)"
        # N/D con comprobantes asociados
        wsmtxca = self.wsmtxca
        # obtengo el próximo número de comprobante
        tipo_cbte = 2
        punto_vta = 4000
        nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
        cbte_nro = long(nro) + 1
        # obtengo CAE
        wsmtxca.Reprocesar = True
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsmtxca.Reproceso, "")
        # intento reprocesar:
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, servicios=False)
        self.assertEqual(wsmtxca.Reproceso, "S")

    def test_reproceso_sin_tributos(self):
        "Prueba de reproceso de un comprobante (recupero de CAE por consulta)"
        wsmtxca = self.wsmtxca
        # obtengo el próximo número de comprobante
        tipo_cbte = 1
        punto_vta = 4000
        nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
        cbte_nro = long(nro) + 1
        # obtengo CAE (sin tributos)
        wsmtxca.Reprocesar = True
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, tributos=False)
        self.assertEqual(wsmtxca.Reproceso, "")
        # intento reprocesar:
        self.test_autorizar_comprobante(tipo_cbte, cbte_nro, tributos=False)
        self.assertEqual(wsmtxca.Reproceso, "S")

        
        
if __name__ == '__main__':
    unittest.main()

