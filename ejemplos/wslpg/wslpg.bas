Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Liquidación Primaria Electrónica de Granos
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
' 2013 (C) Mariano Reingart <reingart@gmail.com>

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
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    ok = WSLPG.Dummy()
    If Not ok Then
        ' muestro el mensaje de error
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    Else
        Debug.Print "appserver status", WSLPG.AppServerStatus
        Debug.Print "dbserver status", WSLPG.DbServerStatus
        Debug.Print "authserver status", WSLPG.AuthServerStatus
    End If
    
    ' Consulto las campanias (usando dos puntos como separador)
    For Each parametro In WSLPG.ConsultarCampanias(":")
        Debug.Print parametro ' devuelve un string ": codigo : descripcion :"
    Next
    
    ' obtengo el último número de orden registrado
    ok = WSLPG.ConsultarUltNroOrden()
    If ok Then
        nro_orden = WSLPG.NroOrden + 1   ' uso el siguiente
    Else
        ' revisar el error, posiblemente no se pueda continuar
        Debug.Print WSLPG.Traceback
        Debug.Print WSLPG.ErrMsg
        MsgBox "No se pudo obtener el último número de orden!"
        nro_orden = 1                    ' uso el primero
    End If
    
    cuit_comprador = "23000000000"
    nro_act_comprador = 99: nro_ing_bruto_comprador = "23000000000"
    cod_tipo_operacion = 1
    es_liquidacion_propia = "N": es_canje = "N"
    cod_puerto = 14: des_puerto_localidad = "DETALLE PUERTO"
    cod_grano = 31
    cuit_vendedor = "30000000007": nro_ing_bruto_vendedor = "30000000007"
    actua_corredor = "S": liquida_corredor = "S": cuit_corredor = "20267565393"
    comision_corredor = 1: nro_ing_bruto_corredor = "20267565393"
    fecha_precio_operacion = "2013-02-07"
    precio_ref_tn = 2000
    cod_grado_ref = "G1"
    cod_grado_ent = "G1"
    factor_ent = 98
    precio_flete_tn = 10
    cont_proteico = 20
    alic_iva_operacion = 10.5
    campania_ppal = 1213
    cod_localidad_procedencia = 3
    datos_adicionales = "DATOS ADICIONALES"
       
    ok = WSLPG.CrearLiquidacion(nro_orden, cuit_comprador, _
                               nro_act_comprador, nro_ing_bruto_comprador, _
                               cod_tipo_operacion, _
                               es_liquidacion_propia, es_canje, _
                               cod_puerto, des_puerto_localidad, cod_grano, _
                               cuit_vendedor, nro_ing_bruto_vendedor, _
                               actua_corredor, liquida_corredor, cuit_corredor, _
                               comision_corredor, nro_ing_bruto_corredor, _
                               fecha_precio_operacion, _
                               precio_ref_tn, cod_grado_ref, cod_grado_ent, _
                               factor_ent, precio_flete_tn, cont_proteico, _
                               alic_iva_operacion, campania_ppal, _
                               cod_localidad_procedencia, _
                               datos_adicionales)
    
    ' Agergo un certificado de Depósito a la liquidación:
    
    tipo_certificado_dposito = 5
    nro_certificado_deposito = 101200604
    peso_neto = 1000
    cod_localidad_procedencia = 3
    cod_prov_procedencia = 1
    campania = 1213
    fecha_cierre = "2013-01-13"
                
    ok = WSLPG.AgregarCertificado(tipo_certificado_dposito, _
                           nro_certificado_deposito, _
                           peso_neto, _
                           cod_localidad_procedencia, _
                           cod_prov_procedencia, _
                           campania, _
                           fecha_cierre)
    
    ' Agrego retenciones (opcional):
    
    codigo_concepto = "RI"
    detalle_aclaratorio = "DETALLE DE IVA"
    base_calculo = 1970
    alicuota = 8

    ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
    
    codigo_concepto = "RG"
    detalle_aclaratorio = "DETALLE DE GANANCIAS"
    base_calculo = 100
    alicuota = 2
    
    ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
               
    ' Cargo respuesta de prueba según documentación de AFIP (Ejemplo 1)
    ' (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
    ''WSLPG.LoadTestXML ("wslpg_aut_test.xml")
               
    ' llamo al webservice con los datos cargados:
    
    ok = WSLPG.AutorizarLiquidacion()
         
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        
        Debug.Print "COE", WSLPG.COE
        Debug.Print "COEAjustado", WSLPG.COEAjustado
        Debug.Print "TootalDeduccion", WSLPG.TotalDeduccion
        Debug.Print "TotalRetencion", WSLPG.TotalRetencion
        Debug.Print "TotalRetencionAfip", WSLPG.TotalRetencionAfip
        Debug.Print "TotalOtrasRetenciones", WSLPG.TotalOtrasRetenciones
        Debug.Print "TotalNetoAPagar", WSLPG.TotalNetoAPagar
        Debug.Print "TotalIvaRg2300_07", WSLPG.TotalIvaRg2300_07
        Debug.Print "TotalPagoSegunCondicion", WSLPG.TotalPagoSegunCondicion
        
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
        Debug.Print WSLPG.XmlResponse
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
    
    ' consulto una liquidacion
    
    ok = WSLPG.ConsultarLiquidacion(nro_orden)
    If ok Then
        MsgBox "COE:" & WSLPG.COE & vbCrLf & "Estado: " & WSLPG.Estado & vbCrLf, vbInformation, "Consultar Liquidación:"
        For Each er In WSLPG.Errores
            MsgBox er, vbExclamation, "Error"
        Next
    End If
    
    
    ' anulo una liquidacion
    
    COE = "330100000357"     ' nro ejemplo AFIP
    ok = WSLPG.AnularLiquidacion(COE)
    If ok Then
        MsgBox "Resultado: " & WSLPG.Resultado & vbCrLf, vbInformation, "AnularLiquidación:"
        For Each er In WSLPG.Errores
            MsgBox er, vbExclamation, "Error"
        Next
    End If
    
End Sub
