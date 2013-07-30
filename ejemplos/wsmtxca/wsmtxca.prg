*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Factura Electronica mercado interno (programa MATRIX)
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- Según RG2904/2010 Artículo 4 Opción A (con detalle, CAE tradicional)
*-- 2011 (C) Mariano Reingart <reingart@gmail.com>

ON ERROR DO errhand1;

CLEAR

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 

*-- Generar un Ticket de Requerimiento de Acceso (TRA)
tra = WSAA.CreateTRA("wsmtxca")

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

ON ERROR DO errhand2;

*-- Crear objeto interface Web Service de Factura Electrónica
WSMTXCA = CREATEOBJECT("WSMTXCA") 

*-- Setear tocken y sing de autorización (pasos previos)
WSMTXCA.Token = WSAA.Token 
WSMTXCA.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSMTXCA.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturación
*-- Producción usar: 
*--ok = WSMTXCA.Conectar("", "https://serviciosjava.afip.gob.ar/wsmtxca/services/MTXCAService?wsdl") && Producción
ok = WSMTXCA.Conectar("")      && Homologación

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSMTXCA.Dummy()
? "appserver status", WSMTXCA.AppServerStatus
? "dbserver status", WSMTXCA.DbServerStatus
? "authserver status", WSMTXCA.AuthServerStatus


*-- Recupero último número de comprobante para un punto de venta y tipo (opcional)
tipo_cbte = 1
punto_vta = 4003
cbte_nro = WSMTXCA.CompUltimoAutorizado(tipo_cbte, punto_vta)
? "CompUltimoAutorizado " + cbte_nro
*-- convertir a numero 
cbte_nro = VAL(cbte_nro) + 1
*-- volver a string sin espacios
cbte_nro = ALLTRIM(STR(cbte_nro))
? "cbte_nro " + cbte_nro

*-- Establezco los valores de la factura o lote a autorizar:
concepto = 3
Fecha = STRTRAN(STR(YEAR(DATE()),4) + "-" + STR(MONTH(DATE()),2) + "-" + STR(DAY(DATE()),2)," ","0")
? fecha && formato: AAAA-MM-DD
tipo_doc = 80 
nro_doc = "30000000007"
cbt_desde = cbte_nro
cbt_hasta = cbte_nro
imp_total = "122.00"
imp_tot_conc = "0.00"
imp_neto = "100.00"
imp_trib = "1.00"
imp_op_ex = "0.00"
imp_subtotal = "100.00"
fecha_cbte = fecha
fecha_venc_pago = fecha
*-- Fechas del período del servicio facturado (solo si concepto = 1?)
fecha_serv_desde = fecha
fecha_serv_hasta = fecha
moneda_id = "PES"
moneda_ctz = "1.000"
obs = "Observaciones Comerciales, libre"

*-- Llamo al WebService de Autorización para obtener el CAE
ok = WSMTXCA.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, ;
        cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, ;
        imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, ;
        fecha_serv_desde, fecha_serv_hasta, ;
        moneda_id, moneda_ctz, obs)
*-- si presta_serv = 0 no pasar estas fechas

*-- Agrego los comprobantes asociados:
IF tipo_cbte = 3 THEN
	 *-- solo si es nc o nd
    tipo = 19
    pto_vta = 2
    nro = 1234
    ok = WSMTXCA.AgregarCmpAsoc(tipo, pto_vta, nro)
ENDIF

*-- Agrego impuestos varios
id = 99
Desc = "Impuesto Municipal Matanza'"
base_imp = "100.00"
alic = "1.00"
importe = "1.00"
ok = WSMTXCA.AgregarTributo(id, Desc, base_imp, alic, importe)

*-- Agrego subtotales de IVA
*-- 21%
id = 5 
base_im = "100.00"
importe = "21.00"
ok = WSMTXCA.AgregarIva(id, base_imp, importe)

*-- Agrego los artículos
u_mtx = 123456
cod_mtx = "1234567890"
codigo = "P0001"
ds = "Descripcion del producto P0001"
qty = "1.0000"
umed = "7"
precio = "100.00"
bonif = "0.00"
cod_iva = "5"
imp_iva = "21.00"
imp_subtotal = "121.00"
ok = WSMTXCA.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, ;
            umed, precio, bonif, cod_iva, imp_iva, imp_subtotal)
ok = WSMTXCA.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, ;
            umed, precio, bonif, cod_iva, imp_iva, imp_subtotal)
ok = WSMTXCA.AgregarItem(u_mtx, cod_mtx, "DESC", "Descuento", 0, ;
            "99", 0, 0, cod_iva, "-21.00", "-121.00")

**-- Solicito CAE:

ON ERROR DO errhand2;

cae = WSMTXCA.AutorizarComprobante()

? WSMTXCA.Excepcion
? WSMTXCA.Traceback

? "CAE: ", cae
? "Vencimiento ", WSMTXCA.Vencimiento && Fecha de vencimiento o vencimiento de la autorización
? "Resultado: ", WSMTXCA.Resultado && A=Aceptado, R=Rechazado
? "Motivo de rechazo o advertencia", WSMTXCA.Obs
? WSMTXCA.XmlResponse

MESSAGEBOX("Resultado: " + WSMTXCA.Resultado + " CAE " + cae + ". Observaciones: " + WSMTXCA.Obs + " Errores: " + WSMTXCA.ErrMsg, 0)


*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSMTXCA.Token + CHR(13))
* =FWRITE(gnErrFile, WSMTXCA.Sign + CHR(13))	
* =FWRITE(gnErrFile, WSMTXCA.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, WSMTXCA.XmlResponse + CHR(13))
* =FWRITE(gnErrFile, WSMTXCA.Excepcion + CHR(13))
* =FWRITE(gnErrFile, WSMTXCA.Traceback + CHR(13))
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
	
	? WSMTXCA.Excepcion
	? WSMTXCA.Traceback
	*--? WSMTXCA.XmlRequest
	? WSMTXCA.XmlResponse
	
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSMTXCA.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC