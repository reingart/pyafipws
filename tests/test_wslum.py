# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Test para Módulo WSLUM para obtener código de autorización
electrónica (CAE) Liquidación Única Mensual (lechería).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os

from pyafipws.wsaa import WSAA
from pyafipws.wslum import WSLUM


WSDL = "https://fwshomo.afip.gov.ar/wslum/LumService?wsdl"
CUIT = os.environ['CUIT']
CERT = 'rei.crt'
PKEY = 'rei.key'
CACHE = ""

# obteniendo el TA para pruebas
wsaa = WSAA()
wslum = WSLUM()
ta = wsaa.Autenticar("wslum", CERT, PKEY)
wslum.Cuit = CUIT
wslum.SetTicketAcceso(ta)


def test_conectar():
    """Conectar con servidor."""
    conexion = wslum.Conectar(CACHE, WSDL)
    assert conexion


def test_server_status():
    """Test de estado de servidores."""
    wslum.Dummy()
    assert wslum.AppServerStatus == 'OK'
    assert wslum.DbServerStatus == 'OK'
    assert wslum.AuthServerStatus == 'OK'


def test_inicializar():
    """Test inicializar variables de BaseWS."""
    wslum.inicializar()
    assert wslum.Total is None
    assert wslum.FechaComprobante == ''


def test___analizar_errores():
    """Test Analizar si se encuentran errores en clientes."""
    ret = {'numeroComprobante': 286}
    wslum._WSLUM__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wslum.ErrMsg == ''


def test_crear_liquidacion():
    """Test solicitud de liquidacion."""
    tipo_cbte = 27
    pto_vta = 1
    nro_cbte = 1
    fecha = "2015-12-31"
    periodo = "2015/12"
    iibb_adquirente = "123456789012345"
    domicilio_sede = "Domicilio Administrativo"
    inscripcion_registro_publico = "Nro IGJ"
    datos_adicionales = "Datos Adicionales Varios"
    alicuota_iva = 21.00
    liquidacion = wslum.CrearLiquidacion(tipo_cbte, pto_vta, nro_cbte,
                                         fecha, periodo,
                                         iibb_adquirente,
                                         domicilio_sede,
                                         inscripcion_registro_publico,
                                         datos_adicionales,
                                         alicuota_iva)
    assert liquidacion


def test_agregar_condicion_venta():
    """Test condiciones de venta."""
    codigo = 1
    descripcion = None
    agregado = wslum.AgregarCondicionVenta(codigo, descripcion)
    assert agregado


def test_agregar_tambero():
    """Test agrega tambero."""
    cuit = 11111111111
    iibb = "123456789012345"
    agregado = wslum.AgregarTambero(cuit, iibb)
    assert agregado


def test_agregar_tambo():
    """Test agregar tambo."""
    nro_tambo_interno = 123456789
    nro_renspa = "12.345.6.78901/12"
    fecha_venc_cert_tuberculosis = "2015-01-01"
    fecha_venc_cert_brucelosis = "2015-01-01"
    nro_tambo_provincial = 100000000
    agregado = wslum.AgregarTambo(nro_tambo_interno,
                                  nro_renspa,
                                  fecha_venc_cert_tuberculosis,
                                  fecha_venc_cert_brucelosis,
                                  nro_tambo_provincial)
    assert agregado


def test_agregar_ubicacion_tambo():
    """Test agregar ubicacion del tambo."""
    latitud = -34.62987
    longitud = -58.65155
    domicilio = "Domicilio Tambo"
    cod_localidad = 10109
    cod_provincia = 1
    codigo_postal = 1234
    nombre_partido_depto = 'Partido Tambo'
    agregado = wslum.AgregarUbicacionTambo(latitud, longitud,
                                           domicilio,
                                           cod_localidad, cod_provincia,
                                           codigo_postal,
                                           nombre_partido_depto)
    assert agregado


def test_agregar_balance_litros_porcentajes_solidos():
    """Test agregar balance de litros y porcentage de solidos."""
    litros_remitidos = 11000
    litros_decomisados = 1000
    kg_grasa = 100.00
    kg_proteina = 100.00
    agregado = wslum.AgregarBalanceLitrosPorcentajesSolidos(litros_remitidos,
                                                            litros_decomisados,
                                                            kg_grasa, kg_proteina)
    # No return
    assert agregado is None
    assert isinstance(wslum.solicitud, dict)


def test_agregar_conceptos_basicos_mercado_interno():
    """Test agregar conceptos basicos mercado interno."""
    kg_produccion_gb = 100
    precio_por_kg_produccion_gb = 5.00
    kg_produccion_pr = 100
    precio_por_kg_produccion_pr = 5.00
    kg_crecimiento_gb = 0
    precio_por_kg_crecimiento_gb = 0.00
    kg_crecimiento_pr = 0
    precio_por_kg_crecimiento_pr = 0.00
    agregado = wslum.AgregarConceptosBasicosMercadoInterno(
                    kg_produccion_gb, precio_por_kg_produccion_gb,
                    kg_produccion_pr, precio_por_kg_produccion_pr,
                    kg_crecimiento_gb, precio_por_kg_crecimiento_gb,
                    kg_crecimiento_pr, precio_por_kg_crecimiento_pr)
    assert agregado


def test_agregar_conceptos_basicos_mercado_externo():
    """Test agregar conceptos basicos de mercado externo."""
    kg_produccion_gb = 0
    precio_por_kg_produccion_gb = 0
    kg_produccion_pr = 0
    precio_por_kg_produccion_pr = 0
    kg_crecimiento_gb = 0
    precio_por_kg_crecimiento_gb = 0.00
    kg_crecimiento_pr = 0
    precio_por_kg_crecimiento_pr = 0.00
    agregado = wslum.AgregarConceptosBasicosMercadoInterno(
                    kg_produccion_gb, precio_por_kg_produccion_gb,
                    kg_produccion_pr, precio_por_kg_produccion_pr,
                    kg_crecimiento_gb, precio_por_kg_crecimiento_gb,
                    kg_crecimiento_pr, precio_por_kg_crecimiento_pr)
    assert agregado


def test_agregar_bonificacion_penalizacion():
    """test agregar bonificacion o penalizacion."""
    codigo = 1
    detalle = "opcional"
    resultado = "400"
    porcentaje = 10.00
    agregado = wslum.AgregarBonificacionPenalizacion(codigo, detalle,
                                                     resultado, porcentaje)
    assert agregado


def test_agregar_otro_impuesto():
    """Test agregar otro impuesto."""
    tipo = 1
    base_imponible = 100.00
    alicuota = 10.00
    detalle = ""
    agregado = wslum.AgregarOtroImpuesto(tipo, base_imponible,
                                         alicuota, detalle)
    assert agregado


def test_agregar_remito():
    """Test agregar remito."""
    nro_remito = "123456789012"
    agregado = wslum.AgregarRemito(nro_remito)
    assert agregado


def test_autorizar_liquidacion():
    """Test autorizar liquidacion."""
    autorizado = wslum.AutorizarLiquidacion()
    assert autorizado


def test_analizar_liquidacion():
    """Test analizar liquidacion."""
    # Funciona en conjunto con AutorizarLiquidacion
    pass


def test_agregar_ajuste():
    """Test agregar ajuste."""
    cai = "10000000000000",
    tipo_cbte = 0
    pto_vta = 0
    nro_cbte = 0
    cae_a_ajustar = "75521002437246"
    agregado = wslum.AgregarAjuste(cai, tipo_cbte, pto_vta,
                                   nro_cbte, cae_a_ajustar)
    assert agregado


def test_consultar_liquidacion():
    """Test consultar Liquidacion."""
    tipo_cbte = 27
    pto_vta = 1
    nro_cbte = 0
    cuit = None
    consulta = wslum.ConsultarLiquidacion(tipo_cbte, pto_vta, nro_cbte,
                                          cuit_comprador=cuit)
    assert consulta


def test_consultar_ultimo_comprobante():
    """Test consultar ultimo comprobante."""
    tipo_cbte = 1
    pto_vta = 4000
    consulta = wslum.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
    assert consulta


def test_consultar_provincias():
    """Test consultar provincias."""
    consulta = wslum.ConsultarProvincias()
    assert consulta


def test_consultar_localidades():
    """Test consultar localidades."""
    cod_provincia = 1
    consulta = wslum.ConsultarLocalidades(cod_provincia)
    assert consulta

# No funciona-no existe el metodo en el web service
# def test_consultar_condiciones_venta():
#    """Test consulta de condiciones de venta."""
#    consulta = wslum.ConsultarCondicionesVenta()
#    assert consulta


def test_consultar_otros_impuestos():
    """Test consultar otros impuestos."""
    consulta = wslum.ConsultarOtrosImpuestos()
    assert consulta


def test_consultar_bonificaciones_penalizaciones():
    """Test consultar bonificaciones y penalizaciones."""
    consulta = wslum.ConsultarBonificacionesPenalizaciones()
    assert consulta


def test_consultar_puntos_ventas():
    """Test consultar punto de venta."""
    consulta = wslum.ConsultarPuntosVentas()
    assert consulta


def test_mostrar_pdf():
    """Test mostrar pdf."""
    archivo = 'nota'
    imprimir = False
    pdf_ok = wslum.MostrarPDF(archivo, imprimir)
    assert pdf_ok is False
