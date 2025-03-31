#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.

"Módulo para generar PDF de facturas electrónicas"
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from builtins import input
from builtins import str
from builtins import range
from past.builtins import basestring
from builtins import object
from past.utils import old_div

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011-2025 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.12c"

DEBUG = False
HOMO = False
CONFIG_FILE = "rece.ini"

LICENCIA = u"""
pyfepdf.py: Interfaz para generar Facturas Electrónica en formato PDF
Copyright (C) 2011-2015 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA = u"""
Opciones: 
  --ayuda: este mensaje
  --licencia: muestra la licencia del programa

  --debug: modo depuración (detalla y confirma las operaciones)
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una factura de prueba (no usar en producción!)
  --cargar: carga un archivo de entrada (txt) a la base de datos
  --grabar: graba un archivo de salida (txt) con los datos de los comprobantes procesados
  --pdf: genera la imágen de factura en PDF
  --dbf: utiliza tablas DBF en lugar del archivo de entrada TXT
  --json: utiliza el formato JSON para el archivo de entrada

Ver rece.ini para parámetros de configuración "
"""
import datetime
import decimal
import os
import sys
import tempfile
import traceback
from io import StringIO
from decimal import Decimal
from fpdf import Template
from pyafipws import utils


class FEPDF(object):
    "Interfaz para generar PDF de Factura Electrónica"
    _public_methods_ = [
        "CrearFactura",
        "AgregarDetalleItem",
        "AgregarIva",
        "AgregarTributo",
        "AgregarCmpAsoc",
        "AgregarPermiso",
        "AgregarDato",
        "EstablecerParametro",
        "CargarFormato",
        "AgregarCampo",
        "CrearPlantilla",
        "ProcesarPlantilla",
        "GenerarPDF",
        "MostrarPDF",
        "GenerarQR",
    ]
    _public_attrs_ = [
        "Version",
        "Excepcion",
        "Traceback",
        "InstallDir",
        "Locale",
        "FmtCantidad",
        "FmtPrecio",
        "CUIT",
        "TipoCodAut",
        "LanzarExcepciones",
        "archivo_qr",
    ]

    _reg_progid_ = "PyFEPDF"
    _reg_clsid_ = "{C9B5D7BB-0388-4A5E-87D5-0B4376C7A336}"

    tipos_doc = {
        80: "CUIT",
        86: "CUIL",
        96: "DNI",
        99: "",
        87: u"CDI",
        89: u"LE",
        90: u"LC",
        91: u"CI Extranjera",
        92: u"en trámite",
        93: u"Acta Nacimiento",
        94: u"Pasaporte",
        95: u"CI Bs. As. RNP",
        0: u"CI Policía Federal",
        1: u"CI Buenos Aires",
        2: u"CI Catamarca",
        3: u"CI Córdoba",
        4: u"CI Corrientes",
        5: u"CI Entre Ríos",
        6: u"CI Jujuy",
        7: u"CI Mendoza",
        8: u"CI La Rioja",
        9: u"CI Salta",
        10: u"CI San Juan",
        11: u"CI San Luis",
        12: u"CI Santa Fe",
        13: u"CI Santiago del Estero",
        14: u"CI Tucumán",
        16: u"CI Chaco",
        17: u"CI Chubut",
        18: u"CI Formosa",
        19: u"CI Misiones",
        20: u"CI Neuquén",
        21: u"CI La Pampa",
        22: u"CI Río Negro",
        23: u"CI Santa Cruz",
        24: u"CI Tierra del Fuego",
    }

    umeds_ds = {
        0: "",
        1: u"kg",
        2: u"m",
        3: u"m2",
        4: u"m3",
        5: u"l",
        6: u"1000 kWh",
        7: u"u",
        8: u"pares",
        9: u"docenas",
        10: u"quilates",
        11: u"millares",
        14: u"g",
        15: u"mm",
        16: u"mm3",
        17: u"km",
        18: u"hl",
        20: u"cm",
        25: u"jgo. pqt. mazo naipes",
        27: u"cm3",
        29: u"tn",
        30: u"dam3",
        31: u"hm3",
        32: u"km3",
        33: u"ug",
        34: u"ng",
        35: u"pg",
        41: u"mg",
        47: u"mm",
        48: u"curie",
        49: u"milicurie",
        50: u"microcurie",
        51: u"uiacthor",
        52: u"muiacthor",
        53: u"kg base",
        54: u"gruesa",
        61: u"kg bruto",
        62: u"uiactant",
        63: u"muiactant",
        64: u"uiactig",
        65: u"muiactig",
        66: u"kg activo",
        67: u"gramo activo",
        68: u"gramo base",
        96: u"packs",
        97: u"hormas",
        96: u"packs",
        97: u"seña/anticipo",
        99: u"bonificaci\xf3n",
        98: u"otras unidades",
    }

    ivas_ds = {3: 0, 4: 10.5, 5: 21, 6: 27, 8: 5, 9: 2.5}

    paises = {
        512: u"FIJI, ISLAS",
        513: u"PAPUA NUEVA GUINEA",
        514: u"KIRIBATI, ISLAS",
        515: u"MICRONESIA,EST.FEDER",
        516: u"PALAU",
        517: u"TUVALU",
        518: u"SALOMON,ISLAS",
        519: u"TONGA",
        520: u"MARSHALL,ISLAS",
        521: u"MARIANAS,ISLAS",
        597: u"RESTO OCEANIA",
        598: u"INDET.(OCEANIA)",
        101: u"BURKINA FASO",
        102: u"ARGELIA",
        103: u"BOTSWANA",
        104: u"BURUNDI",
        105: u"CAMERUN",
        107: u"REP. CENTROAFRICANA.",
        108: u"CONGO",
        109: u"REP.DEMOCRAT.DEL CONGO EX ZAIRE",
        110: u"COSTA DE MARFIL",
        111: u"CHAD",
        112: u"BENIN",
        113: u"EGIPTO",
        115: u"GABON",
        116: u"GAMBIA",
        117: u"GHANA",
        118: u"GUINEA",
        119: u"GUINEA ECUATORIAL",
        120: u"KENYA",
        121: u"LESOTHO",
        122: u"LIBERIA",
        123: u"LIBIA",
        124: u"MADAGASCAR",
        125: u"MALAWI",
        126: u"MALI",
        127: u"MARRUECOS",
        128: u"MAURICIO,ISLAS",
        129: u"MAURITANIA",
        130: u"NIGER",
        131: u"NIGERIA",
        132: u"ZIMBABWE",
        133: u"RWANDA",
        134: u"SENEGAL",
        135: u"SIERRA LEONA",
        136: u"SOMALIA",
        137: u"SWAZILANDIA",
        138: u"SUDAN",
        139: u"TANZANIA",
        140: u"TOGO",
        141: u"TUNEZ",
        142: u"UGANDA",
        144: u"ZAMBIA",
        145: u"TERRIT.VINCULADOS AL R UNIDO",
        146: u"TERRIT.VINCULADOS A ESPA\xd1A",
        147: u"TERRIT.VINCULADOS A FRANCIA",
        149: u"ANGOLA",
        150: u"CABO VERDE",
        151: u"MOZAMBIQUE",
        152: u"SEYCHELLES",
        153: u"DJIBOUTI",
        155: u"COMORAS",
        156: u"GUINEA BISSAU",
        157: u"STO.TOME Y PRINCIPE",
        158: u"NAMIBIA",
        159: u"SUDAFRICA",
        160: u"ERITREA",
        161: u"ETIOPIA",
        197: u"RESTO (AFRICA)",
        198: u"INDETERMINADO (AFRICA)",
        200: u"ARGENTINA",
        201: u"BARBADOS",
        202: u"BOLIVIA",
        203: u"BRASIL",
        204: u"CANADA",
        205: u"COLOMBIA",
        206: u"COSTA RICA",
        207: u"CUBA",
        208: u"CHILE",
        209: u"REP\xdaBLICA DOMINICANA",
        210: u"ECUADOR",
        211: u"EL SALVADOR",
        212: u"ESTADOS UNIDOS",
        213: u"GUATEMALA",
        214: u"GUYANA",
        215: u"HAITI",
        216: u"HONDURAS",
        217: u"JAMAICA",
        218: u"MEXICO",
        219: u"NICARAGUA",
        220: u"PANAMA",
        221: u"PARAGUAY",
        222: u"PERU",
        223: u"PUERTO RICO",
        224: u"TRINIDAD Y TOBAGO",
        225: u"URUGUAY",
        226: u"VENEZUELA",
        227: u"TERRIT.VINCULADO AL R.UNIDO",
        228: u"TER.VINCULADOS A DINAMARCA",
        229: u"TERRIT.VINCULADOS A FRANCIA AMERIC.",
        230: u"TERRIT. HOLANDESES",
        231: u"TER.VINCULADOS A ESTADOS UNIDOS",
        232: u"SURINAME",
        233: u"DOMINICA",
        234: u"SANTA LUCIA",
        235: u"SAN VICENTE Y LAS GRANADINAS",
        236: u"BELICE",
        237: u"ANTIGUA Y BARBUDA",
        238: u"S.CRISTOBAL Y NEVIS",
        239: u"BAHAMAS",
        240: u"GRENADA",
        241: u"ANTILLAS HOLANDESAS",
        250: u"AAE Tierra del Fuego - ARGENTINA",
        251: u"ZF La Plata - ARGENTINA",
        252: u"ZF Justo Daract - ARGENTINA",
        253: u"ZF R\xedo Gallegos - ARGENTINA",
        254: u"Islas Malvinas - ARGENTINA",
        255: u"ZF Tucum\xe1n - ARGENTINA",
        256: u"ZF C\xf3rdoba - ARGENTINA",
        257: u"ZF Mendoza - ARGENTINA",
        258: u"ZF General Pico - ARGENTINA",
        259: u"ZF Comodoro Rivadavia - ARGENTINA",
        260: u"ZF Iquique",
        261: u"ZF Punta Arenas",
        262: u"ZF Salta - ARGENTINA",
        263: u"ZF Paso de los Libres - ARGENTINA",
        264: u"ZF Puerto Iguaz\xfa - ARGENTINA",
        265: u"SECTOR ANTARTICO ARG.",
        270: u"ZF Col\xf3n - REP\xdaBLICA DE PANAM\xc1",
        271: u"ZF Winner (Sta. C. de la Sierra) - BOLIVIA",
        280: u"ZF Colonia - URUGUAY",
        281: u"ZF Florida - URUGUAY",
        282: u"ZF Libertad - URUGUAY",
        283: u"ZF Zonamerica - URUGUAY",
        284: u"ZF Nueva Helvecia - URUGUAY",
        285: u"ZF Nueva Palmira - URUGUAY",
        286: u"ZF R\xedo Negro - URUGUAY",
        287: u"ZF Rivera - URUGUAY",
        288: u"ZF San Jos\xe9 - URUGUAY",
        291: u"ZF Manaos - BRASIL",
        295: u"MAR ARG ZONA ECO.EX",
        296: u"RIOS ARG NAVEG INTER",
        297: u"RESTO AMERICA",
        298: u"INDETERMINADO (AMERICA)",
        301: u"AFGANISTAN",
        302: u"ARABIA SAUDITA",
        303: u"BAHREIN",
        304: u"MYANMAR (EX-BIRMANIA)",
        305: u"BUTAN",
        306: u"CAMBODYA (EX-KAMPUCHE)",
        307: u"SRI LANKA",
        308: u"COREA DEMOCRATICA",
        309: u"COREA REPUBLICANA",
        310: u"CHINA",
        312: u"FILIPINAS",
        313: u"TAIWAN",
        315: u"INDIA",
        316: u"INDONESIA",
        317: u"IRAK",
        318: u"IRAN",
        319: u"ISRAEL",
        320: u"JAPON",
        321: u"JORDANIA",
        322: u"QATAR",
        323: u"KUWAIT",
        324: u"LAOS",
        325: u"LIBANO",
        326: u"MALASIA",
        327: u"MALDIVAS ISLAS",
        328: u"OMAN",
        329: u"MONGOLIA",
        330: u"NEPAL",
        331: u"EMIRATOS ARABES UNIDOS",
        332: u"PAKIST\xc1N",
        333: u"SINGAPUR",
        334: u"SIRIA",
        335: u"THAILANDIA",
        337: u"VIETNAM",
        341: u"HONG KONG",
        344: u"MACAO",
        345: u"BANGLADESH",
        346: u"BRUNEI",
        348: u"REPUBLICA DE YEMEN",
        349: u"ARMENIA",
        350: u"AZERBAIJAN",
        351: u"GEORGIA",
        352: u"KAZAJSTAN",
        353: u"KIRGUIZISTAN",
        354: u"TAYIKISTAN",
        355: u"TURKMENISTAN",
        356: u"UZBEKISTAN",
        357: u"TERR. AU. PALESTINOS",
        397: u"RESTO DE ASIA",
        398: u"INDET.(ASIA)",
        401: u"ALBANIA",
        404: u"ANDORRA",
        405: u"AUSTRIA",
        406: u"BELGICA",
        407: u"BULGARIA",
        409: u"DINAMARCA",
        410: u"ESPA\xd1A",
        411: u"FINLANDIA",
        412: u"FRANCIA",
        413: u"GRECIA",
        414: u"HUNGRIA",
        415: u"IRLANDA",
        416: u"ISLANDIA",
        417: u"ITALIA",
        418: u"LIECHTENSTEIN",
        419: u"LUXEMBURGO",
        420: u"MALTA",
        421: u"MONACO",
        422: u"NORUEGA",
        423: u"PAISES BAJOS",
        424: u"POLONIA",
        425: u"PORTUGAL",
        426: u"REINO UNIDO",
        427: u"RUMANIA",
        428: u"SAN MARINO",
        429: u"SUECIA",
        430: u"SUIZA",
        431: u"VATICANO(SANTA SEDE)",
        433: u"POS.BRIT.(EUROPA)",
        435: u"CHIPRE",
        436: u"TURQUIA",
        438: u"ALEMANIA,REP.FED.",
        439: u"BIELORRUSIA",
        440: u"ESTONIA",
        441: u"LETONIA",
        442: u"LITUANIA",
        443: u"MOLDAVIA",
        444: u"RUSIA",
        445: u"UCRANIA",
        446: u"BOSNIA HERZEGOVINA",
        447: u"CROACIA",
        448: u"ESLOVAQUIA",
        449: u"ESLOVENIA",
        450: u"MACEDONIA",
        451: u"REP. CHECA",
        453: u"MONTENEGRO",
        454: u"SERBIA",
        997: u"RESTO CONTINENTE",
        998: u"INDET.(CONTINENTE)",
        497: u"RESTO EUROPA",
        498: u"INDET.(EUROPA)",
        501: u"AUSTRALIA",
        503: u"NAURU",
        504: u"NUEVA ZELANDIA",
        505: u"VANATU",
        506: u"SAMOA OCCIDENTAL",
        507: u"TERRITORIO VINCULADOS A AUSTRALIA",
        508: u"TERRITORIOS VINCULADOS AL R. UNIDO",
        509: u"TERRITORIOS VINCULADOS A FRANCIA",
        510: u"TER VINCULADOS A NUEVA. ZELANDA",
        511: u"TER. VINCULADOS A ESTADOS UNIDOS",
    }

    monedas_ds = {
        "DOL": u"USD: Dólar",
        "PES": u"ARS: Pesos",
        "010": u"MXN: Pesos Mejicanos",
        "011": u"UYU: Pesos Uruguayos",
        "012": u"BRL: Real",
        "014": u"Coronas Danesas",
        "015": u"Coronas Noruegas",
        "016": u"Coronas Suecas",
        "019": u"JPY: Yens",
        "018": u"CAD: D\xf3lar Canadiense",
        "033": u"CLP: Peso Chileno",
        "056": u"Forint (Hungr\xeda)",
        "031": u"BOV: Peso Boliviano",
        "036": u"Sucre Ecuatoriano",
        "051": u"D\xf3lar de Hong Kong",
        "034": u"Rand Sudafricano",
        "053": u"D\xf3lar de Jamaica",
        "057": u"Baht (Tailandia)",
        "043": u"Balboas Paname\xf1as",
        "042": u"Peso Dominicano",
        "052": u"D\xf3lar de Singapur",
        "032": u"Peso Colombiano",
        "035": u"Nuevo Sol Peruano",
        "061": u"Zloty Polaco",
        "060": u"EUR: Euro",
        "063": u"Lempira Hondure\xf1a",
        "062": u"Rupia Hind\xfa",
        "064": u"Yuan (Rep. Pop. China)",
        "009": u"Franco Suizo",
        "025": u"Dinar Yugoslavo",
        "002": u"USD: D\xf3lar Libre EEUU",
        "027": u"Dracma Griego",
        "026": u"D\xf3lar Australiano",
        "007": u"Florines Holandeses",
        "023": u"VEB: Bol\xedvar Venezolano",
        "047": u"Riyal Saudita",
        "046": u"Libra Egipcia",
        "045": u"Dirham Marroqu\xed",
        "044": u"C\xf3rdoba Nicarag\xfcense",
        "029": u"G\xfcaran\xed",
        "028": u"Flor\xedn (Antillas Holandesas)",
        "054": u"D\xf3lar de Taiwan",
        "040": u"Lei Rumano",
        "024": u"Corona Checa",
        "030": u"Shekel (Israel)",
        "021": u"Libra Esterlina",
        "055": u"Quetzal Guatemalteco",
        "059": u"Dinar Kuwaiti",
    }

    tributos_ds = {
        1: "Impuestos nacionales",
        2: "Impuestos provinciales",
        3: "Impuestos municipales",
        4: "Impuestos Internos",
        99: "Otro",
    }

    tipos_fact = {
        (1, 6, 11, 19, 51): u"Factura",
        (2, 7, 12, 20, 52): u"Nota de Débito",
        (3, 8, 13, 21, 53): u"Nota de Crédito",
        (201, 206, 211): u"Factura de Crédito electrónica MiPyMEs (FCE)",
        (202, 207, 212): u"Nota de Débito electrónica MiPyMEs (FCE)",
        (203, 208, 213): u"Nota de Crédito electrónica MiPyMEs (FCE)",
        (4, 9, 15, 54): u"Recibo",
        (10, 5): u"Nota de Venta al contado",
        (60, 61): u"Cuenta de Venta y Líquido producto",
        (63, 64): u"Liquidación",
        (91,): u"Remito",
        (39, 40): u"???? (R.G. N° 3419)",
    }

    letras_fact = {
        (1, 2, 3, 4, 5, 39, 60, 63, 201, 202, 203): "A",
        (6, 7, 8, 9, 10, 40, 61, 64, 206, 207, 208): "B",
        (11, 12, 13, 15, 211, 212, 213): "C",
        (51, 52, 53, 54): "M",
        (19, 20, 21): "E",
        (91,): "R",
    }

    def __init__(self):
        self.Version = __version__
        self.factura = None
        self.Exception = self.Traceback = ""
        self.InstallDir = INSTALL_DIR
        if sys.platform == "win32":
            self.Locale = "Spanish_Argentina.1252"
        elif sys.platform == "linux2":
            self.Locale = "es_AR.utf8"
        else:
            # plataforma no soportada aun (jython?), emular
            self.Locale = None
        self.FmtCantidad = self.FmtPrecio = "0.2"
        self.CUIT = ""
        self.factura = {}
        self.datos = []
        self.elements = []
        self.pdf = {}
        self.log = StringIO()
        # sys.stdout = self.log
        # sys.stderr = self.log
        self.LanzarExcepciones = True
        self.archivo_qr = None
        self.TipoCodAut = "E"

    def DebugLog(self):
        "Devolver bitácora de depuración"
        msg = self.log.getvalue()
        return msg

    def inicializar(self):
        self.Excepcion = self.Traceback = ""

    @utils.inicializar_y_capturar_excepciones_simple
    def CrearFactura(
        self,
        concepto=1,
        tipo_doc=80,
        nro_doc="",
        tipo_cbte=1,
        punto_vta=0,
        cbte_nro=0,
        imp_total=0.00,
        imp_tot_conc=0.00,
        imp_neto=0.00,
        imp_iva=0.00,
        imp_trib=0.00,
        imp_op_ex=0.00,
        fecha_cbte="",
        fecha_venc_pago="",
        fecha_serv_desde=None,
        fecha_serv_hasta=None,
        moneda_id="PES",
        moneda_ctz="1.0000",
        cae="",
        fch_venc_cae="",
        id_impositivo="",
        nombre_cliente="",
        domicilio_cliente="",
        pais_dst_cmp=None,
        obs_comerciales="",
        obs_generales="",
        forma_pago="",
        incoterms="",
        idioma_cbte=7,
        motivos_obs="",
        descuento=0.0,
        **kwargs
    ):
        "Creo un objeto factura (internamente)"
        fact = {
            "tipo_doc": tipo_doc,
            "nro_doc": nro_doc,
            "tipo_cbte": tipo_cbte,
            "punto_vta": punto_vta,
            "cbte_nro": cbte_nro,
            "imp_total": imp_total,
            "imp_tot_conc": imp_tot_conc,
            "imp_neto": imp_neto,
            "imp_iva": imp_iva,
            "imp_trib": imp_trib,
            "imp_op_ex": imp_op_ex,
            "fecha_cbte": fecha_cbte,
            "fecha_venc_pago": fecha_venc_pago,
            "moneda_id": moneda_id,
            "moneda_ctz": moneda_ctz,
            "concepto": concepto,
            "nombre_cliente": nombre_cliente,
            "domicilio_cliente": domicilio_cliente,
            "pais_dst_cmp": pais_dst_cmp,
            "obs_comerciales": obs_comerciales,
            "obs_generales": obs_generales,
            "id_impositivo": id_impositivo,
            "forma_pago": forma_pago,
            "incoterms": incoterms,
            "cae": cae,
            "fecha_vto": fch_venc_cae,
            "motivos_obs": motivos_obs,
            "descuento": descuento,
            "cbtes_asoc": [],
            "tributos": [],
            "ivas": [],
            "permisos": [],
            "detalles": [],
        }
        if fecha_serv_desde:
            fact["fecha_serv_desde"] = fecha_serv_desde
        if fecha_serv_hasta:
            fact["fecha_serv_hasta"] = fecha_serv_hasta
        self.archivo_qr = None

        self.factura = fact
        return True

    def EstablecerParametro(self, parametro, valor):
        "Modifico un parametro general a la factura (internamente)"
        self.factura[parametro] = valor
        return True

    def AgregarDato(self, campo, valor, pagina="T"):
        "Agrego un dato a la factura (internamente)"
        self.datos.append({"campo": campo, "valor": valor, "pagina": pagina})
        return True

    def AgregarDetalleItem(
        self,
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
        dato_a=None,
        dato_b=None,
        dato_c=None,
        dato_d=None,
        dato_e=None,
    ):
        "Agrego un item a una factura (internamente)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        item = {
            "u_mtx": u_mtx,
            "cod_mtx": cod_mtx,
            "codigo": codigo,
            "ds": ds,
            "qty": qty,
            "umed": umed,
            "precio": precio,
            "bonif": bonif,
            "iva_id": iva_id,
            "imp_iva": imp_iva,
            "importe": importe,
            "despacho": despacho,
            "dato_a": dato_a,
            "dato_b": dato_b,
            "dato_c": dato_c,
            "dato_d": dato_d,
            "dato_e": dato_e,
        }
        self.factura["detalles"].append(item)
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwarg):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {"cbte_tipo": tipo, "cbte_punto_vta": pto_vta, "cbte_nro": nro}
        self.factura["cbtes_asoc"].append(cmp_asoc)
        return True

    def AgregarTributo(
        self, tributo_id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg
    ):
        "Agrego un tributo a una factura (interna)"
        tributo = {
            "tributo_id": tributo_id,
            "desc": desc,
            "base_imp": base_imp,
            "alic": alic,
            "importe": importe,
        }
        self.factura["tributos"].append(tributo)
        return True

    def AgregarIva(self, iva_id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = {"iva_id": iva_id, "base_imp": base_imp, "importe": importe}
        self.factura["ivas"].append(iva)
        return True

    def AgregarPermiso(self, id_permiso, dst_merc, **kwargs):
        "Agrego un permiso a una factura (interna)"
        self.factura["permisos"].append(
            {
                "id_permiso": id_permiso,
                "dst_merc": dst_merc,
            }
        )
        return True

    # funciones de formateo de strings:

    def fmt_date(self, d):
        "Formatear una fecha"
        if not d or len(d) != 8:
            return d or ""
        else:
            return "%s/%s/%s" % (d[6:8], d[4:6], d[0:4])

    def fmt_num(self, i, fmt="%0.2f", monetary=True):
        "Formatear un número"
        if i is not None and str(i) and not isinstance(i, bool):
            loc = self.Locale
            if loc:
                import locale

                locale.setlocale(locale.LC_ALL, loc)
                return locale.format_string(
                    fmt,
                    Decimal(str(i).replace(",", ".")),
                    grouping=True,
                    monetary=monetary,
                )
            else:
                return (fmt % Decimal(str(i).replace(",", "."))).replace(".", ",")
        else:
            return ""

    fmt_imp = lambda self, i: self.fmt_num(i, "%0.2f")
    fmt_qty = lambda self, i: self.fmt_num(i, "%" + self.FmtCantidad + "f", False)
    fmt_pre = lambda self, i: self.fmt_num(i, "%" + self.FmtPrecio + "f")

    def fmt_iva(self, i):
        if int(i) in self.ivas_ds:
            p = self.ivas_ds[int(i)]
            if p == int(p):
                return self.fmt_num(p, "%d") + "%"
            else:
                return self.fmt_num(p, "%.1f") + "%"
        else:
            return ""

    def fmt_cuit(self, c):
        if c is not None and str(c):
            c = str(c)
            return len(c) == 11 and "%s-%s-%s" % (c[0:2], c[2:10], c[10:]) or c
        return ""

    def fmt_fact(self, tipo_cbte, punto_vta, cbte_nro):
        "Formatear tipo, letra y punto de venta y número de factura"
        n = "%05d-%08d" % (int(punto_vta), int(cbte_nro))
        t, l = tipo_cbte, ""
        for k, v in list(self.tipos_fact.items()):
            if int(tipo_cbte) in k:
                t = v
        for k, v in list(self.letras_fact.items()):
            if int(int(tipo_cbte)) in k:
                l = v
        return t, l, n

    def digito_verificador_modulo10(self, codigo):
        "Rutina para el cálculo del dígito verificador 'módulo 10'"
        # http://www.consejo.org.ar/Bib_elect/diciembre04_CT/documentos/rafip1702.htm
        # Etapa 1: comenzar desde la izquierda, sumar todos los caracteres ubicados en las posiciones impares.
        codigo = codigo.strip()
        if not codigo or not codigo.isdigit():
            return ""
        etapa1 = sum([int(c) for i, c in enumerate(codigo) if not i % 2])
        # Etapa 2: multiplicar la suma obtenida en la etapa 1 por el número 3
        etapa2 = etapa1 * 3
        # Etapa 3: comenzar desde la izquierda, sumar todos los caracteres que están ubicados en las posiciones pares.
        etapa3 = sum([int(c) for i, c in enumerate(codigo) if i % 2])
        # Etapa 4: sumar los resultados obtenidos en las etapas 2 y 3.
        etapa4 = etapa2 + etapa3
        # Etapa 5: buscar el menor número que sumado al resultado obtenido en la etapa 4 dé un número múltiplo de 10. Este será el valor del dígito verificador del módulo 10.
        digito = 10 - (etapa4 - (int(old_div(etapa4, 10)) * 10))
        if digito == 10:
            digito = 0
        return str(digito)

    # Funciones públicas:

    @utils.inicializar_y_capturar_excepciones_simple
    def CargarFormato(self, archivo="factura.csv"):
        "Cargo el formato de campos a generar desde una planilla CSV"

        # si no encuentro archivo, lo busco en el directorio predeterminado:
        if not os.path.exists(archivo):
            archivo = os.path.join(
                self.InstallDir, "plantillas", os.path.basename(archivo)
            )

        if DEBUG:
            print("abriendo archivo ", archivo)

        for lno, linea in enumerate(open(archivo.encode("latin1")).readlines()):
            if DEBUG:
                print("procesando linea ", lno, linea)
            args = []
            for i, v in enumerate(linea.split(";")):
                if "\xba" in v:
                    v = v.replace("\xba", "º")
                if not v.startswith("'"):
                    v = v.replace(",", ".")
                else:
                    v = v  # .decode('latin1')
                if v.strip() == "":
                    v = None
                else:
                    v = eval(v.strip())
                args.append(v)
            self.AgregarCampo(*args)
        return True

    @utils.inicializar_y_capturar_excepciones_simple
    def AgregarCampo(
        self,
        nombre,
        tipo,
        x1,
        y1,
        x2,
        y2,
        font="Arial",
        size=12,
        bold=False,
        italic=False,
        underline=False,
        foreground=0x000000,
        background=0xFFFFFF,
        align="L",
        text="",
        priority=0,
        **kwargs
    ):
        "Agrego un campo a la plantilla"
        # convierto colores de string (en hexadecimal)
        if isinstance(foreground, basestring):
            foreground = int(foreground, 16)
        if isinstance(background, basestring):
            background = int(background, 16)
        if isinstance(text, str):
            text = text
        field = {
            "name": nombre,
            "type": tipo,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "font": font,
            "size": size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "foreground": foreground,
            "background": background,
            "align": align,
            "text": text,
            "priority": priority,
        }
        field.update(kwargs)
        self.elements.append(field)
        return True

    @utils.inicializar_y_capturar_excepciones_simple
    def CrearPlantilla(self, papel="A4", orientacion="portrait"):
        "Iniciar la creación del archivo PDF"

        fact = self.factura
        tipo, letra, nro = self.fmt_fact(
            fact["tipo_cbte"], fact["punto_vta"], fact["cbte_nro"]
        )

        if HOMO:
            self.AgregarCampo(
                "homo",
                "T",
                100,
                250,
                0,
                0,
                size=70,
                rotate=45,
                foreground=0x808080,
                priority=-1,
            )

        # sanity check:
        for field in self.elements:
            # si la imagen no existe, eliminar nombre para que no falle fpdf
            text = field["text"]
            if text and not isinstance(text, str):
                text = str(text, "latin1", "ignore")
            if field["type"] == "I" and not os.path.exists(text):
                # ajustar rutas relativas a las imágenes predeterminadas:
                if os.path.exists(os.path.join(self.InstallDir, text)):
                    field["text"] = os.path.join(self.InstallDir, text)
                else:
                    field["text"] = ""
                    ##field['type'] = "T"
                    ##field['font'] = ""
                    ##field['foreground'] = 0xff0000

        # genero el renderizador con propiedades del PDF
        t = Template(
            elements=self.elements,
            format=papel,
            orientation=orientacion,
            title="%s %s %s" % (tipo.encode("latin1", "ignore"), letra, nro),
            author="CUIT %s" % self.CUIT,
            subject="CAE %s" % fact["cae"],
            keywords="AFIP Factura Electrónica",
            creator="PyFEPDF %s (http://www.PyAfipWs.com.ar)" % __version__,
        )
        self.template = t
        return True

    @utils.inicializar_y_capturar_excepciones_simple
    def ProcesarPlantilla(self, num_copias=3, lineas_max=36, qty_pos="izq"):
        "Generar el PDF según la factura creada y plantilla cargada"

        ret = False
        try:
            if isinstance(num_copias, basestring):
                num_copias = int(num_copias)
            if isinstance(lineas_max, basestring):
                lineas_max = int(lineas_max)

            f = self.template
            fact = self.factura

            tipo_fact, letra_fact, numero_fact = self.fmt_fact(
                fact["tipo_cbte"], fact["punto_vta"], fact["cbte_nro"]
            )
            fact["_fmt_fact"] = tipo_fact, letra_fact, numero_fact
            if fact["tipo_cbte"] in (19, 20, 21):
                tipo_fact_ex = tipo_fact + u" de Exportación"
            else:
                tipo_fact_ex = tipo_fact

            # dividir y contar líneas:
            lineas = 0
            li_items = []
            for it in fact["detalles"]:
                qty = qty_pos == "izq" and it["qty"] or None
                codigo = it["codigo"]
                umed = it["umed"]
                # si umed es 0 (desc.), no imprimir cant/importes en 0
                if umed is not None and umed != "":
                    umed = int(umed)
                ds = it["ds"] or ""
                if "\x00" in ds:
                    # limpiar descripción (campos dbf):
                    ds = ds.replace("\x00", "")
                if "<br/>" in ds:
                    # reemplazar saltos de linea:
                    ds = ds.replace("<br/>", "\n")
                if DEBUG:
                    print("dividiendo", ds)
                # divido la descripción (simil célda múltiple de PDF)
                n_li = 0
                for ds in f.split_multicell(ds, "Item.Descripcion01"):
                    if DEBUG:
                        print("multicell", ds)
                    # agrego un item por linea (sin precio ni importe):
                    li_items.append(
                        dict(
                            codigo=codigo,
                            ds=ds,
                            qty=qty,
                            umed=umed if not n_li else None,
                            precio=None,
                            importe=None,
                        )
                    )
                    # limpio cantidad y código (solo en el primero)
                    qty = codigo = None
                    n_li += 1
                # asigno el precio a la última línea del item
                li_items[-1].update(
                    importe=it["importe"]
                    if float(it["importe"] or 0) or umed
                    else None,
                    despacho=it.get("despacho"),
                    precio=it["precio"] if float(it["precio"] or 0) or umed else None,
                    qty=(n_li == 1 or qty_pos == "der") and it["qty"] or None,
                    bonif=it.get("bonif") if float(it["bonif"] or 0) or umed else None,
                    iva_id=it.get("iva_id"),
                    imp_iva=it.get("imp_iva"),
                    dato_a=it.get("dato_a"),
                    dato_b=it.get("dato_b"),
                    dato_c=it.get("dato_c"),
                    dato_d=it.get("dato_d"),
                    dato_e=it.get("dato_e"),
                    u_mtx=it.get("u_mtx"),
                    cod_mtx=it.get("cod_mtx"),
                )

            # reemplazar saltos de linea en observaciones:
            for k in ("obs_generales", "obs_comerciales"):
                ds = fact.get(k, "")
                if isinstance(ds, basestring) and "<br/>" in ds:
                    fact[k] = ds.replace("<br/>", "\n")

            # divido las observaciones por linea:
            if (
                fact.get("obs_generales")
                and not f.has_key("obs")
                and not f.has_key("ObservacionesGenerales1")
            ):
                obs = "\n<U>Observaciones:</U>\n\n" + fact["obs_generales"]
                # limpiar texto (campos dbf) y reemplazar saltos de linea:
                obs = obs.replace("\x00", "").replace("<br/>", "\n")
                for ds in f.split_multicell(obs, "Item.Descripcion01"):
                    li_items.append(
                        dict(
                            codigo=None,
                            ds=ds,
                            qty=None,
                            umed=None,
                            precio=None,
                            importe=None,
                        )
                    )
            if (
                fact.get("obs_comerciales")
                and not f.has_key("obs_comerciales")
                and not f.has_key("ObservacionesComerciales1")
            ):
                obs = (
                    "\n<U>Observaciones Comerciales:</U>\n\n" + fact["obs_comerciales"]
                )
                # limpiar texto (campos dbf) y reemplazar saltos de linea:
                obs = obs.replace("\x00", "").replace("<br/>", "\n")
                for ds in f.split_multicell(obs, "Item.Descripcion01"):
                    li_items.append(
                        dict(
                            codigo=None,
                            ds=ds,
                            qty=None,
                            umed=None,
                            precio=None,
                            importe=None,
                        )
                    )

            # agrego permisos a descripciones (si corresponde)
            permisos = [
                u"Codigo de Despacho %s - Destino de la mercadería: %s"
                % (p["id_permiso"], self.paises.get(p["dst_merc"], p["dst_merc"]))
                for p in fact.get("permisos", [])
            ]
            # import dbg; dbg.set_trace()
            if f.has_key("permiso.id1") and f.has_key("permiso.delivery1"):
                for i, p in enumerate(fact.get("permisos", [])):
                    self.AgregarDato("permiso.id%d" % (i + 1), p["id_permiso"])
                    pais_dst = self.paises.get(p["dst_merc"], p["dst_merc"])
                    self.AgregarDato("permiso.delivery%d" % (i + 1), pais_dst)
            elif not f.has_key("permisos") and permisos:
                obs = "\n<U>Permisos de Embarque:</U>\n\n" + "\n".join(permisos)
                for ds in f.split_multicell(obs, "Item.Descripcion01"):
                    li_items.append(
                        dict(
                            codigo=None,
                            ds=ds,
                            qty=None,
                            umed=None,
                            precio=None,
                            importe=None,
                        )
                    )
            permisos_ds = ", ".join(permisos)

            # agrego comprobantes asociados
            cmps_asoc = [
                u"%s %s %s"
                % self.fmt_fact(c["cbte_tipo"], c["cbte_punto_vta"], c["cbte_nro"])
                for c in fact.get("cbtes_asoc", [])
            ]
            if not f.has_key("cmps_asoc") and cmps_asoc:
                obs = "\n<U>Comprobantes Asociados:</U>\n\n" + "\n".join(cmps_asoc)
                for ds in f.split_multicell(obs, "Item.Descripcion01"):
                    li_items.append(
                        dict(
                            codigo=None,
                            ds=ds,
                            qty=None,
                            umed=None,
                            precio=None,
                            importe=None,
                        )
                    )
            cmps_asoc_ds = ", ".join(cmps_asoc)

            # calcular cantidad de páginas:
            lineas = len(li_items)
            if lineas_max > 0:
                hojas = old_div(lineas, (lineas_max - 1))
                if lineas % (lineas_max - 1):
                    hojas = hojas + 1
                if not hojas:
                    hojas = 1
            else:
                hojas = 1

            if HOMO:
                self.AgregarDato("homo", u"HOMOLOGACIÓN")

            # mostrar las validaciones no excluyentes de AFIP (observaciones)

            if fact.get("motivos_obs") and fact["motivos_obs"] != "00":
                if not f.has_key("motivos_ds.L"):
                    motivos_ds = (
                        u"Irregularidades observadas por AFIP (F136): %s"
                        % fact["motivos_obs"]
                    )
                else:
                    motivos_ds = u"%s" % fact["motivos_obs"]
            elif HOMO:
                motivos_ds = u"Ejemplo Sin validez fiscal - Homologación - Testing"
            else:
                motivos_ds = ""

            if letra_fact in ("A", "M"):
                msg_no_iva = u"\nEl IVA discriminado no puede computarse como Crédito Fiscal (RG2485/08 Art. 30 inc. c)."
                if not f.has_key("leyenda_credito_fiscal") and motivos_ds:
                    motivos_ds += msg_no_iva

            # Facturas B Ley 27743
            cat_iva_rg = fact.get('categoria', fact.get('id_impositivo', '')).upper()
            consumidor_final = ("CONS" in cat_iva_rg and "FINAL" in cat_iva_rg) or ("EXENTO" in cat_iva_rg)

            copias = {1: "Original", 2: "Duplicado", 3: "Triplicado"}

            for copia in range(1, num_copias + 1):

                # completo campos y hojas
                for hoja in range(1, hojas + 1):
                    f.add_page()
                    f.set("copia", copias.get(copia, "Adicional %s" % copia))
                    f.set("hoja", str(hoja))
                    f.set("hojas", str(hojas))
                    f.set("pagina", "Pagina %s de %s" % (hoja, hojas))
                    if hojas > 1 and hoja < hojas:
                        s = "Continúa en hoja %s" % (hoja + 1)
                    else:
                        s = ""
                    f.set("continua", s)
                    f.set("Item.Descripcion%02d" % (lineas_max + 1), s)

                    if hoja > 1:
                        s = "Continúa de hoja %s" % (hoja - 1)
                    else:
                        s = ""
                    f.set("continua_de", s)
                    f.set("Item.Descripcion%02d" % (0), s)

                    if DEBUG:
                        print(u"generando pagina %s de %s" % (hoja, hojas))

                    # establezco datos según configuración:
                    for d in self.datos:
                        if d["pagina"] == "P" and hoja != 1:
                            continue
                        if d["pagina"] == "U" and hojas != hoja:
                            # no es la última hoja
                            continue
                        f.set(d["campo"], d["valor"])

                    # establezco campos según tabla encabezado:
                    for k, v in list(fact.items()):
                        f.set(k, v)

                    f.set("Numero", numero_fact)
                    f.set("Fecha", self.fmt_date(fact["fecha_cbte"]))
                    f.set("Vencimiento", self.fmt_date(fact["fecha_venc_pago"]))

                    f.set("LETRA", letra_fact)
                    f.set("TipoCBTE", "COD.%02d" % int(fact["tipo_cbte"]))

                    f.set("Comprobante.L", tipo_fact)
                    f.set("ComprobanteEx.L", tipo_fact_ex)

                    if fact.get("fecha_serv_desde"):
                        f.set("Periodo.Desde", self.fmt_date(fact["fecha_serv_desde"]))
                        f.set("Periodo.Hasta", self.fmt_date(fact["fecha_serv_hasta"]))
                    else:
                        for k in "Periodo.Desde", "Periodo.Hasta", "PeriodoFacturadoL":
                            f.set(k, "")

                    f.set(
                        "Cliente.Nombre", fact.get("nombre", fact.get("nombre_cliente"))
                    )
                    f.set(
                        "Cliente.Domicilio",
                        fact.get("domicilio", fact.get("domicilio_cliente")),
                    )
                    f.set(
                        "Cliente.Localidad",
                        fact.get("localidad", fact.get("localidad_cliente")),
                    )
                    f.set(
                        "Cliente.Provincia",
                        fact.get("provincia", fact.get("provincia_cliente")),
                    )
                    f.set(
                        "Cliente.Telefono",
                        fact.get("telefono", fact.get("telefono_cliente")),
                    )
                    f.set(
                        "Cliente.IVA", fact.get("categoria", fact.get("id_impositivo"))
                    )
                    f.set("Cliente.CUIT", self.fmt_cuit(str(fact["nro_doc"])))
                    f.set(
                        "Cliente.TipoDoc",
                        u"%s:" % self.tipos_doc[int(str(fact["tipo_doc"]))],
                    )
                    f.set("Cliente.Observaciones", fact.get("obs_comerciales"))
                    f.set(
                        "Cliente.PaisDestino",
                        self.paises.get(
                            fact.get("pais_dst_cmp"), fact.get("pais_dst_cmp")
                        )
                        or "",
                    )

                    if fact["moneda_id"]:
                        f.set("moneda_ds", self.monedas_ds.get(fact["moneda_id"], ""))
                    else:
                        for k in (
                            "moneda.L",
                            "moneda_id",
                            "moneda_ds",
                            "moneda_ctz.L",
                            "moneda_ctz",
                        ):
                            f.set(k, "")

                    if not fact.get("incoterms"):
                        for k in "incoterms.L", "incoterms", "incoterms_ds":
                            f.set(k, "")

                    li = 0
                    k = 0
                    subtotal = Decimal("0.00")
                    iva_liq = Decimal("0.00")
                    for it in li_items:
                        k = k + 1
                        if k > hoja * (lineas_max - 1):
                            break
                        # acumular subtotal (sin IVA facturas A):
                        if it["importe"]:
                            subtotal += Decimal("%.6f" % float(it["importe"]))
                            if letra_fact in ("A", "M") and it["imp_iva"]:
                                subtotal -= Decimal("%.6f" % float(it["imp_iva"]))
                        # agregar el item si encuadra en la hoja especificada:
                        if k > (hoja - 1) * (lineas_max - 1):
                            if DEBUG:
                                print("it", it)
                            li += 1
                            if it["qty"] is not None:
                                f.set("Item.Cantidad%02d" % li, self.fmt_qty(it["qty"]))
                            if it["codigo"] is not None:
                                f.set("Item.Codigo%02d" % li, it["codigo"])
                            if it["umed"] is not None:
                                if it["umed"] and f.has_key("Item.Umed_ds01"):
                                    # recortar descripción:
                                    umed_ds = self.umeds_ds.get(int(it["umed"]))
                                    s = f.split_multicell(umed_ds, "Item.Umed_ds01")
                                    f.set("Item.Umed_ds%02d" % li, s[0])
                            # solo discriminar IVA en A/M (mostrar tasa en B)
                            if letra_fact in ("A", "M", "B"):
                                if it.get("iva_id") is not None:
                                    if letra_fact != "B" or consumidor_final:
                                        f.set("Item.IvaId%02d" % li, it["iva_id"])
                                        if it["iva_id"]:
                                            f.set(
                                                "Item.AlicuotaIva%02d" % li,
                                                self.fmt_iva(it["iva_id"]),
                                            )
                                            imp_it_iva = Decimal(it['imp_iva'] or "0.00")
                                            if not imp_it_iva and it['importe']:
                                                p = self.ivas_ds[int(it['iva_id'])]
                                                importe_it = Decimal(it['importe'])
                                                if p == int(p):
                                                    imp_it_bruto = importe_it / (Decimal(p) / Decimal(100) + Decimal(1))
                                                    imp_it_iva = importe_it - imp_it_bruto
                                            iva_liq += imp_it_iva

                            if letra_fact in ("A", "M"):
                                if it.get("imp_iva") is not None:
                                    f.set(
                                        "Item.ImporteIva%02d" % li,
                                        self.fmt_pre(it["imp_iva"]),
                                    )
                            if it.get("despacho") is not None:
                                f.set("Item.Numero_Despacho%02d" % li, it["despacho"])
                            if it.get("bonif") is not None:
                                f.set("Item.Bonif%02d" % li, self.fmt_pre(it["bonif"]))
                            f.set("Item.Descripcion%02d" % li, it["ds"])
                            if it["precio"] is not None:
                                f.set(
                                    "Item.Precio%02d" % li, self.fmt_pre(it["precio"])
                                )
                            if it["importe"] is not None:
                                f.set(
                                    "Item.Importe%02d" % li, self.fmt_num(it["importe"])
                                )

                            # Datos MTX
                            if it.get("u_mtx") is not None:
                                f.set("Item.U_MTX%02d" % li, it["u_mtx"])
                            if it.get("cod_mtx") is not None:
                                f.set("Item.COD_MTX%02d" % li, it["cod_mtx"])

                            # datos adicionales de items
                            for adic in [
                                "dato_a",
                                "dato_b",
                                "dato_c",
                                "dato_d",
                                "dato_e",
                            ]:
                                if adic in it:
                                    f.set("Item.%s%02d" % (adic, li), it[adic])

                    if hojas == hoja:
                        # última hoja, imprimo los totales
                        li += 1

                        # agrego otros tributos
                        lit = 0
                        for it in fact["tributos"]:
                            lit += 1
                            if it["desc"]:
                                f.set("Tributo.Descripcion%02d" % lit, it["desc"])
                            else:
                                trib_id = int(it["tributo_id"])
                                trib_ds = self.tributos_ds[trib_id]
                                f.set("Tributo.Descripcion%02d" % lit, trib_ds)
                            if it["base_imp"] is not None:
                                f.set(
                                    "Tributo.BaseImp%02d" % lit,
                                    self.fmt_num(it["base_imp"]),
                                )
                            if it["alic"] is not None:
                                f.set(
                                    "Tributo.Alicuota%02d" % lit,
                                    self.fmt_num(it["alic"]) + "%",
                                )
                            if it["importe"] is not None:
                                f.set(
                                    "Tributo.Importe%02d" % lit,
                                    self.fmt_imp(it["importe"]),
                                )

                        # reiniciar el subtotal neto, independiente de detalles:
                        subtotal = Decimal(0)
                        if fact["imp_neto"]:
                            subtotal += Decimal("%.6f" % float(fact["imp_neto"]))
                        # agregar IVA al subtotal si no es factura A
                        if not letra_fact in ("A", "M") and fact["imp_iva"]:
                            subtotal += Decimal("%.6f" % float(fact["imp_iva"]))
                        # mostrar descuento general solo si se utiliza:
                        if "descuento" in fact and fact["descuento"]:
                            descuento = Decimal("%.6f" % float(fact["descuento"]))
                            f.set("descuento", self.fmt_imp(descuento))
                            subtotal -= descuento
                        # al subtotal neto sumo exento y no gravado:
                        if fact["imp_tot_conc"]:
                            subtotal += Decimal("%.6f" % float(fact["imp_tot_conc"]))
                        if fact["imp_op_ex"]:
                            subtotal += Decimal("%.6f" % float(fact["imp_op_ex"]))
                        # si no se envia subtotal, usar el calculado:
                        if fact.get("imp_subtotal"):
                            f.set("subtotal", self.fmt_imp(fact.get("imp_subtotal")))
                        else:
                            f.set("subtotal", self.fmt_imp(subtotal))

                        # importes generales de IVA y netos gravado / no gravado
                        f.set("imp_neto", self.fmt_imp(fact["imp_neto"]))
                        f.set("impto_liq", self.fmt_imp(fact.get("impto_liq")))
                        f.set("impto_liq_nri", self.fmt_imp(fact.get("impto_liq_nri")))
                        f.set("imp_iva", self.fmt_imp(fact.get("imp_iva")))
                        f.set("imp_trib", self.fmt_imp(fact.get("imp_trib")))
                        f.set("imp_total", self.fmt_imp(fact["imp_total"]))
                        f.set("imp_subtotal", self.fmt_imp(fact.get("imp_subtotal")))
                        f.set("imp_tot_conc", self.fmt_imp(fact["imp_tot_conc"]))
                        f.set("imp_op_ex", self.fmt_imp(fact["imp_op_ex"]))

                        # campos antiguos (por compatibilidad hacia atrás)
                        f.set("IMPTO_PERC", self.fmt_imp(fact.get("impto_perc")))
                        f.set("IMP_OP_EX", self.fmt_imp(fact.get("imp_op_ex")))
                        f.set("IMP_IIBB", self.fmt_imp(fact.get("imp_iibb")))
                        f.set(
                            "IMPTO_PERC_MUN", self.fmt_imp(fact.get("impto_perc_mun"))
                        )
                        f.set("IMP_INTERNOS", self.fmt_imp(fact.get("imp_internos")))

                        # mostrar u ocultar el IVA discriminado si es clase A/B:
                        if letra_fact in ("A", "M"):
                            f.set("NETO", self.fmt_imp(fact["imp_neto"]))
                            f.set(
                                "IVALIQ",
                                self.fmt_imp(
                                    fact.get("impto_liq", fact.get("imp_iva"))
                                ),
                            )
                            f.set("LeyendaIVA", "")

                            # limpio etiquetas y establezco subtotal de iva liq.
                            for p in list(self.ivas_ds.values()):
                                f.set("IVA%s.L" % p, "")
                            for iva in fact["ivas"]:
                                p = self.ivas_ds[int(iva["iva_id"])]
                                f.set("IVA%s" % p, self.fmt_imp(iva["importe"]))
                                f.set("NETO%s" % p, self.fmt_imp(iva["base_imp"]))
                                f.set(
                                    "IVA%s.L" % p,
                                    "IVA %s" % self.fmt_iva(iva["iva_id"]),
                                )
                        else:
                            # Factura C y E no llevan columna IVA (B solo tasa)
                            if letra_fact in ("C", "E"):
                                f.set("Item.AlicuotaIVA", "")
                            f.set("NETO.L", "")
                            f.set("IVA.L", "")
                            f.set("LeyendaIVA", "")
                            # Facturas B Ley 27743
                            if letra_fact == "B" and consumidor_final:
                                if fact.get('impto_liq', fact.get('imp_iva')):
                                    iva_liq = fact.get('impto_liq', fact.get('imp_iva'))
                                    f.set('IVA.L', "IVA Contenido:")
                                else:
                                    f.set('IVA.L', "IVA Contenido (*est.):")
                                f.set('IVALIQ', self.fmt_imp(iva_liq))
                                f.set('LeyendaIVA', "Regimen de Transparencia Fiscal al Consumidor (Ley 27.743)")
                            for p in list(self.ivas_ds.values()):
                                f.set("IVA%s.L" % p, "")
                                f.set("NETO%s.L" % p, "")
                        f.set("Total.L", "Total:")
                        f.set("TOTAL", self.fmt_imp(fact["imp_total"]))
                    else:
                        # limpio todas las etiquetas (no es la última hoja)
                        for k in (
                            "imp_neto",
                            "impto_liq",
                            "imp_total",
                            "impto_perc",
                            "imp_iva",
                            "impto_liq_nri",
                            "imp_trib",
                            "imp_op_ex",
                            "imp_tot_conc",
                            "imp_op_ex",
                            "IMP_IIBB",
                            "imp_iibb",
                            "impto_perc_mun",
                            "imp_internos",
                            "NGRA.L",
                            "EXENTO.L",
                            "descuento.L",
                            "descuento",
                            "subtotal.L",
                            "NETO.L",
                            "NETO",
                            "IVA.L",
                            "LeyendaIVA",
                        ):
                            f.set(k, "")
                        for p in list(self.ivas_ds.values()):
                            f.set("IVA%s.L" % p, "")
                            f.set("NETO%s.L" % p, "")
                        f.set("Total.L", "Subtotal:")
                        f.set("TOTAL", self.fmt_imp(subtotal))

                    f.set("cmps_asoc_ds", cmps_asoc_ds)
                    f.set("permisos_ds", permisos_ds)

                    # Datos del pie de factura (obtenidos desde AFIP):
                    f.set("motivos_ds", motivos_ds)
                    if f.has_key("motivos_ds1") and motivos_ds:
                        if letra_fact in ("A", "M"):
                            if f.has_key("leyenda_credito_fiscal"):
                                f.set("leyenda_credito_fiscal", msg_no_iva)
                        for i, txt in enumerate(
                            f.split_multicell(motivos_ds, "motivos_ds1")
                        ):
                            f.set("motivos_ds%d" % (i + 1), txt)
                    if not motivos_ds:
                        f.set("motivos_ds.L", "")

                    f.set("CAE", fact["cae"])
                    f.set("CAE.Vencimiento", self.fmt_date(fact["fecha_vto"]))
                    if (
                        fact["cae"] != "NULL"
                        and str(fact["cae"]).isdigit()
                        and str(fact["fecha_vto"]).isdigit()
                        and self.CUIT
                    ):
                        cuit = "".join([x for x in str(self.CUIT) if x.isdigit()])
                        barras = "".join(
                            [
                                cuit,
                                "%03d" % int(fact["tipo_cbte"]),
                                "%05d" % int(fact["punto_vta"]),
                                str(fact["cae"]),
                                fact["fecha_vto"],
                            ]
                        )
                        barras = barras + self.digito_verificador_modulo10(barras)
                    else:
                        barras = ""

                    f.set("CodigoBarras", str(barras))
                    f.set("CodigoBarrasLegible", barras)

                    if not HOMO and barras and fact.get("resultado") == "A":
                        f.set("estado", "Comprobante Autorizado")
                    elif fact.get("resultado") == "R":
                        f.set("estado", "Comprobante Rechazado")
                    elif fact.get("resultado") == "O":
                        f.set("estado", "Comprobante Observado")
                    elif fact.get("resultado"):
                        f.set("estado", "Comprobante No Autorizado")
                    else:
                        f.set("estado", "")  # compatibilidad hacia atras

                    # colocar campos de observaciones (si no van en ds)
                    if f.has_key("observacionesgenerales1") and "obs_generales" in fact:
                        for i, txt in enumerate(
                            f.split_multicell(
                                fact["obs_generales"], "ObservacionesGenerales1"
                            )
                        ):
                            f.set("ObservacionesGenerales%d" % (i + 1), txt)
                    if (
                        f.has_key("observacionescomerciales1")
                        and "obs_comerciales" in fact
                    ):
                        for i, txt in enumerate(
                            f.split_multicell(
                                fact["obs_comerciales"], "ObservacionesComerciales1"
                            )
                        ):
                            f.set("ObservacionesComerciales%d" % (i + 1), txt)
                    if f.has_key("enletras1") and "en_letras" in fact:
                        for i, txt in enumerate(
                            f.split_multicell(fact["en_letras"], "EnLetras1")
                        ):
                            f.set("EnLetras%d" % (i + 1), txt)

                    if f.has_key("AFIP_QR"):
                        if not self.archivo_qr:
                            self.GenerarQR()
                        f.set("AFIP_QR", self.archivo_qr)
                        if DEBUG:
                            print("Usando imagen codigo QR:", self.archivo_qr)

            ret = True
        except Exception as e:
            # capturar la excepción manualmente, para imprimirla en el PDF:
            ex = utils.exception_info()
            if DEBUG:
                print(self.Excepcion)
                print(self.Traceback)

            # guardar la traza de la excepción en un archivo temporal:
            fname = os.path.join(tempfile.gettempdir(), "traceback.txt")
            self.template.add_page()
            # agregar el texto de la excepción y ubicación de la traza al PDF:
            self.AgregarCampo(
                "traceback",
                "T",
                25,
                270,
                0,
                0,
                size=10,
                rotate=0,
                foreground=0xF00000,
                priority=-1,
                text="Traceback %s" % (fname,),
            )
            self.AgregarCampo(
                "excepcion",
                "T",
                25,
                250,
                0,
                0,
                size=10,
                rotate=0,
                foreground=0xF00000,
                priority=-1,
                text="Excepcion %(name)s:%(lineno)s" % ex,
            )
            if DEBUG:
                print("grabando...", fname, self.Excepcion, self.Traceback, ex)
            f = open(fname, "w")
            try:
                f.write(str(ex))
            except Exception as e:
                f.write("imposible grabar")
            finally:
                f.close()
            # guardar la info de la excepcion a lo último, para que no sea
            # limpiada por el decorador de otros métodos (AgregarCampo) ...
            self.Excepcion = ex["msg"]
            self.Traceback = ex["tb"]
        finally:
            return ret

    @utils.inicializar_y_capturar_excepciones_simple
    def GenerarPDF(self, archivo=""):
        "Generar archivo de salida en formato PDF"
        if not archivo:
            dest = "S"  # devolver buffer (string)
        else:
            dest = "F"  # guardar en archivo
        return self.template.render(archivo, dest)

    @utils.inicializar_y_capturar_excepciones_simple
    def MostrarPDF(self, archivo, imprimir=False):
        if sys.platform.startswith(("linux2", "java", "linux")):
            os.system("evince " "%s" "" % archivo)
        else:
            operation = imprimir and "print" or ""
            os.startfile(archivo, operation)
        return True

    @utils.inicializar_y_capturar_excepciones_simple
    def GenerarQR(self):
        from pyafipws.pyqr import PyQR

        # instanciar el objeto para codigos QR y crear un archivo temporal:
        pyqr = PyQR()
        pyqr.CrearArchivo()

        if DEBUG:
            print("Archivo:", pyqr.Archivo)
        # convertir campos al formato que requiere AFIP:
        fact = self.factura
        cuit = "".join([c for c in self.CUIT if c.isdigit()])  # sólo numeros
        f = fact["fecha_cbte"]
        fecha = "-".join([f[0:4], f[4:6], f[6:9]])  # 'AAAA-MM-DD'

        # generar el código QR para esta factura:
        url = pyqr.GenerarImagen(
            fecha=fecha,
            cuit=cuit,
            pto_vta=fact["punto_vta"],
            tipo_cmp=fact["tipo_cbte"],
            nro_cmp=fact["cbte_nro"],
            importe=fact["imp_total"],
            moneda=fact.get("moneda_id", "PES"),
            ctz=fact.get("moneda_ctz", 1),
            tipo_doc_rec=fact["tipo_doc"],
            nro_doc_rec=fact["nro_doc"],
            tipo_cod_aut=fact.get("tipo_cod_aut") or self.TipoCodAut,
            cod_aut=fact["cae"],
        )

        # guardar el nombre de archivo para usarlo en el PDF:
        self.archivo_qr = pyqr.Archivo
        return url


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"):
    basepath = __file__
elif sys.frozen == "dll":
    import win32api

    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


def main():
    global CONFIG_FILE, DEBUG, HOMO
    
    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register

        win32com.server.register.UseCommandLine(FEPDF)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver

        # win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([FEPDF._reg_clsid_])
    else:
        from pyafipws.utils import SafeConfigParser

        DEBUG = "--debug" in sys.argv
        utils.safe_console()

        # leeo configuración (primer argumento o rece.ini por defecto)
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
            CONFIG_FILE = sys.argv.pop(1)
        if DEBUG:
            print("CONFIG_FILE:", CONFIG_FILE)

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        conf_fact = dict(config.items("FACTURA"))
        conf_pdf = dict(config.items("PDF"))

        if "--ayuda" in sys.argv:
            print(AYUDA)
            sys.exit(0)

        if "--licencia" in sys.argv:
            print(LICENCIA)
            sys.exit(0)

        if "--formato" in sys.argv:
            if "--dbf" in sys.argv:
                from pyafipws.formatos import formato_dbf

                formato_dbf.ayuda()
            else:
                from pyafipws.formatos import formato_txt

                formato_txt.ayuda()
            sys.exit(0)

        fepdf = FEPDF()

        # cargo el formato CSV por defecto (factura.csv)
        fepdf.CargarFormato(conf_fact.get("formato", "factura.csv"))

        # establezco formatos (cantidad de decimales) según configuración:
        fepdf.FmtCantidad = conf_fact.get("fmt_cantidad", "0.2")
        fepdf.FmtPrecio = conf_fact.get("fmt_precio", "0.2")

        # CAE predeterminado (configurar "A" para CAEA)
        if config.has_option("FACTURA", "tipo_cod_aut"):
            fepdf.TipoCodAut = conf_fact.get("tipo_cod_aut", "E")

        if "--cargar" in sys.argv:
            if "--dbf" in sys.argv:
                from pyafipws.formatos import formato_dbf

                conf_dbf = dict(config.items("DBF"))
                if DEBUG:
                    print("conf_dbf", conf_dbf)
                regs = list(formato_dbf.leer(conf_dbf).values())
            elif "--json" in sys.argv:
                from pyafipws.formatos import formato_json

                if "--entrada" in sys.argv:
                    entrada = sys.argv[sys.argv.index("--entrada") + 1]
                else:
                    entrada = conf_fact.get("entrada", "entrada.txt")
                if DEBUG:
                    print("entrada", entrada)
                regs = formato_json.leer(entrada)
            else:
                from pyafipws.formatos import formato_txt

                if "--entrada" in sys.argv:
                    entrada = sys.argv[sys.argv.index("--entrada") + 1]
                else:
                    entrada = conf_fact.get("entrada", "entrada.txt")
                if DEBUG:
                    print("entrada", entrada)
                regs = formato_txt.leer(entrada)
            if DEBUG:
                print(regs)
                input("continuar...")
            fepdf.factura = regs[0]
            for d in regs[0]["datos"]:
                fepdf.AgregarDato(d["campo"], d["valor"], d["pagina"])

        if "--prueba" in sys.argv:
            # creo una factura de ejemplo
            HOMO = True

            # datos generales del encabezado:
            tipo_cbte = 19 if "--expo" in sys.argv else 201
            punto_vta = 4000
            fecha = '20210805' if "--fecha_prueba" in sys.argv else datetime.datetime.now().strftime("%Y%m%d")
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

            fepdf.CrearFactura(
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

            # completo campos extra del encabezado:
            ok = fepdf.EstablecerParametro("localidad_cliente", "Hurlingham")
            ok = fepdf.EstablecerParametro("provincia_cliente", "Buenos Aires")

            # imprimir leyenda "Comprobante Autorizado" (constatar con WSCDC!)
            ok = fepdf.EstablecerParametro("resultado", "A")

            # agrego remitos y otros comprobantes asociados:
            for i in range(3):
                tipo = 91
                pto_vta = 2
                nro = 1234 + i
                fepdf.AgregarCmpAsoc(tipo, pto_vta, nro)
            tipo = 5
            pto_vta = 2
            nro = 1234
            fepdf.AgregarCmpAsoc(tipo, pto_vta, nro)

            # tributos adicionales:
            tributo_id = 99
            desc = "Impuesto Municipal Matanza"
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            fepdf.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            tributo_id = 4
            desc = "Impuestos Internos"
            base_imp = None
            alic = None
            importe = "0.00"
            fepdf.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            # subtotales por alícuota de IVA:
            iva_id = 5  # 21%
            base_imp = 100
            importe = 21
            fepdf.AgregarIva(iva_id, base_imp, importe)

            for id in (4, 6):
                fepdf.AgregarIva(iva_id=id, base_imp=0.00, importe=0.00)

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
            fepdf.AgregarDetalleItem(
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
            fepdf.AgregarDetalleItem(
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
            fepdf.AgregarDetalleItem(
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

            # Agrego un permiso (ver manual para el desarrollador WSFEXv1)
            if "--expo" in sys.argv:
                id_permiso = "99999AAXX999999A"
                dst_merc = 225  # país destino de la mercaderia
                ok = fepdf.AgregarPermiso(id_permiso, dst_merc)

            # completo campos personalizados de la plantilla:
            fepdf.AgregarDato("custom-nro-cli", "Cod.123")
            fepdf.AgregarDato("custom-pedido", "1234")
            fepdf.AgregarDato("custom-remito", "12345")
            fepdf.AgregarDato("custom-transporte", "Camiones Ej.")
            print("Prueba!")

        # grabar muestra en dbf:
        if "--grabar" in sys.argv:
            reg = fepdf.factura.copy()
            reg["id"] = 0
            reg["datos"] = fepdf.datos
            reg["err_code"] = "OK"
            if "--dbf" in sys.argv:
                from pyafipws.formatos import formato_dbf

                conf_dbf = dict(config.items("DBF"))
                if DEBUG:
                    print("conf_dbf", conf_dbf)
                regs = formato_dbf.escribir([reg], conf_dbf)
            elif "--json" in sys.argv:
                from pyafipws.formatos import formato_json

                archivo = conf_fact.get("entrada", "entrada.txt")
                if DEBUG:
                    print("Escribiendo", archivo)
                if sys.version_info[0] < 3:
                    regs = formato_json.escribir([reg], archivo, encoding='utf-8')
                else:
                    regs = formato_json.escribir([reg], archivo)
            else:
                from pyafipws.formatos import formato_txt

                archivo = conf_fact.get("entrada", "entrada.txt")
                if DEBUG:
                    print("Escribiendo", archivo)
                regs = formato_txt.escribir([reg], archivo)

        # datos fijos:
        for k, v in list(conf_pdf.items()):
            fepdf.AgregarDato(k, v)
            if k.upper() == "CUIT":
                fepdf.CUIT = v  # CUIT del emisor para código de barras

        fepdf.CrearPlantilla(
            papel=conf_fact.get("papel", "legal"),
            orientacion=conf_fact.get("orientacion", "portrait"),
        )

        fepdf.ProcesarPlantilla(
            num_copias=int(conf_fact.get("copias", 1)),
            lineas_max=int(conf_fact.get("lineas_max", 24)),
            qty_pos=conf_fact.get("cant_pos") or "izq",
        )
        salida = conf_fact.get("salida", "")
        fact = fepdf.factura
        if salida:
            pass
        elif "pdf" in fact and fact["pdf"]:
            salida = fact["pdf"]
        else:
            # genero el nombre de archivo según datos de factura
            d = conf_fact.get("directorio", ".")
            clave_subdir = conf_fact.get("subdirectorio", "fecha_cbte")
            if clave_subdir:
                d = os.path.join(d, fact[clave_subdir])
            if not os.path.isdir(d):
                os.makedirs(d)
            fs = conf_fact.get("archivo", "numero").split(",")
            it = fact.copy()
            tipo_fact, letra_fact, numero_fact = fact["_fmt_fact"]
            it["tipo"] = tipo_fact.replace(" ", "_")
            it["letra"] = letra_fact
            it["numero"] = numero_fact
            it["mes"] = fact["fecha_cbte"][4:6]
            it["año"] = fact["fecha_cbte"][0:4]
            fn = u"".join([str(it.get(ff, ff)) for ff in fs])
            fn = fn.encode("ascii", "replace").replace("?", "_")
            salida = os.path.join(d, "%s.pdf" % fn)
        if DEBUG:
            print("archivo generado", salida)
        fepdf.GenerarPDF(archivo=salida)
        if "--mostrar" in sys.argv:
            fepdf.MostrarPDF(archivo=salida, imprimir="--imprimir" in sys.argv)

    return fepdf

if __name__ == "__main__":
    main()
