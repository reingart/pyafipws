*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- WebService de Consulta de Operaciones Cambiarias RG3210/11
*-- 2011 (C) Mariano Reingart <reingart@gmail.com>

*-- ON ERROR DO errhand;

CLEAR

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 

*-- Deshabilito lanzar errores (revisar manualmente)
WSAA.LanzarExcepciones = .F.

*-- Generar un Ticket de Requerimiento de Acceso (TRA)
tra = WSAA.CreateTRA("wscoc")

*-- obtengo el path actual de los certificados para pasarle a la interfase
cCurrentProcedure = SYS(16,1) 
nPathStart = AT(":",cCurrentProcedure)- 1
nLenOfPath = RAT("\", cCurrentProcedure) - (nPathStart)
ruta = (SUBSTR(cCurrentProcedure, nPathStart, nLenofPath)) + "\"
? "ruta",ruta

*-- Generar el mensaje firmado (CMS)
cert = "olano.crt"
priv = "olanoycia.key" 
cms = WSAA.SignTRA(tra, ruta + cert, ruta + priv) && Cert. Demo
*-- cms = WSAA.SignTRA(tra, ruta + "homo.crt", ruta + "homo.key") 
? "CMS", cms
? WSAA.Traceback

*-- Me conecto al servicio web
url_wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" && Homologación
ok = WSAA.Conectar("", url_wsdl)
IF ok = .F. THEN
	? WSAA.Traceback
	ch = MESSAGEBOX(WSAA.Excepcion, 5 + 48, "Imposible Conectar:")
	CANCEL
ENDIF

*-- Llamar al web service para autenticar
*-- Producción usar: ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") && Producción
ta = WSAA.LoginCMS(cms)

IF ta == "" THEN
	? WSAA.Traceback
	ch = MESSAGEBOX(WSAA.Excepcion, 5 + 48, "Imposible obtener Ticket de Acceso")
	CANCEL
ENDIF



*-- Una vez obtenido, se puede usar el mismo token y sign por 12 horas
*-- (este período se puede cambiar)


*-- Crear objeto interface Web Service de Factura Electrónica
WSCOC = CREATEOBJECT("WSCOC") 

* WSCOC.LanzarExcepciones = .F.

*-- Setear tocken y sing de autorización (pasos previos)
*-- IMPORTANTE: almacenar Token y Sign para no pediro repetidamente
WSCOC.Token = WSAA.Token 
WSCOC.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSCOC.Cuit = "30587808990"

*-- Conectar al Servicio Web
ok = WSCOC.Conectar("", "https://fwshomo.afip.gov.ar/wscoc/COCService?wsdl")      && Homologación
*-- Producción usar: ok = WSCOC.Conectar("", "https://serviciosjava.afip.gov.ar/wscoc/COCService?wsdl) && Producción

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSCOC.Dummy()
? "appserver status", WSCOC.AppServerStatus
? "dbserver status", WSCOC.DbServerStatus
? "authserver status", WSCOC.AuthServerStatus
? WSCOC.Excepcion
? WSCOC.Traceback

? "Consultado CUITs...."

nro_doc = 99999999
tipo_doc = 96
WSCOC.ConsultarCUIT(nro_doc, tipo_doc)

DO HuboErrores

*-- recorro el detalle de los cuit devueltos:
DO WHILE WSCOC.LeerCUITConsultado():
     ? "CUIT", WSCOC.CUITConsultada
     ? "Denominación", WSCOC.DenominacionConsultada
ENDDO


*-- Genero una solicitud de operación de cambio
cuit_comprador = "20267565393"
codigo_moneda = "1"
cotizacion_moneda = "4.26"
monto_pesos = "100"
cuit_representante = NULL
codigo_destino = 625

*-- ok = WSCOC.LoadTestXML("f:\ws\wscoc_response.xml")

ok = WSCOC.GenerarSolicitudCompraDivisa( ;
		cuit_comprador, codigo_moneda, ;
        cotizacion_moneda, monto_pesos, ;
        cuit_representante, codigo_destino)

DO HuboErrores

? 'Resultado', WSCOC.Resultado
? 'COC', WSCOC.COC
? "FechaEmisionCOC", WSCOC.FechaEmisionCOC
? 'CodigoSolicitud', WSCOC.CodigoSolicitud
? "EstadoSolicitud", WSCOC.EstadoSolicitud
? "FechaEstado", WSCOC.FechaEstado
? "DetalleCUITComprador", WSCOC.CUITComprador, WSCOC.DenominacionComprador
? "CodigoMoneda", WSCOC.CodigoMoneda
? "CotizacionMoneda", WSCOC.CotizacionMoneda
? "MontoPesos", WSCOC.MontoPesos
? "CodigoDestino", WSCOC.CodigoDestino

*-- Almacenar Request y Response como respaldo
*-- ? WSCOC.XmlRequest
*-- ? WSCOC.XmlResponse

ok = MESSAGEBOX("Resultado: " + WSCOC.Resultado +  "Nº COC: " + WSCOC.COC + "Estado: " + WSCOC.EstadoSolicitud, 64, "Generar Solicitud")

*-- Informar la aceptación o desistir una solicitud generada con anterioridad
COC = WSCOC.COC
codigo_solicitud = WSCOC.CodigoSolicitud
*-- "CO": confirmar, o "DC" (desistio cliente) "DB" (desistio banco)
nuevo_estado = "CO"
ok = WSCOC.InformarSolicitudCompraDivisa(codigo_solicitud, nuevo_estado)
    
DO HuboErrores
    
? 'Resultado', WSCOC.Resultado
? 'COC', WSCOC.COC
? "EstadoSolicitud", WSCOC.EstadoSolicitud

*-- Almacenar Request y Response como respaldo
*-- ? WSCOC.XmlRequest
*-- ? WSCOC.XmlResponse

ok = MESSAGEBOX("Resultado: " + WSCOC.Resultado +  "Nº COC: " + WSCOC.COC + "Estado: " + WSCOC.EstadoSolicitud, 64, "Informar Solicitud")
           

*--  para pruebas, anulo la solicitud de cambio
ok = WSCOC.AnularCOC(COC, cuit_comprador)

DO HuboErrores

? 'Resultado', WSCOC.Resultado
? 'COC', WSCOC.COC
? "EstadoSolicitud", WSCOC.EstadoSolicitud

ok = MESSAGEBOX("Resultado: " + WSCOC.Resultado +  "Nº COC: " + WSCOC.COC + "Estado: " + WSCOC.EstadoSolicitud, 64, "Anular Solicitud")

*-- consulto para verificar el estado
ok = WSCOC.ConsultarSolicitudCompraDivisa(codigo_solicitud)

DO HuboErrores

? 'Resultado', WSCOC.Resultado
? 'COC', WSCOC.COC
? "FechaEmisionCOC", WSCOC.FechaEmisionCOC
? 'CodigoSolicitud', WSCOC.CodigoSolicitud
? "EstadoSolicitud", WSCOC.EstadoSolicitud
? "FechaEstado", WSCOC.FechaEstado
? "DetalleCUITComprador", WSCOC.CUITComprador, WSCOC.DenominacionComprador
? "CodigoMoneda", WSCOC.CodigoMoneda
? "CotizacionMoneda", WSCOC.CotizacionMoneda
? "MontoPesos", WSCOC.MontoPesos
? "CodigoDestino", WSCOC.CodigoDestino

ok = MESSAGEBOX("Resultado: " + WSCOC.Resultado +  "Nº COC: " + WSCOC.COC + "Estado: " + WSCOC.EstadoSolicitud, 64, "Consultar Solicitud")

CANCEL           

*-- Procedimiento para manejar errores
PROCEDURE errhand
	*--PARAMETER merror, mess, mess1, mprog, mlineno

	*-- trato de extraer el código de error de afip (1000)
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
	ch = MESSAGEBOX(MESSAGE(), 5 + 48, "Error:")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC

PROCEDURE HuboErrores
    cancelar = .F.
	DO WHILE .T.
		er = WSCOC.LeerError()
		IF LEN(er) = 0 THEN 
			EXIT
		ENDIF
        ? "Error:", er
	    MESSAGEBOX(ER, 5 + 48, "Error:")
	    cancelar = .T.
	ENDDO
	DO WHILE .T.
		er = WSCOC.LeerErrorFormato()
		IF LEN(er) = 0 THEN 
			EXIT
		ENDIF
        ? "Error Formato:", er
	    MESSAGEBOX(ER, 5 + 48, "Error Formato:")
	    cancelar = .T.
	ENDDO
	DO WHILE .T.
		er = WSCOC.LeerInconsistencia()
		IF LEN(er) = 0 THEN 
			EXIT
		ENDIF
        ? "Inconsistencia:", er
	    MESSAGEBOX(ER, 5 + 48, "Inconsistencia:")
	    cancelar = .T.
	ENDDO
	IF LEN(WSCOC.Excepcion) > 0 THEN 
	    ? WSCOC.Traceback
	    MESSAGEBOX(WSCOC.Excepcion, 5 + 48, "Excepcion")
	    cancelar = .T.
	ENDIF	
    IF cancelar THEN
		*-- Depuración (grabar a un archivo los datos de prueba)
		gnErrFile = FCREATE('c:\error.txt')  
		=FWRITE(gnErrFile, WSCOC.Token + CHR(13))
		=FWRITE(gnErrFile, WSCOC.Sign + CHR(13))	
		=FWRITE(gnErrFile, WSCOC.XmlRequest + CHR(13))
		=FWRITE(gnErrFile, WSCOC.XmlResponse + CHR(13))
		=FWRITE(gnErrFile, WSCOC.Excepcion + CHR(13))
		=FWRITE(gnErrFile, WSCOC.Traceback + CHR(13))
		=FCLOSE(gnErrFile)
    	CANCEL
    ENDIF
ENDPROC
