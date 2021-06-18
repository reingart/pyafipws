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

"""Test para Módulo WSRemCarne
(Remito Electronico Carnico).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os

from pyafipws.wsaa import WSAA
from pyafipws.wsremcarne import WSRemCarne


WSDL = "https://fwshomo.afip.gov.ar/wsremcarne/RemCarneService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""


# obteniendo el TA para pruebas
wsaa = WSAA()
wsremcarne = WSRemCarne()
ta = wsaa.Autenticar("wsremcarne", CERT, PKEY)
print(ta)
wsremcarne.Cuit = CUIT
wsremcarne.SetTicketAcceso(ta)


def test_conectar():
    """Conectar con BaseWS."""
    conexion = wsremcarne.Conectar(CACHE, WSDL)
    assert conexion


def test_server_status():
    """Test de estado de servidores."""
    wsremcarne.Dummy()
    assert wsremcarne.AppServerStatus == "OK"
    assert wsremcarne.DbServerStatus == "OK"
    assert wsremcarne.AuthServerStatus == "OK"


def test_inicializar():
    """Test inicializar variables de BaseWS."""
    wsremcarne.inicializar()
    assert wsremcarne.TipoComprobante is None
    assert wsremcarne.Obs == ""
    assert wsremcarne.Errores == []


def test_analizar_errores():
    """Test analizar si se encuentran errores."""
    ret = {"numeroComprobante": 286}
    wsremcarne._WSRemCarne__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsremcarne.ErrMsg == ""


def test_analizar_observaciones():
    """Test analizar si se encuentran errores."""
    ret = {"numeroComprobante": 286}
    wsremcarne._WSRemCarne__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsremcarne.Obs == ""


def test_analizar_evento():
    """Test analizar si se encuentran eventos."""
    ret = {"numeroComprobante": 286}
    wsremcarne._WSRemCarne__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsremcarne.Evento == ""


def test_crear_remito():
    """Test generacion de remito(interno)."""
    tipo_comprobante = 995
    punto_emision = 1
    # ENV: Envio Normal, PLA: Retiro en planta, REP: Reparto, RED: Redestino
    tipo_movimiento = "ENV"
    categoria_emisor = 1
    cuit_titular_mercaderia = "20222222223"
    cod_dom_origen = 1
    # 'EM': DEPOSITO EMISOR, 'MI': MERCADO INTERNO, 'RP': REPARTO
    tipo_receptor = "EM"
    categoria_receptor = 1
    cuit_receptor = "20111111112"
    cuit_depositario = None
    cod_dom_destino = 1
    cod_rem_redestinar = None
    cod_remito = 30
    estado = "A"
    remito = wsremcarne.CrearRemito(
        tipo_comprobante,
        punto_emision,
        tipo_movimiento,
        categoria_emisor,
        cuit_titular_mercaderia,
        cod_dom_origen,
        tipo_receptor,
        categoria_receptor,
        cuit_receptor,
        cuit_depositario,
        cod_dom_destino,
        cod_rem_redestinar,
        cod_remito,
        estado,
    )
    assert remito


def test_agregar_viaje():
    """Test agregar viaje."""
    cuit_transportista = "20333333334"
    cuit_conductor = "20333333334"
    fecha_inicio_viaje = "2019-05-24"
    distancia_km = 8888

    agregado = wsremcarne.AgregarViaje(
        cuit_transportista, cuit_conductor, fecha_inicio_viaje, distancia_km
    )
    assert agregado


def test_agregar_vehiculo():
    """Test agregar vehiculo."""
    dominio_vehiculo = "AAA000"
    dominio_acoplado = "ZZZ000"
    agregado = wsremcarne.AgregarVehiculo(dominio_vehiculo, dominio_acoplado)
    assert agregado


def test_agregar_mercaderia():
    """Test agregar mercaderia."""
    orden = 1
    tropa = 1
    cod_tipo_prod = "2.13"
    kilos = 10
    unidades = 1
    agregado = wsremcarne.AgregarMercaderia(
        orden, tropa, cod_tipo_prod, kilos, unidades
    )
    assert agregado


def test_agregar_datos_autorizacion():
    """Test agregar datos autorizacion."""
    agregado = wsremcarne.AgregarDatosAutorizacion(None)
    assert agregado


def test_agregar_contingencias():
    """Test agregar contingencias."""
    tipo = 1
    observacion = "anulacion"
    agregado = wsremcarne.AgregarContingencias(tipo, observacion)
    assert agregado


def test_generar_remito():
    """Test generar remito."""
    ok = wsremcarne.GenerarRemito(id_req=1565890584, archivo=None)
    assert ok is False


def test_analizar_remito():
    """Test analizar remito."""
    ret = {"Codigo": "Descripcion X"}
    archivo = None
    analisis = wsremcarne.AnalizarRemito(ret, archivo)
    assert analisis is None


def test_emitir_remito():
    """Test emitir remito."""
    archivo = None
    remito = wsremcarne.EmitirRemito(archivo)
    assert remito is False


def test_autorizar_remito():
    """Test autorizar remito."""
    archivo = None
    remito = wsremcarne.AutorizarRemito(archivo)
    assert remito


def test_anular_remito():
    """Test anular remito."""
    remito = wsremcarne.AnularRemito()
    assert remito


def test_consultar_ultimo_remito_emitido():
    """Test consultar ultimo remito ."""
    tipo_comprobante = 995
    pto_emision = 1
    consulta = wsremcarne.ConsultarUltimoRemitoEmitido(tipo_comprobante, pto_emision)
    assert consulta == 0


def test_consultar_remito():
    """Test consultar remito."""
    cod_remito = 100
    ok = wsremcarne.ConsultarRemito(cod_remito)
    assert ok == 0


def test_consultar_tipos_comprobante():
    """Test consultar tipos de comprobante."""
    consulta = wsremcarne.ConsultarTiposComprobante()
    assert consulta


def test_consultar_tipos_contingencia():
    """Tes consulatr tipos de contingencia."""
    consulta = wsremcarne.ConsultarTiposContingencia()
    assert consulta


def test_consultar_tipos_categoria_emisor():
    """Test consultar tipos de categoria emisor."""
    consulta = wsremcarne.ConsultarTiposCategoriaEmisor()
    assert consulta


def test_consultar_tipos_categoria_receptor():
    """Test consultar tipos de categoria receptor."""
    consulta = wsremcarne.ConsultarTiposCategoriaReceptor()
    assert consulta


def test_consultar_tipos_estado():
    """Test consultar tipos de estado."""
    consulta = wsremcarne.ConsultarTiposEstado()
    assert consulta


def test_consultar_grupos_carne():
    """Test consultar grupos de carne."""
    consulta = wsremcarne.ConsultarGruposCarne()
    assert consulta


def test_consultar_tipos_carne():
    """Test consultar tipos de carne."""
    consulta = wsremcarne.ConsultarTiposCarne()
    assert consulta


def test_consultar_codigos_domicilio():
    """Test consultar codigos de domicilio con cuit."""
    cuit = 20333333331
    consulta = wsremcarne.ConsultarCodigosDomicilio(cuit)
    assert consulta == []
