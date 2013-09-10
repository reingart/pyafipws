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

"Pruebas para Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP Disp. 3683/11"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"

import unittest
import os, time, sys
from decimal import Decimal
import datetime

sys.path.append("/home/reingart")        # TODO: proper packaging

from pyafipws.trazamed import TrazaMed

WSDL = "https://servicios.pami.org.ar/trazamed.WebService?wsdl"
CACHE = "/home/reingart/pyafipws/cache"


class TestTZM(unittest.TestCase):
    
    def setUp(self):
        sys.argv.append("--trace")                  # TODO: use logging
        self.ws = ws = TrazaMed()
        
        ws.Username = 'testwservice'
        ws.Password = 'testwservicepsw'
    
        ws.Conectar(CACHE, WSDL)
    
    def test_basico(self):
        "Prueba básica para informar un medicamento"
        ws = self.ws
        ws.SetParametro('nro_asociado', "9999999999999")
        ws.SendMedicamentos(
            usuario='pruebasws', password='pruebasws',
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()*10), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_documento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",
            )
        self.assertFalse(ws.Excepcion)
        self.assertTrue(ws.Resultado)
        self.assertIsInstance(ws.CodigoTransaccion, basestring)
        self.assertEqual(len(ws.CodigoTransaccion), len("23312897")) 

    def test_fraccion(self):
        "Prueba básica para informar un medicamento fraccionado"
        ws = self.ws
        ws.SetParametro('nro_asociado', "9999999999999")
        ws.SetParametro('cantidad', 5)
        ws.SendMedicamentosFraccion(
            usuario='pruebasws', password='pruebasws',
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()*10), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_documento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",)
        self.assertFalse(ws.Resultado)
        # verificar error "Su tipo de agente no esta habilitado para fraccionar"
        self.assertEqual(ws.Errores[0][:4], "3105")
 
    def test_dh(self):
        "Prueba básica para informar un medicamento desde - hasta"
        ws = self.ws
        ws.SetParametro('nro_asociado', "1234")
        ws.SendMedicamentosDHSerie(
            usuario='pruebasws', password='pruebasws',
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            desde_numero_serial=int(time.time()*10)-1, hasta_numero_serial=int(time.time()*10)+1, 
            id_obra_social=None, id_evento=134,
            )
        self.assertTrue(ws.Resultado)
        self.assertIsInstance(ws.CodigoTransaccion, basestring)
        self.assertEqual(len(ws.CodigoTransaccion), len("23312897")) 

    def test_cancela_parcial(self):
        "Prueba de cancelación parcial"
        ws = self.ws
        ws.SendCancelacTransaccParcial(
            usuario='pruebasws', password='pruebasws',
            codigo_transaccion="23312897", 
            gtin_medicamento="GTIN1", 
            numero_serial="13788431940")
        # por el momento ANMAT devuelve error en pruebas:
        self.assertFalse(ws.Resultado)
        # verificar error "3: Transaccion NO encontrada, NO se puede anular."
        self.assertEqual(ws.Errores[0][:2], "3:")

    def test_consultar(self):
        "Prueba para obtener las transacciones no confirmadas"
        ws = self.ws
        ws.GetTransaccionesNoConfirmadas(
            usuario='pruebasws', password='pruebasws',
            id_medicamento="GTIN1", 
            )
        
        self.assertFalse(ws.HayError)
        q = 0
        while ws.LeerTransaccion():
            q += 1
            for clave in '_id_transaccion', '_gtin', '_lote', '_numero_serial':
                valor = ws.GetParametro(clave)
                self.assertIsNot(valor, None)
        self.assert_(q)    

    def test_consultar_alertadas(self):
        "Prueba para obtener las transacciones propias alertadas"
        ws = self.ws
        ws.GetEnviosPropiosAlertados(
            usuario='pruebasws', password='pruebasws',
            id_medicamento="GTIN1", 
            )
        
        self.assertFalse(ws.HayError)
        q = 0
        while ws.LeerTransaccion():
            q += 1
            for clave in '_id_transaccion', '_gtin', '_lote', '_numero_serial':
                valor = ws.GetParametro(clave)
                self.assertIsNot(valor, None)
        self.assert_(q)    


    def test_confirmar(self):
        "Prueba para confirmar las transacciones no confirmadas"
        ws = self.ws
        # obtengo las transacciones pendientes para confirmar:
        ws.GetTransaccionesNoConfirmadas(
            usuario='pruebasws', password='pruebasws',
            id_medicamento="GTIN1", 
            )
        # no debería haber error:
        self.assertFalse(ws.HayError)
        # 
        while ws.LeerTransaccion():
            _id_transaccion = ws.GetParametro('_id_transaccion')
            _f_operacion = datetime.datetime.now().strftime("%d/%m/%Y")
            # confirmo la transacción:
            ws.SendConfirmaTransacc(
                usuario='pruebasws', password='pruebasws',
                p_ids_transac=_id_transaccion, 
                f_operacion=_f_operacion,
                )
            # verifico que se haya confirmado correctamente:
            self.assertTrue(ws.Resultado)
            # verifico que haya devuelto id_transac_asociada:
            self.assertIsInstance(ws.CodigoTransaccion, basestring)
            self.assertEqual(len(ws.CodigoTransaccion), len("23312897"))
            # salgo del ciclo (solo confirmo una transacción)
            break
        else:
            self.fail("no se devolvieron transacciones para confirmar!")    
        

    def test_alertar(self):
        "Prueba para alertar (rechazar) una transaccion no confirmada"
        ws = self.ws
        # obtengo las transacciones pendientes para confirmar:
        ws.GetTransaccionesNoConfirmadas(
            usuario='pruebasws', password='pruebasws',
            id_medicamento="GTIN1", 
            )
        # no debería haber error:
        self.assertFalse(ws.HayError)
        # 
        while ws.LeerTransaccion():
            _id_transaccion = ws.GetParametro('_id_transaccion')
            # alerto la transacción:
            ws.SendAlertaTransacc(
                usuario='pruebasws', password='pruebasws',
                p_ids_transac_ws=_id_transaccion, 
                )
            # verifico que se haya confirmado correctamente:
            self.assertTrue(ws.Resultado)
            # salgo del ciclo (solo alerto una transacción)
            break
        else:
            self.fail("no se devolvieron transacciones para alertar!")    
        
if __name__ == '__main__':
    unittest.main()

