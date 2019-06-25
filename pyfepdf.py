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

from . import utils
from fpdf import Template
from decimal import Decimal
from io import StringIO
import traceback
import tempfile
import sys
import os
import decimal
import datetime
"Módulo para generar PDF de facturas electrónicas"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011-2019 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.09c"

DEBUG = False
HOMO = False
CONFIG_FILE = "rece.ini"

LICENCIA = """
pyfepdf.py: Interfaz para generar Facturas Electrónica en formato PDF
Copyright (C) 2011-2015 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA = """
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


class FEPDF:
    "Interfaz para generar PDF de Factura Electrónica"
    _public_methods_ = ['CrearFactura',
                        'AgregarDetalleItem', 'AgregarIva', 'AgregarTributo',
                        'AgregarCmpAsoc', 'AgregarPermiso',
                        'AgregarDato', 'EstablecerParametro',
                        'CargarFormato', 'AgregarCampo',
                        'CrearPlantilla', 'ProcesarPlantilla', 'GenerarPDF',
                        'MostrarPDF',
                        ]
    _public_attrs_ = ['Version', 'Excepcion', 'Traceback', 'InstallDir',
                      'Locale', 'FmtCantidad', 'FmtPrecio', 'CUIT',
                      'LanzarExcepciones',
                      ]

    _reg_progid_ = "PyFEPDF"
    _reg_clsid_ = "{C9B5D7BB-0388-4A5E-87D5-0B4376C7A336}"

    tipos_doc = {80: 'CUIT', 86: 'CUIL', 96: 'DNI', 99: '', 87: "CDI",
                 89: "LE", 90: "LC", 91: "CI Extranjera",
                 92: "en trámite", 93: "Acta Nacimiento", 94: "Pasaporte",
                 95: "CI Bs. As. RNP",
                 0: "CI Policía Federal", 1: "CI Buenos Aires",
                 2: "CI Catamarca", 3: "CI Córdoba", 4: "CI Corrientes",
                 5: "CI Entre Ríos", 6: "CI Jujuy", 7: "CI Mendoza",
                 8: "CI La Rioja", 9: "CI Salta", 10: "CI San Juan",
                 11: "CI San Luis", 12: "CI Santa Fe",
                 13: "CI Santiago del Estero", 14: "CI Tucumán",
                 16: "CI Chaco", 17: "CI Chubut", 18: "CI Formosa",
                 19: "CI Misiones", 20: "CI Neuquén", 21: "CI La Pampa",
                 22: "CI Río Negro", 23: "CI Santa Cruz",
                 24: "CI Tierra del Fuego",
                 }

    umeds_ds = {0: '', 1: 'kg', 2: 'm', 3: 'm2', 4: 'm3', 5: 'l',
                6: '1000 kWh', 7: 'u',
                8: 'pares', 9: 'docenas', 10: 'quilates', 11: 'millares',
                14: 'g', 15: 'mm', 16: 'mm3', 17: 'km', 18: 'hl', 20: 'cm',
                25: 'jgo. pqt. mazo naipes', 27: 'cm3', 29: 'tn',
                30: 'dam3', 31: 'hm3', 32: 'km3', 33: 'ug', 34: 'ng', 35: 'pg', 41: 'mg', 47: 'mm',
                48: 'curie', 49: 'milicurie', 50: 'microcurie', 51: 'uiacthor', 52: 'muiacthor',
                53: 'kg base', 54: 'gruesa', 61: 'kg bruto',
                62: 'uiactant', 63: 'muiactant', 64: 'uiactig', 65: 'muiactig', 66: 'kg activo',
                67: 'gramo activo', 68: 'gramo base', 96: 'packs', 97: 'hormas',
                96: 'packs', 97: 'seña/anticipo',
                99: 'bonificaci\xf3n', 98: 'otras unidades'}

    ivas_ds = {3: 0, 4: 10.5, 5: 21, 6: 27, 8: 5, 9: 2.5}

    paises = {512: 'FIJI, ISLAS', 513: 'PAPUA NUEVA GUINEA', 514: 'KIRIBATI, ISLAS', 515: 'MICRONESIA,EST.FEDER', 516: 'PALAU', 517: 'TUVALU', 518: 'SALOMON,ISLAS', 519: 'TONGA', 520: 'MARSHALL,ISLAS', 521: 'MARIANAS,ISLAS', 597: 'RESTO OCEANIA', 598: 'INDET.(OCEANIA)', 101: 'BURKINA FASO', 102: 'ARGELIA', 103: 'BOTSWANA', 104: 'BURUNDI', 105: 'CAMERUN', 107: 'REP. CENTROAFRICANA.', 108: 'CONGO', 109: 'REP.DEMOCRAT.DEL CONGO EX ZAIRE', 110: 'COSTA DE MARFIL', 111: 'CHAD', 112: 'BENIN', 113: 'EGIPTO', 115: 'GABON', 116: 'GAMBIA', 117: 'GHANA', 118: 'GUINEA', 119: 'GUINEA ECUATORIAL', 120: 'KENYA', 121: 'LESOTHO', 122: 'LIBERIA', 123: 'LIBIA', 124: 'MADAGASCAR', 125: 'MALAWI', 126: 'MALI', 127: 'MARRUECOS', 128: 'MAURICIO,ISLAS', 129: 'MAURITANIA', 130: 'NIGER', 131: 'NIGERIA', 132: 'ZIMBABWE', 133: 'RWANDA', 134: 'SENEGAL', 135: 'SIERRA LEONA', 136: 'SOMALIA', 137: 'SWAZILANDIA', 138: 'SUDAN', 139: 'TANZANIA', 140: 'TOGO', 141: 'TUNEZ', 142: 'UGANDA', 144: 'ZAMBIA', 145: 'TERRIT.VINCULADOS AL R UNIDO', 146: 'TERRIT.VINCULADOS A ESPA\xd1A', 147: 'TERRIT.VINCULADOS A FRANCIA', 149: 'ANGOLA', 150: 'CABO VERDE', 151: 'MOZAMBIQUE', 152: 'SEYCHELLES', 153: 'DJIBOUTI', 155: 'COMORAS', 156: 'GUINEA BISSAU', 157: 'STO.TOME Y PRINCIPE', 158: 'NAMIBIA', 159: 'SUDAFRICA', 160: 'ERITREA', 161: 'ETIOPIA', 197: 'RESTO (AFRICA)', 198: 'INDETERMINADO (AFRICA)', 200: 'ARGENTINA', 201: 'BARBADOS', 202: 'BOLIVIA', 203: 'BRASIL', 204: 'CANADA', 205: 'COLOMBIA', 206: 'COSTA RICA', 207: 'CUBA', 208: 'CHILE', 209: 'REP\xdaBLICA DOMINICANA', 210: 'ECUADOR', 211: 'EL SALVADOR', 212: 'ESTADOS UNIDOS', 213: 'GUATEMALA', 214: 'GUYANA', 215: 'HAITI', 216: 'HONDURAS', 217: 'JAMAICA', 218: 'MEXICO', 219: 'NICARAGUA', 220: 'PANAMA', 221: 'PARAGUAY', 222: 'PERU', 223: 'PUERTO RICO', 224: 'TRINIDAD Y TOBAGO', 225: 'URUGUAY', 226: 'VENEZUELA', 227: 'TERRIT.VINCULADO AL R.UNIDO', 228: 'TER.VINCULADOS A DINAMARCA', 229: 'TERRIT.VINCULADOS A FRANCIA AMERIC.', 230: 'TERRIT. HOLANDESES', 231: 'TER.VINCULADOS A ESTADOS UNIDOS', 232: 'SURINAME', 233: 'DOMINICA', 234: 'SANTA LUCIA', 235: 'SAN VICENTE Y LAS GRANADINAS', 236: 'BELICE', 237: 'ANTIGUA Y BARBUDA', 238: 'S.CRISTOBAL Y NEVIS', 239: 'BAHAMAS', 240: 'GRENADA', 241: 'ANTILLAS HOLANDESAS', 250: 'AAE Tierra del Fuego - ARGENTINA', 251: 'ZF La Plata - ARGENTINA', 252: 'ZF Justo Daract - ARGENTINA', 253: 'ZF R\xedo Gallegos - ARGENTINA', 254: 'Islas Malvinas - ARGENTINA', 255: 'ZF Tucum\xe1n - ARGENTINA', 256: 'ZF C\xf3rdoba - ARGENTINA', 257: 'ZF Mendoza - ARGENTINA', 258: 'ZF General Pico - ARGENTINA', 259: 'ZF Comodoro Rivadavia - ARGENTINA', 260: 'ZF Iquique', 261: 'ZF Punta Arenas', 262: 'ZF Salta - ARGENTINA', 263: 'ZF Paso de los Libres - ARGENTINA', 264: 'ZF Puerto Iguaz\xfa - ARGENTINA', 265: 'SECTOR ANTARTICO ARG.', 270: 'ZF Col\xf3n - REP\xdaBLICA DE PANAM\xc1', 271: 'ZF Winner (Sta. C. de la Sierra) - BOLIVIA', 280: 'ZF Colonia - URUGUAY', 281: 'ZF Florida - URUGUAY', 282: 'ZF Libertad - URUGUAY', 283: 'ZF Zonamerica - URUGUAY', 284: 'ZF Nueva Helvecia - URUGUAY', 285: 'ZF Nueva Palmira - URUGUAY', 286: 'ZF R\xedo Negro - URUGUAY', 287: 'ZF Rivera - URUGUAY', 288: 'ZF San Jos\xe9 - URUGUAY', 291: 'ZF Manaos - BRASIL', 295: 'MAR ARG ZONA ECO.EX', 296: 'RIOS ARG NAVEG INTER', 297: 'RESTO AMERICA', 298: 'INDETERMINADO (AMERICA)', 301: 'AFGANISTAN', 302: 'ARABIA SAUDITA', 303: 'BAHREIN', 304: 'MYANMAR (EX-BIRMANIA)', 305: 'BUTAN', 306: 'CAMBODYA (EX-KAMPUCHE)', 307: 'SRI LANKA', 308: 'COREA DEMOCRATICA', 309: 'COREA REPUBLICANA', 310: 'CHINA', 312: 'FILIPINAS', 313: 'TAIWAN', 315: 'INDIA', 316: 'INDONESIA', 317: 'IRAK', 318: 'IRAN', 319: 'ISRAEL', 320: 'JAPON', 321: 'JORDANIA', 322: 'QATAR', 323: 'KUWAIT', 324: 'LAOS', 325: 'LIBANO', 326: 'MALASIA', 327: 'MALDIVAS ISLAS', 328: 'OMAN', 329: 'MONGOLIA', 330: 'NEPAL', 331: 'EMIRATOS ARABES UNIDOS', 332: 'PAKIST\xc1N', 333: 'SINGAPUR', 334: 'SIRIA', 335: 'THAILANDIA', 337: 'VIETNAM', 341: 'HONG KONG', 344: 'MACAO', 345: 'BANGLADESH', 346: 'BRUNEI', 348: 'REPUBLICA DE YEMEN', 349: 'ARMENIA', 350: 'AZERBAIJAN', 351: 'GEORGIA', 352: 'KAZAJSTAN', 353: 'KIRGUIZISTAN', 354: 'TAYIKISTAN', 355: 'TURKMENISTAN', 356: 'UZBEKISTAN', 357: 'TERR. AU. PALESTINOS', 397: 'RESTO DE ASIA', 398: 'INDET.(ASIA)', 401: 'ALBANIA', 404: 'ANDORRA', 405: 'AUSTRIA', 406: 'BELGICA', 407: 'BULGARIA', 409: 'DINAMARCA', 410: 'ESPA\xd1A', 411: 'FINLANDIA', 412: 'FRANCIA', 413: 'GRECIA', 414: 'HUNGRIA', 415: 'IRLANDA', 416: 'ISLANDIA', 417: 'ITALIA', 418: 'LIECHTENSTEIN', 419: 'LUXEMBURGO', 420: 'MALTA', 421: 'MONACO', 422: 'NORUEGA', 423: 'PAISES BAJOS', 424: 'POLONIA', 425: 'PORTUGAL', 426: 'REINO UNIDO', 427: 'RUMANIA', 428: 'SAN MARINO', 429: 'SUECIA', 430: 'SUIZA', 431: 'VATICANO(SANTA SEDE)', 433: 'POS.BRIT.(EUROPA)', 435: 'CHIPRE', 436: 'TURQUIA', 438: 'ALEMANIA,REP.FED.', 439: 'BIELORRUSIA', 440: 'ESTONIA', 441: 'LETONIA', 442: 'LITUANIA', 443: 'MOLDAVIA', 444: 'RUSIA', 445: 'UCRANIA', 446: 'BOSNIA HERZEGOVINA', 447: 'CROACIA', 448: 'ESLOVAQUIA', 449: 'ESLOVENIA', 450: 'MACEDONIA', 451: 'REP. CHECA', 453: 'MONTENEGRO', 454: 'SERBIA', 997: 'RESTO CONTINENTE', 998: 'INDET.(CONTINENTE)', 497: 'RESTO EUROPA', 498: 'INDET.(EUROPA)', 501: 'AUSTRALIA', 503: 'NAURU', 504: 'NUEVA ZELANDIA', 505: 'VANATU', 506: 'SAMOA OCCIDENTAL', 507: 'TERRITORIO VINCULADOS A AUSTRALIA', 508: 'TERRITORIOS VINCULADOS AL R. UNIDO', 509: 'TERRITORIOS VINCULADOS A FRANCIA', 510: 'TER VINCULADOS A NUEVA. ZELANDA', 511: 'TER. VINCULADOS A ESTADOS UNIDOS'}

    monedas_ds = {'DOL': 'USD: Dólar', 'PES': 'ARS: Pesos', '010': 'MXN: Pesos Mejicanos', '011': 'UYU: Pesos Uruguayos', '012': 'BRL: Real', '014': 'Coronas Danesas', '015': 'Coronas Noruegas', '016': 'Coronas Suecas', '019': 'JPY: Yens', '018': 'CAD: D\xf3lar Canadiense', '033': 'CLP: Peso Chileno', '056': 'Forint (Hungr\xeda)', '031': 'BOV: Peso Boliviano', '036': 'Sucre Ecuatoriano', '051': 'D\xf3lar de Hong Kong', '034': 'Rand Sudafricano', '053': 'D\xf3lar de Jamaica', '057': 'Baht (Tailandia)', '043': 'Balboas Paname\xf1as', '042': 'Peso Dominicano', '052': 'D\xf3lar de Singapur', '032': 'Peso Colombiano', '035': 'Nuevo Sol Peruano', '061': 'Zloty Polaco', '060': 'EUR: Euro', '063': 'Lempira Hondure\xf1a', '062': 'Rupia Hind\xfa', '064': 'Yuan (Rep. Pop. China)', '009': 'Franco Suizo', '025': 'Dinar Yugoslavo', '002': 'USD: D\xf3lar Libre EEUU', '027': 'Dracma Griego', '026': 'D\xf3lar Australiano', '007': 'Florines Holandeses', '023': 'VEB: Bol\xedvar Venezolano', '047': 'Riyal Saudita', '046': 'Libra Egipcia', '045': 'Dirham Marroqu\xed', '044': 'C\xf3rdoba Nicarag\xfcense', '029': 'G\xfcaran\xed', '028': 'Flor\xedn (Antillas Holandesas)', '054': 'D\xf3lar de Taiwan', '040': 'Lei Rumano', '024': 'Corona Checa', '030': 'Shekel (Israel)', '021': 'Libra Esterlina', '055': 'Quetzal Guatemalteco', '059': 'Dinar Kuwaiti'}

    tributos_ds = {1: 'Impuestos nacionales', 2: 'Impuestos provinciales', 3: 'Impuestos municipales', 4: 'Impuestos Internos', 99: 'Otro'}

    tipos_fact = {
        (1, 6, 11, 19, 51): 'Factura',
        (2, 7, 12, 20, 52): 'Nota de Débito',
        (3, 8, 13, 21, 53): 'Nota de Crédito',
        (201, 206, 211): 'Factura de Crédito MiPyMEs',
        (202, 207, 212): 'Nota de Débito MiPyMEs',
        (203, 208, 213): 'Nota de Crédito MiPyMEs',
        (4, 9, 15, 54): 'Recibo',
        (10, 5): 'Nota de Venta al contado',
        (60, 61): 'Cuenta de Venta y Líquido producto',
        (63, 64): 'Liquidación',
        (91, ): 'Remito',
        (39, 40): '???? (R.G. N° 3419)'}

    letras_fact = {(1, 2, 3, 4, 5, 39, 60, 63, 201, 202, 203): 'A',
                   (6, 7, 8, 9, 10, 40, 61, 64, 206, 207, 208): 'B',
                   (11, 12, 13, 15, 211, 212, 213): 'C',
                   (51, 52, 53, 54): 'M',
                   (19, 20, 21): 'E',
                   (91, ): 'R',
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
        self.CUIT = ''
        self.factura = {}
        self.datos = []
        self.elements = []
        self.pdf = {}
        self.log = StringIO()
        #sys.stdout = self.log
        #sys.stderr = self.log
        self.LanzarExcepciones = True

    def DebugLog(self):
        "Devolver bitácora de depuración"
        msg = self.log.getvalue()
        return msg

    def inicializar(self):
        self.Excepcion = self.Traceback = ""

    @utils.inicializar_y_capturar_excepciones_simple
    def CrearFactura(self, concepto=1, tipo_doc=80, nro_doc="", tipo_cbte=1, punto_vta=0,
                     cbte_nro=0, imp_total=0.00, imp_tot_conc=0.00, imp_neto=0.00,
                     imp_iva=0.00, imp_trib=0.00, imp_op_ex=0.00, fecha_cbte="", fecha_venc_pago="",
                     fecha_serv_desde=None, fecha_serv_hasta=None,
                     moneda_id="PES", moneda_ctz="1.0000", cae="", fch_venc_cae="", id_impositivo='',
                     nombre_cliente="", domicilio_cliente="", pais_dst_cmp=None,
                     obs_comerciales="", obs_generales="", forma_pago="", incoterms="",
                     idioma_cbte=7, motivos_obs="", descuento=0.0,
                     **kwargs
                     ):
        "Creo un objeto factura (internamente)"
        fact = {'tipo_doc': tipo_doc, 'nro_doc': nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbte_nro': cbte_nro,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto, 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'nombre_cliente': nombre_cliente,
                'domicilio_cliente': domicilio_cliente,
                'pais_dst_cmp': pais_dst_cmp,
                'obs_comerciales': obs_comerciales,
                'obs_generales': obs_generales,
                'id_impositivo': id_impositivo,
                'forma_pago': forma_pago, 'incoterms': incoterms,
                'cae': cae, 'fecha_vto': fch_venc_cae,
                'motivos_obs': motivos_obs,
                'descuento': descuento,
                'cbtes_asoc': [],
                'tributos': [],
                'ivas': [],
                'permisos': [],
                'detalles': [],
                }
        if fecha_serv_desde:
            fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta:
            fact['fecha_serv_hasta'] = fecha_serv_hasta

        self.factura = fact
        return True

    def EstablecerParametro(self, parametro, valor):
        "Modifico un parametro general a la factura (internamente)"
        self.factura[parametro] = valor
        return True

    def AgregarDato(self, campo, valor, pagina='T'):
        "Agrego un dato a la factura (internamente)"
        self.datos.append({'campo': campo, 'valor': valor, 'pagina': pagina})
        return True

    def AgregarDetalleItem(self, u_mtx, cod_mtx, codigo, ds, qty, umed, precio,
                           bonif, iva_id, imp_iva, importe, despacho,
                           dato_a=None, dato_b=None, dato_c=None, dato_d=None, dato_e=None):
        "Agrego un item a una factura (internamente)"
        # ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        item = {
            'u_mtx': u_mtx,
            'cod_mtx': cod_mtx,
            'codigo': codigo,
            'ds': ds,
            'qty': qty,
            'umed': umed,
            'precio': precio,
            'bonif': bonif,
            'iva_id': iva_id,
            'imp_iva': imp_iva,
            'importe': importe,
            'despacho': despacho,
            'dato_a': dato_a,
            'dato_b': dato_b,
            'dato_c': dato_c,
            'dato_d': dato_d,
            'dato_e': dato_e,
        }
        self.factura['detalles'].append(item)
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwarg):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'cbte_tipo': tipo, 'cbte_punto_vta': pto_vta, 'cbte_nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, tributo_id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg):
        "Agrego un tributo a una factura (interna)"
        tributo = {'tributo_id': tributo_id, 'desc': desc, 'base_imp': base_imp,
                   'alic': alic, 'importe': importe}
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, iva_id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = {'iva_id': iva_id, 'base_imp': base_imp, 'importe': importe}
        self.factura['ivas'].append(iva)
        return True

    def AgregarPermiso(self, id_permiso, dst_merc, **kwargs):
        "Agrego un permiso a una factura (interna)"
        self.factura['permisos'].append({
            'id_permiso': id_permiso,
            'dst_merc': dst_merc,
        })
        return True

    # funciones de formateo de strings:

    def fmt_date(self, d):
        "Formatear una fecha"
        if not d or len(d) != 8:
            return d or ''
        else:
            return "%s/%s/%s" % (d[6:8], d[4:6], d[0:4])

    def fmt_num(self, i, fmt="%0.2f", monetary=True):
        "Formatear un número"
        if i is not None and str(i) and not isinstance(i, bool):
            loc = self.Locale
            if loc:
                import locale
                locale.setlocale(locale.LC_ALL, loc)
                return locale.format(fmt, Decimal(str(i).replace(",", ".")), grouping=True, monetary=monetary)
            else:
                return (fmt % Decimal(str(i).replace(",", "."))).replace(".", ",")
        else:
            return ''

    def fmt_imp(self, i):
        return self.fmt_num(i, "%0.2f")

    def fmt_qty(self, i):
        return self.fmt_num(i, "%" + self.FmtCantidad + "f", False)

    def fmt_pre(self, i):
        return self.fmt_num(i, "%" + self.FmtPrecio + "f")

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
        return ''

    def fmt_fact(self, tipo_cbte, punto_vta, cbte_nro):
        "Formatear tipo, letra y punto de venta y número de factura"
        n = "%05d-%08d" % (int(punto_vta), int(cbte_nro))
        t, l = tipo_cbte, ''
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
            return ''
        etapa1 = sum([int(c) for i, c in enumerate(codigo) if not i % 2])
        # Etapa 2: multiplicar la suma obtenida en la etapa 1 por el número 3
        etapa2 = etapa1 * 3
        # Etapa 3: comenzar desde la izquierda, sumar todos los caracteres que están ubicados en las posiciones pares.
        etapa3 = sum([int(c) for i, c in enumerate(codigo) if i % 2])
        # Etapa 4: sumar los resultados obtenidos en las etapas 2 y 3.
        etapa4 = etapa2 + etapa3
        # Etapa 5: buscar el menor número que sumado al resultado obtenido en la etapa 4 dé un número múltiplo de 10. Este será el valor del dígito verificador del módulo 10.
        digito = 10 - (etapa4 - (int(etapa4 / 10) * 10))
        if digito == 10:
            digito = 0
        return str(digito)

    # Funciones públicas:

    @utils.inicializar_y_capturar_excepciones_simple
    def CargarFormato(self, archivo="factura.csv"):
        "Cargo el formato de campos a generar desde una planilla CSV"

        # si no encuentro archivo, lo busco en el directorio predeterminado:
        if not os.path.exists(archivo):
            archivo = os.path.join(self.InstallDir, "plantillas", os.path.basename(archivo))

        if DEBUG:
            print("abriendo archivo ", archivo)

        for lno, linea in enumerate(open(archivo.encode('latin1')).readlines()):
            if DEBUG:
                print("procesando linea ", lno, linea)
            args = []
            for i, v in enumerate(linea.split(";")):
                if not v.startswith("'"):
                    v = v.replace(",", ".")
                else:
                    v = v  # .decode('latin1')
                if v.strip() == '':
                    v = None
                else:
                    v = eval(v.strip())
                args.append(v)
            self.AgregarCampo(*args)
        return True

    @utils.inicializar_y_capturar_excepciones_simple
    def AgregarCampo(self, nombre, tipo, x1, y1, x2, y2,
                     font="Arial", size=12,
                     bold=False, italic=False, underline=False,
                     foreground=0x000000, background=0xFFFFFF,
                     align="L", text="", priority=0, **kwargs):
        "Agrego un campo a la plantilla"
        # convierto colores de string (en hexadecimal)
        if isinstance(foreground, str):
            foreground = int(foreground, 16)
        if isinstance(background, str):
            background = int(background, 16)
        ##if isinstance(text, str): text = text.encode("latin1")
        field = {
            'name': nombre,
            'type': tipo,
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'font': font, 'size': size,
            'bold': bold, 'italic': italic, 'underline': underline,
            'foreground': foreground, 'background': background,
            'align': align, 'text': text, 'priority': priority}
        field.update(kwargs)
        self.elements.append(field)
        return True

    @utils.inicializar_y_capturar_excepciones_simple
    def CrearPlantilla(self, papel="A4", orientacion="portrait"):
        "Iniciar la creación del archivo PDF"

        fact = self.factura
        tipo, letra, nro = self.fmt_fact(fact['tipo_cbte'], fact['punto_vta'], fact['cbte_nro'])

        if HOMO:
            self.AgregarCampo("homo", 'T', 100, 250, 0, 0,
                              size=70, rotate=45, foreground=0x808080, priority=-1)

        # sanity check:
        for field in self.elements:
            # si la imagen no existe, eliminar nombre para que no falle fpdf
            if field['type'] == 'I' and not os.path.exists(field["text"]):
                # ajustar rutas relativas a las imágenes predeterminadas:
                if os.path.exists(os.path.join(self.InstallDir, field["text"])):
                    field['text'] = os.path.join(self.InstallDir, field["text"])
                else:
                    field['text'] = ""
                    ##field['type'] = "T"
                    ##field['font'] = ""
                    ##field['foreground'] = 0xff0000

        # genero el renderizador con propiedades del PDF
        t = Template(elements=self.elements,
                     format=papel, orientation=orientacion,
                     title="%s %s %s" % (tipo.encode("latin1", "ignore"), letra, nro),
                     author="CUIT %s" % self.CUIT,
                     subject="CAE %s" % fact['cae'],
                     keywords="AFIP Factura Electrónica",
                     creator='PyFEPDF %s (http://www.PyAfipWs.com.ar)' % __version__,)
        self.template = t
        return True

    @utils.inicializar_y_capturar_excepciones_simple
    def ProcesarPlantilla(self, num_copias=3, lineas_max=36, qty_pos='izq'):
        "Generar el PDF según la factura creada y plantilla cargada"

        ret = False
        try:
            if isinstance(num_copias, str):
                num_copias = int(num_copias)
            if isinstance(lineas_max, str):
                lineas_max = int(lineas_max)

            f = self.template
            fact = self.factura

            tipo_fact, letra_fact, numero_fact = self.fmt_fact(fact['tipo_cbte'], fact['punto_vta'], fact['cbte_nro'])
            fact['_fmt_fact'] = tipo_fact, letra_fact, numero_fact
            if fact['tipo_cbte'] in (19, 20, 21):
                tipo_fact_ex = tipo_fact + " de Exportación"
            else:
                tipo_fact_ex = tipo_fact

            # dividir y contar líneas:
            lineas = 0
            li_items = []
            for it in fact['detalles']:
                qty = qty_pos == 'izq' and it['qty'] or None
                codigo = it['codigo']
                umed = it['umed']
                # si umed es 0 (desc.), no imprimir cant/importes en 0
                if umed is not None and umed != "":
                    umed = int(umed)
                ds = it['ds'] or ""
                if '\x00' in ds:
                    # limpiar descripción (campos dbf):
                    ds = ds.replace('\x00', '')
                if '<br/>' in ds:
                    # reemplazar saltos de linea:
                    ds = ds.replace('<br/>', '\n')
                if DEBUG:
                    print("dividiendo", ds)
                # divido la descripción (simil célda múltiple de PDF)
                n_li = 0
                for ds in f.split_multicell(ds, 'Item.Descripcion01'):
                    if DEBUG:
                        print("multicell", ds)
                    # agrego un item por linea (sin precio ni importe):
                    li_items.append(dict(codigo=codigo, ds=ds, qty=qty,
                                         umed=umed if not n_li else None,
                                         precio=None, importe=None))
                    # limpio cantidad y código (solo en el primero)
                    qty = codigo = None
                    n_li += 1
                # asigno el precio a la última línea del item
                li_items[-1].update(importe=it['importe'] if float(it['importe'] or 0) or umed else None,
                                    despacho=it.get('despacho'),
                                    precio=it['precio'] if float(it['precio'] or 0) or umed else None,
                                    qty=(n_li == 1 or qty_pos == 'der') and it['qty'] or None,
                                    bonif=it.get('bonif') if float(it['bonif'] or 0) or umed else None,
                                    iva_id=it.get('iva_id'),
                                    imp_iva=it.get('imp_iva'),
                                    dato_a=it.get('dato_a'),
                                    dato_b=it.get('dato_b'),
                                    dato_c=it.get('dato_c'),
                                    dato_d=it.get('dato_d'),
                                    dato_e=it.get('dato_e'),
                                    u_mtx=it.get('u_mtx'),
                                    cod_mtx=it.get('cod_mtx'),
                                    )

            # reemplazar saltos de linea en observaciones:
            for k in ('obs_generales', 'obs_comerciales'):
                ds = fact.get(k, '')
                if isinstance(ds, str) and '<br/>' in ds:
                    fact[k] = ds.replace('<br/>', '\n')

            # divido las observaciones por linea:
            if fact.get('obs_generales') and not f.has_key('obs') and not f.has_key('ObservacionesGenerales1'):
                obs = "\n<U>Observaciones:</U>\n\n" + fact['obs_generales']
                # limpiar texto (campos dbf) y reemplazar saltos de linea:
                obs = obs.replace('\x00', '').replace('<br/>', '\n')
                for ds in f.split_multicell(obs, 'Item.Descripcion01'):
                    li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, importe=None))
            if fact.get('obs_comerciales') and not f.has_key('obs_comerciales') and not f.has_key('ObservacionesComerciales1'):
                obs = "\n<U>Observaciones Comerciales:</U>\n\n" + fact['obs_comerciales']
                # limpiar texto (campos dbf) y reemplazar saltos de linea:
                obs = obs.replace('\x00', '').replace('<br/>', '\n')
                for ds in f.split_multicell(obs, 'Item.Descripcion01'):
                    li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, importe=None))

            # agrego permisos a descripciones (si corresponde)
            permisos = ['Codigo de Despacho %s - Destino de la mercadería: %s' % (
                p['id_permiso'], self.paises.get(p['dst_merc'], p['dst_merc']))
                for p in fact.get('permisos', [])]

            if f.has_key('permiso.id1') and f.has_key("permiso.delivery1"):
                for i, p in enumerate(fact.get('permisos', [])):
                    self.AgregarDato("permiso.id%d" % (i + 1), p['id_permiso'])
                    pais_dst = self.paises.get(p['dst_merc'], p['dst_merc'])
                    self.AgregarDato("permiso.delivery%d" % (i + 1), pais_dst)
            elif not f.has_key('permisos') and permisos:
                obs = "\n<U>Permisos de Embarque:</U>\n\n" + '\n'.join(permisos)
                for ds in f.split_multicell(obs, 'Item.Descripcion01'):
                    li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, importe=None))
            permisos_ds = ', '.join(permisos)

            # agrego comprobantes asociados
            cmps_asoc = ['%s %s %s' % self.fmt_fact(c['cbte_tipo'], c['cbte_punto_vta'], c['cbte_nro'])
                         for c in fact.get('cbtes_asoc', [])]
            if not f.has_key('cmps_asoc') and cmps_asoc:
                obs = "\n<U>Comprobantes Asociados:</U>\n\n" + '\n'.join(cmps_asoc)
                for ds in f.split_multicell(obs, 'Item.Descripcion01'):
                    li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, importe=None))
            cmps_asoc_ds = ', '.join(cmps_asoc)

            # calcular cantidad de páginas:
            lineas = len(li_items)
            if lineas_max > 0:
                hojas = lineas // (lineas_max - 1)
                if lineas % (lineas_max - 1):
                    hojas = hojas + 1
                if not hojas:
                    hojas = 1
            else:
                hojas = 1

            if HOMO:
                self.AgregarDato("homo", "HOMOLOGACIÓN")

            # mostrar las validaciones no excluyentes de AFIP (observaciones)

            if fact.get('motivos_obs') and fact['motivos_obs'] != '00':
                if not f.has_key('motivos_ds.L'):
                    motivos_ds = "Irregularidades observadas por AFIP (F136): %s" % fact['motivos_obs']
                else:
                    motivos_ds = "%s" % fact['motivos_obs']
            elif HOMO:
                motivos_ds = "Ejemplo Sin validez fiscal - Homologación - Testing"
            else:
                motivos_ds = ""

            if letra_fact in ('A', 'M'):
                msg_no_iva = "\nEl IVA discriminado no puede computarse como Crédito Fiscal (RG2485/08 Art. 30 inc. c)."
                if not f.has_key('leyenda_credito_fiscal') and motivos_ds:
                    motivos_ds += msg_no_iva

            copias = {1: 'Original', 2: 'Duplicado', 3: 'Triplicado'}

            for copia in range(1, num_copias + 1):

                # completo campos y hojas
                for hoja in range(1, hojas + 1):
                    f.add_page()
                    f.set('copia', copias.get(copia, "Adicional %s" % copia))
                    f.set('hoja', str(hoja))
                    f.set('hojas', str(hojas))
                    f.set('pagina', 'Pagina %s de %s' % (hoja, hojas))
                    if hojas > 1 and hoja < hojas:
                        s = 'Continúa en hoja %s' % (hoja + 1)
                    else:
                        s = ''
                    f.set('continua', s)
                    f.set('Item.Descripcion%02d' % (lineas_max + 1), s)

                    if hoja > 1:
                        s = 'Continúa de hoja %s' % (hoja - 1)
                    else:
                        s = ''
                    f.set('continua_de', s)
                    f.set('Item.Descripcion%02d' % (0), s)

                    if DEBUG:
                        print("generando pagina %s de %s" % (hoja, hojas))

                    # establezco datos según configuración:
                    for d in self.datos:
                        if d['pagina'] == 'P' and hoja != 1:
                            continue
                        if d['pagina'] == 'U' and hojas != hoja:
                            # no es la última hoja
                            continue
                        f.set(d['campo'], d['valor'])

                    # establezco campos según tabla encabezado:
                    for k, v in list(fact.items()):
                        f.set(k, v)

                    f.set('Numero', numero_fact)
                    f.set('Fecha', self.fmt_date(fact['fecha_cbte']))
                    f.set('Vencimiento', self.fmt_date(fact['fecha_venc_pago']))

                    f.set('LETRA', letra_fact)
                    f.set('TipoCBTE', "COD.%02d" % int(fact['tipo_cbte']))

                    f.set('Comprobante.L', tipo_fact)
                    f.set('ComprobanteEx.L', tipo_fact_ex)

                    if fact.get('fecha_serv_desde'):
                        f.set('Periodo.Desde', self.fmt_date(fact['fecha_serv_desde']))
                        f.set('Periodo.Hasta', self.fmt_date(fact['fecha_serv_hasta']))
                    else:
                        for k in 'Periodo.Desde', 'Periodo.Hasta', 'PeriodoFacturadoL':
                            f.set(k, '')

                    f.set('Cliente.Nombre', fact.get('nombre', fact.get('nombre_cliente')))
                    f.set('Cliente.Domicilio', fact.get('domicilio', fact.get('domicilio_cliente')))
                    f.set('Cliente.Localidad', fact.get('localidad', fact.get('localidad_cliente')))
                    f.set('Cliente.Provincia', fact.get('provincia', fact.get('provincia_cliente')))
                    f.set('Cliente.Telefono', fact.get('telefono', fact.get('telefono_cliente')))
                    f.set('Cliente.IVA', fact.get('categoria', fact.get('id_impositivo')))
                    f.set('Cliente.CUIT', self.fmt_cuit(str(fact['nro_doc'])))
                    f.set('Cliente.TipoDoc', "%s:" % self.tipos_doc[int(str(fact['tipo_doc']))])
                    f.set('Cliente.Observaciones', fact.get('obs_comerciales'))
                    f.set('Cliente.PaisDestino', self.paises.get(fact.get('pais_dst_cmp'), fact.get('pais_dst_cmp')) or '')

                    if fact['moneda_id']:
                        f.set('moneda_ds', self.monedas_ds.get(fact['moneda_id'], ''))
                    else:
                        for k in 'moneda.L', 'moneda_id', 'moneda_ds', 'moneda_ctz.L', 'moneda_ctz':
                            f.set(k, '')

                    if not fact.get('incoterms'):
                        for k in 'incoterms.L', 'incoterms', 'incoterms_ds':
                            f.set(k, '')

                    li = 0
                    k = 0
                    subtotal = Decimal("0.00")
                    for it in li_items:
                        k = k + 1
                        if k > hoja * (lineas_max - 1):
                            break
                        # acumular subtotal (sin IVA facturas A):
                        if it['importe']:
                            subtotal += Decimal("%.6f" % float(it['importe']))
                            if letra_fact in ('A', 'M') and it['imp_iva']:
                                subtotal -= Decimal("%.6f" % float(it['imp_iva']))
                        # agregar el item si encuadra en la hoja especificada:
                        if k > (hoja - 1) * (lineas_max - 1):
                            if DEBUG:
                                print("it", it)
                            li += 1
                            if it['qty'] is not None:
                                f.set('Item.Cantidad%02d' % li, self.fmt_qty(it['qty']))
                            if it['codigo'] is not None:
                                f.set('Item.Codigo%02d' % li, it['codigo'])
                            if it['umed'] is not None:
                                if it['umed'] and f.has_key("Item.Umed_ds01"):
                                    # recortar descripción:
                                    umed_ds = self.umeds_ds.get(int(it['umed']))
                                    s = f.split_multicell(umed_ds, 'Item.Umed_ds01')
                                    f.set('Item.Umed_ds%02d' % li, s[0])
                            # solo discriminar IVA en A/M (mostrar tasa en B)
                            if letra_fact in ('A', 'M', 'B'):
                                if it.get('iva_id') is not None:
                                    f.set('Item.IvaId%02d' % li, it['iva_id'])
                                    if it['iva_id']:
                                        f.set('Item.AlicuotaIva%02d' % li, self.fmt_iva(it['iva_id']))
                            if letra_fact in ('A', 'M'):
                                if it.get('imp_iva') is not None:
                                    f.set('Item.ImporteIva%02d' % li, self.fmt_pre(it['imp_iva']))
                            if it.get('despacho') is not None:
                                f.set('Item.Numero_Despacho%02d' % li, it['despacho'])
                            if it.get('bonif') is not None:
                                f.set('Item.Bonif%02d' % li, self.fmt_pre(it['bonif']))
                            f.set('Item.Descripcion%02d' % li, it['ds'])
                            if it['precio'] is not None:
                                f.set('Item.Precio%02d' % li, self.fmt_pre(it['precio']))
                            if it['importe'] is not None:
                                f.set('Item.Importe%02d' % li, self.fmt_num(it['importe']))

                            # Datos MTX
                            if it.get('u_mtx') is not None:
                                f.set('Item.U_MTX%02d' % li, it['u_mtx'])
                            if it.get('cod_mtx') is not None:
                                f.set('Item.COD_MTX%02d' % li, it['cod_mtx'])

                            # datos adicionales de items
                            for adic in ['dato_a', 'dato_b', 'dato_c', 'dato_d', 'dato_e']:
                                if adic in it:
                                    f.set('Item.%s%02d' % (adic, li), it[adic])

                    if hojas == hoja:
                        # última hoja, imprimo los totales
                        li += 1

                        # agrego otros tributos
                        lit = 0
                        for it in fact['tributos']:
                            lit += 1
                            if it['desc']:
                                f.set('Tributo.Descripcion%02d' % lit, it['desc'])
                            else:
                                trib_id = int(it['tributo_id'])
                                trib_ds = self.tributos_ds[trib_id]
                                f.set('Tributo.Descripcion%02d' % lit, trib_ds)
                            if it['base_imp'] is not None:
                                f.set('Tributo.BaseImp%02d' % lit, self.fmt_num(it['base_imp']))
                            if it['alic'] is not None:
                                f.set('Tributo.Alicuota%02d' % lit, self.fmt_num(it['alic']) + "%")
                            if it['importe'] is not None:
                                f.set('Tributo.Importe%02d' % lit, self.fmt_imp(it['importe']))

                        # reiniciar el subtotal neto, independiente de detalles:
                        subtotal = Decimal(0)
                        if fact['imp_neto']:
                            subtotal += Decimal("%.6f" % float(fact['imp_neto']))
                        # agregar IVA al subtotal si no es factura A
                        if not letra_fact in ('A', 'M') and fact['imp_iva']:
                            subtotal += Decimal("%.6f" % float(fact['imp_iva']))
                        # mostrar descuento general solo si se utiliza:
                        if 'descuento' in fact and fact['descuento']:
                            descuento = Decimal("%.6f" % float(fact['descuento']))
                            f.set('descuento', self.fmt_imp(descuento))
                            subtotal -= descuento
                        # al subtotal neto sumo exento y no gravado:
                        if fact['imp_tot_conc']:
                            subtotal += Decimal("%.6f" % float(fact['imp_tot_conc']))
                        if fact['imp_op_ex']:
                            subtotal += Decimal("%.6f" % float(fact['imp_op_ex']))
                        # si no se envia subtotal, usar el calculado:
                        if fact.get('imp_subtotal'):
                            f.set('subtotal', self.fmt_imp(fact.get('imp_subtotal')))
                        else:
                            f.set('subtotal', self.fmt_imp(subtotal))

                        # importes generales de IVA y netos gravado / no gravado
                        f.set('imp_neto', self.fmt_imp(fact['imp_neto']))
                        f.set('impto_liq', self.fmt_imp(fact.get('impto_liq')))
                        f.set('impto_liq_nri', self.fmt_imp(fact.get('impto_liq_nri')))
                        f.set('imp_iva', self.fmt_imp(fact.get('imp_iva')))
                        f.set('imp_trib', self.fmt_imp(fact.get('imp_trib')))
                        f.set('imp_total', self.fmt_imp(fact['imp_total']))
                        f.set('imp_subtotal', self.fmt_imp(fact.get('imp_subtotal')))
                        f.set('imp_tot_conc', self.fmt_imp(fact['imp_tot_conc']))
                        f.set('imp_op_ex', self.fmt_imp(fact['imp_op_ex']))

                        # campos antiguos (por compatibilidad hacia atrás)
                        f.set('IMPTO_PERC', self.fmt_imp(fact.get('impto_perc')))
                        f.set('IMP_OP_EX', self.fmt_imp(fact.get('imp_op_ex')))
                        f.set('IMP_IIBB', self.fmt_imp(fact.get('imp_iibb')))
                        f.set('IMPTO_PERC_MUN', self.fmt_imp(fact.get('impto_perc_mun')))
                        f.set('IMP_INTERNOS', self.fmt_imp(fact.get('imp_internos')))

                        # mostrar u ocultar el IVA discriminado si es clase A/B:
                        if letra_fact in ('A', 'M'):
                            f.set('NETO', self.fmt_imp(fact['imp_neto']))
                            f.set('IVALIQ', self.fmt_imp(fact.get('impto_liq', fact.get('imp_iva'))))
                            f.set('LeyendaIVA', "")

                            # limpio etiquetas y establezco subtotal de iva liq.
                            for p in list(self.ivas_ds.values()):
                                f.set('IVA%s.L' % p, "")
                            for iva in fact['ivas']:
                                p = self.ivas_ds[int(iva['iva_id'])]
                                f.set('IVA%s' % p, self.fmt_imp(iva['importe']))
                                f.set('NETO%s' % p, self.fmt_imp(iva['base_imp']))
                                f.set('IVA%s.L' % p, "IVA %s" % self.fmt_iva(iva['iva_id']))
                        else:
                            # Factura C y E no llevan columna IVA (B solo tasa)
                            if letra_fact in ('C', 'E'):
                                f.set('Item.AlicuotaIVA', "")
                            f.set('NETO.L', "")
                            f.set('IVA.L', "")
                            f.set('LeyendaIVA', "")
                            for p in list(self.ivas_ds.values()):
                                f.set('IVA%s.L' % p, "")
                                f.set('NETO%s.L' % p, "")
                        f.set('Total.L', 'Total:')
                        f.set('TOTAL', self.fmt_imp(fact['imp_total']))
                    else:
                        # limpio todas las etiquetas (no es la última hoja)
                        for k in ('imp_neto', 'impto_liq', 'imp_total', 'impto_perc',
                                  'imp_iva', 'impto_liq_nri', 'imp_trib', 'imp_op_ex', 'imp_tot_conc',
                                  'imp_op_ex', 'IMP_IIBB', 'imp_iibb', 'impto_perc_mun', 'imp_internos',
                                  'NGRA.L', 'EXENTO.L', 'descuento.L', 'descuento', 'subtotal.L',
                                  'NETO.L', 'NETO', 'IVA.L', 'LeyendaIVA'):
                            f.set(k, "")
                        for p in list(self.ivas_ds.values()):
                            f.set('IVA%s.L' % p, "")
                            f.set('NETO%s.L' % p, "")
                        f.set('Total.L', 'Subtotal:')
                        f.set('TOTAL', self.fmt_imp(subtotal))

                    f.set('cmps_asoc_ds', cmps_asoc_ds)
                    f.set('permisos_ds', permisos_ds)

                    # Datos del pie de factura (obtenidos desde AFIP):
                    f.set('motivos_ds', motivos_ds)
                    if f.has_key('motivos_ds1') and motivos_ds:
                        if letra_fact in ('A', 'M'):
                            if f.has_key('leyenda_credito_fiscal'):
                                f.set('leyenda_credito_fiscal', msg_no_iva)
                        for i, txt in enumerate(f.split_multicell(motivos_ds, 'motivos_ds1')):
                            f.set('motivos_ds%d' % (i + 1), txt)
                    if not motivos_ds:
                        f.set("motivos_ds.L", "")

                    f.set('CAE', fact['cae'])
                    f.set('CAE.Vencimiento', self.fmt_date(fact['fecha_vto']))
                    if fact['cae'] != "NULL" and str(fact['cae']).isdigit() and str(fact['fecha_vto']).isdigit() and self.CUIT:
                        cuit = ''.join([x for x in str(self.CUIT) if x.isdigit()])
                        barras = ''.join([cuit, "%03d" % int(fact['tipo_cbte']), "%05d" % int(fact['punto_vta']),
                                          str(fact['cae']), fact['fecha_vto']])
                        barras = barras + self.digito_verificador_modulo10(barras)
                    else:
                        barras = ""

                    f.set('CodigoBarras', barras)
                    f.set('CodigoBarrasLegible', barras)

                    if not HOMO and barras and fact.get("resultado") == 'A':
                        f.set('estado', "Comprobante Autorizado")
                    elif fact.get("resultado") == 'R':
                        f.set('estado', "Comprobante Rechazado")
                    elif fact.get("resultado") == 'O':
                        f.set('estado', "Comprobante Observado")
                    elif fact.get("resultado"):
                        f.set('estado', "Comprobante No Autorizado")
                    else:
                        f.set('estado', "")  # compatibilidad hacia atras

                    # colocar campos de observaciones (si no van en ds)
                    if f.has_key('observacionesgenerales1') and 'obs_generales' in fact:
                        for i, txt in enumerate(f.split_multicell(fact['obs_generales'], 'ObservacionesGenerales1')):
                            f.set('ObservacionesGenerales%d' % (i + 1), txt)
                    if f.has_key('observacionescomerciales1') and 'obs_comerciales' in fact:
                        for i, txt in enumerate(f.split_multicell(fact['obs_comerciales'], 'ObservacionesComerciales1')):
                            f.set('ObservacionesComerciales%d' % (i + 1), txt)
                    if f.has_key('enletras1') and 'en_letras' in fact:
                        for i, txt in enumerate(f.split_multicell(fact['en_letras'], 'EnLetras1')):
                            f.set('EnLetras%d' % (i + 1), txt)

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
            self.AgregarCampo("traceback", 'T', 25, 270, 0, 0,
                              size=10, rotate=0, foreground=0xF00000, priority=-1,
                              text="Traceback %s" % (fname, ))
            self.AgregarCampo("excepcion", 'T', 25, 250, 0, 0,
                              size=10, rotate=0, foreground=0xF00000, priority=-1,
                              text="Excepcion %(name)s:%(lineno)s" % ex)
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
            self.Excepcion = ex['msg']
            self.Traceback = ex['tb']
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
        if sys.platform.startswith(("linux", 'java')):
            os.system("evince ""%s""" % archivo)
        else:
            operation = imprimir and "print" or ""
            os.startfile(archivo, operation)
        return True


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"):
    basepath = __file__
elif sys.frozen == 'dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == '__main__':

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
        from configparser import SafeConfigParser

        DEBUG = '--debug' in sys.argv
        utils.safe_console()

        # leeo configuración (primer argumento o rece.ini por defecto)
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
            CONFIG_FILE = sys.argv.pop(1)
        if DEBUG:
            print("CONFIG_FILE:", CONFIG_FILE)

        config = SafeConfigParser()
        config.read(CONFIG_FILE, encoding="latin1")
        conf_fact = dict(config.items('FACTURA'))
        conf_pdf = dict(config.items('PDF'))

        if '--ayuda' in sys.argv:
            print(AYUDA)
            sys.exit(0)

        if '--licencia' in sys.argv:
            print(LICENCIA)
            sys.exit(0)

        if '--formato' in sys.argv:
            if '--dbf' in sys.argv:
                from .formatos import formato_dbf
                formato_dbf.ayuda()
            else:
                from .formatos import formato_txt
                formato_txt.ayuda()
            sys.exit(0)

        fepdf = FEPDF()

        # cargo el formato CSV por defecto (factura.csv)
        fepdf.CargarFormato(conf_fact.get("formato", "factura.csv"))

        # establezco formatos (cantidad de decimales) según configuración:
        fepdf.FmtCantidad = conf_fact.get("fmt_cantidad", "0.2")
        fepdf.FmtPrecio = conf_fact.get("fmt_precio", "0.2")

        if '--cargar' in sys.argv:
            if '--dbf' in sys.argv:
                from .formatos import formato_dbf
                conf_dbf = dict(config.items('DBF'))
                if DEBUG:
                    print("conf_dbf", conf_dbf)
                regs = list(formato_dbf.leer(conf_dbf).values())
            elif '--json' in sys.argv:
                from .formatos import formato_json
                if '--entrada' in sys.argv:
                    entrada = sys.argv[sys.argv.index("--entrada") + 1]
                else:
                    entrada = conf_fact.get("entrada", "entrada.txt")
                if DEBUG:
                    print("entrada", entrada)
                regs = formato_json.leer(entrada)
            else:
                from .formatos import formato_txt
                if '--entrada' in sys.argv:
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
            for d in regs[0]['datos']:
                fepdf.AgregarDato(d['campo'], d['valor'], d['pagina'])

        if '--prueba' in sys.argv:
            # creo una factura de ejemplo
            HOMO = True

            # datos generales del encabezado:
            tipo_cbte = 19 if '--expo' in sys.argv else 201
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
            moneda_id = 'DOL' if '--expo' in sys.argv else 'PES'
            moneda_ctz = 1 if moneda_id == 'PES' else 14.90
            incoterms = 'FOB'                   # solo exportación
            idioma_cbte = 1                     # 1: es, 2: en, 3: pt

            # datos adicionales del encabezado:
            nombre_cliente = 'Joao Da Silva'
            domicilio_cliente = 'Rua 76 km 34.5 Alagoas'
            pais_dst_cmp = 212                  # 200: Argentina, ver tabla
            id_impositivo = 'PJ54482221-l'      # cat. iva (mercado interno)
            forma_pago = '30 dias'

            obs_generales = "Observaciones Generales<br/>linea2<br/>linea3"
            obs_comerciales = "Observaciones Comerciales<br/>texto libre"

            # datos devueltos por el webservice (WSFEv1, WSMTXCA, etc.):
            motivo_obs = "Factura individual, DocTipo: 80, DocNro 30000000007 no se encuentra registrado en los padrones de AFIP."
            cae = "61123022925855"
            fch_venc_cae = "20110320"

            fepdf.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                               cbte_nro, imp_total, imp_tot_conc, imp_neto,
                               imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago,
                               fecha_serv_desde, fecha_serv_hasta,
                               moneda_id, moneda_ctz, cae, fch_venc_cae, id_impositivo,
                               nombre_cliente, domicilio_cliente, pais_dst_cmp,
                               obs_comerciales, obs_generales, forma_pago, incoterms,
                               idioma_cbte, motivo_obs)

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
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            fepdf.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            tributo_id = 4
            desc = 'Impuestos Internos'
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
            despacho = 'Nº 123456'
            dato_a = "Dato A"
            fepdf.AgregarDetalleItem(u_mtx, cod_mtx, codigo, ds, qty, umed,
                                     precio, bonif, iva_id, imp_iva, importe, despacho, dato_a)

            # descuento general (a tasa 21%):
            u_mtx = cod_mtx = codigo = None
            ds = "Bonificación/Descuento 10%"
            qty = precio = bonif = None
            umed = 99
            iva_id = 5
            if tipo_cbte in (1, 2, 3, 4, 5, 34, 39, 51, 52, 53, 54, 60, 64):
                # discriminar IVA si es clase A / M
                imp_iva = -2.21
            else:
                imp_iva = None
            importe = -12.10
            fepdf.AgregarDetalleItem(u_mtx, cod_mtx, codigo, ds, qty, umed,
                                     precio, bonif, iva_id, imp_iva, importe, "")

            # descripción (sin importes ni cantidad):
            u_mtx = cod_mtx = codigo = None
            qty = precio = bonif = iva_id = imp_iva = importe = None
            umed = 0
            ds = "Descripción Ejemplo"
            fepdf.AgregarDetalleItem(u_mtx, cod_mtx, codigo, ds, qty, umed,
                                     precio, bonif, iva_id, imp_iva, importe, "")

            # Agrego un permiso (ver manual para el desarrollador WSFEXv1)
            if '--expo' in sys.argv:
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
        if '--grabar' in sys.argv:
            reg = fepdf.factura.copy()
            reg['id'] = 0
            reg['datos'] = fepdf.datos
            reg['err_code'] = 'OK'
            if '--dbf' in sys.argv:
                from .formatos import formato_dbf
                conf_dbf = dict(config.items('DBF'))
                if DEBUG:
                    print("conf_dbf", conf_dbf)
                regs = formato_dbf.escribir([reg], conf_dbf)
            elif '--json' in sys.argv:
                from .formatos import formato_json
                archivo = conf_fact.get("entrada", "entrada.txt")
                if DEBUG:
                    print("Escribiendo", archivo)
                regs = formato_json.escribir([reg], archivo)
            else:
                from .formatos import formato_txt
                archivo = conf_fact.get("entrada", "entrada.txt")
                if DEBUG:
                    print("Escribiendo", archivo)
                regs = formato_txt.escribir([reg], archivo)

        # datos fijos:
        for k, v in list(conf_pdf.items()):
            fepdf.AgregarDato(k, v)
            if k.upper() == 'CUIT':
                fepdf.CUIT = v  # CUIT del emisor para código de barras

        fepdf.CrearPlantilla(papel=conf_fact.get("papel", "legal"),
                             orientacion=conf_fact.get("orientacion", "portrait"))
        fepdf.ProcesarPlantilla(num_copias=int(conf_fact.get("copias", 1)),
                                lineas_max=int(conf_fact.get("lineas_max", 24)),
                                qty_pos=conf_fact.get("cant_pos") or 'izq')
        salida = conf_fact.get("salida", "")
        fact = fepdf.factura
        if salida:
            pass
        elif 'pdf' in fact and fact['pdf']:
            salida = fact['pdf']
        else:
            # genero el nombre de archivo según datos de factura
            d = conf_fact.get('directorio', ".")
            clave_subdir = conf_fact.get('subdirectorio', 'fecha_cbte')
            if clave_subdir:
                d = os.path.join(d, fact[clave_subdir])
            if not os.path.isdir(d):
                os.makedirs(d)
            fs = conf_fact.get('archivo', 'numero').split(",")
            it = fact.copy()
            tipo_fact, letra_fact, numero_fact = fact['_fmt_fact']
            it['tipo'] = tipo_fact.replace(" ", "_")
            it['letra'] = letra_fact
            it['numero'] = numero_fact
            it['mes'] = fact['fecha_cbte'][4:6]
            it['año'] = fact['fecha_cbte'][0:4]
            fn = ''.join([str(it.get(ff, ff)) for ff in fs])
            fn = fn.encode('ascii', 'replace').replace('?', '_')
            salida = os.path.join(d, "%s.pdf" % fn)
        if DEBUG:
            print("archivo generado", salida)
        fepdf.GenerarPDF(archivo=salida)
        if '--mostrar' in sys.argv:
            fepdf.MostrarPDF(archivo=salida, imprimir='--imprimir' in sys.argv)
