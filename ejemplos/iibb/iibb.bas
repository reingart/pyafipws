Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para consultar
' Alicuotas Ingresos Brutos ARBA
' 2015 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim IIBB As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set IIBB = CreateObject("IIBB")
    
    Debug.Print IIBB.Version
    Debug.Print IIBB.InstallDir
    
    ' Establecer Datos de acceso (ARBA)
    IIBB.Usuario = "20267565393"
    IIBB.Password = "999999"        ' CIT
    
    url = "https://dfe.arba.gov.ar/DomicilioElectronico/SeguridadCliente/dfeServicioConsulta.do"
    
    ' Conectar al servidor (produccion)
    ok = IIBB.Conectar(url)
    
    ' Enviar el archivo y procesar la respuesta:
    fecha_desde = "20150301"
    fecha_hasta = "20150331"
    cuit_contribuyente = "27269434894"
    ok = IIBB.ConsultarContribuyentes(fecha_desde, fecha_hasta, cuit_contribuyente)
    
    ' Hubo error interno?
    If IIBB.Excepcion <> "" Then
        Debug.Print IIBB.Excepcion, IIBB.Traceback
        MsgBox IIBB.Traceback, vbCritical, "Excepcion:" & IIBB.Excepcion
    Else
        Debug.Print IIBB.XmlResponse
        Debug.Print "Error General:", IIBB.TipoError, "|", IIBB.CodigoError, "|", IIBB.MensajeError
        
        ' Hubo error general de ARBA?
        If IIBB.CodigoError <> "" Then
            MsgBox IIBB.MensajeError, vbExclamation, "Error " & IIBB.TipoError & ":" & IIBB.CodigoError
        End If
        
        ' Datos generales de la respuesta:
        Debug.Print "Numero Comprobante:", IIBB.NumeroComprobante
        Debug.Print "Codigo Hash:", IIBB.CodigoHash
    
        ' Datos del contribuyente consultado:
        Debug.Print "CUIT Contribuytente:", IIBB.CuitContribuyente
        Debug.Print "AlicuotaPercepcion:", IIBB.AlicuotaPercepcion
        Debug.Print "AlicuotaRetencion:", IIBB.AlicuotaRetencion
        Debug.Print "GrupoPercepcion:", IIBB.GrupoPercepcion
        Debug.Print "GrupoRetencion:", IIBB.GrupoRetencion
        
    
        MsgBox "CUIT Contribuytente: " & IIBB.CuitContribuyente & vbCrLf & _
                "Numero Comprobante: " & IIBB.NumeroComprobante & vbCrLf & _
                "Codigo Hash: " & IIBB.CodigoHash & vbCrLf & _
                "AlicuotaPercepcion: " & IIBB.AlicuotaPercepcion & vbCrLf & _
                "AlicuotaRetencion: " & IIBB.AlicuotaRetencion & vbCrLf & _
                "GrupoPercepcion: " & IIBB.GrupoPercepcion & vbCrLf & _
                "GrupoRetencion: " & IIBB.GrupoRetencion, _
                vbInformation, "Resultado"
        
    End If
End Sub
