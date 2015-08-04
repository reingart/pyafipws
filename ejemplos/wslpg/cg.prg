*-- Ejemplo de Uso de Interface COM con Web Service Certificación Electrónica de Granos
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
&& cCurrentProcedure = SYS(16,1) 
&& nPathStart = AT(":",cCurrentProcedure)- 1
&& nLenOfPath = RAT("\", cCurrentProcedure) - (nPathStart)
&& ruta = (SUBSTR(cCurrentProcedure, nPathStart, nLenofPath)) + "\"
*-- usar la ruta a las credenciales predeterminadas para homologaciòn
ruta = WSAA.InstallDir + "\"
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

*-- ON ERROR DO errhand2;

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
tipo_certificado = "P"      &&  cambiar P: primaria, R: retiro, T: transf, E: preexistente
    
*-- genero una certificación de ejemplo a autorizar (datos generales de cabecera):
pto_emision = 99

*-- Obtengo el último nro de certificación
ok = WSLPG.ConsultarCertificacionUltNroOrden(pto_emision)
nro_orden = WSLPG.NroOrden + 1
? "Nro. CG: ", nro_orden

nro_planta = "3091"
nro_ing_bruto_depositario = "20267565393"
titular_grano = "T"
cuit_depositante = "20111111112"
nro_ing_bruto_depositante = "123"
cuit_corredor = null && "20222222223"
cod_grano = 2
campania = 1314
datos_adicionales = "Prueba"

*-- Establezco los datos de cabecera
ok = WSLPG.CrearCertificacionCabecera( ;
        pto_emision, nro_orden, ;
        tipo_certificado, nro_planta, ;
        nro_ing_bruto_depositario, ;
        titular_grano, ;
        cuit_depositante, ;
        nro_ing_bruto_depositante, ;
        cuit_corredor, ;
        cod_grano, campania, ;
        datos_adicionales)

DO CASE
	
    CASE INLIST(tipo_certificado, "P")
        *-- datos del certificado depósito F1116A:
        ok = WSLPG.SetParametro("nro_act_depositario", "29")
        ok = WSLPG.SetParametro("descripcion_tipo_grano", "SOJA")
        ok = WSLPG.SetParametro("monto_almacenaje", 0)
        ok = WSLPG.SetParametro("monto_acarreo", 0)
        ok = WSLPG.SetParametro("monto_gastos_generales", 0)
        ok = WSLPG.SetParametro("monto_zarandeo", 0)
        ok = WSLPG.SetParametro("porcentaje_secado_de", 6)
        ok = WSLPG.SetParametro("porcentaje_secado_a", 5)
        ok = WSLPG.SetParametro("monto_secado", 0)
        ok = WSLPG.SetParametro("monto_por_cada_punto_exceso", 0)
        ok = WSLPG.SetParametro("monto_otros", 0)
        ok = WSLPG.SetParametro("porcentaje_merma_volatil", 0)
        ok = WSLPG.SetParametro("peso_neto_merma_volatil", 0)
        ok = WSLPG.SetParametro("porcentaje_merma_secado", 0)
        ok = WSLPG.SetParametro("peso_neto_merma_secado", 0)
        ok = WSLPG.SetParametro("porcentaje_merma_zarandeo", 0)
        ok = WSLPG.SetParametro("peso_neto_merma_zarandeo", 0)
        ok = WSLPG.SetParametro("peso_neto_certificado", 10000)
        ok = WSLPG.SetParametro("servicios_secado", 0)
        ok = WSLPG.SetParametro("servicios_zarandeo", 0)
        ok = WSLPG.SetParametro("servicios_otros", 0)
        ok = WSLPG.SetParametro("servicios_forma_de_pago", 0)
        
        ok = WSLPG.AgregarCertificacionPrimaria()
        
        analisis_muestra = 10
        nro_boletin = 11
        cod_grado = "F1"
        valor_grado = 1.02
        valor_contenido_proteico = 1
        valor_factor = 1

        ok = WSLPG.AgregarCalidad(analisis_muestra, nro_boletin, cod_grado, valor_grado, valor_contenido_proteico, valor_factor)
    
        descripcion_rubro = "bonif"
        tipo_rubro = "B"
        porcentaje = 1
        valor = 1
        ok = WSLPG.AgregarDetalleMuestraAnalisis( ;
            descripcion_rubro, tipo_rubro, porcentaje, valor)

        nro_ctg = "437"
        nro_carta_porte = "530305318"
        porcentaje_secado_humedad = 0
        importe_secado = 0
        peso_neto_merma_secado = 0
        tarifa_secado = 0
        importe_zarandeo = 0
        peso_neto_merma_zarandeo = 0
        tarifa_zarandeo = 0
        peso_neto_confirmado_definitivo = 1
        ok = WSLPG.AgregarCTG( ;
            nro_ctg, nro_carta_porte, ;
            porcentaje_secado_humedad, importe_secado, ;
            peso_neto_merma_secado, tarifa_secado, ;
            importe_zarandeo, peso_neto_merma_zarandeo, ;
            tarifa_zarandeo, peso_neto_confirmado_definitivo)

    CASE INLIST(tipo_certificado, "R", "T")
        *-- establezco datos del certificado retiro/transferencia F1116R/T:
        cuit_receptor = "20111111112"
        fecha = "2014-11-26"
        nro_carta_porte_a_utilizar = "12345"
        cee_carta_porte_a_utilizar = "530305322"
        nro_act_depositario = "29"
        ok = WSLPG.AgregarCertificacionRetiroTransferencia( ;
                nro_act_depositario, cuit_receptor, fecha, ;
                nro_carta_porte_a_utilizar, ;
                cee_carta_porte_a_utilizar)
        *-- datos del certificado (los NULL no se utilizan por el momento)
        ok = WSLPG.SetParametro("peso_neto", 20000)
        ok = WSLPG.SetParametro("coe_certificado_deposito", "123456789012")
        ok = WSLPG.AgregarCertificado()
        
    CASE INLIST(tipo_certificado, "E")
        *-- establezco datos del certificado preexistente:
        tipo_certificado_deposito_preexistente = 1  && "R" o "T"
        nro_certificado_deposito_preexistente = "530305327"
        cac_certificado_deposito_preexistente = "85113524869336"
        fecha_emision_certificado_deposito_preexistente = "2014-11-26"
        peso_neto = 1000
        nro_planta = 1234
        ok = WSLPG.AgregarCertificacionPreexistente( ;
                tipo_certificado_deposito_preexistente, ;
                nro_certificado_deposito_preexistente, ;
                cac_certificado_deposito_preexistente, ;
                fecha_emision_certificado_deposito_preexistente, ;
                peso_neto, nro_planta)

ENDCASE

*-- cargar respuesta predeterminada de prueba (solo usar en evaluacion/testing)
If .F. Then
	ok = WSLPG.LoadTestXML(WSLPG.InstallDir + "\tests\wslpg_cert_autorizar_resp.xml")
Endif

*-- Llamo al metodo remoto cgAutorizar:

ok = WSLPG.AutorizarCertificacion()

IF ok THEN
    *-- muestro los resultados devueltos por el webservice:
    
    coe = WSLPG.GetParametro("coe")   && obtener string, valor long (WSLPG.COE) no soportado en algunas versiones de VFP
    ? "COE", coe
    ? "Estado", WSLPG.Estado
    ? "Fecha", WSLPG.GetParametro("fecha_certificacion")

    *-- Planta (opcional):
    ? "Nro. Planta", WSLPG.GetParametro("nro_planta")
    ? "Cuit Titular Planta", WSLPG.GetParametro("cuit_titular_planta")
    ? "Razon Titular Planta", WSLPG.GetParametro("razon_titular_planta")

    *-- Resumen de pesos (si fue autorizada):
    ? "peso_bruto_certificado", WSLPG.GetParametro("peso_bruto_certificado")
    ? "peso_merma_secado", WSLPG.GetParametro("peso_merma_secado")
    ? "peso_merma_volatil", WSLPG.GetParametro("peso_merma_volatil")
    ? "peso_merma_zarandeo", WSLPG.GetParametro("peso_merma_zarandeo")
    ? "peso_neto_certificado", WSLPG.GetParametro("peso_neto_certificado")

    *-- Resumen de servicios (si fue autorizada):
    ? "importe_iva", WSLPG.GetParametro("importe_iva")
    ? "servicio_gastos_generales", WSLPG.GetParametro("servicio_gastos_generales")
    ? "servicio_otros", WSLPG.GetParametro("servicio_otros")
    ? "servicio_total", WSLPG.GetParametro("servicio_total")
    ? "servicio_zarandeo", WSLPG.GetParametro("servicio_zarandeo")

    ? "Errores", WSLPG.ErrMsg
    IF LEN(WSLPG.ErrMsg) > 0
	    MESSAGEBOX(WSLPG.ErrMsg, 0, "Autorizar Certificación:")
	    ? WSLPG.XmlRequest
    	? WSLPG.XmlResponse
    ELSE
        ch = MESSAGEBOX("COE: " + coe, 5, "Autorizar Certificación:")
        ok = WSLPG.AnularCertificacion(coe)
        ? "Estado Anulado", WSLPG.Estado
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
