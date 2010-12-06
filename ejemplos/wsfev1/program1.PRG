*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Factura Electronica Version 1 - para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- 2010 (C) Mariano Reingart <reingart@gmail.com>

ON ERROR DO errhand;

CLEAR

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 

*-- Generar un Ticket de Requerimiento de Acceso (TRA)
tra = WSAA.CreateTRA()

*-- obtengo el path actual de los certificados para pasarle a la interfase
cCurrentProcedure = SYS(16,1) 
nPathStart = AT(":",cCurrentProcedure)- 1
nLenOfPath = RAT("\", cCurrentProcedure) - (nPathStart)
ruta = (SUBSTR(cCurrentProcedure, nPathStart, nLenofPath)) + "\"
? "ruta",ruta

*-- Generar el mensaje firmado (CMS) 
cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") && Cert. Demo
*-- cms = WSAA.SignTRA(tra, ruta + "homo.crt", ruta + "homo.key") 

*-- Llamar al web service para autenticar
*-- Producción usar: ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") && Producción
ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") && Homologación

*-- Crear objeto interface Web Service de Factura Electrónica
WSFE = CREATEOBJECT("WSFEv1") 

*-- Setear tocken y sing de autorización (pasos previos)
WSFE.Token = WSAA.Token 
WSFE.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSFE.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturación
*-- Producción usar: ok = WSFE.Conectar("https://wsw.afip.gov.ar/wsfe/service.asmx") && Producción
ok = WSFE.Conectar("")      && Homologación

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSFE.Dummy()
? "appserver status", WSFE.AppServerStatus
? "dbserver status", WSFE.DbServerStatus
? "authserver status", WSFE.AuthServerStatus


*-- Recupero último número de comprobante para un punto de venta y tipo (opcional)
tipo_cbte = 1
punto_vta = 1
LastCBTE = WSFE.CompUltimoAutorizado(tipo_cbte, punto_vta)
    
*-- Establezco los valores de la factura o lote a autorizar:
concepto = 3
Fecha = STRTRAN(STR(YEAR(DATE()),4) + STR(MONTH(DATE()),2) + STR(DAY(DATE()),2)," ","0")
? fecha && formato: AAAAMMDD
presta_serv = 1
tipo_doc = 80
nro_doc = "27269434894"
cbt_desde = LastCBTE + 1
cbt_hasta = LastCBTE + 1
imp_total = "122.00"
imp_tot_conc = "0.00"
imp_neto = "100.00"
imp_iva = "21.00"
imp_trib = "1.00"
impto_liq_rni = "0.00"
imp_op_ex = "0.00"
fecha_cbte = Fecha
fecha_venc_pago = Fecha
*-- Fechas del período del servicio facturado (solo si presta_serv = 1)
fecha_serv_desde = Fecha
fecha_serv_hasta = Fecha
moneda_id = "PES"
moneda_ctz = "1.000"

*-- Llamo al WebService de Autorización para obtener el CAE
ok = WSFE.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, ;
        cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, ;
        imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, ;
        fecha_serv_desde, fecha_serv_hasta, ;
        moneda_id, moneda_ctz) 
*-- si presta_serv = 0 no pasar estas fechas

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
? "Vencimiento ", WSFE.Vencimiento && Fecha de vencimiento o vencimiento de la autorización
? "Resultado: ", WSFE.Resultado && A=Aceptado, R=Rechazado
? "Motivo de rechazo o advertencia", WSFE.Obs
? WSFE.XmlResponse

*-- Verifico que no haya rechazo o advertencia al generar el CAE
IF LEN(cae)=0 THEN
    MESSAGEBOX("La página esta caida o la respuesta es inválida", 0)
ELSE 
	IF cae = "NULL" OR WSFE.Resultado <> "A" THEN
    	MESSAGEBOX("No se asignó CAE (Rechazado). Motivos: " + WSFE.Motivo, 0)
	ELSE
		IF WSFE.Obs<> "NULL" AND WSFE.Obs<> "00" THEN
		    MESSAGEBOX("Se asignó CAE pero con advertencias. Motivos: " + WSFE.Obs, 0)
		ENDIF
	ENDIF
ENDIF

MESSAGEBOX("CAE obtenido: " + cae, 0)


*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSFE.Token + CHR(13))
* =FWRITE(gnErrFile, WSFE.Sign + CHR(13))	
* =FWRITE(gnErrFile, WSFE.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, WSFE.XmlResponse + CHR(13))
* =FCLOSE(gnErrFile)  


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