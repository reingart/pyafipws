#!usr/bin/python
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

"Régimen de información de Compras y Ventas RG3685/14 AFIP"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2016 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

import sys 
from utils import leer, escribir, C, N, A, I, B, get_install_dir


# Diseño de registro de Importación de comprobantes de Ventas

REGINFO_CV_VENTAS_CBTE = [
    ('fecha_cbte', 8, N),
    ('tipo_cbte', 3, N),
    ('punto_vta', 5, N),
    ('cbt_desde', 20, N),
    ('cbt_hasta', 20, N),
    ('tipo_doc', 2, N),
    ('nro_doc', 20, N),
    ('nombre', 30, A),
    ('imp_total', 15, I),
    ('imp_tot_conc', 15, I),
    ('impto_liq_rni', 15, I),
    ('imp_op_ex', 15, I),
    ('impto_perc', 15, I),
    ('imp_iibb', 15, I),
    ('impto_perc_mun', 15, I),
    ('imp_internos', 15, I),
    ('moneda_id', 3, A),
    ('moneda_ctz', 10, I, 6),
    ('cant_alicuota_iva', 1, N),
    ('codigo_operacion', 1, C),
    ('imp_trib', 15, I),
    ('fecha_venc_pago', 8, A),
    ]

# Diseño de registro de Importación de Alícuotas de comprobantes de Ventas

REGINFO_CV_VENTAS_CBTE_ALICUOTA = [
    ('tipo_cbte', 3, N),
    ('punto_vta', 5, N),
    ('cbt_numero', 20, N),
    ('base_imp', 15, I),
    ('iva_id', 4, N),
    ('importe', 15, I),
    ]


if __name__ == "__main__":

    print "Usando formato registro RG3685 (regimen informativo compras/ventas)"

    if '--caea' in sys.argv:
        caea = sys.argv[sys.argv.index("--caea")+1]
        print "Usando CAEA:", caea
    else:
        caea = ""
    
    if '--serv' in sys.argv:
        fecha_serv_desde = sys.argv[sys.argv.index("--serv")+1]
        fecha_serv_hasta = sys.argv[sys.argv.index("--serv")+2]
        concepto = 2
    else:
        concepto = 1

    ops = {}
    for linea in open("CAB.txt"):
        reg = leer(linea, REGINFO_CV_VENTAS_CBTE)
        reg["cae"] = caea
        reg["concepto"] = concepto
        if concepto == 2:
            reg["fecha_serv_desde"] = fecha_serv_desde
            reg["fecha_serv_hasta"] = fecha_serv_hasta
        else:
            del reg['fecha_venc_pago']
        key = (reg["tipo_cbte"], reg["punto_vta"], reg["cbt_desde"])
        ops[key] = reg
        print key

    for linea in open("ALI.txt"):
        iva = leer(linea, REGINFO_CV_VENTAS_CBTE_ALICUOTA)
        key = (iva["tipo_cbte"], iva["punto_vta"], iva["cbt_numero"])
        reg = ops[key]
        reg["imp_neto"] = reg.get("imp_neto", 0.00) + iva["base_imp"]
        reg["imp_iva"] = reg.get("imp_iva", 0.00) + iva["importe"]
        reg.setdefault("iva", []).append(iva)

    import rece1
    facts = sorted(ops.values(), 
                key=lambda f: (f["tipo_cbte"], f["punto_vta"], f["cbt_desde"]))
    rece1.escribir_facturas(facts, open("entrada.txt", "w"))
    
    print "Hecho."

