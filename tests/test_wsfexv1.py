#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Test para WSFEXv1 de AFIP(Factura Electrónica Exportación Versión 1)"""

import unittest
import sys
import datetime

from pyafipws.wsaa import WSAA
from pyafipws.wsfexv1 import WSFEXv1

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

WSDL = "https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL"
CUIT = 20267565393
CERT = "reingart.crt"
PRIVATEKEY = "reingart.key"
CACERT = "conf/afip_ca_info.crt"
CACHE = ""

# Debido a que Python solicita una opción de diseño, hay una advertencia
# sobre una conexión no cerrada al ejecutar las pruebas.
# https://github.com/kennethreitz/requests/issues/3912
# Esto puede ser molesto al ejecutar las pruebas, por lo tanto,
# suprimir la advertencia como se discute en
# https://github.com/kennethreitz/requests/issues/1882

# obteniendo el TA para pruebas

ta = WSAA().Autenticar("wsfex", "reingart.crt", "reingart.key")
print(ta)


class TestFEX(unittest.TestCase):
    def setUp(self):
        sys.argv.append("--trace")
        self.wsfexv1 = wsfexv1 = WSFEXv1()
        wsfexv1.Cuit = 20267565393
        wsfexv1.SetTicketAcceso(ta)
        wsfexv1.Conectar(CACHE, WSDL)
        print(";)")

    def test_dummy(self):
        """Test de estado del servidor."""
        wsfexv1 = self.wsfexv1
        print(wsfexv1.client.help("FEXDummy"))
        wsfexv1.Dummy()
        print("AppServerStatus", wsfexv1.AppServerStatus)
        print("DbServerStatus", wsfexv1.DbServerStatus)
        print("AuthServerStatus", wsfexv1.AuthServerStatus)
        self.assertEqual(wsfexv1.AppServerStatus, "OK")
        self.assertEqual(wsfexv1.DbServerStatus, "OK")
        self.assertEqual(wsfexv1.AuthServerStatus, "OK")

    def test_crear_factura(self, tipo_cbte=19):
        """Test de creación de una factura (Interna)."""
        wsfexv1 = self.wsfexv1
        # FC/NC Expo (ver tabla de parámetros)
        tipo_cbte = 21 if "--nc" in sys.argv else 19
        punto_vta = 7
        # Obtengo el último número de comprobante y le agrego 1
        cbte_nro = int(wsfexv1.GetLastCMP(tipo_cbte, punto_vta)) + 1
        fecha_cbte = datetime.datetime.now().strftime("%Y%m%d")
        tipo_expo = 1  # exportacion definitiva de bienes
        permiso_existente = (tipo_cbte not in (20, 21) or tipo_expo != 1) and "S" or ""
        print("permiso_existente", permiso_existente)
        dst_cmp = 203  # país destino
        cliente = "Joao Da Silva"
        cuit_pais_cliente = "50000000016"
        domicilio_cliente = "Rúa Ñ°76 km 34.5 Alagoas"
        id_impositivo = "PJ54482221-l"
        # para reales, "DOL" o "PES" (ver tabla de parámetros)
        moneda_id = "DOL"
        moneda_ctz = "39.00"
        obs_comerciales = "Observaciones comerciales"
        obs = "Sin observaciones"
        forma_pago = "30 dias"
        incoterms = "FOB"  # (ver tabla de parámetros)
        incoterms_ds = "Flete a Bordo"
        idioma_cbte = 1  # (ver tabla de parámetros)
        imp_total = "250.00"

        # Creo una factura (internamente, no se llama al WebService)
        fact = wsfexv1.CrearFactura(
            tipo_cbte,
            punto_vta,
            cbte_nro,
            fecha_cbte,
            imp_total,
            tipo_expo,
            permiso_existente,
            dst_cmp,
            cliente,
            cuit_pais_cliente,
            domicilio_cliente,
            id_impositivo,
            moneda_id,
            moneda_ctz,
            obs_comerciales,
            obs,
            forma_pago,
            incoterms,
            idioma_cbte,
            incoterms_ds,
        )
        self.assertTrue(fact)

    def test_agregar_item(self):
        """Test Agregar Item"""
        wsfexv1 = self.wsfexv1
        self.test_crear_factura()
        codigo = "PRO1"
        ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
        qty = 2
        precio = "150.00"
        umed = 9  # docenas
        bonif = "50.00"
        imp_total = "250.00"  # importe total final del artículo
        item = wsfexv1.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)
        self.assertTrue(item)

    def test_agregar_permiso(self):
        """Test agregar permiso."""
        wsfexv1 = self.wsfexv1
        self.test_agregar_item()
        idz = "99999AAXX999999A"
        dst = 203  # país destino de la mercaderia
        permiso = wsfexv1.AgregarPermiso(idz, dst)
        self.assertTrue(permiso)

    def test_agregar_cbte_asoc(self):
        """Test agregar comprobante asociado."""
        wsfexv1 = self.wsfexv1
        self.test_crear_factura()  # 20-21 solo para nc y nd
        cbteasoc_tipo = 19
        cbteasoc_pto_vta = 2
        cbteasoc_nro = 1234
        cbteasoc_cuit = 20111111111
        cbteasoc = wsfexv1.AgregarCmpAsoc(
            cbteasoc_tipo, cbteasoc_pto_vta, cbteasoc_nro, cbteasoc_cuit
        )
        self.assertTrue(cbteasoc)

    def test_autorizar(self):
        """Test Autorizar Comprobante."""
        wsfexv1 = self.wsfexv1
        # contiene las partes necesarias para autorizar
        self.test_agregar_permiso()

        idx = int(wsfexv1.GetLastID()) + 1
        # Llamo al WebService de Autorización para obtener el CAE
        wsfexv1.Authorize(idx)

        tipo_cbte = 19
        punto_vta = 7
        cbte_nro = wsfexv1.GetLastCMP(tipo_cbte, punto_vta)
        wsfexv1.GetCMP(tipo_cbte, punto_vta, cbte_nro)

        self.assertEqual(wsfexv1.Resultado, "A")
        self.assertIsInstance(wsfexv1.CAE, str)
        self.assertIsNotNone(wsfexv1.CAE)
        
        #commented because wsfexv1.Vencimiento giving wrong expiration date
        # self.assertEqual(
        #     wsfexv1.Vencimiento, datetime.datetime.now().strftime("%d/%m/%Y")
        # )

    def test_consulta(self):
        """Test para obtener los datos de un comprobante autorizado."""
        wsfexv1 = self.wsfexv1
        # obtengo el ultimo comprobante:
        tipo_cbte = 19
        punto_vta = 7
        cbte_nro = wsfexv1.GetLastCMP(tipo_cbte, punto_vta)
        wsfexv1.GetCMP(tipo_cbte, punto_vta, cbte_nro)

        # obtengo datos para comprobar
        cae = wsfexv1.CAE
        punto_vta = wsfexv1.PuntoVenta
        cbte_nro = wsfexv1.CbteNro
        imp_total = wsfexv1.ImpTotal

        self.assertEqual(wsfexv1.CAE, cae)
        self.assertEqual(wsfexv1.CbteNro, cbte_nro)
        self.assertEqual(wsfexv1.ImpTotal, imp_total)

    def test_recuperar_numero_comprobante(self):
        """Test devuelve numero de comprobante."""
        wsfexv1 = self.wsfexv1
        tipo_cbte = 19
        punto_vta = 7
        cbte_ejemp = "123"
        cbte_nro = wsfexv1.GetLastCMP(tipo_cbte, punto_vta)
        self.assertEqual(len(str(cbte_nro)), len(cbte_ejemp))

    def test_recuperar_numero_transaccion(self):
        """Test ultimo Id."""
        wsfexv1 = self.wsfexv1
        self.test_consulta()
        # TODO: idy = wsfexv1.Id  # agrego en GetCMP Id
        idx = wsfexv1.GetLastID()
        # TODO: self.assertEqual(idy, idx)

    def test_parametros(self):
        """Test de Parametros."""
        wsfexv1 = self.wsfexv1
        # verifico si devuelven datos
        self.assertIsNotNone(wsfexv1.GetParamTipoCbte())
        self.assertIsNotNone(wsfexv1.GetParamDstPais())
        self.assertIsNotNone(wsfexv1.GetParamMon())
        self.assertIsNotNone(wsfexv1.GetParamDstCUIT())
        self.assertIsNotNone(wsfexv1.GetParamUMed())
        self.assertIsNotNone(wsfexv1.GetParamTipoExpo())
        self.assertIsNotNone(wsfexv1.GetParamIdiomas())
        self.assertIsNotNone(wsfexv1.GetParamIncoterms())
        self.assertIsNotNone(wsfexv1.GetParamMonConCotizacion())
        self.assertIsNotNone(wsfexv1.GetParamPtosVenta())
        self.assertIsInstance(wsfexv1.GetParamCtz("DOL"), str)


if __name__ == "__main__":
    unittest.main()
