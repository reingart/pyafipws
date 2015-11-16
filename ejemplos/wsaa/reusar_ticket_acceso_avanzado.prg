*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Reutilizaci騨 ticket de Acceso (Web service autenticaci騨 WSAA) 
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- 2015 (C) Mariano Reingart <reingart@gmail.com>

CLEAR

*-- Crear objeto interface Web Service de Factura Electronica
WSFE = CREATEOBJECT("WSFEv1") 

? WSFE.Version
? WSFE.InstallDir

*-- solicito ticket de acceso
TA = Autenticar()

*-- solicito ticket de acceso (nuevamente para chequear rutina)
*-- (no es necesario hacerlo dos veces en producci騨)
TA = Autenticar()

*-- Setear tocken y sign de autorizacion (ticket de accesso, pasos previos)
WSFE.SetTicketAcceso(TA)  

* CUIT del emisor (debe estar registrado en la AFIP)
WSFE.Cuit = "20267565393"

ON ERROR DO errhand2

*-- Conectar al Servicio Web de Facturacion
*-- Produccion usar: 
*-- ok = WSFE.Conectar("", "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL") && Producci贸n
ok = WSFE.Conectar("")      && Homologacion

? WSFE.DebugLog()

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSFE.Dummy()
? "appserver status", WSFE.AppServerStatus
? "dbserver status", WSFE.DbServerStatus
? "authserver status", WSFE.AuthServerStatus


*-- Recupero 煤ltimo n煤mero de comprobante para un punto de venta y tipo (opcional)
tipo_cbte = 1
punto_vta = 1
LastCBTE = WSFE.CompUltimoAutorizado(tipo_cbte, punto_vta)
    
*-- Establezco los valores de la factura o lote a autorizar:
concepto = 3
Fecha = STRTRAN(STR(YEAR(DATE()),4) + STR(MONTH(DATE()),2) + STR(DAY(DATE()),2)," ","0")
? fecha && formato: AAAAMMDD
tipo_doc = 80
nro_doc = "27269434894"
cbt_desde = INT(VAL(LastCBTE)) + 1
cbt_hasta = INT(VAL(LastCBTE)) + 1
imp_total = "122.00"
imp_tot_conc = "0.00"
imp_neto = "100.00"
imp_iva = "21.00"
imp_trib = "1.00"
impto_liq_rni = "0.00"
imp_op_ex = "0.00"
fecha_cbte = Fecha
fecha_venc_pago = Fecha
*-- Fechas del periodo del servicio facturado (solo si concepto > 1)
fecha_serv_desde = Fecha
fecha_serv_hasta = Fecha
moneda_id = "PES"
moneda_ctz = "1.000"

*-- Llamo al WebService de Autorizacion para obtener el CAE
ok = WSFE.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, ;
        cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, ;
        imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, ;
        fecha_serv_desde, fecha_serv_hasta, ;
        moneda_id, moneda_ctz) 
*-- si concepto = 1 (productos) no pasar estas fechas

*-- Agrego impuestos varios
id = 99
desc = "Impuesto Municipal Matanza"
base_imp = "100.00"
alic = "1.00"
importe = "1.00"
ok = WSFE.AgregarTributo(id, Desc, base_imp, alic, importe)


*-- Agrego tasas de IVA
id = 5 && 21%
base_im = "100.00"
importe = "21.00"
ok = WSFE.AgregarIva(id, base_imp, importe)

**-- Solicito CAE:

cae = WSFE.CAESolicitar()

? "LastCBTE:", LastCBTE 
? "CAE: ", cae
? "Vencimiento ", WSFE.Vencimiento && Fecha de vencimiento o vencimiento de la autorizaci贸n
? "Resultado: ", WSFE.Resultado && A=Aceptado, R=Rechazado
? "Motivo de rechazo o advertencia", WSFE.Obs
? "Errores", WSFE.ErrMsg
*--? WSFE.XmlResponse

MESSAGEBOX("Resultado: " + WSFE.Resultado + " CAE " + cae + " Vencimiento: " + WSFE.Vencimiento + " Reproceso " + WSFE.Reproceso + " EmisionTipo " + WSFE.EmisionTipo + " Observaciones: " + WSFE.Obs + " Errores: " + WSFE.ErrMsg, 0)



*-- Depuracion (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSFE.Token + CHR(13))
* =FWRITE(gnErrFile, WSFE.Sign + CHR(13))	
* =FWRITE(gnErrFile, WSFE.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, WSFE.XmlResponse + CHR(13))
* =FWRITE(gnErrFile, WSFE.Excepcion + CHR(13))
* =FWRITE(gnErrFile, WSFE.Traceback + CHR(13))
* =FCLOSE(gnErrFile)  

*-- Funcion para autenticar, devuelve el ticket de acceso (reutilizado o nuevo)
FUNCTION Autenticar 

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
		tra = WSAA.CreateTRA()

		*-- uso la ruta a la carpeta de instalaci騨 con los certificados de prueba
		ruta = WSAA.InstallDir + "\"
		? "ruta", ruta

		*-- Generar el mensaje firmado (CMS) 
		cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") && Cert. Demo
		*-- cms = WSAA.SignTRA(tra, ruta + "homo.crt", ruta + "homo.key") 

		*-- Produccion usar: ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") && Producci贸n
		ok = WSAA.Conectar("", "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") && Homologaci贸n

		*-- Llamar al web service para autenticar
		ta = WSAA.LoginCMS(cms)
		
		*-- Grabo el ticket de acceso para poder reutilizarlo
		*-- (revisar temas de seguridad y permisos)
		f = FCREATE(archivo)  
		w = FWRITE(f, ta)
		? "bytes escritos:", w, "descriptor", f
		=FCLOSE(f)

	ELSE
		? "no expirado!", "Reutilizando!"
	ENDIF
	
	*-- devuelvo el ticket de acceso
	RETURN ta
ENDPROC

*-- Procedimiento para manejar errores WSAA
PROCEDURE errhand1
	*--PARAMETER merror, mess, mess1, mprog, mlineno
	
	? WSAA.Excepcion
	? WSAA.Traceback
	*--? WSAA.XmlRequest
	*--? WSAA.XmlResponse

	*-- trato de extraer el codigo de error de afip (1000)
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
	
	? WSFE.Excepcion
	? WSFE.Traceback
	*--? WSFE.XmlRequest
	*--? WSFE.XmlResponse
		
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSFE.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC
