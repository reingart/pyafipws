# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Test para Módulo WSLSP
Liquidación Sector Pecuario (hacienda/carne).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os

from pyafipws.wsaa import WSAA
from pyafipws.wslsp import WSLSP


WSDL = "https://fwshomo.afip.gov.ar/wslsp/LspService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""

# obteniendo el TA para pruebas
wsaa = WSAA()
wslsp = WSLSP()
ta = wsaa.Autenticar("wslsp", CERT, PKEY)
wslsp.Cuit = CUIT
wslsp.SetTicketAcceso(ta)


def test_conectar():
    """Conectar con servidor."""
    conexion = wslsp.Conectar(CACHE, WSDL)
    assert conexion


def test_server_status():
    """Test de estado de servidores."""
    wslsp.Dummy()
    assert wslsp.AppServerStatus == "OK"
    assert wslsp.DbServerStatus == "OK"
    assert wslsp.AuthServerStatus == "OK"


def test_inicializar():
    """Test inicializar variables de BaseWS."""
    wslsp.inicializar()
    assert wslsp.ImporteTotalNeto is None
    assert wslsp.FechaProcesoAFIP == ""
    assert wslsp.datos == {}


def test_analizar_errores():
    """Test Analizar si se encuentran errores."""
    ret = {"numeroComprobante": 286}
    wslsp._WSLSP__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wslsp.ErrMsg == ""


def test_crear_liquidacion():
    """Test crear liquidacion."""
    cod_operacion = 1
    fecha_cbte = "2019-04-23"
    fecha_op = "2019-04-23"
    cod_motivo = 6
    cod_localidad_procedencia = 8274
    cod_provincia_procedencia = 1
    cod_localidad_destino = 8274
    cod_provincia_destino = 1
    lugar_realizacion = "CORONEL SUAREZ"
    fecha_recepcion = None
    fecha_faena = None
    datos_adicionales = None
    liquidacion = wslsp.CrearLiquidacion(
        cod_operacion,
        fecha_cbte,
        fecha_op,
        cod_motivo,
        cod_localidad_procedencia,
        cod_provincia_procedencia,
        cod_localidad_destino,
        cod_provincia_destino,
        lugar_realizacion,
        fecha_recepcion,
        fecha_faena,
        datos_adicionales,
    )
    assert liquidacion


def test_agregar_frigorifico():
    """Test agregar frigorifico."""
    cuit = 20160000156
    nro_planta = 1
    agregado = wslsp.AgregarFrigorifico(cuit, nro_planta)
    assert agregado


def test_agregar_emisor():
    """Test agregar emisor."""
    tipo_cbte = 180
    pto_vta = 3000
    nro_cbte = 64
    cod_caracter = 5
    fecha_inicio_act = ("2016-01-01",)
    iibb = "123456789"
    nro_ruca = 305
    nro_renspa = None
    agregado = wslsp.AgregarEmisor(
        tipo_cbte,
        pto_vta,
        nro_cbte,
        cod_caracter,
        fecha_inicio_act,
        iibb,
        nro_ruca,
        nro_renspa,
    )
    assert agregado


def test_agregar_receptor():
    """Test agregar receptor."""
    agregado = wslsp.AgregarReceptor(cod_caracter=3)
    assert agregado


def test_agregar_operador():
    """Test agregar operador."""
    cuit = 30160000011
    iibb = 3456
    nro_renspa = "22.123.1.12345/A4"
    agregado = wslsp.AgregarOperador(cuit, iibb, nro_renspa)
    assert agregado


def test_agregar_item_detalle():
    """Test agregar item detalle."""
    cuit_cliente = "20160000199"
    cod_categoria = 51020102
    tipo_liquidacion = 1
    cantidad = 2
    precio_unitario = 10.0
    alicuota_iva = 10.5
    cod_raza = 1
    cantidad_cabezas = None
    nro_tropa = None
    cod_corte = None
    cantidad_kg_vivo = None
    precio_recupero = None
    detalle_raza = None
    nro_item = 1
    agregado = wslsp.AgregarItemDetalle(
        cuit_cliente,
        cod_categoria,
        tipo_liquidacion,
        cantidad,
        precio_unitario,
        alicuota_iva,
        cod_raza,
        cantidad_cabezas,
        nro_tropa,
        cod_corte,
        cantidad_kg_vivo,
        precio_recupero,
        detalle_raza,
        nro_item,
    )

    assert agregado


def test_agregar_compra_asociada():
    """Test agregar compra asociada."""
    tipo_cbte = 185
    pto_vta = 3000
    nro_cbte = 33
    cant_asoc = 2
    nro_item = 1
    agregado = wslsp.AgregarCompraAsociada(
        tipo_cbte, pto_vta, nro_cbte, cant_asoc, nro_item
    )
    assert agregado


def test_agregar_gasto():
    """Test agregar gasto."""
    cod_gasto = 99
    base_imponible = None
    alicuota = 1
    alicuota_iva = (0,)
    descripcion = "Exento WSLSPv1.4.1"
    tipo_iva_nulo = "EX"
    agregado = wslsp.AgregarGasto(
        cod_gasto, base_imponible, alicuota, alicuota_iva, descripcion, tipo_iva_nulo
    )
    assert agregado


def test_agregar_tributo():
    """Test agregar tributo."""
    cod_tributo = 5
    base_imponible = 230520.60
    alicuota = 2.5
    agregado = wslsp.AgregarTributo(cod_tributo, base_imponible, alicuota)
    assert agregado


def test_agregar_dte():
    """Test agregar dte."""
    nro_dte = "418-3"
    nro_renspa = None
    agregado = wslsp.AgregarDTE(nro_dte, nro_renspa)
    assert agregado


def test_agregar_guia():
    """Test agregar guia."""
    agregado = wslsp.AgregarGuia(nro_guia=1)
    assert agregado


def test_autorizar_liquidacion():
    """Test autorizar liquidacion."""
    # autorizado = wslsp.AutorizarLiquidacion()
    # assert autorizado
    # afip esta pidiendo DTe validos
    pass


def test_analizar_liquidacion():
    """Test analizar liquidacion."""
    # assert
    # Metodo utilizado con Autorizar liquidacion
    pass


def test_consultar_liquidacion():
    """Test consultar liquidacion."""
    tipo_cbte = 180
    pto_vta = 3000
    nro_cbte = 1
    cuit = None
    consulta = wslsp.ConsultarLiquidacion(
        tipo_cbte, pto_vta, nro_cbte, cuit_comprador=cuit
    )
    assert consulta


def test_consultar_ultimo_comprobante():
    """Test consultar ultimo comprobante."""
    tipo_cbte = 27
    pto_vta = 1
    consulta = wslsp.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
    assert consulta


def test_crear_ajuste():
    """Test crear ajuste."""
    tipo_ajuste = "C"
    fecha_cbte = "2019-01-06"
    datos_adicionales = "Ajuste sobre liquidacion de compra directa"
    ajuste = wslsp.CrearAjuste(tipo_ajuste, fecha_cbte, datos_adicionales)
    assert ajuste


def test_agregar_comprobante_a_ajustar():
    """Test agregar comprobante a ajustar."""
    tipo_cbte = 186
    pto_vta = 2000
    nro_cbte = 4
    agregado = wslsp.AgregarComprobanteAAjustar(tipo_cbte, pto_vta, nro_cbte)
    assert agregado


def test_agregar_item_detalle_ajuste():
    """Test agregar item detalle ajuste ."""
    agregado = wslsp.AgregarItemDetalleAjuste(nro_item_ajustar=1)
    assert agregado


def test_agregar_ajuste_fisico():
    """Test agregar ajuste fisico."""
    cantidad = 1
    cantidad_cabezas = None
    cantidad_kg_vivo = None
    agregado = wslsp.AgregarAjusteFisico(cantidad, cantidad_cabezas, cantidad_kg_vivo)
    assert agregado


def test_agregar_ajuste_monetario():
    """Test agregar ajuste monetario."""
    precio_unitario = 15.995
    precio_recupero = None
    agregado = wslsp.AgregarAjusteMonetario(precio_unitario, precio_recupero)
    assert agregado


def test_agregar_ajuste_financiero():
    """Test agregar ajuste financiero."""
    agregado = wslsp.AgregarAjusteFinanciero()
    assert agregado


def test_ajustar_liquidacion():
    """Test ajustar liquidacion."""
    ajuste = wslsp.AjustarLiquidacion()
    assert ajuste


def test_consultar_provincias():
    """Test consultar provincias."""
    consulta = wslsp.ConsultarProvincias()
    assert consulta


def test_consultar_localidades():
    """Test consultar localidades."""
    consulta = wslsp.ConsultarLocalidades(cod_provincia=1)
    assert consulta


def test_consultar_operaciones():
    """Test consultar operaciones."""
    consulta = wslsp.ConsultarOperaciones()
    assert consulta


def test_consultar_tributos():
    """Test consultar tributos."""
    consulta = wslsp.ConsultarTributos()
    assert consulta


def test_consultar_gastos():
    """Test consultar gastos."""
    consulta = wslsp.ConsultarGastos()
    assert consulta


def test_consultar_tipos_comprobante():
    """Test consultar tipos comprobantes."""
    consulta = wslsp.ConsultarTiposComprobante()
    assert consulta


def test_consultar_tipos_liquidacion():
    """Test consultar tipoe liquidacion."""
    consulta = wslsp.ConsultarTiposLiquidacion()
    assert consulta


def test_consultar_caracteres():
    """Test consultar caracteres."""
    consulta = wslsp.ConsultarCaracteres()
    assert consulta


def test_consultar_categorias():
    """Test consultar categorias."""
    consulta = wslsp.ConsultarCategorias()
    assert consulta


def test_consultar_motivos():
    """Test consultar motivos."""
    consulta = wslsp.ConsultarMotivos()
    assert consulta


def test_consultar_razas():
    """Test consultar razas."""
    consulta = wslsp.ConsultarRazas()
    assert consulta


def test_consultar_cortes():
    """Test consultar cortes."""
    consulta = wslsp.ConsultarCortes()
    assert consulta


def test_consultar_puntos_ventas():
    """Test consultar puntos de venta."""
    consulta = wslsp.ConsultarPuntosVentas()
    assert consulta


def test_mostrar_pdf():
    """Test mostrar pdf."""
    show = wslsp.MostrarPDF(archivo="liq.pdf", imprimir=True)
    assert show is False
