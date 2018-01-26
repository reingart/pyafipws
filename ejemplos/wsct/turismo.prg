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
tra = WSAA.CreateTRA("wsct")

*-- obtengo el path actual de los certificados para pasarle a la interfase
cCurrentProcedure = SYS(16,1) 
nPathStart = AT(":",cCurrentProcedure)- 1
nLenOfPath = RAT("\", cCurrentProcedure) - (nPathStart)
ruta = (SUBSTR(cCurrentProcedure, nPathStart, nLenofPath)) + "\"
? "ruta",ruta
*-- usar ruta predeterminada de instalación:
ruta = WSAA.InstallDir + "\"

*-- Generar el mensaje firmado (CMS) 
cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") && Cert. Demo
*-- cms = WSAA.SignTRA(tra, ruta + "homo.crt", ruta + "homo.key") 

*-- Llamar al web service para autenticar
*-- Producción usar: ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") && Producción
ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") && Homologación

ON ERROR DO errhand2;

*-- Crear objeto interface Web Service de Factura Electrónica
WSCT = CREATEOBJECT("WSCT") 
WSCT.LanzarExcepciones = .F.

*-- Setear tocken y sing de autorización (pasos previos)
WSCT.Token = WSAA.Token 
WSCT.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSCT.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturación
*-- Producción usar: 
*--ok = WSCT.Conectar("", "https://serviciosjava.afip.gob.ar/WSCT/services/MTXCAService?wsdl") && Producción
ok = WSCT.Conectar("")      && Homologación

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSCT.Dummy()
? "appserver status", WSCT.AppServerStatus
? "dbserver status", WSCT.DbServerStatus
? "authserver status", WSCT.AuthServerStatus


*-- Recupero último número de comprobante para un punto de venta y tipo (opcional)
tipo_cbte = 195
punto_vta = 4003
cbte_nro = "0" && WSCT.CompUltimoAutorizado(tipo_cbte, punto_vta)
? "CompUltimoAutorizado " + cbte_nro
*-- convertir a numero 
cbte_nro = VAL(cbte_nro) + 1
*-- volver a string sin espacios
cbte_nro = ALLTRIM(STR(cbte_nro))
? "cbte_nro " + cbte_nro

*-- Establezco los valores de la factura o lote a autorizar:
fecha_cbte = STRTRAN(STR(YEAR(DATE()),4) + "-" + STR(MONTH(DATE()),2) + "-" + STR(DAY(DATE()),2)," ","0")
? fecha_cbte && formato: AAAA-MM-DD
tipo_doc = 80 
nro_doc = "50000000059"
id_impositivo = 9                       && "Cliente del Exterior"
cod_relacion = 3                        && Alojamiento Directo a Turista No Residente
imp_total = "101.00"
imp_tot_conc = "0.00"
imp_neto = "100.00"
imp_trib = "1.00"
imp_op_ex = "0.00"
imp_subtotal = "100.00"
imp_reintegro = "-21.00"                &&  validación AFIP 346
cod_pais = 203                          && Brasil
domicilio = "Rua N.76 km 34.5 Alagoas"
moneda_id = "PES"
moneda_ctz = "1.000"
obs = "Observaciones Comerciales, libre"

*-- Llamo al WebService de Autorización para obtener el CAE
ok = WSCT.CrearFactura(tipo_doc, nro_doc, tipo_cbte, punto_vta, ;
                  cbte_nro, imp_total, imp_tot_conc, imp_neto, ;
                  imp_subtotal, imp_trib, imp_op_ex, imp_reintegro, ;
                  fecha_cbte, id_impositivo, cod_pais, domicilio, ;
                  cod_relacion, moneda_id, moneda_ctz, obs)

*-- Agrego los comprobantes asociados:
IF tipo_cbte = 3 THEN
	 *-- solo si es nc o nd
    tipo = 19
    pto_vta = 2
    nro = 1234
    ok = WSCT.AgregarCmpAsoc(tipo, pto_vta, nro)
ENDIF

*-- Agrego impuestos varios
id = 99
Desc = "Impuesto Municipal Matanza'"
base_imp = "100.00"
alic = "1.00"
importe = "1.00"
ok = WSCT.AgregarTributo(id, Desc, base_imp, alic, importe)

*-- Agrego subtotales de IVA
*-- 21%
id = 5 
base_imp = "100.00"
importe = "21.00"
ok = WSCT.AgregarIva(id, base_imp, importe)

*-- Agrego los artículos
tipo = 0            && Item General
cod_tur = 1         && Servicio de hotelería - alojamiento sin desayuno
codigo = "T0001"
ds = "Descripcion del producto P0001"
iva_id = 5
imp_iva = "21.00"
imp_subtotal = "121.00"
ok = WSCT.AgregarItem(tipo, cod_tur, codigo, ds, ;
                      iva_id, imp_iva, imp_subtotal)

codigo = 68                 && tarjeta de crédito
tipo_tarjeta = 99           && otra (ver tabla de parámetros)
numero_tarjeta = "999999"
swift_code = Null
tipo_cuenta = Null
numero_cuenta = Null
ok = WSCT.AgregarFormaPago(codigo, tipo_tarjeta, numero_tarjeta, ;
                           swift_code, tipo_cuenta, numero_cuenta)

**-- Solicito CAE:

ON ERROR DO errhand2;

cae = WSCT.AutorizarComprobante()

? WSCT.Excepcion
? WSCT.Traceback

? "CAE: ", cae
? "Vencimiento ", WSCT.Vencimiento && Fecha de vencimiento o vencimiento de la autorización
? "Resultado: ", WSCT.Resultado && A=Aceptado, R=Rechazado
? "Motivo de rechazo o advertencia", WSCT.Obs
? WSCT.XmlResponse

MESSAGEBOX("Resultado: " + WSCT.Resultado + " CAE " + cae + ". Observaciones: " + WSCT.Obs + " Errores: " + WSCT.ErrMsg, 0)


*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSCT.Token + CHR(13))
* =FWRITE(gnErrFile, WSCT.Sign + CHR(13))	
* =FWRITE(gnErrFile, WSCT.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, WSCT.XmlResponse + CHR(13))
* =FWRITE(gnErrFile, WSCT.Excepcion + CHR(13))
* =FWRITE(gnErrFile, WSCT.Traceback + CHR(13))
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
	
	? WSCT.Excepcion
	? WSCT.Traceback
	*--? WSCT.XmlRequest
	? WSCT.XmlResponse
	
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSCT.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC
