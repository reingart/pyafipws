*-- Ejemplo de Uso de Interface COM con Web Service Liquidación Secundaria de Granos
*--  más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
*--  2014 (C) Mariano Reingart <reingart@gmail.com>

CLEAR

ON ERROR;

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 
? WSAA.Version
? WSAA.InstallDir

*-- evitar "Error fatal: código de excepción C0000005" en algunas versiones de VFP
WSAA.LanzarExcepciones = .F.

*-- Producción usar: ta = WSAA.Conectar("", "https://wsaa.afip.gov.ar/ws/services/LoginCms")
ok = WSAA.Conectar("", "")

*-- Generar un Ticket de Requerimiento de Acceso (TRA)
tra = WSAA.CreateTRA("wslpg")

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
ta = WSAA.LoginCMS(cms) && Homologación

*-- chequeo si hubo error
IF LEN(WSAA.Excepcion) > 0 THEN 
	? WSAA.Excepcion
	? WSAA.Traceback
	MESSAGEBOX("No se pudo obtener token y sign WSAA")
ENDIF

ON ERROR DO errhand2;

*-- Crear objeto interface Web Service de Liquidación Primaria de Granos
WSLPG = CREATEOBJECT("WSLPG")

? WSLPG.Version
? WSLPG.InstallDir

*-- evitar "Error fatal: código de excepción C0000005" en algunas versiones de VFP
WSLPG.LanzarExcepciones = .F.

*--  Setear tocken y sing de autorización (pasos previos)
WSLPG.Token = WSAA.Token
WSLPG.Sign = WSAA.Sign
*-- CUIT (debe estar registrado en la AFIP)
WSLPG.cuit = "20267565393"

*-- Conectar al Servicio Web
ok = WSLPG.Conectar("", "", "") && homologación
IF ! ok Then
    ? WSLPG.Traceback
    MESSAGEBOX(WSLPG.Traceback, 5 + 48, WSLPG.Excepcion)
ENDIF

*-- Establecer tipo de certificación a autorizar
tipo_certificado = "P"      &&  cambiar D: deposito, P: planta, R: retiro, T: transf, E: preexistente
    
*-- genero una liq. sec. de ejemplo a autorizar (datos generales):
ok = WSLPG.SetParametro("pto_emision", 99)
ok = WSLPG.SetParametro("nro_orden", 1)
ok = WSLPG.SetParametro("nro_contrato", 100001232)
ok = WSLPG.SetParametro("cuit_comprador", "20111111112")
ok = WSLPG.SetParametro("nro_ing_bruto_comprador", "123")
ok = WSLPG.SetParametro("cod_puerto", 14)
ok = WSLPG.SetParametro("des_puerto_localidad", "DETALLE PUERTO")
ok = WSLPG.SetParametro("cod_grano", 2)
ok = WSLPG.SetParametro("cantidad_tn", 100)
ok = WSLPG.SetParametro("cuit_vendedor", "20222222223")
ok = WSLPG.SetParametro("nro_act_vendedor", 29)
ok = WSLPG.SetParametro("nro_ing_bruto_vendedor", 123456)
ok = WSLPG.SetParametro("actua_corredor", "S")
ok = WSLPG.SetParametro("liquida_corredor", "S")
ok = WSLPG.SetParametro("cuit_corredor", "20267565393")
ok = WSLPG.SetParametro("nro_ing_bruto_corredor", "20267565393")
ok = WSLPG.SetParametro("fecha_precio_operacion", "2014-10-10")
ok = WSLPG.SetParametro("precio_ref_tn", 100)
ok = WSLPG.SetParametro("precio_operacion", 150)
ok = WSLPG.SetParametro("alic_iva_operacion", 10.5)
ok = WSLPG.SetParametro("campania_ppal", 1314)
ok = WSLPG.SetParametro("cod_localidad_procedencia", 197)
ok = WSLPG.SetParametro("cod_prov_procedencia", 10)
ok = WSLPG.SetParametro("datos_adicionales", "Prueba")

*-- Establezco los datos de la Liquidación Sec. Base
ok = WSLPG.CrearLiqSecundariaBase()

*-- Detalle de Deducciones:

codigo_concepto = ""                    && no usado por el momento
detalle_aclaratorio = "deduccion 1"
dias_almacenaje = ""                    && no usado por el momento
precio_pkg_diario = "0"                 && no usado por el momento
comision_gastos_adm = "0"               && no usado por el momento
base_calculo = "1000.00"
alicuota = "21.00"

ok = WSLPG.AgregarDeduccion( ;
    codigo_concepto, ;
    detalle_aclaratorio, ;
    dias_almacenaje, ;
    precio_pkg_diario, ;
    comision_gastos_adm, ;
    base_calculo, ;
    alicuota)

*-- Detalle de Percepciones:

codigo_concepto = ""                    && no usado por el momento
detalle_aclaratoria = "percepcion 1"
base_calculo = "1000.00"
alicuota = "21.00"
ok = WSLPG.AgregarPercepcion( ;
    codigo_concepto, ;
    detalle_aclaratoria, ;
    base_calculo, ;
    alicuota)

*-- Detalle de Opciona:

codigo = "1"
descripcion = "opcional"
ok = WSLPG.AgregarOpcional(codigo, descripcion)

*-- Llamo al metodo remoto lsgAutorizar:

ok = WSLPG.AutorizarLiquidacionSecundaria()

IF ok THEN
    *-- muestro los resultados devueltos por el webservice:
    
    ? "COE", WSLPG.COE

    *-- obtengo los datos adcionales desde losparametros de salida:
    ? "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
	? wslpg.GetParametro("cod_tipo_operacion")
    ? wslpg.GetParametro("fecha_liquidacion") 
    ? wslpg.GetParametro("subtotal")
    ? wslpg.GetParametro("importe_iva")
    ? wslpg.GetParametro("operacion_con_iva")
    ? wslpg.GetParametro("total_peso_neto")
    ? wslpg.GetParametro("numero_contrato")
    ? "Errores", WSLPG.ErrMsg
    IF LEN(WSLPG.ErrMsg) > 0
	    MESSAGEBOX(WSLPG.ErrMsg, 0, "Autorizar Liquidación:")
	    ? WSLPG.XmlRequest
    	? WSLPG.XmlResponse
   	ELSE
   	    MESSAGEBOX("COE: " + STR(WSLPG.COE), 0, "Autorizar Liquidación:")
   	ENDIF

ELSE
	*-- muestro el mensaje de error
    ? WSLPG.Traceback
    ? WSLPG.XmlRequest
    ? WSLPG.XmlResponse
    MESSAGEBOX(WSLPG.Traceback, 5 + 48, WSLPG.Excepcion)
ENDIF

*-- DepuraciÓn (grabar a un archivo los datos de prueba)
gnErrFile = FCREATE('c:\error.txt')  
=FWRITE(gnErrFile, WSLPG.Token + CHR(13))
=FWRITE(gnErrFile, WSLPG.Sign + CHR(13))	
=FWRITE(gnErrFile, WSLPG.XmlRequest + CHR(13))
=FWRITE(gnErrFile, WSLPG.XmlResponse + CHR(13))
=FWRITE(gnErrFile, WSLPG.Excepcion + CHR(13))
=FWRITE(gnErrFile, WSLPG.Traceback + CHR(13))
=FCLOSE(gnErrFile)  


*-- Procedimiento para manejar errores WSFE
PROCEDURE errhand2
	*--PARAMETER merror, mess, mess1, mprog, mlineno
	
	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()
	
	? WSLPG.Excepcion
	? WSLPG.Traceback
	*-- ? WSLPG.XmlRequest
	*-- ? WSLPG.XmlResponse
	
	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(WSLPG.Excepcion, 5 + 48, "Error")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC
