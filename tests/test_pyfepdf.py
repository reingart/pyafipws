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

"""Test para FEPDF"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import sys
import datetime
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.pyfepdf import FEPDF
from pyafipws.pyfepdf import main
from builtins import str
from pyafipws.utils import SafeConfigParser
import shutil


CERT = "reingart.crt"
PKEY = "reingart.key"
CONFIG_FILE = "rece.ini"

URL = [
    "https://www.afip.gob.ar/fe/qr/?p=b'eyJ2ZXIiOiAxLCAiZmVjaGEiOiAiMjAyMS0wOC0wNSIsICJjdWl0IjogMzAwMDAwMDAwMDcsICJwdG9WdGEiOiA0MDAwLCAidGlwb0NtcCI6IDIwMSwgIm5yb0NtcCI6IDEyMzQ1Njc4LCAiaW1wb3J0ZSI6IDEyNy4wLCAibW9uZWRhIjogIlBFUyIsICJjdHoiOiAxLjAsICJ0aXBvRG9jUmVjIjogODAsICJucm9Eb2NSZWMiOiAzMDAwMDAwMDAwNywgInRpcG9Db2RBdXQiOiAiRSIsICJjb2RBdXQiOiA2MTEyMzAyMjkyNTg1NX0='",
    "https://www.afip.gob.ar/fe/qr/?p=eyJjdWl0IjogMzAwMDAwMDAwMDcsICJ0aXBvRG9jUmVjIjogODAsICJtb25lZGEiOiAiUEVTIiwgInB0b1Z0YSI6IDQwMDAsICJpbXBvcnRlIjogMTI3LjAsICJ2ZXIiOiAxLCAiY29kQXV0IjogNjExMjMwMjI5MjU4NTUsICJ0aXBvQ29kQXV0IjogIkUiLCAiZmVjaGEiOiAiMjAyMS0wOC0wNSIsICJjdHoiOiAxLjAsICJ0aXBvQ21wIjogMjAxLCAibnJvQ21wIjogMTIzNDU2NzgsICJucm9Eb2NSZWMiOiAzMDAwMDAwMDAwN30=",
]

fepdf = FEPDF()

pytestmark = [pytest.mark.dontusefix]
shutil.copy("tests/facturas.json", "facturas.json")


def test_crear_factura():
    """Test de creación de una factura (Interna)."""

    tipo_cbte = 19 if "--expo" in sys.argv else 201
    punto_vta = 4000
    fecha = datetime.datetime.now().strftime("%Y%m%d")
    concepto = 3
    tipo_doc = 80
    nro_doc = "30000000007"
    cbte_nro = 12345678
    imp_total = "127.00"
    imp_tot_conc = "3.00"
    imp_neto = "100.00"
    imp_iva = "21.00"
    imp_trib = "1.00"
    imp_op_ex = "2.00"
    imp_subtotal = "105.00"
    fecha_cbte = fecha
    fecha_venc_pago = fecha
    # Fechas del período del servicio facturado (solo si concepto> 1)
    fecha_serv_desde = fecha
    fecha_serv_hasta = fecha
    # campos p/exportación (ej): DOL para USD, indicando cotización:
    moneda_id = "DOL" if "--expo" in sys.argv else "PES"
    moneda_ctz = 1 if moneda_id == "PES" else 14.90
    incoterms = "FOB"  # solo exportación
    idioma_cbte = 1  # 1: es, 2: en, 3: pt

    # datos adicionales del encabezado:
    nombre_cliente = "Joao Da Silva"
    domicilio_cliente = "Rua 76 km 34.5 Alagoas"
    pais_dst_cmp = 212  # 200: Argentina, ver tabla
    id_impositivo = "PJ54482221-l"  # cat. iva (mercado interno)
    forma_pago = "30 dias"

    obs_generales = "Observaciones Generales<br/>linea2<br/>linea3"
    obs_comerciales = "Observaciones Comerciales<br/>texto libre"

    # datos devueltos por el webservice (WSFEv1, WSMTXCA, etc.):
    motivo_obs = "Factura individual, DocTipo: 80, DocNro 30000000007 no se encuentra registrado en los padrones de AFIP."
    cae = "61123022925855"
    fch_venc_cae = "20110320"

    fact = fepdf.CrearFactura(
        concepto,
        tipo_doc,
        nro_doc,
        tipo_cbte,
        punto_vta,
        cbte_nro,
        imp_total,
        imp_tot_conc,
        imp_neto,
        imp_iva,
        imp_trib,
        imp_op_ex,
        fecha_cbte,
        fecha_venc_pago,
        fecha_serv_desde,
        fecha_serv_hasta,
        moneda_id,
        moneda_ctz,
        cae,
        fch_venc_cae,
        id_impositivo,
        nombre_cliente,
        domicilio_cliente,
        pais_dst_cmp,
        obs_comerciales,
        obs_generales,
        forma_pago,
        incoterms,
        idioma_cbte,
        motivo_obs,
    )

    assert fact == True


def test_agregar_detalle_item():
    """Test de agregando un artículo a una factura (interna).."""

    tipo_cbte = 19 if "--expo" in sys.argv else 201

    test_crear_factura()

    # detalle de artículos:
    u_mtx = 123456
    cod_mtx = 1234567890123
    codigo = "P0001"
    ds = "Descripcion del producto P0001\n" + "Lorem ipsum sit amet " * 10
    qty = 1.00
    umed = 7
    if tipo_cbte in (1, 2, 3, 4, 5, 34, 39, 51, 52, 53, 54, 60, 64):
        # discriminar IVA si es clase A / M
        precio = 110.00
        imp_iva = 23.10
    else:
        # no discriminar IVA si es clase B (importe final iva incluido)
        precio = 133.10
        imp_iva = None
    bonif = 0.00
    iva_id = 5
    importe = 133.10
    despacho = u"Nº 123456"
    dato_a = "Dato A"
    chk1 = fepdf.AgregarDetalleItem(
        u_mtx,
        cod_mtx,
        codigo,
        ds,
        qty,
        umed,
        precio,
        bonif,
        iva_id,
        imp_iva,
        importe,
        despacho,
        dato_a,
    )

    # descuento general (a tasa 21%):
    u_mtx = cod_mtx = codigo = None
    ds = u"Bonificación/Descuento 10%"
    qty = precio = bonif = None
    umed = 99
    iva_id = 5
    if tipo_cbte in (1, 2, 3, 4, 5, 34, 39, 51, 52, 53, 54, 60, 64):
        # discriminar IVA si es clase A / M
        imp_iva = -2.21
    else:
        imp_iva = None
    importe = -12.10
    chk2 = fepdf.AgregarDetalleItem(
        u_mtx,
        cod_mtx,
        codigo,
        ds,
        qty,
        umed,
        precio,
        bonif,
        iva_id,
        imp_iva,
        importe,
        "",
    )

    # descripción (sin importes ni cantidad):
    u_mtx = cod_mtx = codigo = None
    qty = precio = bonif = iva_id = imp_iva = importe = None
    umed = 0
    ds = u"Descripción Ejemplo"
    chk3 = fepdf.AgregarDetalleItem(
        u_mtx,
        cod_mtx,
        codigo,
        ds,
        qty,
        umed,
        precio,
        bonif,
        iva_id,
        imp_iva,
        importe,
        "",
    )

    assert chk1 == True
    assert chk2 == True
    assert chk3 == True


def test_agregar_iva():
    iva_id = 5  # 21%
    base_imp = 100
    importe = 21
    chk = fepdf.AgregarIva(iva_id, base_imp, importe)
    assert chk == True


def test_agregar_tributo():
    tributo_id = 99
    desc = "Impuesto Municipal Matanza"
    base_imp = "100.00"
    alic = "1.00"
    importe = "1.00"
    chk = fepdf.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

    assert chk == True


def test_agregar_cmp_asoc():
    tipo = 5
    pto_vta = 2
    nro = 1234
    chk = fepdf.AgregarCmpAsoc(tipo, pto_vta, nro)

    assert chk == True


def test_crear_plantilla():
    sys.argv = []

    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    conf_fact = dict(config.items("FACTURA"))

    fepdf.CrearPlantilla(
        papel=conf_fact.get("papel", "legal"),
        orientacion=conf_fact.get("orientacion", "portrait"),
    )


def test_procesar_plantilla():
    sys.argv = []
    sys.argv.append("--debug")

    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    conf_fact = dict(config.items("FACTURA"))

    chk = fepdf.ProcesarPlantilla(
        num_copias=int(conf_fact.get("copias", 1)),
        lineas_max=int(conf_fact.get("lineas_max", 24)),
        qty_pos=conf_fact.get("cant_pos") or "izq",
    )

    assert chk == False


def test_generar_qr():
    fepdf.CUIT = "30000000007"
    url = fepdf.GenerarQR()
    assert url in URL


def test_main_prueba():
    sys.argv = []
    sys.argv.append("--prueba")
    sys.argv.append("--debug")
    main()


def test_main_cargar():
    sys.argv = []
    sys.argv.append("--cargar")
    sys.argv.append("--entrada")
    sys.argv.append("tests/facturas.txt")
    main()


def test_main_cargar_json():
    sys.argv = []
    sys.argv.append("--cargar")
    sys.argv.append("--json")
    sys.argv.append("--entrada")
    sys.argv.append("facturas.json")
    main()


def test_main_grabar():
    sys.argv = []
    sys.argv.append("--prueba")
    sys.argv.append("--grabar")
    # sys.argv.append("--debug")
    main()
    f1 = open("facturas.txt", "rb")
    f2 = open("tests/facturas.txt", "rb")
    d1 = f1.readlines()
    d2 = f2.readlines()
    f1.close()
    f2.close()
    diff = [x for x in d1 if x not in d2]
    assert diff == []


def test_main_grabar_json():
    sys.argv = []
    sys.argv.append("--prueba")
    sys.argv.append("--grabar")
    sys.argv.append("--json")
    sys.argv.append("--debug")
    main()
    f1 = open("facturas.json", "r")
    f2 = open("tests/facturas.json", "r")
    d1 = f1.readlines()
    d2 = f2.readlines()
    f1.close()
    f2.close()
    diff = [x for x in d1 if x not in d2]
    assert diff == []


def test_mostrar_pdf(mocker):
    sys.argv = []
    mocker.patch("os.system")
    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    conf_fact = dict(config.items("FACTURA"))

    salida = conf_fact.get("salida", "")
    fepdf.MostrarPDF(archivo=salida)
    if sys.platform.startswith("linux" or "linux2"):
        os.system.assert_called_with("evince %s" % salida)
