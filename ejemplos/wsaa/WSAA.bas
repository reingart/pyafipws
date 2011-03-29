Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
' Web service de Autenticación y Autorización -
' (para Version Interfaz 2.0 o superior, no funciona con instaladores previos)
' 2010, 2011 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    ' Defino el objeto WSAA usando la librería de tipos PyAfipWs
    ' (Agregar archivo PyAfipWs.tlb a Referencias del Proyecto)
    Dim WSAA As Object
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Debug.Print Err.Description
    Set WSAA = CreateObject("WSAA")
    Debug.Print WSAA.Version

    ' Generar un Ticket de Requerimiento de Acceso (TRA)
    tra = WSAA.CreateTRA("wsfe", 2400)
    Debug.Print tra
    
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "..\..\reingart.crt" ' certificado de prueba
    ClavePrivada = "..\..\reingart.key" ' clave privada de prueba
    
    ' Leo el contenido del certificado y clave privada
    Open Path + Certificado For Input As #1
    cert = ""
    Do Until EOF(1)
        Line Input #1, li
        cert = cert + li + vbLf
    Loop
    Close #1
    Open Path + ClavePrivada For Input As #1
    clave = ""
    Do Until EOF(1)
        Line Input #1, li
        clave = clave + li + vbLf
    Loop
    Close #1
    
    ' Generar el mensaje firmado (CMS)
    Debug.Print Err.Description
    cms = WSAA.SignTRA(tra, cert, clave)
    Debug.Print cms
    
    ' Llamar al web service para autenticar:
    'ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") ' Hologación
    Debug.Print Err.Description
    cache = "" ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" ' homologación
    proxy = "" ' usar "usuario:clave@servidor:puerto"
    ok = WSAA.Conectar(cache, wsdl, proxy)
    ta = WSAA.LoginCMS(cms) ' Producción

    Debug.Print "excepcion", WSAA.Excepcion
    If WSAA.Excepcion <> "" Then
        Debug.Print WSAA.Traceback
        MsgBox WSAA.Excepcion, vbCritical, "Excepción"
    End If
    
    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign

    Debug.Assert False
    MsgBox "Token: " + WSAA.Token
    MsgBox "Sign: " + WSAA.Sign
End Sub
