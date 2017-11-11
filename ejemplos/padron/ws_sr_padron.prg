*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Factura Electronica Comprobantes de Turismo
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- Según RG3971 / 566 (con detalle, CAE tradicional)
*-- 2017 (C) Mariano Reingart <reingart@gmail.com>

ON ERROR DO errhand1;

CLEAR

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 

*-- Generar un Ticket de Requerimiento de Acceso (TRA)
tra = WSAA.CreateTRA("ws_sr_padron_a4")

*-- obtengo el path de los certificados para pasarle a la interfase
*-- usar ruta predeterminada de instalación:
ruta = WSAA.InstallDir + "\"

*-- Generar el mensaje firmado (CMS) 
cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") && Cert. Demo
*-- cms = WSAA.SignTRA(tra, ruta + "homo.crt", ruta + "homo.key") 

*-- Llamar al web service para autenticar (homologación)
WSAA.Conectar("", "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl")
ta = WSAA.LoginCMS(cms)

ON ERROR DO errhand2;

*-- Crear objeto interface Web Service de Factura Electrónica
Padron = CREATEOBJECT("WSSrPadronA4") 
Padron.LanzarExcepciones = .F.

*-- Setear tocken y sing de autorización (pasos previos)
Padron.Token = WSAA.Token 
Padron.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
Padron.Cuit = "20267565393"

*-- Conectar al Servicio Web de Consulta Padron Alcance 4
ok = Padron.Conectar("", "https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA4?wsdl")      && Homologación


*-- Consultar CUIT (online con AFIP):
id_persona = "30708900873"
ok = Padron.Consultar(id_persona)
? ok, Padron.Excepcion

*-- Imprimir respuesta obtenida
? "Denominacion:", Padron.denominacion
? "Tipo:", Padron.tipo_persona, Padron.tipo_doc, Padron.nro_doc
? "Estado:", Padron.Estado
? "Direccion:", Padron.direccion
? "Localidad:", Padron.localidad
? "Provincia:", Padron.provincia
? "Codigo Postal:", Padron.cod_postal
FOR EACH impuesto IN Padron.impuestos
    ? "Impuesto:", impuesto
NEXT
FOR EACH actividad IN Padron.actividades
    ? "Actividad:", actividad
NEXT
? "IVA", Padron.imp_iva
? "MT", Padron.monotributo, Padron.actividad_monotributo
? "Empleador", Padron.empleador

IF Padron.Excepcion = "" THEN
	MESSAGEBOX(Padron.denominacion + " " + Padron.Estado + CHR(13) + Padron.direccion + CHR(13) + Padron.localidad + CHR(13) + Padron.provincia + CHR(13) + Padron.cod_postal)
ELSE
*-- respuesta del servidor (para depuración)
    ? Padron.response
    MESSAGEBOX(Padron.Traceback, 0, Padron.Excepcion)
ENDIF


*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, Padron.Token + CHR(13))
* =FWRITE(gnErrFile, Padron.Sign + CHR(13))	
* =FWRITE(gnErrFile, Padron.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, Padron.XmlResponse + CHR(13))
* =FWRITE(gnErrFile, Padron.Excepcion + CHR(13))
* =FWRITE(gnErrFile, Padron.Traceback + CHR(13))
* =FCLOSE(gnErrFile)  


*-- Procedimiento para manejar errores WSAA
PROCEDURE errhand1
	*--PARAMETER merror, mess, mess1, mprog, mlineno
	
	? WSAA.Excepcion
	? WSAA.Traceback
	*--? WSAA.XmlRequest
	*--? WSAA.XmlResponse

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

*-- Procedimiento para manejar errores WSMTX
PROCEDURE errhand2
	*--PARAMETER merror, mess, mess1, mprog, mlineno
	
	? Padron.Excepcion
	? Padron.Traceback
	*--? Padron.XmlRequest
	? Padron.XmlResponse
	
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(Padron.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC
