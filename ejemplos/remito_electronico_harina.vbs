'
' Ejemplo de Uso de Interfaz PyAfipWs para Windows Script Host
' (Visual Basic / Visual Fox y lenguages con soporte ActiveX simil OCX)
' con Web Service Autenticaci�n / Remito Electr�nico Harina AFIP
' 2018(C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3
'  Requerimientos: scripts wsaa.py y wsfev1.py registrados (ver instaladores)
' Documentacion:
'  http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoHarina
'  http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
'  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs

' Crear el objeto WSAA (Web Service de Autenticaci�n y Autorizaci�n) AFIP
Set WSAA = Wscript.CreateObject("WSAA")
Wscript.Echo "InstallDir", WSAA.InstallDir, WSAA.Version

' Solicitar Ticket de Acceso
wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" ' Homologaci�n!
scriptdir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
proxy = ""   ' en caso de ser necesario: "usuario:clave@servidor:puerto"
wrapper = "" ' usar "pycurl" como transporte alternativo en caso de inconvenientes con SSL
cacert = ""  ' para verificacion de canal seguro usar: "conf\afip_ca_info.crt"
cache = "C:\WINDOWS\TEMP"
ok = WSAA.Autenticar("wsremharina", scriptdir & "\..\reingart.crt", scriptdir & "\..\reingart.key",  wsdl, proxy, wrapper, cacert, cache)
Wscript.Echo "Excepcion", WSAA.Excepcion
Wscript.Echo "Token", WSAA.Token
Wscript.Echo "Sign", WSAA.Sign

' Crear el objeto WSRemHarina (Web Service de Remito Harinero) AFIP

Set WSRemHarina = Wscript.CreateObject("WSRemHarina")
Wscript.Echo "WSRemHarina Version", WSRemHarina.Version

' Establecer parametros de uso:
WSRemHarina.Cuit = "20267565393"
WSRemHarina.Token = WSAA.Token
WSRemHarina.Sign = WSAA.Sign

' Conectar al websrvice
wsdl = "https://fwshomo.afip.gov.ar/wsremharina/RemHarinaService?wsdl"
timeout = 30    ' tiempo de espera predeterminado
WSRemHarina.Conectar cache, wsdl, proxy, wrapper, cacert, timeout

' Consultar �ltimo comprobante autorizado en AFIP
tipo_comprobante = 993
punto_emision = 1
ult = 1

If ult = 0 Then
    ok = WSRemHarina.ConsultarUltimoRemitoEmitido(tipo_comprobante, punto_emision)

    If ok Then
        ult = WSRemHarina.NroRemito
    Else
        Wscript.Echo WSRemHarina.Traceback, "Traceback"
        Wscript.Echo WSRemHarina.XmlResponse, "XmlResponse"
        Wscript.Echo WSRemHarina.XmlRequest, "XmlRequest"
        ult = 0
    End If
    Wscript.Echo ult, "Ultimo comprobante: "
    Wscript.Echo WSRemHarina.ErrMsg, "ErrMsg:"
    if WSRemHarina.Excepcion <> "" Then Wscript.Echo WSRemHarina.Excepcion, "Excepcion:"
End If

' Calculo el pr�ximo n�mero de comprobante:
If ult = "" Then
    nro_remito = 0                ' no hay comprobantes emitidos
Else
    nro_remito = CLng(ult)        ' convertir a entero largo
End If
nro_remito = nro_remito + 1

' Establezco los valores del remito a autorizar:
tipo_movimiento = "ENV"  ' ENV: envio, RET: retiro, CAN: canje, RED: redestino
cuit_titular = "20267565393"
es_entrega_mostrador = "N"
es_mercaderia_consignacion = "N"
cuit_titular = "20267565393"
importe_cot = "10000.0"
tipo_emisor = "I"        ' U: Usiario de molienda de trigo I: Industrial
ruca_est_emisor = 1031
cod_rem_redestinar = Null
cod_remito = Null
estado = Null
observaciones = Null

ok = WSRemHarina.CrearRemito(tipo_comprobante, punto_emision, tipo_movimiento, _
                    cuit_titular, es_entrega_mostrador, es_mercaderia_consignacion, _
                    importe_cot, _
                    tipo_emisor, ruca_est_emisor, _
                    cod_rem_redestinar, _
                    cod_remito, estado, observaciones)

cuit_pais_receptor = "55000002002"
cuit_receptor = "20111111112"
tipo_dom_receptor = 1    ' 1: fiscal, 3: comercial
cod_dom_receptor = 1234
cuit_despachante = Null
codigo_aduana = Null
denominacion_receptor = Null
domicilio_receptor = Null

ok = WSRemHarina.AgregarReceptor(cuit_pais_receptor, _
                        cuit_receptor, tipo_dom_receptor, cod_dom_receptor, _
                        cuit_despachante, codigo_aduana, _
                        denominacion_receptor, domicilio_receptor):

tipo_depositario = "E"  ' I: Industrial de Molino/Trigo, E: Emisor D: Depositario
cuit_depositario = "23000000019"
ruca_est_depositario = 7297
tipo_dom_origen = 1
cod_dom_origen = 1

ok = WSRemHarina.AgregarDepositario(tipo_depositario, cuit_depositario, ruca_est_depositario, _
                                 tipo_dom_origen=None, cod_dom_origen)

' Agrego el viaje:
fecha_inicio_viaje = "2018-10-01"
distancia_km = 999
ok = WSRemHarina.AgregarViaje(fecha_inicio_viaje, distancia_km)

cod_pais_transportista = 200
cuit_transportista = "20333333334"
cuit_conductor = "20333333334"
apellido_conductor = Null
cedula_conductor = Null
denom_transportista = Null
id_impositivo = Null
nombre_conductor = Null

ok = WSRemHarina.AgregarTransportista(cod_pais_transportista, _
                          cuit_transportista, cuit_conductor, _
                          apellido_conductor, cedula_conductor, denom_transportista, _
                          id_impositivo, nombre_conductor)

' Agregar vehiculo al viaje
dominio_vehiculo = "AAA000"
dominio_acoplado = "ZZZ000"
ok = WSRemHarina.AgregarVehiculo(dominio_vehiculo, dominio_acoplado)

' Agregar Mercaderia
orden = 1
cod_tipo = 0
cod_tipo_emb = 0
cantidad_emb = 0
cod_tipo_unidad = 0
cant_unidad = 0
ok = WSRemHarina.AgregarMercaderia(orden, cod_tipo, cod_tipo_emb, cantidad_emb, cod_tipo_unidad, cant_unidad)

' WSRemHarina.AgregarContingencias(tipo=1, observacion="anulacion")

' Solicito CodRemito:
id_req = Int(DateDiff("s","24-Sep-23 00:00:00", Now))     ' usar un numero interno �nico / clave primaria (id_remito)
archivo = "qr.png"
ok = WSRemHarina.GenerarRemito(id_req, archivo)

If not ok Then
    ' Imprimo pedido y respuesta XML para depuraci�n (errores de formato)
    Wscript.Echo "Traceback", WSRemHarina.Traceback
    Wscript.Echo "XmlResponse", WSRemHarina.XmlResponse
    Wscript.Echo "XmlRequest", WSRemHarina.XmlRequest
End If

Wscript.Echo "Resultado: ", WSRemHarina.Resultado
Wscript.Echo "Cod Remito: ", WSRemHarina.CodRemito
If WSRemHarina.CodAutorizacion Then
    Wscript.Echo "Numero Remito: ", WSRemHarina.NumeroRemito
    Wscript.Echo "Cod Autorizacion: ", WSRemHarina.CodAutorizacion
    Wscript.Echo "Fecha Emision", WSRemHarina.FechaEmision
    Wscript.Echo "Fecha Vencimiento", WSRemHarina.FechaVencimiento
End If
Wscript.Echo "Estado: ", WSRemHarina.Estado
Wscript.Echo "Observaciones: ", WSRemHarina.Obs
Wscript.Echo "Errores:", WSRemHarina.ErrMsg
Wscript.Echo "Evento:", WSRemHarina.Evento

MsgBox "Resultado:" & WSRemHarina.Resultado & " CodRemito: " & WSRemHarina.CodRemito, vbInformation + vbOKOnly
