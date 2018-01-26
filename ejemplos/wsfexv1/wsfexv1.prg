*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Factura Electronica exportación RG2758 Version 1 (V.1)
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- 2010-2016 (C) Mariano Reingart <reingart@gmail.com>

ON ERROR DO errhand1;

CLEAR

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 

*-- Generar un Ticket de Requerimiento de Acceso (TRA)
tra = WSAA.CreateTRA("wsfex")

*-- uso la ruta de los certificados predeterminados (homologacion)

ruta = WSAA.InstallDir + "\"

*-- Generar el mensaje firmado (CMS) 
cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") && Cert. Demo

*-- Conectarse con el webservice
ok = WSAA.Conectar("", "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") && Homologación

*-- Llamar al web service para autenticar
*-- Producción usar: ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") && Producción
ta = WSAA.LoginCMS(cms) 

ON ERROR DO errhand2;

*-- Crear objeto interface Web Service de Factura Electrónica Exportación
WSFEX = CREATEOBJECT("WSFEXv1") 

? WSFEX.Version
? WSFEX.InstallDir

*-- Setear tocken y sing de autorización (pasos previos)
WSFEX.Token = WSAA.Token 
WSFEX.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSFEX.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturación
*-- Producción usar: 
*-- ok = WSFEX.Conectar("", "https://servicios1.afip.gov.ar/WSFEXv1/service.asmx?WSDL") && Producción
ok = WSFEX.Conectar("", "https://wswhomo.afip.gov.ar/WSFEXv1/service.asmx?WSDL")      && Homologación

? WSFEX.DebugLog()

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSFEX.Dummy()
? "appserver status", WSFEX.AppServerStatus
? "dbserver status", WSFEX.DbServerStatus
? "authserver status", WSFEX.AuthServerStatus


*-- Recupero último número de comprobante para un punto de venta y tipo (opcional)
tipo_cbte = 19 && FC Expo (ver tabla de parámetros)
punto_vta = 1
LastCBTE = WSFEX.GetLastCMP(tipo_cbte, punto_vta) 
? "Ult. Cbte:", LastCBTE

IF ISNULL(LastCBTE) THEN
	MESSAGEBOX("No se pudo obtener el ult. nro de comprobante. ErrMsg: " + WSFEX.ErrMsg + " Excepcion: " + WSFEX.Excepcion, 0)
	CANCEL
ENDIF

*-- Establezco los valores de la factura o lote a autorizar:
tipo_expo = 1 && tipo de exportación (ver tabla de parámetros)
fecha_cbte = STRTRAN(STR(YEAR(DATE()),4) + STR(MONTH(DATE()),2) + STR(DAY(DATE()),2)," ","0")
? fecha_cbte && formato: AAAAMMDD
cbte_nro = LastCBTE + 1

permiso_existente = "N"
dst_cmp = 235 && país destino
cliente = "Joao Da Silva"
cuit_pais_cliente = "50000000016"
domicilio_cliente = "Rua N°76 km 34.5 Alagoas"
id_impositivo = "PJ54482221-l"
moneda_id = "DOL" && para reales, "DOL" o "PES" (ver tabla de parámetros)
moneda_ctz = "14.00"
obs_comerciales = "Observaciones comerciales"
obs = "Sin observaciones"
forma_pago = "takataka"
incoterms = "FOB" && (ver tabla de parámetros)
incoterms_ds = "Info complementaria" && (opcional) Nuevo! 20 caracteres
idioma_cbte = 1 && Español (ver tabla de parámetros)
imp_total = "250.00"
  

*-- Creo una factura (internamente, no se llama al WebService):

ok = WSFEX.CrearFactura(tipo_cbte, punto_vta, cbte_nro, fecha_cbte, ;
        imp_total, tipo_expo, permiso_existente, dst_cmp, ;
        cliente, cuit_pais_cliente, domicilio_cliente, ;
        id_impositivo, moneda_id, moneda_ctz, ;
        obs_comerciales, obs, forma_pago, incoterms, ;
        idioma_cbte, incoterms_ds)

*-- Agrego un item:

codigo = "PRO1"
ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
qty = 2
precio = "130.00"
umed = 1 && Ver tabla de parámetros (unidades de medida)
imp_total = "250.00" && importe total final del artículo
bonif = "10.00" && Nuevo!

*-- lo agrego a la factura (internamente, no se llama al WebService):

ok = WSFEX.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)
ok = WSFEX.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)
ok = WSFEX.AgregarItem(codigo, "Descuento", 0, 99, 0, "-250.00", 0)
ok = WSFEX.AgregarItem("--", "texto adicional", 0, 0, 0, 0, 0)

*-- Agrego un permiso (ver manual para el desarrollador)

IF permiso_existente = "S"
    id = "99999AAXX999999A"
    dst = 225 && país destino de la mercaderia
    ok = WSFEX.AgregarPermiso(id, dst)
ENDIF

*-- Agrego un comprobante asociado (ver manual para el desarrollador)

IF tipo_cbte <> 19
    tipo_cbte_asoc = 19
    punto_vta_asoc = 2
    cbte_nro_asoc = 1
    cuit_asoc = "20111111111" && CUIT Asociado Nuevo!
    ok = WSFEX.AgregarCmpAsoc(tipo_cbte_asoc, punto_vta_asoc, cbte_nro_asoc, cuit_asoc)
ENDIF


&& id = "99000000000100" ' número propio de transacción

*-- obtengo el último ID y le adiciono 1 (advertencia: evitar overflow!)

WSFEX.GetLastID
WSFEX.AnalizarXml "XmlResponse"			&& workaround para evitar problema de tipos en VFP antiguo
LastID = WSFEX.ObtenerTagXml('Id')		&& leo desde el XML devuelto por AFIP
? "LastID:", LastID
id = VAL(LastID) + 1            && convertir a valor numerico e incrementar
id = STR(id, 24)		    	&& convertir a string sin exp.

&& NOTA: el ID puede ser un valor arbitrario mientras no se repita (no es necesario que sea un LONG)

*-- Deshabilito errores no capturados:

WSFEX.LanzarExcepciones = .F.

*-- Llamo al WebService de Autorización para obtener el CAE

CAE = WSFEX.Authorize(id)

? "LastCBTE:", LastCBTE 
? "CAE: ", cae
? "Vencimiento ", WSFEX.Vencimiento && Fecha de vencimiento o vencimiento de la autorización
? "Resultado: ", WSFEX.Resultado && A=Aceptado, R=Rechazado
? "Motivo de rechazo o advertencia", WSFEX.Obs
? "Mensaje Error", WSFEX.ErrMsg
? " Reproceso ", WSFEX.Reproceso

** ? WSFEX.XmlRequest
** ? WSFEX.XmlResponse

MESSAGEBOX("Resultado:" + WSFEX.Resultado + " CAE: " + cae , 0)

IF NOT ISNULL(WSFEX.Obs)
	MESSAGEBOX("Observaciones AFIP" + WSFEX.Obs , 0)
ENDIF

MESSAGEBOX("Mensajes Error AFIP: " + WSFEX.ErrMsg, 0)

*-- Depuración (grabar a un archivo los datos de prueba)
** gnErrFile = FCREATE('c:\error.txt')  
** =FWRITE(gnErrFile, WSFEX.Token + CHR(13))
** =FWRITE(gnErrFile, WSFEX.Sign + CHR(13))	
** =FWRITE(gnErrFile, WSFEX.XmlRequest + CHR(13))
** =FWRITE(gnErrFile, WSFEX.XmlResponse + CHR(13))
** =FWRITE(gnErrFile, WSFEX.Excepcion + CHR(13))
** =FWRITE(gnErrFile, WSFEX.Traceback + CHR(13))
** =FCLOSE(gnErrFile)  


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

*-- Procedimiento para manejar errores WSFEX
PROCEDURE errhand2
	*--PARAMETER merror, mess, mess1, mprog, mlineno
	
	? WSFEX.Excepcion
	? WSFEX.Traceback
	*--? WSFEX.XmlRequest
	*--? WSFEX.XmlResponse
		
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSFEX.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC
