Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
' 2010 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    ' Defino el objeto WSAA usando la librería de tipos PyAfipWs
    ' (Agregar archivo PyAfipWs.tlb a Referencias del Proyecto)
    Dim WSAA As PyAfipWs.WSAA
    
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
    Certificado = "..\..\..\reingart.crt" ' certificado de prueba
    ClavePrivada = "..\..\..\reingart.key" ' clave privada de prueba
    
    
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Path + Certificado, Path + ClavePrivada)
    Debug.Print cms
    
    ' Llamar al web service para autenticar:
    'ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") ' Hologación
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms", "") ' Producción

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign

    Debug.Assert False
    MsgBox "Token: " + WSAA.Token
    MsgBox "Sign: " + WSAA.Sign
End Sub
