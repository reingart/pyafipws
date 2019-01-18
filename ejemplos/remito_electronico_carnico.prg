*-- 
*-- Ejemplo de Uso de Interfaz PyAfipWs para Windows Script Host
*-- (Visual Basic / Visual Fox y lenguages con soporte ActiveX simil OCX)
*-- con Web Service Autenticaci髇 / Remito Electr髇ico C醤ico AFIP
*-- 2018(C) Mariano Reingart <reingart@gmail.com>
*-- Licencia: GPLv3
*--  Requerimientos: scripts wsaa.py y wsfev1.py registrados (ver instaladores)
*-- Documentacion: 
*--  http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCarnico
*--  http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
*--  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
 
&& ON ERROR DO errhand1;

CLEAR

*-- Crear objeto interface Web Service Autenticaci贸n y Autorizaci贸n
WSAA = CREATEOBJECT("WSAA") 

*-- solicito ticket de acceso
ta = Autenticar()

ON ERROR

&& ON ERROR DO errhand2;

*-- Crear el objeto WSRemCarne (Web Service de Factura Electr髇ica version 1) AFIP

WSRemCarne = CreateObject("WSRemCarne")
? "WSRemCarne Version", WSRemCarne.Version

*--  Establecer parametros de uso:
WSRemCarne.Cuit = "20267565393"
WSRemCarne.SetTicketAcceso(ta)

*--  Conectar al websrvice
wsdl = "https://fwshomo.afip.gov.ar/wsremcarne/RemCarneService?wsdl"
ok = WSRemCarne.Conectar("", wsdl)

*-- Consultar 鷏timo comprobante autorizado en AFIP (ejemplo, no es obligatorio)
tipo_comprobante = 995
punto_emision = 1

If .F. Then

	ok = WSRemCarne.ConsultarUltimoRemitoEmitido(tipo_comprobante, punto_emision)

	If ok Then
	    ult = WSRemCarne.NroRemito
	Else
	    ? WSRemCarne.Traceback, "Traceback"
	    ? WSRemCarne.Traceback, "XmlResponse"
	    ? WSRemCarne.Traceback, "XmlRequest"
	    ult = 0
	EndIf
	? "Ultimo comprobante: ", ult
Else
	ult = ""
EndIf

*-- Calculo el pr髕imo n鷐ero de comprobante:
If ult = "" Then
    nro_remito = 0               && no hay comprobantes emitidos
Else
    nro_remito = INT(ult)        && convertir a entero largo
EndIf
nro_remito = nro_remito + 1

*-- Establezco los valores del remito a autorizar:
tipo_movimiento = "ENV" && ENV: Envio Normal, PLA: Retiro en planta, REP: Reparto, RED: Redestino
categoria_emisor = 1
cuit_titular_mercaderia = "20222222223"
cod_dom_origen = 1
tipo_receptor = "EM"  && "EM": DEPOSITO EMISOR, "MI": MERCADO INTERNO, "RP": REPARTO
caracter_receptor = 1
cuit_receptor = "20111111112"
cuit_depositario = Null
cod_dom_destino = 1
cod_rem_redestinar = Null
cod_remito = Null
estado = Null

ok = WSRemCarne.CrearRemito(tipo_comprobante, punto_emision, tipo_movimiento, categoria_emisor, ;
                            cuit_titular_mercaderia, cod_dom_origen, tipo_receptor, ;
                            caracter_receptor, cuit_receptor, cuit_depositario, ;
                            cod_dom_destino, cod_rem_redestinar, cod_remito, estado)

*-- Agrego el viaje:
cuit_transportista = "20333333334"
cuit_conductor = "20333333334"
fecha_inicio_viaje = "2018-10-01"
distancia_km = 999
ok = WSRemCarne.AgregarViaje(cuit_transportista, cuit_conductor, fecha_inicio_viaje, distancia_km)

*-- Agregar vehiculo al viaje
dominio_vehiculo = "AAA000"
dominio_acoplado = "ZZZ000"
ok = WSRemCarne.AgregarVehiculo(dominio_vehiculo, dominio_acoplado)

*-- Agregar Mercaderia
orden = 1
tropa = 1
cod_tipo_prod = "2.13"  && http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCarnico#Tiposdecarne
cantidad = 10
unidades=1
ok = WSRemCarne.AgregarMercaderia(orden, cod_tipo_prod, cantidad, unidades, tropa)

*-- WSRemCarne.AgregarContingencias(tipo=1, observacion="anulacion")

*-- Armo un ID 鷑ico (usar clave primaria de tabla de remito o similar!)
id_cliente = 1

*-- Solicito CodRemito:
archivo = "qr.png"
WSRemCarne.LanzarExcepciones = .F.
ok = WSRemCarne.GenerarRemito(id_cliente, archivo)

If not ok Then 
    *-- Imprimo pedido y respuesta XML para depuraci髇 (errores de formato)
    ? "Traceback", WSRemCarne.Traceback
    ? "XmlResponse", WSRemCarne.Traceback
    ? "XmlRequest", WSRemCarne.Traceback
EndIf

? "Resultado: ", WSRemCarne.Resultado
? "Cod Remito: ", WSRemCarne.CodRemito
If WSRemCarne.CodAutorizacion Then
    ? "Numero Remito: ", WSRemCarne.NumeroRemito
    ? "Cod Autorizacion: ", WSRemCarne.CodAutorizacion
    ? "Fecha Emision", WSRemCarne.FechaEmision
    ? "Fecha Vencimiento", WSRemCarne.FechaVencimiento
EndIf
? "Observaciones: ", WSRemCarne.Obs
? "Errores:", WSRemCarne.ErrMsg
? "Evento:", WSRemCarne.Evento

&& MESSAGEBOX("Resultado:" + WSRemCarne.Resultado, 0, "WsRemCarne")


*-- Procedimiento para autenticar y reutilizar el ticket de acceso
PROCEDURE Autenticar 
	ON ERROR DO errhand1

   
	*-- Crear objeto interface Web Service Autenticacion y Autorizacion
	WSAA = CREATEOBJECT("WSAA") 
	
	*-- ubicaci髇 del ticket de acceso (puede guardarse tambi閚 en memoria)
	*-- (en el mismo directorio que el programa -predeterminado-)
	ruta_prg = SYS(16,1) 
    inicio = AT(":", ruta_prg)- 1
    longitud = RAT("\", ruta_prg) - (inicio)
    ruta = (SUBSTR(ruta_prg, inicio, longitud)) + "\"
	archivo = ruta + 'TA.xml'
	? "ruta archivo", archivo

	f = FOPEN(archivo)  
	IF f = -1 THEN
		ta = ""		&& no existe el TA previo
	ELSE
		ta = FREAD(f, 65535)
		? "TA leido:", ta
		=FCLOSE(f)
	ENDIF
	ok = WSAA.AnalizarXml(ta)
	expiracion = WSAA.ObtenerTagXml("expirationTime")
	? "Fecha Expiracion ticket: ", expiracion
	IF ISNULL(expiracion) THEN
	    solicitar = .T.         					&& solicitud inicial
	ELSE
		solicitar = WSAA.Expirado(expiracion)		&& chequear solicitud previa
	ENDIF
	
	IF solicitar THEn
		*-- Generar un Ticket de Requerimiento de Acceso (TRA)
		tra = WSAA.CreateTRA("wsremcarne")
		*-- uso la ruta a la carpeta de instalaci騨 con los certificados de prueba
		ruta = WSAA.InstallDir + "\"
		? "ruta", ruta

		*-- Generar el mensaje firmado (CMS) 
		cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") && Cert. Demo
		
		*-- Produccion usar: ta = WSAA.Conectar("", "https://wsaa.afip.gov.ar/ws/services/LoginCms") && Producci贸n
		
		ok = WSAA.Conectar("", "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") && Homologaci贸n

		*-- Llamar al web service para autenticar
		ta = WSAA.LoginCMS(cms)
		
		*-- Grabo el ticket de acceso para poder reutilizarlo
		*-- (revisar temas de seguridad y permisos)
		f = FCREATE(archivo)  
		w = FWRITE(f, ta)
		=FCLOSE(f)

	ELSE
		? "no expirado!", "Reutilizando!"
	ENDIF
	
	*-- devuelvo el ticket de acceso
	RETURN ta
ENDPROC
*-- Depuraci髇 (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSFE.Token + CHR(13))
* =FWRITE(gnErrFile, WSFE.Sign + CHR(13))	
* =FWRITE(gnErrFile, WSFE.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, WSFE.XmlResponse + CHR(13))
* =FWRITE(gnErrFile, WSFE.Excepcion + CHR(13))
* =FWRITE(gnErrFile, WSFE.Traceback + CHR(13))
* =FCLOSE(gnErrFile)  


*-- Procedimiento para manejar errores WSAA
PROCEDURE errhand1
	*--PARAMETER merror, mess, mess1, mprog, mlineno
	
	? WSAA.Excepcion
	? WSAA.Traceback
	*--? WSAA.XmlRequest
	*--? WSAA.XmlResponse

	*-- trato de extraer el c贸digo de error de afip (1000)
	afiperr = ERROR() -2147221504 
	if afiperr>1000 and afiperr<2000 then
		? 'codigo error afip:',afiperr
	else
		afiperr = 0
	endif
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSAA.Excepcion, 5 + 48, "Error:")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC

*-- Procedimiento para manejar errores WSFE
PROCEDURE errhand2
	*--PARAMETER merror, mess, mess1, mprog, mlineno
	
	? WSRemCarne.Excepcion
	? WSRemCarne.Traceback
	*--? WSFE.XmlRequest
	*--? WSFE.XmlResponse
		
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSRemCarne.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC
