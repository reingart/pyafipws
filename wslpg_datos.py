#!/usr/bin/python
# -*- coding: utf8 -*-
from decimal import Decimal

TIPOS_OP = {1: 'Compraventa de granos', 2: 'Consignación de granos'}
GRANOS = {
        1: 'LINO', 2: 'GIRASOL', 3: 'MANI EN CAJA', 
        4: 'GIRASOL DESCASCARADO', 5: 'MANI PARA INDUSTRIA DE SELECCION', 
        6: 'MANI PARA INDUSTRIA ACEITERA', 7: 'MANI TIPO CONFITERIA',
        8: 'COLZA', 9: 'COLZA 00 CANOLA', 10: 'TRIGO FORRAJERO',
        11: 'CEBADA FORRAJERA', 12: 'CEBADA APTA PARA MALTERIA',
        14: 'TRIGO CANDEAL', 15: 'TRIGO PAN',
        16: 'AVENA', 17: 'CEBADA CERVECERA', 18: 'CENTENO',
        19: 'MAIZ', 20: 'MIJO', 21: 'ARROZ CASCARA',
        22: 'SORGO GRANIFERO', 23: 'SOJA', 25: 'TRIGO PLATA',
        26: 'MAIZ FLYNT O PLATA', 27: 'MAIZ PISINGALLO',
        28: 'TRITICALE', 30: 'ALPISTE', 31: 'ALGODON', 32: 'CARTAMO',
        33: 'POROTO BLANCO NATURAL OVAL Y ALUBIA',
        34: 'POROTO DISTINTO DEL BLANCO OVAL Y ALUBIA',
        35: 'ARROZ', 46: 'LENTEJA', 47: 'ARVEJA',
        48: 'POROTO BLANCO SELECCIONADO OVAL Y ALUBIA',
        49: 'OTRAS LEGUMBRES', 50: 'OTROS GRANOS', 59: 'GARBANZO', }
                
PUERTOS = {1: "SAN LORENZO/SAN MARTIN", 2: "ROSARIO", 
           3: "BAHIA BLANCA", 4: "NECOCHEA", 5: "RAMALLO", 6: "LIMA",
           7: "DIAMANTE", 8: "BUENOS AIRES", 9: "SAN PEDRO", 
           10: "SAN NICOLAS", 11: "TERMINAL DEL GUAZU", 12: "ZARATE",
           13: "VILLA CONSTITUCION"}

PROVINCIAS = {1: 'BUENOS AIRES', 0: 'CAPITAL FEDERAL', 
              2: 'CATAMARCA', 16: 'CHACO', 17: 'CHUBUT', 
              4: 'CORRIENTES', 3: 'CÓRDOBA', 5: 'ENTRE RIOS',
              18: 'FORMOSA', 6: 'JUJUY', 21: 'LA PAMPA',
              8: 'LA RIOJA', 7: 'MENDOZA', 19: 'MISIONES', 
              20: 'NEUQUÉN', 22: 'RIO NEGRO', 9: 'SALTA',
              10: 'SAN JUAN', 11: 'SAN LUIS', 23: 'SANTA CRUZ',
              12: 'SANTA FE', 13: 'SANTIAGO DEL ESTERO',
              24: 'TIERRA DEL FUEGO', 14: 'TUCUMÁN'}

TIPO_CERT_DEP = {1: "F1116/RT", 5: "F1116/A", 332: "Cert.Elec."}

CAMPANIAS = {1213: "2012/2013", 1112: "2011/2012", 1011: "2010/2011",
             910: "2009/2010", 809: "2008/2009", 708: "2007/2008",
             607: "2006/2007", 506: "2005/2006", 405: "2004/2005",
             304: "2003/2004", 1314: "2013/2014", 1415: "2014/2015"}

ACTIVIDADES = {41: "FRACCIONADOR DE GRANOS", 29: "ACOPIADOR - CONSIGNATARIO",
               33: "CANJEADOR DE BIENES Y/O SERVICIOS POR GRANO", 
               40: "EXPORTADOR", 31: "ACOPIADOR DE MANÍ", 
               30: "ACOPIADOR DE LEGUMBRES", 
               35: "COMPRADOR DE GRANO PARA CONSUMO PROPIO",
               44: "INDUSTRIAL ACEITERO", 47: "INDUSTRIAL BIOCOMBUSTIBLE",
               46: "INDUSTRIAL BALANCEADOR", 48: "INDUSTRIAL CERVECERO",
               49: "INDUSTRIAL DESTILERIA", 
               51: "INDUSTRIAL MOLINO DE HARINA DE TRIGO",
               50: "INDUSTRIAL MOLINERO", 45: "INDUSTRIAL ARROCERO",
               59: "USUARIO DE MOLIENDA DE TRIGO(incluye MAQUILA)",
               57: "USUARIO DE INDUSTRIA (Otros granos MENOS trigo)",
               52: "INDUSTRIAL SELECCIONADOR", 34: "COMPLEJO INDUSTRIAL",
               28: "ACONDICIONADOR", 36: "CORREDOR", 
               55: "MERCADO DE FUTUROS Y OPCIONES O MERCADO A TERMINO",
               39: "EXPLOTADOR DE DEPOSITO Y/O ELEVADOR DE GRANOS",
               37: "DESMOTADOR DE ALGODON",
               }

# Grados
GRADOS_REF = {'G3': 'Grado 3', 'G2': 'Grado 2', 'G1': 'Grado 1'}

# Datos de grado entregado por tipo de granos:
GRADO_ENT_VALOR = {
    49 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    25 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    26 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    27 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    20 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    21 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    22 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    23 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    46 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    47 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    48 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    28 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    1 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    3 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    2 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    5 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    4 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    7 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    6 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    9 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    8 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    59 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    11 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    10 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    12 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    15 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.99'), 'G2': Decimal('1.00'), 'G1': Decimal('1.015'), 'FG': Decimal('0')},
    14 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    17 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    16 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    19 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    18 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    31 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    30 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    50 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    35 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    34 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    33 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
    32 : {'F1': Decimal('0'), 'F2': Decimal('0'), 'F3': Decimal('0'), 'G3': Decimal('0.985'), 'G2': Decimal('1.00'), 'G1': Decimal('1.01'), 'FG': Decimal('0')},
}

# Diccionario de localidades por provincia 
# (wslpg.py lo reemplaza con un shelve si es posible)
LOCALIDADES = {}

