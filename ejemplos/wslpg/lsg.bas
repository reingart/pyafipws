Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Liquidación Secundaria Electrónica de Granos
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
' 2014 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSLPG As Object
    Dim ok As Boolean
    
    ttl = 2400 ' tiempo de vida en segundos
    cache = "" ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    proxy = "" ' usar "usuario:clave@servidor:puerto"

    Certificado = App.Path & "\..\..\reingart.crt"   ' certificado es el firmado por la afip
    ClavePrivada = App.Path & "\..\..\reingart.key"  ' clave privada usada para crear el cert.
        
    Token = ""
    Sign = ""
    
    Set WSAA = CreateObject("WSAA")
    Debug.Print WSAA.InstallDir
    tra = WSAA.CreateTRA("wslpg", ttl)
    Debug.Print tra
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Certificado, ClavePrivada)
    Debug.Print cms
    
    wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" ' homologación
    ok = WSAA.Conectar(cache, wsdl, proxy)
    ta = WSAA.LoginCMS(cms) 'obtener ticket de acceso
    
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Crear objeto interface Web Service de Liquidación Primaria de Granos
    Set WSLPG = CreateObject("WSLPG")
    Debug.Print WSLPG.Version
    Debug.Print WSLPG.InstallDir
    ' Setear tocken y sing de autorización (pasos previos)
    WSLPG.Token = WSAA.Token
    WSLPG.Sign = WSAA.Sign
    ' CUIT (debe estar registrado en la AFIP)
    WSLPG.cuit = "20267565393"
    
    ' Conectar al Servicio Web
    ok = WSLPG.Conectar("", "", "") ' homologación
    If Not ok Then
        Debug.Print WSLPG.Traceback
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
    
    pto_emision = 99
    nro_orden = 1
    nro_contrato = Null '100001232
    cuit_comprador = "20111111112"
    nro_ing_bruto_comprador = "123"
    cod_puerto = 14
    des_puerto_localidad = "DETALLE PUERTO"
    cod_grano = 2
    cantidad_tn = 100
    cuit_vendedor = "20267565393"
    nro_act_vendedor = 29
    nro_ing_bruto_vendedor = 123456
    actua_corredor = "S"
    liquida_corredor = "S"
    cuit_corredor = "20267565393"
    nro_ing_bruto_corredor = "20267565393"
    fecha_precio_operacion = "2014-10-10"
    precio_ref_tn = 100
    precio_operacion = 150
    alic_iva_operacion = 10.5
    campania_ppal = 1314
    cod_localidad_procedencia = 197
    cod_prov_procedencia = 10
    datos_adicionales = "Prueba"
          
    ok = WSLPG.CrearLiqSecundariaBase(pto_emision, nro_orden, _
            nro_contrato, cuit_comprador, nro_ing_bruto_comprador, _
            cod_puerto, des_puerto_localidad, _
            cod_grano, cantidad_tn, _
            cuit_vendedor, nro_act_vendedor, nro_ing_bruto_vendedor, _
            actua_corredor, liquida_corredor, cuit_corredor, nro_ing_bruto_corredor, _
            fecha_precio_operacion, precio_ref_tn, precio_operacion, _
            alic_iva_operacion, campania_ppal, _
            cod_localidad_procedencia, cod_prov_procedencia, _
            datos_adicionales)
    
    ' Detalle de Deducciones:
    
    codigo_concepto = ""                    ' no usado por el momento
    detalle_aclaratorio = "deduccion 1"
    dias_almacenaje = ""                    ' no usado por el momento
    precio_pkg_diario = "0"                 ' no usado por el momento
    comision_gastos_adm = "0"               ' no usado por el momento
    base_calculo = "1000.00"
    alicuota = "21.00"
    
    ok = WSLPG.AgregarDeduccion( _
        codigo_concepto, _
        detalle_aclaratorio, _
        dias_almacenaje, _
        precio_pkg_diario, _
        comision_gastos_adm, _
        base_calculo, _
        alicuota)

    ' Detalle de Percepciones:
    codigo_concepto = ""                    ' no usado por el momento
    detalle_aclaratoria = "percepcion 1"
    base_calculo = "1000.00"
    alicuota = "21.00"
    ok = WSLPG.AgregarPercepcion( _
        codigo_concepto, _
        detalle_aclaratoria, _
        base_calculo, _
        alicuota)
    
    ' Detalle de Opciona:
    codigo = "1"
    descripcion = "opcional"
    ok = WSLPG.AgregarOpcional(codigo, descripcion)
    
    ' LLamada al webservice para autorizar la LSG:
    
    ok = WSLPG.AutorizarLiquidacionSecundaria()
            
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        
        Debug.Print "COE", WSLPG.COE
        
        ' obtengo los datos adcionales desde losparametros de salida:
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        
        MsgBox "COE: " & WSLPG.COE & vbCrLf, vbInformation, "Autorizar Liquidación:"
        If WSLPG.ErrMsg <> "" Then
            Debug.Print "Errores", WSLPG.ErrMsg
            ' recorro y muestro los errores
            For Each er In WSLPG.Errores
                MsgBox er, vbExclamation, "Error"
            Next
        End If

    Else
        ' muestro el mensaje de error
        Debug.Print WSLPG.Traceback
        Debug.Print WSLPG.XmlRequest
        Debug.Print WSLPG.XmlResponse
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
    
End Sub
