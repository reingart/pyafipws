Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
' Web service de Autenticación y Autorización - REUSO DE TICKET DE ACCESO en Visual Basic
' (para Version Interfaz 2.0 o superior, no funciona con instaladores previos)
' 2010, 2011, 2013 (C) Mariano Reingart <reingart@gmail.com>
' para más info ver: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs

Dim WSAA As Object

Sub Main()
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    ' verifico la versión:
    Debug.Assert WSAA.Version >= "2.04a"
    ' deshabilito errores no manejados (version 2.04 o superior)
    WSAA.LanzarExcepciones = False
    
    ' Crear objeto interface Web Service de Factura Electronica
    Set WSFE = CreateObject("WSFEv1")
    
    Debug.Print WSFE.Version
    Debug.Print WSFE.InstallDir
    
    ' solicito ticket de acceso
    Call Autenticar
    
    ' solicito ticket de acceso (nuevamente para chequear rutina)
    ' (no es necesario hacerlo dos veces en producciòn)
    Call Autenticar
    
    ' Setear tocken y sing de autorizacion (pasos previos)
    WSFE.Token = WSAA.Token
    WSFE.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFE.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturacion
    ' Produccion usar:
    ok = WSFE.Conectar("")      ' Homologacion
        
    ' Recupero último número de comprobante para un punto de venta y tipo (opcional)
    tipo_cbte = 1
    punto_vta = 1
    LastCBTE = WSFE.CompUltimoAutorizado(tipo_cbte, punto_vta)
    
    MsgBox "Ult. Nº: " & LastCBTE
    
End Sub

Sub Autenticar()
    ' Procedimiento para autenticar con AFIP y reutilizar el ticket de acceso
    Dim expiracion, solicitar
    expiracion = WSAA.ObtenerTagXml("expirationTime")
    Debug.Print "Fecha Expiracion ticket: ", expiracion
    If IsNull(expiracion) Then
        solicitar = True                 ' solicitud inicial
    Else
        solicitar = WSAA.Expirado()      ' chequear solicitud previa
    End If
    If solicitar Then
        ' Generar un Ticket de Requerimiento de Acceso (TRA)
        tra = WSAA.CreateTRA()

        ' uso la ruta a la carpeta de instalaciòn con los certificados de prueba
        ruta = WSAA.InstallDir + "\"
        Debug.Print "ruta", ruta

        ' Generar el mensaje firmado (CMS)
        cms = WSAA.SignTRA(tra, ruta + "reingart.crt", ruta + "reingart.key") ' Cert. Demo
        
        ok = WSAA.Conectar("", "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologacion

        ' Llamar al web service para autenticar
        ta = WSAA.LoginCMS(cms)
    Else
        Debug.Print "no expirado!", "Reutilizando!"
    End If
    Debug.Print WSAA.ObtenerTagXml("destination")
End Sub

