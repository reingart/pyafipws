Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
' Web service de Autenticación y Autorización - REUSO DE TICKET DE ACCESO en Visual Basic
' (para Version Interfaz 2.0 o superior, no funciona con instaladores previos)
' 2010, 2011, 2013 (C) Mariano Reingart <reingart@gmail.com>
' para más info ver: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs

Sub Main()
    ' Crear objeto interface Web Service Autenticación y Autorización
    Dim WSAA As Object
    Set WSAA = CreateObject("WSAA")
    ' verifico la versión:
    Debug.Assert WSAA.Version >= "2.04a"
    ' deshabilito errores no manejados (version 2.04 o superior)
    WSAA.LanzarExcepciones = False
    
    ' datos de prueba del certificado (para depuración):
    Dest = "C=ar, O=pyafipws-sistemas agiles, SERIALNUMBER=CUIT 20267565393, CN=mariano reingart"
    
' inicializo las variables:
Token = ""
Sign = ""

' busco un ticket de acceso previamente almacenado:
If Dir("ta.xml") <> "" Then
    ' leo el xml almacenado del archivo
    Open "ta.xml" For Input As #1
    Line Input #1, ta_xml
    Close #1
    ' analizo el ticket de acceso previo:
    ok = WSAA.AnalizarXml(ta_xml)
    ' verifico que el destino corresponda (CUIT)
    Debug.Assert WSAA.ObtenerTagXml("destination") = Dest
    ' verificar CUIT
    If Not WSAA.Expirado() Then
        ' puedo reusar el ticket de acceso:
        Token = WSAA.ObtenerTagXml("token")
        Sign = WSAA.ObtenerTagXml("sign")
    End If
End If

' Si no reuso un ticket de acceso, solicito uno nuevo:
If Token = "" Or Sign = "" Then
    ' Generar un Ticket de Requerimiento de Acceso (TRA)
    tra = WSAA.CreateTRA("wsfe", 43200) ' 3600*12hs
    ' Especificar la ubicacion de los archivos certificado y clave privada
    cert = "reingart.crt" ' certificado de prueba
    clave = "reingart.key" ' clave privada de prueba
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, cert, clave)
    If cms <> "" Then
        ' Llamar al web service para autenticar:
        ok = WSAA.Conectar()
        ta_xml = WSAA.LoginCMS(cms)
        If ta_xml <> "" Then
            ' guardo el ticket de acceso en el archivo
            Open "ta.xml" For Output As #1
            Print #1, ta_xml
            Close #1
        End If
        Token = WSAA.Token
        Sign = WSAA.Sign
    End If
    ' reviso que no haya errores:
    Debug.Print "excepcion", WSAA.Excepcion
    If WSAA.Excepcion <> "" Then
        Debug.Print WSAA.Traceback
        MsgBox WSAA.Excepcion, vbCritical, "Excepción"
    End If
End If

' Imprimir los datos del ticket de acceso: ToKen y Sign de autorización
MsgBox "Token: " + Token
MsgBox "Sign: " + Sign
    
End Sub
