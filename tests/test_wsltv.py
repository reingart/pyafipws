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

"""Test para Módulo WSLTV
(Liquidación de Tabaco Verde).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os

from pyafipws.wsaa import WSAA
from pyafipws.wsltv import WSLTV


WSDL = "https://fwshomo.afip.gov.ar/wsltv/LtvService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""

# Obteniendo el TA para pruebas
wsaa = WSAA()
wsltv = WSLTV()
ta = wsaa.Autenticar("wsltv", CERT, PKEY)
wsltv.Cuit = CUIT
wsltv.SetTicketAcceso(ta)


def test_conectar():
    """Conectar con servidor."""
    conexion = wsltv.Conectar(CACHE, WSDL)
    assert conexion


def test_server_status():
    """Test de estado de servidores."""
    wsltv.Dummy()
    assert wsltv.AppServerStatus == "OK"
    assert wsltv.DbServerStatus == "OK"
    assert wsltv.AuthServerStatus == "OK"


def test_inicializar():
    """Test inicializar variables de BaseWS."""
    wsltv.inicializar()
    assert wsltv.Total == ""
    assert wsltv.FechaLiquidacion == ""
    assert wsltv.datos == {}


def test_analizar_errores():
    """Test Analizar si se encuentran errores en clientes."""
    ret = {"numeroComprobante": 286}
    wsltv._WSLTV__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsltv.ErrMsg == ""


def test_crear_liquidacion():
    """Test crear liquidacion."""
    tipo_cbte = 150
    pto_vta = 6
    nro_cbte = wsltv.ConsultarUltimoComprobante(tipo_cbte, pto_vta) + 1
    fecha = "2019-04-18"
    cod_deposito_acopio = 1000
    tipo_compra = "CPS"
    variedad_tabaco = "BR"
    cod_provincia_origen_tabaco = 1
    puerta = 22
    nro_tarjeta = 6569866
    horas = 12
    control = "FFAA"
    nro_interno = "77888"
    fecha_inicio_actividad = "2016-04-01"

    # cargo la liquidación:
    liquidacion = wsltv.CrearLiquidacion(
        tipo_cbte,
        pto_vta,
        nro_cbte,
        fecha,
        cod_deposito_acopio,
        tipo_compra,
        variedad_tabaco,
        cod_provincia_origen_tabaco,
        puerta,
        nro_tarjeta,
        horas,
        control,
        nro_interno,
        iibb_emisor=None,
        fecha_inicio_actividad=fecha_inicio_actividad,
    )
    assert liquidacion


def test_agregar_condicion_venta():
    """Test agregar condicion de venta."""
    codigo = 99
    descripcion = "otra"
    agregado = wsltv.AgregarCondicionVenta(codigo=99, descripcion="otra")
    assert agregado


def test_agregar_receptor():
    """Test agregar receptor."""
    cuit = 20111111112
    iibb = 123456
    nro_socio = 11223
    nro_fet = 22
    agregado = wsltv.AgregarReceptor(cuit, iibb, nro_socio, nro_fet)
    assert agregado


def test_agregar_romaneo():
    """Test agregar romaneo."""
    nro_romaneo = 321
    fecha_romaneo = "2018-12-10"
    agregado = wsltv.AgregarRomaneo(nro_romaneo, fecha_romaneo)
    assert agregado


def test_agregar_fardo():
    """Test agregar fardo."""
    cod_trazabilidad = 356
    clase_tabaco = 4
    peso = 900
    agregado = wsltv.AgregarFardo(cod_trazabilidad, clase_tabaco, peso)
    assert agregado


def test_agregar_precio_clase():
    """Test agregar precio clase."""
    clase_tabaco = 10
    precio = 190
    agregado = wsltv.AgregarPrecioClase(clase_tabaco, precio)
    assert agregado


def test_agregar_retencion():
    """Test agregar retencion."""
    descripcion = "otra retencion"
    cod_retencion = 15
    importe = 12
    agregado = wsltv.AgregarRetencion(cod_retencion, descripcion, importe)
    assert agregado


def test_agregar_tributo():
    """Test agregar tributo."""
    codigo_tributo = 99
    descripcion = "Ganancias"
    base_imponible = 15000
    alicuota = 8
    importe = 1200
    agregado = wsltv.AgregarTributo(
        codigo_tributo, descripcion, base_imponible, alicuota, importe
    )
    assert agregado


def test_agregar_flete():
    """Test agregar flete."""
    descripcion = "transporte"
    importe = 1000.00
    agregado = wsltv.AgregarFlete(descripcion, importe)
    assert agregado


def test_agregar_bonificacion():
    """Test agregar bonificacion."""
    porcentaje = 10.0
    importe = 100.00
    agregado = wsltv.AgregarBonificacion(porcentaje, importe)
    assert agregado


def test_autorizar_liquidacion():
    """Test autorizar liquidacion."""
    autorizado = wsltv.AutorizarLiquidacion()
    assert autorizado


def test_analizar_liquidacion():
    """Test analizar liquidacion."""
    # Metodo utilizado con AutorizarLiquidacion
    pass


def test_crear_ajuste():
    """Test crear ajuste."""
    tipo_cbte = 151
    pto_vta = 2
    nro_cbte = 1
    fecha = "2016-09-09"
    fecha_inicio_actividad = "1900-01-01"
    ajuste = wsltv.CrearAjuste(
        tipo_cbte, pto_vta, nro_cbte, fecha, fecha_inicio_actividad
    )
    assert ajuste


def test_agregar_comprobante_ajustar():
    """Test agregar comprobante ajustar."""
    tipo_cbte = 151
    pto_vta = 3697
    nro_cbte = 2
    agregado = wsltv.AgregarComprobanteAAjustar(tipo_cbte, pto_vta, nro_cbte)
    assert agregado


def test_generar_ajuste_fisico():
    """Test generar ajuste fisico."""
    ajuste = wsltv.GenerarAjusteFisico()
    assert ajuste


def test_ajustar_liquidacion():
    """Test ajustar liquidacion."""
    tipo_cbte = 151
    pto_vta = 2958
    nro_cbte = 13
    fecha = "2015-12-31"
    cod_deposito_acopio = 201
    tipo_ajuste = "C"
    cuit_receptor = 222222222
    iibb_receptor = 2
    fecha_inicio_actividad = "2010-01-01"
    wsltv.CrearAjuste(
        tipo_cbte,
        pto_vta,
        nro_cbte,
        fecha,
        cod_deposito_acopio,
        tipo_ajuste,
        cuit_receptor,
        iibb_receptor,
        fecha_inicio_actividad,
    )

    tipo_cbte = 151
    pto_vta = 4521
    nro_cbte = 12345678
    wsltv.AgregarComprobanteAAjustar(tipo_cbte, pto_vta, nro_cbte)

    clase_tabaco = 111
    precio = 25
    total_kilos = 41
    total_fardos = 1
    wsltv.AgregarPrecioClase(clase_tabaco, precio, total_kilos, total_fardos)

    cod_retencion = 11
    descripcion = None
    importe = 20
    wsltv.AgregarRetencion(cod_retencion, descripcion, importe)

    codigo_tributo = 99
    descripcion = "Descripcion otros tributos"
    base_imponible = 2
    alicuota = 2
    importe = 10
    wsltv.AgregarTributo(codigo_tributo, descripcion, base_imponible, alicuota, importe)

    ajuste = wsltv.AjustarLiquidacion()
    assert ajuste


def test_consultar_liquidacion():
    """Test ocnsultar liquidacion."""
    tipo_cbte = 151
    pto_vta = 1
    nro_cbte = 0
    consulta = wsltv.ConsultarLiquidacion(tipo_cbte, pto_vta, nro_cbte)
    assert consulta


def test_consultar_ultimo_comprobante():
    """Test consultar ultimo comprobante."""
    tipo_cbte = 151
    pto_vta = 1
    consulta = wsltv.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
    assert consulta


def test_consultar_provincias():
    """Test consultar provincias."""
    consulta = wsltv.ConsultarProvincias()
    assert consulta


def test_consultar_condiciones_venta():
    """Tets consultar condiciones venta."""
    consulta = wsltv.ConsultarCondicionesVenta()
    assert consulta


def test_consultar_tributos():
    """Test consultar tributos."""
    consulta = wsltv.ConsultarTributos()
    assert consulta


def test_consultar_variedades_clases_tabaco():
    """Test consultar variedades de tabaco."""
    consulta = wsltv.ConsultarRetencionesTabacaleras()
    assert consulta


def test_consultar_retenciones_tabacaleras():
    """Test consultar retenciones tabacaleras."""
    consulta = wsltv.ConsultarRetencionesTabacaleras()
    assert consulta


def test_consultar_depositos_acopio():
    """Test consultar depositos de acopio."""
    consulta = wsltv.ConsultarDepositosAcopio()
    assert consulta


def test_consultar_puntos_ventas():
    """Test consultar puntos de venta."""
    consulta = wsltv.ConsultarPuntosVentas()
    assert consulta


def test_mostrar_pdf():
    """Test mostrar PDF."""
    pdf = wsltv.GetParametro("pdf")
    if pdf:
        with open("liq.pdf", "wb") as f:
            f.write(pdf)
    show = wsltv.MostrarPDF(archivo="liq.pdf", imprimir=True)
    assert show is False
