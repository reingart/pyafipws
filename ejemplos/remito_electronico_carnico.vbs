' 
' Ejemplo de Uso de Interfaz PyAfipWs para Windows Script Host
' (Visual Basic / Visual Fox y lenguages con soporte ActiveX simil OCX)
' con Web Service Autenticación / Remito Electrónico Cánico AFIP
' 2018(C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3
'  Requerimientos: scripts wsaa.py y wsfev1.py registrados (ver instaladores)
' Documentacion: 
'  http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCarnico
'  http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
'  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
 
' Crear el objeto WSAA (Web Service de Autenticación y Autorización) AFIP
Set WSAA = Wscript.CreateObject("WSAA")
Wscript.Echo "InstallDir", WSAA.InstallDir, WSAA.Version

' Solicitar Ticket de Acceso
wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" ' Homologación!
scriptdir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
proxy = ""   ' en caso de ser necesario: "usuario:clave@servidor:puerto"
wrapper = "" ' usar "pycurl" como transporte alternativo en caso de inconvenientes con SSL
cacert = ""  ' para verificacion de canal seguro usar: "conf\afip_ca_info.crt"
ok = WSAA.Autenticar("wsremcarne", scriptdir & "\..\reingart.crt", scriptdir & "\..\reingart.key",  wsdl, proxy, wrapper, cacert)
Wscript.Echo "Excepcion", WSAA.Excepcion
Wscript.Echo "Token", WSAA.Token
Wscript.Echo "Sign", WSAA.Sign

' Crear el objeto WSRemCarne (Web Service de Factura Electrónica version 1) AFIP

Set WSRemCarne = Wscript.CreateObject("WSRemCarne")
Wscript.Echo "WSRemCarne Version", WSRemCarne.Version

' Establecer parametros de uso:
WSRemCarne.Cuit = "20267565393"
WSRemCarne.Token = WSAA.Token
WSRemCarne.Sign = WSAA.Sign

' Conectar al websrvice
wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
timeout = 30    ' tiempo de espera predeterminado
WSRemCarne.Conectar "", wsdl, proxy, wrapper, cacert, timeout

' Consultar último comprobante autorizado en AFIP
tipo_comprobante = 995
punto_emision = 1
ok = WSRemCarne.ConsultarUltimoRemitoEmitido(tipo_comprobante, punto_emision)

If ok Then
    ult = WSRemCarne.NroRemito
Else
    Wscript.Echo WSRemCarne.Traceback, "Traceback"
    Wscript.Echo WSRemCarne.Traceback, "XmlResponse"
    Wscript.Echo WSRemCarne.Traceback, "XmlRequest"
    ult = 0
End If
Wscript.Echo ult, "Ultimo comprobante: "
Wscript.Echo WSRemCarne.ErrMsg, "ErrMsg:"
if WSRemCarne.Excepcion <> "" Then Wscript.Echo WSRemCarne.Excepcion, "Excepcion:"


' Calculo el próximo número de comprobante:
If ult = "" Then
    nro_remito = 0                ' no hay comprobantes emitidos
Else
    nro_remito = CLng(ult)        ' convertir a entero largo
End If
nro_remito = nro_remito + 1

' Establezco los valores del remito a autorizar:
tipo_movimiento = "ENV"  ' ENV: Envio Normal, PLA: Retiro en planta, REP: Reparto, RED: Redestino
categoria_emisor = 1
cuit_titular_mercaderia = "20222222223"
cod_dom_origen = 1
tipo_receptor = "EM"  ' "EM": DEPOSITO EMISOR, "MI": MERCADO INTERNO, "RP": REPARTO
caracter_receptor = 1
cuit_receptor = "20111111112"
cuit_depositario = Null
cod_dom_destino = 1
cod_rem_redestinar = Null
cod_remito = Null
estado = Null

ok = WSRemCarne.CrearRemito(tipo_comprobante, punto_emision, tipo_movimiento, categoria_emisor, _
                            cuit_titular_mercaderia, cod_dom_origen, tipo_receptor, _
                            caracter_receptor, cuit_receptor, cuit_depositario, _
                            cod_dom_destino, cod_rem_redestinar, cod_remito, estado)

' Agrego el viaje:
cuit_transportista = "20333333334"
cuit_conductor = "20333333334"
fecha_inicio_viaje = "2018-10-01"
distancia_km = 999
ok = WSRemCarne.AgregarViaje(cuit_transportista, cuit_conductor, fecha_inicio_viaje, distancia_km)

' Agregar vehiculo al viaje
dominio_vehiculo = "AAA000"
dominio_acoplado = "ZZZ000"
ok = WSRemCarne.AgregarVehiculo(dominio_vehiculo, dominio_acoplado)

' Agregar Mercaderia
orden = 1
tropa = 1
cod_tipo_prod = "2.13"  ' http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCarnico#Tiposdecarne
cantidad = 10
unidades=1
ok = WSRemCarne.AgregarMercaderia(orden, cod_tipo_prod, cantidad, unidades, tropa)

' WSRemCarne.AgregarContingencias(tipo=1, observacion="anulacion")

' Solicito CodRemito:
id_cliente = Int(DateDiff("s","20-Oct-18 00:00:00", Now))     ' usar un numero interno único / clave primaria (id_remito)
archivo = "qr.png"
ok = WSRemCarne.GenerarRemito(id_cliente, archivo)

If not ok Then 
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Wscript.Echo "Traceback", WSRemCarne.Traceback
    Wscript.Echo "XmlResponse", WSRemCarne.Traceback
    Wscript.Echo "XmlRequest", WSRemCarne.Traceback
End If

Wscript.Echo "Resultado: ", WSRemCarne.Resultado
Wscript.Echo "Cod Remito: ", WSRemCarne.CodRemito
If WSRemCarne.CodAutorizacion Then
    Wscript.Echo "Numero Remito: ", WSRemCarne.NumeroRemito
    Wscript.Echo "Cod Autorizacion: ", WSRemCarne.CodAutorizacion
    Wscript.Echo "Fecha Emision", WSRemCarne.FechaEmision
    Wscript.Echo "Fecha Vencimiento", WSRemCarne.FechaVencimiento
End If
Wscript.Echo "Observaciones: ", WSRemCarne.Obs
Wscript.Echo "Errores:", WSRemCarne.ErrMsg
Wscript.Echo "Evento:", WSRemCarne.Evento

MsgBox "Resultado:" & WSRemCarne.Resultado & " CodRemito: " & WSRemCarne.CodRemito, vbInformation + vbOKOnly

