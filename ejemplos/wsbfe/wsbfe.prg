*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Factura Electronica Bono Fiscal Bienes de Capital (WSBFEv1) 
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- Seg煤n RG2557 (con  detalle, )
*-- 2010-2015 (C) Mariano Reingart <reingart@gmail.com>

ON ERROR DO errhand1;

CLEAR

*-- Crear objeto interface Web Service Autenticaci贸n y Autorizaci贸n
WSAA = CREATEOBJECT("WSAA") 

*-- Generar un Ticket de Requerimiento de Acceso (TRA)
tra = WSAA.CreateTRA("wsbfe")

*-- uso la ruta de los certificados predeterminados (homologacion)

ruta = WSAA.InstallDir + "\"

*-- Generar el mensaje firmado (CMS) 
cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") && Cert. Demo

*-- Conectarse con el webservice
ok = WSAA.Conectar("", "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl") && Homologaci贸n

*-- Llamar al web service para autenticar
*-- Producci贸n usar: ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") && Producci贸n
ta = WSAA.LoginCMS(cms) 

ON ERROR DO errhand2

*-- Imprimir el ticket de acceso, ToKen y Sign de autorizaci髇
? ta
? "Token:", WSAA.Token
? "Sign:", WSAA.Sign
    
*-- Una vez obtenido, se puede usar el mismo token y sign por 12 horas

*-- Crear objeto interface Web Service de Factura Electr髇ica
WSBFE = CREATEOBJECT("WSBFEv1")
*-- Setear tocken y sing de autorizaci髇 (pasos previos)
WSBFE.Token = WSAA.Token
WSBFE.Sign = WSAA.Sign

*-- CUIT del emisor (debe estar registrado en la AFIP)
WSBFE.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturaci髇
ok = WSBFE.Conectar("", "http://wswhomo.afip.gov.ar/wsbfev1/service.asmx?WSDL") && homologaci髇

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSBFE.Dummy
? "appserver status", WSBFE.AppServerStatus
? "dbserver status", WSBFE.DbServerStatus
? "authserver status", WSBFE.AuthServerStatus
   
*-- Establezco los valores de la factura o lote a autorizar:
fecha = STRTRAN(STR(YEAR(DATE()),4) + STR(MONTH(DATE()),2) + STR(DAY(DATE()),2)," ","0")
tipo_doc = 80
nro_doc = "23111111113"
zona = 1 								&& Nacional (Ver tabla de zonas)
tipo_cbte = 1 							&& Ver tabla de tipos de comprobante
punto_vta = 5
*-- Obtengo el 鷏timo n鷐ero de comprobante y le agrego 1
cbte_nro = WSBFE.GetLastCMP(tipo_cbte, punto_vta) + 1

*-- Imprimo pedido y respuesta XML para depuraci髇
? WSBFE.XmlRequest
? WSBFE.XmlResponse

fecha_cbte = fecha
Imp_total = "121.00"
imp_tot_conc = "0.00"
imp_neto = "100.00"
impto_liq = "21.00"
impto_liq_rni = "0.00"
imp_op_ex = "0.00"
imp_perc = "0.00"
imp_iibb = "0.00"
imp_perc_mun = "0.00"
imp_internos = "0.00"
imp_moneda_id = "PES" 	&& Ver tabla de tipos de moneda
Imp_moneda_ctz = "1" 	&& cotizaci髇 de la moneda (respecto al peso argentino?)

*-- Creo una factura (internamente, no se llama al WebService):
ok = WSBFE.CrearFactura(tipo_doc, nro_doc, ;
        zona, tipo_cbte, punto_vta, cbte_nro, fecha_cbte, ;
        Imp_total, imp_neto, impto_liq, ;
        imp_tot_conc, impto_liq_rni, imp_op_ex, ;
        imp_perc, imp_iibb, imp_perc_mun, imp_internos, ;
        imp_moneda_id, Imp_moneda_ctz)

*-- Agrego un item:
ncm = "7308.10.00"  && Ver tabla de c骴igos habilitados del nomenclador comun del mercosur (NCM)
sec = "" && C骴igo de la Secretar韆 (no usado por el momento)
ds = "prueba anafe economico" && Descripci髇 completa del art韈ulo (hasta 4000 caracteres)
umed = 7 && un, Ver tabla de unidades de medida
qty = "2.0" && cantidad
precio = "20.00" && precio neto (facturas A), precio final (facturas B)
bonif = "5.00" && descuentos (en positivo)
iva_id = 5 && 21%, ver tabla al韈uota de iva
imp_total = "60.50" && importe total final del art韈ulo (sin descuentos, iva incluido)
*-- lo agrego a la factura (internamente, no se llama al WebService):
ok = WSBFE.AgregarItem(ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total)

*-- agrego otro item:
ncm = "7308.20.00" && Ver tabla de c骴igos habilitados del nomenclador comun del mercosur (NCM)
sec = "" && C骴igo de la Secretar韆 (no usado por el momento)
ds = "Prueba" && Descripci髇 completa del art韈ulo (hasta 4000 caracteres)
umed = 1 && kg, Ver tabla de unidades de medida
qty = "1.0" && cantidad
precio = "50.00" && precio neto (facturas A), precio final (facturas B)
bonif = "0.00" && descuentos (en positivo)
iva_id = 5 && 21%, ver tabla al韈uota de iva
imp_total = "60.50" && importe total final del art韈ulo (sin descuentos, iva incluido)
*-- lo agrego a la factura (internamente, no se llama al WebService):
ok = WSBFE.AgregarItem(ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total)

*-- Verifico que no haya rechazo o advertencia al generar el CAE
*-- Llamo al WebService de Autorizaci髇 para obtener el CAE
&& obtengo el 鷏timo ID y le adiciono 1 
WSBFE.GetLastID
WSBFE.AnalizarXML("XmlResponse")	&& (desde el XML porque VFP no puede convertir LONG...)
ult_id = WSBFE.ObtenerTagXML("Id")  && se puede simplificar si se utilizan ID mas peque駉s
ult_id = VAL(ult_id) + 1            && convertir a valor numerico e incrementar
ult_id = STR(ult_id, 20)		    && convertir a string sin exp.
cae = WSBFE.Authorize(ult_id)
    
? "Fecha Vencimiento CAE:", WSBFE.Vencimiento
    
*-- Imprimo pedido y respuesta XML para depuraci髇 (errores de formato)
? WSBFE.XmlRequest
? WSBFE.XmlResponse

MESSAGEBOX("Resultado:" + WSBFE.Resultado + " CAE: " + cae + " Reproceso: " + WSBFE.Reproceso + " Obs: " + WSBFE.Obs + " ErrMsg: " + WSBFE.ErrMsg, 0)

*-- Buscar la factura
cae2 = WSBFE.GetCMP(tipo_cbte, punto_vta, cbte_nro)

? "Fecha Comprobante:", WSBFE.FechaCbte
? "Importe Neto:", WSBFE.ImpNeto
? "Impuesto Liquidado:", WSBFE.ImptoLiq
? "Importe Total:", WSBFE.ImpTotal

If cae <> cae2 Then
    MESSAGEBOX("El CAE de la factura no concuerdan con el recuperado en la AFIP!", 0)
Else
    MESSAGEBOX("El CAE de la factura concuerdan con el recuperado de la AFIP", 0)
EndIf

? WSBFE.XmlRequest
? WSBFE.XmlResponse
    
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
	
	? WSBFE.Excepcion
	? WSBFE.Traceback
	*--? WSBFE.XmlRequest
	*--? WSBFE.XmlResponse
		
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSBFE.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC
