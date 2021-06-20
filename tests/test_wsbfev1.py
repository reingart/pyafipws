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

"""Test para WSBFEv1"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import unittest
import os
import sys
from datetime import datetime, timedelta
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.wsbfev1 import WSBFEv1
from pysimplesoap.simplexml import SimpleXMLElement

WSDL = "http://wswhomo.afip.gov.ar/WSBFEv1/service.asmx"
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
pytestmark =pytest.mark.vcr

@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)



wsbfev1 = WSBFEv1()
@pytest.fixture(autouse=True)
def auth():
    wsaa=WSAA()
    ta = wsaa.Autenticar("wsbfe", CERT, PKEY)
    wsbfev1.Cuit = CUIT
    wsbfev1.SetTicketAcceso(ta)
    wsbfev1.Conectar(CACHE, WSDL)
    return wsbfev1

def test_dummy(auth):
    """Test de estado del servidor."""
    wsbfev1 = auth
    print(wsbfev1.client.help("BFEDummy"))
    wsbfev1.Dummy()
    print("AppServerStatus", wsbfev1.AppServerStatus)
    print("DbServerStatus", wsbfev1.DbServerStatus)
    print("AuthServerStatus", wsbfev1.AuthServerStatus)
    assert wsbfev1.AppServerStatus == "OK"
    assert wsbfev1.DbServerStatus=="OK"
    assert wsbfev1.AuthServerStatus== "OK"

def test_crear_factura(auth):
    """Test de creación de una factura (Interna)."""
    wsbfev1 =auth
    tipo_cbte = 1  # factura "A"
    punto_vta = 5
    tipo_doc = 80
    nro_doc = 20888888883
    zona = 1
    # Obtengo el último número de comprobante y le agrego 1
    cbte_nro = int(wsbfev1.GetLastCMP(tipo_cbte, punto_vta)) + 1
    fecha_cbte = datetime.now().strftime("%Y%m%d")
    imp_moneda_id = "PES"  # (ver tabla de parámetros)
    imp_moneda_ctz = 1
    imp_neto = "1450.00"
    impto_liq = "304.50"  # 21% IVA
    impto_liq_rni = imp_tot_conc = imp_op_ex = "0.00"
    imp_perc = imp_iibb = imp_perc_mun = imp_internos = "0.00"
    imp_total = "1754.50"
    fecha_venc_pago = None

    # Creo una factura (internamente, no se llama al WebService)
    fact = wsbfev1.CrearFactura(
        tipo_doc,
        nro_doc,
        zona,
        tipo_cbte,
        punto_vta,
        cbte_nro,
        fecha_cbte,
        imp_total,
        imp_neto,
        impto_liq,
        imp_tot_conc,
        impto_liq_rni,
        imp_op_ex,
        imp_perc,
        imp_iibb,
        imp_perc_mun,
        imp_internos,
        imp_moneda_id,
        imp_moneda_ctz,
        fecha_venc_pago,
    )
    assert fact==True

def test_agregar_item(auth):
    """Test Agregar Item."""
    wsbfev1 =auth
    test_crear_factura(auth)
    # Agrego un item:
    ncm = "2101.11.10"
    sec = ""
    umed = 5  # unidades
    ds = "Cafe"
    qty = "10.00"
    precio = "150.00"
    bonif = "50.00"
    iva_id = 5
    imp_total = "1754.50"
    item = wsbfev1.AgregarItem(
        ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total
    )
    assert item==True

def test_agregar_cbte_asoc(auth):
    """Test agregar comprobante asociado."""
    wsbfev1 =auth
    test_crear_factura(auth)  # 20-21 solo para nc y nd
    cbteasoc_tipo = 19
    cbteasoc_pto_vta = 40
    cbteasoc_nro = 1234
    cbteasoc_cuit = 20111111111
    cbteasoc_fecha = None
    cbteasoc = wsbfev1.AgregarCmpAsoc(
        cbteasoc_tipo, cbteasoc_pto_vta, cbteasoc_nro, cbteasoc_cuit, cbteasoc_fecha
    )
    assert cbteasoc==True

def test_agregar_opcional(auth):
    """Test agregar opcional."""
    wsbfev1 =auth
    test_agregar_item(auth)
    idz = "1010"
    ds = "pyafipws"
    opcional = wsbfev1.AgregarOpcional(idz, ds)
    assert opcional==True

def test_autorizar(auth):
    """Test Autorizar Comprobante."""
    wsbfev1 =auth
    test_agregar_item(auth)
    # test_agregar_cbte_asoc

    idx = int(wsbfev1.GetLastID()) + 1
    # Llamo al WebService de Autorización para obtener el CAE
    wsbfev1.Authorize(idx)

    assert (wsbfev1.Resultado== "A")
    assert isinstance(wsbfev1.CAE,str)
    assert (wsbfev1.CAE)
    ten = datetime.now() + timedelta(days=10)
    assert (wsbfev1.Vencimiento == ten.strftime("%d/%m/%Y"))

def test_consulta(auth):
    """Test para obtener los datos de un comprobante autorizado."""
    wsbfev1 = auth
    # obtengo el ultimo comprobante:
    tipo_cbte = 1
    punto_vta = 5

    cbte_nro = wsbfev1.GetLastCMP(tipo_cbte, punto_vta)
    wsbfev1.GetCMP(tipo_cbte, punto_vta, cbte_nro)

    # obtengo datos para comprobar
    cae = wsbfev1.CAE
    punto_vta = wsbfev1.PuntoVenta
    cbte_nro = wsbfev1.CbteNro
    imp_total = wsbfev1.ImpTotal

    assert wsbfev1.CAE== cae
    assert (wsbfev1.CbteNro== cbte_nro)
    assert (wsbfev1.ImpTotal== imp_total)

def test_recuperar_numero_comprobante(auth):
    """Test devuelve numero de comprobante."""
    wsbfev1 = auth
    tipo_cbte = 1
    punto_vta = 5
    cbte_ejemp = "1234"

    cbte_nro = wsbfev1.GetLastCMP(tipo_cbte, punto_vta)
    assert len(str(cbte_nro)) == len(cbte_ejemp)

def test_recuperar_ultima_id(auth):
    """Test ultimo Id."""
    test_consulta(auth)
    wsbfev1 = auth
    t = wsbfev1.XmlResponse.decode('utf-8')
    idy = str(t[t.find("<Id>")+4:t.find("</Id>")])
    idx = str(wsbfev1.GetLastID())
    print(idy)
    assert idy==idx

def test_parametros(auth):
    """Test Parametros."""
    wsbfev1 = auth
    # verifico si devuelven datos
    assert wsbfev1.GetParamTipoCbte()
    assert wsbfev1.GetParamZonas()
    assert wsbfev1.GetParamMon()
    assert wsbfev1.GetParamTipoDoc()
    assert wsbfev1.GetParamTipoIVA()
    assert wsbfev1.GetParamUMed()
    assert wsbfev1.GetParamNCM()
    # no funciona / no existe en el servidor homo wsbfe
    # assertIsNotNone(wsbfev1.GetParamCtz('DOL'))



