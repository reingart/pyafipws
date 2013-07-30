Attribute VB_Name = "Modulo1"
' Ejemplo de Uso de Biblioteca Dinámica LibPyAfipWS DLL en Windows
' para: Web Service de Autenticación y Autorizacion
'       Web Service Factura Electrónica Mercado Interno AFIP
'       según RG2485 (sin detalle, Version 1)
' 2013 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

' NOTA: este ejemplo es solo para usos avanzados, ver:
'       http://www.sistemasagiles.com.ar/trac/wiki/LibPyAfipWs
'       Para Visual Basic, Visual Fox Pro y similares se recomienda la interfaz COM:
'       http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs

' Usar la ruta completa a la DLL (por ej. C:\Archivos ...\libpyafipws.dll)

Declare Function test Lib "..\libpyafipws.dll" () As String
Declare Sub PYAFIPWS_Free Lib "..\libpyafipws.dll" (ByVal bstr As String)
Declare Function WSAA_CreateTRA Lib "..\libpyafipws.dll" (ByVal service As String, ByVal ttl As Long) As String
Declare Function WSAA_SignTRA Lib "..\libpyafipws.dll" (ByVal tra As String, ByVal cert As String, ByVal pk As String) As String
Declare Function WSAA_LoginCMS Lib "..\libpyafipws.dll" (ByVal tra As String) As String


Sub Main()

    ' Llamo a la Prueba Genérica
    s = test()
    Debug.Print s
    Call PYAFIPWS_Free(s)
            
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSFEv1
    ttl = 36000 ' tiempo de vida = 10hs hasta expiración
    tra = WSAA_CreateTRA("wsfe", ttl)
    
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "..\reingart.crt" ' certificado de prueba
    ClavePrivada = "..\reingart.key" ' clave privada de prueba
    
    ' Generar el mensaje firmado (CMS)
    cms = WSAA_SignTRA(tra, Path + Certificado, Path + ClavePrivada)
    Debug.Print cms
    
    ' Llamar al webservice de autenticación:
    ta = WSAA_LoginCMS(cms)

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta

    MsgBox ta, vbExclamation, "LibPyAfipWs: Ticket de Acceso (VB)"

End Sub

