Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para consultar
' Padron Unico de Contribuyentes AFIP via webservice (servicio web WS-SR-Padron Alcance 4)
' Documentación: http://www.sistemasagiles.com.ar/trac/wiki/PadronContribuyentesAFIP
' 2025 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim Padron As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set Padron = CreateObject("WSSrPadronA5")
    
    Debug.Print Padron.Version
    Debug.Print Padron.InstallDir
        
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' URL de produccion
    wsaa_url = "https://wsaa.afip.gov.ar/ws/services/LoginCms"
    padron_a5_url = "https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA5"
    
    ' PRODUCCION !!
    ' ta = WSAA.Autenticar("ws_sr_constancia_inscripcion", WSAA.InstallDir + "\reingart.crt", WSAA.InstallDir + "\reingart.key", wsaa_url)
        
    ta = WSAA.Autenticar("ws_sr_constancia_inscripcion", WSAA.InstallDir + "\reingart.crt", WSAA.InstallDir + "\reingart.key")
    
    Padron.SetTicketAcceso ta
    Padron.Cuit = "20471277534"
    
    ' PRODUCCION !!
    ' Padron.Token = WSAA.Token
    ' Padron.Sign = WSAA.Sign
    ' ok = Padron.Conectar("cache", padron_a5_url)
    
    ok = Padron.Conectar()
    
    ' Consultar CUIT (online con AFIP):
    ' Usar CUITs brindados por ARCA en Homologacion
    id_persona = InputBox("Ingrese CUIT a buscar:", "Consultar Padron AFIP", "20201731594")
    ok = Padron.Consultar(id_persona)
    Debug.Print ok, Err.Description

    ' Imprimir respuesta obtenida
    Debug.Print "Denominacion:", Padron.denominacion
    Debug.Print "Tipo:", Padron.tipo_persona, Padron.tipo_doc, Padron.nro_doc
    Debug.Print "Estado:", Padron.Estado
    Debug.Print "Direccion:", Padron.direccion
    Debug.Print "Localidad:", Padron.localidad
    Debug.Print "Provincia:", Padron.provincia
    Debug.Print "Codigo Postal:", Padron.cod_postal
    For Each impuesto In Padron.impuestos
        Debug.Print "Impuesto:", impuesto
    Next
    For Each actividad In Padron.actividades
        Debug.Print "Actividad:", actividad
    Next
    Debug.Print "IVA", Padron.imp_iva
    Debug.Print "MT", Padron.monotributo, Padron.actividad_monotributo
    Debug.Print "Empleador", Padron.empleador
    
    ' Muestro campos del Impuesto (actualizacion 1.06)
    For Each id_impuesto In Padron.impuestos
        Debug.Print "Id Impuesto: ", id_impuesto
        Debug.Print "Descripcion Impuesto: ", Padron.ObtenerCampoImpuesto(id_impuesto, "descripcionImpuesto")
        Debug.Print "Motivo: ", Padron.ObtenerCampoImpuesto(id_impuesto, "motivo")
        Debug.Print "Estado Impuesto: ", Padron.ObtenerCampoImpuesto(id_impuesto, "estadoImpuesto")
        Debug.Print "Periodo: ", Padron.ObtenerCampoImpuesto(id_impuesto, "periodo")
    Next

    If Padron.Excepcion = "" Then
        MsgBox Padron.denominacion & " " & Padron.Estado & vbCrLf & Padron.direccion & vbCrLf & Padron.localidad & vbCrLf & Padron.provincia & vbCrLf & Padron.cod_postal, vbInformation, "Resultado CUIT " & Cuit & " (online AFIP)"
    Else
        ' respuesta del servidor (para depuración)
        ' Debug.Print Padron.response
        MsgBox "Error AFIP: " & Padron.Excepcion, vbCritical, "Resultado CUIT " & Cuit & " (online)"
    End If

End Sub

