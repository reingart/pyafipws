# Ejemplo de Uso para presentar REMITO ELECTRONICO ARBA
# 2022 (C) Mariano Reingart <reingart@gmail.com>
# Licencia: GPLv3

import json
import sys

from cot import COT

URL = "http://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"
PROXY = None if not "--proxy" in sys.argv else "user:pass@host:1234"
SALIDA = "/tmp/salida_cot.json"

cot = COT()
filename = sys.argv[1]      # TB_20111111112_000000_20080124_000001.txt
cot.Usuario = sys.argv[2]   # 20267565393
cot.Password = sys.argv[3]  # 23456

if '--testing' in sys.argv:
    #test_response = "cot_response_multiple_errores.xml"
    test_response = "cot_respuesta_2019.xml"
else:
    test_response = ""

cot.Conectar(URL, trace='--trace' in sys.argv, cacert="conf/darba.crt", proxy=PROXY)
cot.PresentarRemito(filename, testing=test_response)

resultado = {
        "cuit_empresa": cot.CuitEmpresa,
        "numero_Comprobante": cot.NumeroComprobante,
        "nombre_archivo": cot.NombreArchivo,
        "codigo_integridad": cot.CodigoIntegridad,
}

if cot.Excepcion:
    resultado['excepcion'] = cot.Excepcion
    resultado['traceback'] = cot.Traceback

if cot.TipoError:
    resultado.update({
        "tipo_error": cot.TipoError,
        "codigo_error": cot.CodigoError,
        "mensaje_error": cot.MensajeError,
    })

# recorro los remitos devueltos e imprimo sus datos por cada uno:
resultado["validaciones_remitos"] = []
while cot.LeerValidacionRemito():
    remito = {
        "numero_unico": cot.NumeroUnico,
        "procesado": cot.Procesado,
        "COT": cot.COT,
        "errores": [],
    }
    while cot.LeerErrorValidacion():
        remito["errores"].append({
            "codigo_error": cot.CodigoError,
            "mensaje_error": cot.MensajeError,
        })
    resultado["validaciones_remitos"].append(remito)

print(json.dumps(resultado, indent=4))
with open(SALIDA, "w") as salida:
    json.dump(resultado, salida)
