*-- Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
*-- Liquidación Sector Pecuario
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- 2016 (C) Mariano Reingart <reingart@gmail.com> - Licencia GPLv3

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
tra = WSAA.CreateTRA("wslsp")

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
WSLSP = CREATEOBJECT("WSLSP") 

? WSLSP.Version
? WSLSP.InstallDir

*-- Setear tocken y sig de autorización (pasos previos)
WSLSP.Token = WSAA.Token 
WSLSP.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSLSP.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturación
WSDL = "https://fwshomo.afip.gov.ar/wslsp/LspService?wsdl" && Homologación
&& WSDL = "https://serviciosjava.afip.gob.ar/wslsp/LspService?wsdl" && Producción
ok = WSLSP.Conectar("", WSDL)


*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSLSP.Dummy()
? "appserver status", WSLSP.AppServerStatus
? "dbserver status", WSLSP.DbServerStatus
? "authserver status", WSLSP.AuthServerStatus

*-- Consulto los Puntos de Venta habilitados
ptosvta = WSLSP.ConsultarPuntosVentas()
*-- recorro el array (vector de strings, similar a FOR EACH)
FOR i = 1 TO ALEN(ptosvta)
  ? ptosvta[i]
ENDFOR

*-- obtengo el último número de comprobante registrado (opcional)
pto_vta = 1 
ok = WSLSP.ConsultarUltimoComprobante(pto_vta)
IF ok
    nro_cbte = WSLSP.NroComprobante + 1   && uso el siguiente
    *-- NOTA: es recomendable llevar internamente el control del numero de comprobante
    *--       (ya que sirve para recuperar datos de una liquidación ante AFIP)
    *--       ver documentación oficial de AFIP, sección "Tratamiento Nro Comprobante"
ELSE
    *-- revisar el error, posiblemente no se pueda continuar
    ? WSLSP.Traceback
    ? WSLSP.ErrMsg
    MESSAGEBOX("No se pudo obtener el último número de orden!")
    nro_cbte = 1                    ' uso el primero
ENDIF
       
*-- Establezco los valores de la liquidacion a autorizar:

cod_operacion=1
fecha_cbte="2016-11-12"
fecha_op="2016-11-11"
cod_motivo=6
cod_localidad_procedencia=8274
cod_provincia_procedencia=1
cod_localidad_destino=8274 
cod_provincia_destino=1
lugar_realizacion="CORONEL SUAREZ"
fecha_recepcion=null
fecha_faena=null
datos_adicionales=null

ok = WSLSP.CrearLiquidacion(cod_operacion, fecha_cbte, fecha_op, cod_motivo, ;
    cod_localidad_procedencia, cod_provincia_procedencia, ;
    cod_localidad_destino, cod_provincia_destino, lugar_realizacion, ;
    fecha_recepcion, fecha_faena, datos_adicionales)

&& ok = wslsp.AgregarFrigorifico(cuit, nro_planta)

tipo_cbte=180
pto_vta=3000
nro_cbte=1 
cod_caracter=5
fecha_inicio_act="2016-01-01"
iibb="123456789"
nro_ruca=305
nro_renspa=null

ok = wslsp.AgregarEmisor(tipo_cbte, pto_vta, nro_cbte, ; 
        cod_caracter, fecha_inicio_act, ;
        iibb, nro_ruca, nro_renspa)

cod_caracter=3
ok = wslsp.AgregarReceptor(cod_caracter)

cuit=12222222222
iibb=3456
nro_renspa="22.123.1.12345/A4"
nro_ruca=null
ok = wslsp.AgregarOperador(cuit, iibb, nro_ruca, nro_renspa)

cuit_cliente="12345688888"
cod_categoria=51020102
tipo_liquidacion=1
cantidad=2
precio_unitario=10.0
alicuota_iva=10.5
cod_raza=1
ok = wslsp.AgregarItemDetalle(cuit_cliente, cod_categoria, tipo_liquidacion, ;
        cantidad, precio_unitario, alicuota_iva, cod_raza)
        
tipo_cbte=185
pto_vta=3000
nro_cbte=33
cant_asoc=2
ok = wslsp.AgregarCompraAsociada(tipo_cbte, pto_vta, nro_cbte, cant_asoc)

nro_guia=1
ok = wslsp.AgregarGuia(nro_guia)

nro_dte="418-1"
nro_renspa="22.123.1.12345/A5"
ok = wslsp.AgregarDTE(nro_dte, nro_renspa)

cod_gasto=16
ds=null
base_imponible=230520.60
alicuota=3
alicuota_iva=10.5
ok = wslsp.AgregarGasto(cod_gasto, ds, base_imponible, alicuota, alicuota_iva)

cod_tributo=5
ds=null                             && descripcion para cod_tributo=99  
base_imponible=230520.60
alicuota=2.5
ok = wslsp.AgregarTributo(cod_tributo, ds, base_imponible, alicuota)

cod_tributo=3
ds=null                             && descripcion para cod_tributo=99  
base_imponible=null
alicuota=null
importe=397
ok = wslsp.AgregarTributo(cod_tributo, ds, base_imponible, alicuota, importe)
    
*-- Cargo respuesta de prueba según documentación de AFIP (Ejemplo 1)
*-- (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
&&WSLSP.LoadTestXML ("wslsp_liq_test_response.xml")
&&ok = WSLSP.LoadTestXML("Error001.xml")
           
*-- llamo al webservice con los datos cargados:

ok = WSLSP.AutorizarLiquidacion()
     
IF ok
    *-- muestro los resultados devueltos por el webservice:
    
    ? "CAE", WSLSP.CAE
    ? "NroCodigoBarras", wslsp.NroCodigoBarras
    ? "FechaProcesoAFIP", wslsp.FechaProcesoAFIP
    ? "FechaComprobante", wslsp.FechaComprobante
    ? "NroComprobante", wslsp.NroComprobante
    ? "ImporteBruto", wslsp.ImporteBruto
    ? "ImporteTotalNeto", wslsp.ImporteTotalNeto
    ? "ImporteIVA Sobre Bruto", wslsp.ImporteIVASobreBruto
    ? "ImporteIVA Sobre Gastos", wslsp.ImporteIVASobreGastos
    ? "ImporteTotalNeto", wslsp.ImporteTotalNeto
    
    *-- obtengo los datos adcionales desde los parametros de salida:
    ? "emisor razon_social", WSLSP.GetParametro("emisor", "razon_social")
    ? "emisor domicilio_punto_venta", WSLSP.GetParametro("emisor", "domicilio_punto_venta")
    ? "receptor nombre", WSLSP.GetParametro("receptor", "nombre")
    ? "receptor domicilio", WSLSP.GetParametro("receptor", "domicilio")
    
    MESSAGEBOX("CAE: " + WSLSP.CAE, 0, "Autorizar Liquidación:")
    ? "Errores", WSLSP.ErrMsg
    IF LEN(WSLSP.ErrMsg) > 0
	    MESSAGEBOX(WSLSP.ErrMsg, 0, "Autorizar Liquidación:")
	    ? WSLSP.XmlRequest
    	? WSLSP.XmlResponse
   	ENDIF
ELSE
    *-- muestro el mensaje de error
    ? WSLSP.Traceback
    ? WSLSP.XmlResponse
    MESSAGEBOX(WSLSP.Traceback, 5 + 48, WSLSP.Excepcion)
ENDIF


*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSLSP.Token + CHR(13))
* =FWRITE(gnErrFile, WSLSP.Sign + CHR(13))	
* =FWRITE(gnErrFile, WSLSP.XmlRequest + CHR(13))
* =FWRITE(gnErrFile, WSLSP.XmlResponse + CHR(13))
* =FWRITE(gnErrFile, WSLSP.Excepcion + CHR(13))
* =FWRITE(gnErrFile, WSLSP.Traceback + CHR(13))
* =FCLOSE(gnErrFile)  


