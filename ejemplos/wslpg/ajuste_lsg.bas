Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Liquidación Secundaria Electrónica de Granos (AJUSTE)
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
' 2015 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSLPG As Object
    Dim ok As Boolean
    
    Set WSAA = CreateObject("WSAA")
    
    ttl = 2400 ' tiempo de vida en segundos
    cache = "" ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    proxy = "" ' usar "usuario:clave@servidor:puerto"

    Certificado = WSAA.InstallDir & "\conf\reingart.crt"   ' certificado es el firmado por la afip
    ClavePrivada = WSAA.InstallDir & "\conf\reingart.key"  ' clave privada usada para crear el cert.
        
    Token = ""
    Sign = ""
    
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
    
    ' consulto el ùltimo nro de orden y la primer LSG para ajustarla:
    
    pto_emision = 99
    ok = WSLPG.ConsultarLiquidacionSecundariaUltNroOrden(pto_emision)
    nro_orden = WSLPG.NroOrden
    ok = WSLPG.ConsultarLiquidacionSecundaria(pto_emision, 1)

    Debug.Print WSLPG.XmlResponse
    Debug.Print WSLPG.Traceback
    Debug.Print WSLPG.COE
    
    ' creo el ajuste base y establezco parametros generales:
    
    If WSLPG.COE = "" Then
        ' llamar al méotodo remoto lsgAjustarXContrato
        ok = WSLPG.SetParametro("nro_contrato", "999999999999999")
    Else
        ' llamar al método remoto lsgAjustarXCoe
        ok = WSLPG.SetParametro("coe_ajustado", WSLPG.COE)
    End If
    
    ok = WSLPG.SetParametro("nro_act_comprador", "29")
    ok = WSLPG.SetParametro("cod_grano", "2")
    ok = WSLPG.SetParametro("cuit_vendedor", "20267565393")
    ok = WSLPG.SetParametro("cuit_comprador", "20111111112")
    ok = WSLPG.SetParametro("cuit_corredor", "20267565393")
    ok = WSLPG.SetParametro("cod_localidad", 197)
    ok = WSLPG.SetParametro("cod_provincia", 10)
    
    ok = WSLPG.CrearAjusteBase(pto_emision, nro_orden + 1)

    ' creo el ajuste de crédito (ver documentación AFIP):

    ok = WSLPG.SetParametro("concepto_importe_iva_105", "Alic 10.5")
    ok = WSLPG.SetParametro("importe_ajustar_iva_105", 100)

    ok = WSLPG.SetParametro("concepto_importe_iva_0", "Alic 0")
    ok = WSLPG.SetParametro("importe_ajustar_iva_0", 200)

    ok = WSLPG.SetParametro("datos_adicionales", "AJUSTE CRED LSG")

    ok = WSLPG.CrearAjusteCredito()
    
    ok = WSLPG.SetParametro("concepto_importe_iva_0", "Alic 0")
    ok = WSLPG.SetParametro("importe_ajustar_iva_0", 200)

    ok = WSLPG.SetParametro("concepto_importe_iva_105", "Alic 10.5")
    ok = WSLPG.SetParametro("importe_ajustar_iva_105", 200)

    ok = WSLPG.SetParametro("datos_adicionales", "AJUSTE DEB LSG")
    
    ok = WSLPG.CrearAjusteDebito()

    ' Llamar al método remoto para ajustar la LSG:
    
    ok = WSLPG.AjustarLiquidacionSecundaria()
    
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        
        Debug.Print "COE", WSLPG.COE
        
        ' obtengo los datos adcionales desde losparametros de salida:
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        
        MsgBox "COE: " & WSLPG.COE & vbCrLf, vbInformation, "Ajustar Liquidación:"
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
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
        
    ' Mensajes XML para depuración:
    Debug.Print WSLPG.XmlRequest
    Debug.Print WSLPG.XmlResponse
    
End Sub
