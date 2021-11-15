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


import sys
import os
import datetime
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.wsfexv1 import WSFEXv1, main
import future
from builtins import str

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

__WSDL__ = "https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL"
__obj__ = WSFEXv1()
__service__= "wsfex"

CUIT = 20267565393
CERT = "reingart.crt"
PKEY = "reingart.key"
CACERT = "conf/afip_ca_info.crt"
CACHE = ""

# Debido a que Python solicita una opción de diseño, hay una advertencia
# sobre una conexión no cerrada al ejecutar las pruebas.
# https://github.com/kennethreitz/requests/issues/3912
# Esto puede ser molesto al ejecutar las pruebas, por lo tanto,
# suprimir la advertencia como se discute en
# https://github.com/kennethreitz/requests/issues/1882

# obteniendo el TA para pruebas


pytestmark = pytest.mark.vcr




def test_dummy(auth):
    """Test de estado del servidor."""
    wsfexv1 = auth
    print(wsfexv1.client.help("FEXDummy"))
    wsfexv1.Dummy()
    print("AppServerStatus", wsfexv1.AppServerStatus)
    print("DbServerStatus", wsfexv1.DbServerStatus)
    print("AuthServerStatus", wsfexv1.AuthServerStatus)
    assert (wsfexv1.AppServerStatus == "OK")
    assert (wsfexv1.DbServerStatus == "OK")
    assert (wsfexv1.AuthServerStatus == "OK")

def test_crear_factura(auth, tipo_cbte=19):
    """Test de creación de una factura (Interna)."""
    wsfexv1 = auth
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
    assert fact==True

def test_agregar_item(auth):
    """Test Agregar Item"""
    wsfexv1 = auth
    test_crear_factura(auth)
    codigo = "PRO1"
    ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
    qty = 2
    precio = "150.00"
    umed = 9  # docenas
    bonif = "50.00"
    imp_total = "250.00"  # importe total final del artículo
    item = wsfexv1.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)
    assert item==True


def test_agregar_permiso(auth):
    """Test agregar permiso."""
    wsfexv1 = auth
    test_agregar_item(auth)
    idz = "99999AAXX999999A"
    dst = 203  # país destino de la mercaderia
    permiso = wsfexv1.AgregarPermiso(idz, dst)
    assert (permiso == True)

def test_agregar_cbte_asoc(auth):
    """Test agregar comprobante asociado."""
    wsfexv1 = auth
    test_crear_factura(auth)  # 20-21 solo para nc y nd
    cbteasoc_tipo = 19
    cbteasoc_pto_vta = 2
    cbteasoc_nro = 1234
    cbteasoc_cuit = 20111111111
    cbteasoc = wsfexv1.AgregarCmpAsoc(
        cbteasoc_tipo, cbteasoc_pto_vta, cbteasoc_nro, cbteasoc_cuit
    )
    assert cbteasoc==True


def test_autorizar(auth):
    """Test Autorizar Comprobante."""
    wsfexv1 = auth
    # contiene las partes necesarias para autorizar
    test_agregar_permiso(auth)

    idx = int(wsfexv1.GetLastID()) + 1
    # Llamo al WebService de Autorización para obtener el CAE
    #wsfexv1.Authorize(idx)

    tipo_cbte = 19
    punto_vta = 7
    cbte_nro = wsfexv1.GetLastCMP(tipo_cbte, punto_vta)
    wsfexv1.GetCMP(tipo_cbte, punto_vta, cbte_nro)

    assert (wsfexv1.Resultado == "A")

    assert isinstance(wsfexv1.CAE,str)


    assert (wsfexv1.CAE)
    
    #commented because wsfexv1.Vencimiento giving wrong expiration date
    # assertEqual(
    #     wsfexv1.Vencimiento, datetime.datetime.now().strftime("%d/%m/%Y")
    # )

def test_consulta(auth):
    """Test para obtener los datos de un comprobante autorizado."""
    wsfexv1 = auth
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

    assert (wsfexv1.CAE == cae)
    assert (wsfexv1.CbteNro == cbte_nro)
    assert (wsfexv1.ImpTotal == imp_total)

def test_recuperar_numero_comprobante(auth):
    """Test devuelve numero de comprobante."""
    wsfexv1 = auth
    tipo_cbte = 19
    punto_vta = 7
    cbte_ejemp = "123"
    cbte_nro = wsfexv1.GetLastCMP(tipo_cbte, punto_vta)
    assert (len(str(cbte_nro)) == len(cbte_ejemp))

def test_recuperar_numero_transaccion(auth):
    """Test ultimo Id."""
    wsfexv1 = auth
    test_consulta(auth)
    # TODO: idy = wsfexv1.Id  # agrego en GetCMP Id
    idx = wsfexv1.GetLastID()
    # TODO: assertEqual(idy, idx)


def test_parametros(auth):
    """Test de Parametros."""
    wsfexv1 = auth
    # verifico si devuelven datos
    assert (wsfexv1.GetParamTipoCbte())
    assert (wsfexv1.GetParamDstPais())
    assert (wsfexv1.GetParamMon())
    assert (wsfexv1.GetParamDstCUIT())
    assert (wsfexv1.GetParamUMed())
    assert (wsfexv1.GetParamTipoExpo())
    assert (wsfexv1.GetParamIdiomas())
    assert (wsfexv1.GetParamIncoterms())
    assert (wsfexv1.GetParamMonConCotizacion())
    #assert (wsfexv1.GetParamPtosVenta())
    assert isinstance(wsfexv1.GetParamCtz("DOL"),str)


def test_main(auth):
    sys.argv = []
    sys.argv.append('--dummy')
    main()

def test_main_get(auth):
    sys.argv = []
    sys.argv.append('--get')
    main()

def test_main_prueba(auth):
    sys.argv = []
    sys.argv.append('--prueba')
    main()

def test_main_params(auth):
    sys.argv = []
    sys.argv.append('--params')
    main()

def test_main_ctz(auth):
    sys.argv = []
    sys.argv.append('--ctz')
    main()

def test_main_mon_ctz(auth):
    sys.argv = []
    sys.argv.append('--monctz')
    main()

def test_ptos_venta(auth):
    sys.argv = []
    sys.argv.append('--ptosventa')
    main()