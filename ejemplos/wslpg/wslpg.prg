*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Liquidación Primaria Electrónica de Granos RG3419
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- Según RG3419/2012
*-- 2013 (C) Mariano Reingart <reingart@gmail.com>

CLEAR

ON ERROR

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 
? WSAA.Version
? WSAA.InstallDir

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

*-- Crear objeto interface Web Service de Factura Electrónica
WSLPG = CREATEOBJECT("WSLPG") 

? WSLPG.Version
? WSLPG.InstallDir

*-- Setear tocken y sig de autorización (pasos previos)
WSLPG.Token = WSAA.Token 
WSLPG.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSLPG.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturación
*-- Producción usar: 
*-- ok = WSLPG.Conectar("", "https://serviciosjava.afip.gob.ar/wslpg/LpgService?wsdl") && Producción
ok = WSLPG.Conectar("")      && Homologación


*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSLPG.Dummy()
? "appserver status", WSLPG.AppServerStatus
? "dbserver status", WSLPG.DbServerStatus
? "authserver status", WSLPG.AuthServerStatus

*-- Consulto las Actividades habilitadas
actividades = WSLPG.ConsultarTipoActividad()
*-- recorro el array (vector de strings, similar a FOR EACH)
FOR i = 1 TO ALEN(actividades)
  ? actividades[i]
ENDFOR

*-- obtengo el último número ddie orden registrado (opcional)
pto_emision = 1 && agregado en v1.1
ok = WSLPG.ConsultarUltNroOrden(pto_emision)
IF ok
    nro_orden = WSLPG.NroOrden + 1   && uso el siguiente
    *-- NOTA: es recomendable llevar internamente el control del numero de orden
    *--       (ya que sirve para recuperar datos de una liquidación ante AFIP)
    *--       ver documentación oficial de AFIP, sección "Tratamiento Nro Orden"
ELSE
    *-- revisar el error, posiblemente no se pueda continuar
    ? WSLPG.Traceback
    ? WSLPG.ErrMsg
    MESSAGEBOX("No se pudo obtener el último número de orden!")
    nro_orden = 1                    ' uso el primero
ENDIF
       
*-- Establezco los valores de la liquidacion a autorizar:
ok = WSLPG.SetParametro("pto_emision", pto_emision)  && agregado v1.1
ok = WSLPG.SetParametro("nro_orden", nro_orden)
ok = WSLPG.SetParametro("cuit_comprador", WSLPG.Cuit)
ok = WSLPG.SetParametro("nro_act_comprador", 29)
ok = WSLPG.SetParametro("nro_ing_bruto_comprador", WSLPG.Cuit)
ok = WSLPG.SetParametro("cod_tipo_operacion", 1)
ok = WSLPG.SetParametro("es_liquidacion_propia", "N")
ok = WSLPG.SetParametro("es_canje", "N")
ok = WSLPG.SetParametro("cod_puerto", 14)
ok = WSLPG.SetParametro("des_puerto_localidad", "DETALLE PUERTO")
ok = WSLPG.SetParametro("cod_grano", 31)
ok = WSLPG.SetParametro("cuit_vendedor", "23000000019")
ok = WSLPG.SetParametro("nro_ing_bruto_vendedor", "23000000019")
ok = WSLPG.SetParametro("actua_corredor", "N")
ok = WSLPG.SetParametro("liquida_corredor", "N")
&& ok = WSLPG.SetParametro("cuit_corredor", "")
&& ok = WSLPG.SetParametro("comision_corredor", 0)
&& ok = WSLPG.SetParametro("nro_ing_bruto_corredor", "")
ok = WSLPG.SetParametro("fecha_precio_operacion", "2013-02-07")
ok = WSLPG.SetParametro("precio_ref_tn", 2000)
ok = WSLPG.SetParametro("cod_grado_ref", "G1")
ok = WSLPG.SetParametro("cod_grado_ent", "G1")
ok = WSLPG.SetParametro("factor_ent", 98)
ok = WSLPG.SetParametro("precio_flete_tn", 10)
ok = WSLPG.SetParametro("cont_proteico", 20)
ok = WSLPG.SetParametro("alic_iva_operacion", 10.5)
ok = WSLPG.SetParametro("campania_ppal", 1213)
ok = WSLPG.SetParametro("cod_localidad_procedencia", 3)
ok = WSLPG.SetParametro("cod_prov_procedencia", 1) && agregado v1.1
ok = WSLPG.SetParametro("datos_adicionales", "DATOS ADICIONALES")
   
ok = WSLPG.CrearLiquidacion()

*-- Agergo un certificado de Depósito a la liquidación:

tipo_certificado_dposito = 5
nro_certificado_deposito = "555501200729"
peso_neto = 1000
cod_localidad_procedencia = 3
cod_prov_procedencia = 1
campania = 1213
fecha_cierre = "2013-01-13"
            
ok = WSLPG.AgregarCertificado(tipo_certificado_dposito, ;
                       nro_certificado_deposito, ;
                       peso_neto, ;
                       cod_localidad_procedencia, ;
                       cod_prov_procedencia, ;
                       campania, ;
                       fecha_cierre)

*-- Agrego retenciones (opcional):

codigo_concepto = "RI"
detalle_aclaratorio = "DETALLE DE IVA"
base_calculo = 1000
alicuota = 10.5

ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)

codigo_concepto = "RG"
detalle_aclaratorio = "DETALLE DE GANANCIAS"
base_calculo = 100
alicuota = 15

ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
           
*-- Cargo respuesta de prueba según documentación de AFIP (Ejemplo 1)
*-- (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
&&WSLPG.LoadTestXML ("wslpg_aut_test.xml")
&&ok = WSLPG.LoadTestXML("Error001.xml")
           
*-- llamo al webservice con los datos cargados:

ok = WSLPG.AutorizarLiquidacion()
     
IF ok
    *-- muestro los resultados devueltos por el webservice:
    
    ? "COE", WSLPG.COE
    ? "COEAjustado", WSLPG.COEAjustado
    ? "TootalDeduccion", WSLPG.TotalDeduccion
    ? "TotalRetencion", WSLPG.TotalRetencion
    ? "TotalRetencionAfip", WSLPG.TotalRetencionAfip
    ? "TotalOtrasRetenciones", WSLPG.TotalOtrasRetenciones
    ? "TotalNetoAPagar", WSLPG.TotalNetoAPagar
    ? "TotalIvaRg2300_07", WSLPG.TotalIvaRg2300_07
    ? "TotalPagoSegunCondicion", WSLPG.TotalPagoSegunCondicion
    
    *-- obtengo los datos adcionales desde losparametros de salida:
    ? "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
    ? "subtotal", WSLPG.GetParametro("subtotal")
    ? "primer importe_retencion", WSLPG.GetParametro("retenciones", "0", "importe_retencion")
    ? "segundo importe_retencion", WSLPG.GetParametro("retenciones", 1, "importe_retencion")
    ? "primer importe_deduccion", WSLPG.GetParametro("deducciones", 0, "importe_deduccion")
    
    MESSAGEBOX("COE: " + WSLPG.COE, 0, "Autorizar Liquidación:")
    ? "Errores", WSLPG.ErrMsg
    IF LEN(WSLPG.ErrMsg) > 0
	    MESSAGEBOX(WSLPG.ErrMsg, 0, "Autorizar Liquidación:")
	    ? WSLPG.XmlRequest
    	? WSLPG.XmlResponse
   	ENDIF
ELSE
    *-- muestro el mensaje de error
    ? WSLPG.Traceback
    ? WSLPG.XmlResponse
    MESSAGEBOX(WSLPG.Traceback, 5 + 48, WSLPG.Excepcion)
ENDIF

*-- consulto la liquidación autorizada (pto_emision agregado v1.1)
ok = WSLPG.ConsultarLiquidacion(pto_emision, nro_orden)
IF ok
    *-- muestro los resultados devueltos por el webservice   
    ? "COE", WSLPG.COE    
    ? "Errores", WSLPG.ErrMsg
ELSE
    *-- muestro el mensaje de error
    ? WSLPG.Traceback
    ? WSLPG.XmlResponse
ENDIF

coe = "330100000357"     && nro ejemplo AFIP
ok = WSLPG.AnularLiquidacion(coe)
IF ok
    *-- muestro los resultados devueltos por el webservice   
    ? "RESULTADO", WSLPG.Resultado
    ? "Errores", WSLPG.ErrMsg
ELSE
    *-- muestro el mensaje de error
    ? WSLPG.Traceback
    ? WSLPG.XmlResponse
    MESSAGEBOX(WSLPG.Traceback, 5 + 48, WSLPG.Excepcion)
ENDIF


*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSLPG.Token + CHR(13))
* =FWRITE(gnErrFile, WSLPG.Sign + CHR(13))	
* =FWRITE(gnErrFile, WSLPG.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, WSLPG.XmlResponse + CHR(13))
* =FWRITE(gnErrFile, WSLPG.Excepcion + CHR(13))
* =FWRITE(gnErrFile, WSLPG.Traceback + CHR(13))
* =FCLOSE(gnErrFile)  


