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
tipo_certificado = "P"      &&  cambiar P: primaria, R: retiro, T: transf, E: preexistente
    
*-- genero una certificación de ejemplo a autorizar (datos generales de cabecera):
pto_emision = 99
nro_orden = 1
nro_planta = "1"
nro_ing_bruto_depositario = "20267565393"
titular_grano = "T"
cuit_depositante = "20111111112"
nro_ing_bruto_depositante = "123"
cuit_corredor = "20222222223"
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
        ok = WSLPG.SetParametro("monto_almacenaje", 1)
        ok = WSLPG.SetParametro("monto_acarreo", 2)
        ok = WSLPG.SetParametro("monto_gastos_generales", 3)
        ok = WSLPG.SetParametro("monto_zarandeo", 4)
        ok = WSLPG.SetParametro("porcentaje_secado_de", 5)
        ok = WSLPG.SetParametro("porcentaje_secado_a", 6)
        ok = WSLPG.SetParametro("monto_secado", 7)
        ok = WSLPG.SetParametro("monto_por_cada_punto_exceso", 8)
        ok = WSLPG.SetParametro("monto_otros", 9)
        ok = WSLPG.SetParametro("analisis_muestra", 10)
        ok = WSLPG.SetParametro("nro_boletin", 11)
        ok = WSLPG.SetParametro("valor_grado", 1.02)
        ok = WSLPG.SetParametro("valor_contenido_proteico", 1)
        ok = WSLPG.SetParametro("valor_factor", 1)
        ok = WSLPG.SetParametro("porcentaje_merma_volatil", 15)
        ok = WSLPG.SetParametro("peso_neto_merma_volatil", 16)
        ok = WSLPG.SetParametro("porcentaje_merma_secado", 17)
        ok = WSLPG.SetParametro("peso_neto_merma_secado", 18)
        ok = WSLPG.SetParametro("porcentaje_merma_zarandeo", 19)
        ok = WSLPG.SetParametro("peso_neto_merma_zarandeo", 20)
        ok = WSLPG.SetParametro("peso_neto_certificado", 21)
        ok = WSLPG.SetParametro("servicios_secado", 22)
        ok = WSLPG.SetParametro("servicios_zarandeo", 23)
        ok = WSLPG.SetParametro("servicios_otros", 24)
        ok = WSLPG.SetParametro("servicios_forma_de_pago", 25)
        
        ok = WSLPG.AgregarCertificacionPrimaria()
    
        descripcion_rubro = "bonif"
        tipo_rubro = "B"
        porcentaje = 1
        valor = 1
        ok = WSLPG.AgregarDetalleMuestraAnalisis( ;
            descripcion_rubro, tipo_rubro, porcentaje, valor)

        nro_ctg = "123456"
        nro_carta_porte = 1000
        porcentaje_secado_humedad = 1
        importe_secado = 2
        peso_neto_merma_secado = 3
        tarifa_secado = 4
        importe_zarandeo = 5
        peso_neto_merma_zarandeo = 6
        tarifa_zarandeo = 7
        ok = WSLPG.AgregarCTG( ;
            nro_ctg, nro_carta_porte, ;
            porcentaje_secado_humedad, importe_secado, ;
            peso_neto_merma_secado, tarifa_secado, ;
            importe_zarandeo, peso_neto_merma_zarandeo, ;
            tarifa_zarandeo)

    CASE INLIST(tipo_certificado, "R", "T")
        *-- establezco datos del certificado retiro/transferencia F1116R/T:
        cuit_receptor = "20400000000"
        fecha = "2014-11-26"
        nro_carta_porte_a_utilizar = "12345"
        cee_carta_porte_a_utilizar = "123456789012"
        nro_act_depositario = "29"
        ok = WSLPG.AgregarCertificacionRetiroTransferencia( ;
                nro_act_depositario, cuit_receptor, fecha, ;
                nro_carta_porte_a_utilizar, ;
                cee_carta_porte_a_utilizar)
        *-- datos del certificado (los NULL no se utilizan por el momento)
        ok = WSLPG.SetParametro("peso_neto", 10000)
        ok = WSLPG.SetParametro("coe_certificado_deposito", "123456789012")
        ok = WSLPG.AgregarCertificado()
        
    CASE INLIST(tipo_certificado, "E")
        *-- establezco datos del certificado preexistente:
        tipo_certificado_deposito_preexistente = 1  && "R" o "T"
        nro_certificado_deposito_preexistente = "12345"
        cac_certificado_deposito_preexistente = "123456789012"
        fecha_emision_certificado_deposito_preexistente = "2014-11-26"
        peso_neto = 1000
        ok = WSLPG.AgregarCertificacionPreexistente( ;
                tipo_certificado_deposito_preexistente, ;
                nro_certificado_deposito_preexistente, ;
                cac_certificado_deposito_preexistente, ;
                fecha_emision_certificado_deposito_preexistente, ;
                peso_neto)

ENDCASE

*-- Llamo al metodo remoto cgAutorizar:

ok = WSLPG.AutorizarCertificacion()

IF ok THEN
    *-- muestro los resultados devueltos por el webservice:
    
    ? "COE", WSLPG.COE
    ? "Fecha", WSLPG.FechaCertificacion
    
    MESSAGEBOX("COE: " + STR(WSLPG.COE), 0, "Autorizar Liquidación:")
    ? "Errores", WSLPG.ErrMsg
    IF LEN(WSLPG.ErrMsg) > 0
	    MESSAGEBOX(WSLPG.ErrMsg, 0, "Autorizar Liquidación:")
	    ? WSLPG.XmlRequest
    	? WSLPG.XmlResponse
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
