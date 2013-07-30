Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Digitalización Depositario Fiel
' 2010 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, wDigDepFiel As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para wDigDepFiel
    tra = WSAA.CreateTRA("wDigDepFiel")
    Debug.Print tra
    
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "..\reingart.crt" ' certificado de prueba
    ClavePrivada = "..\reingart.key" ' clave privada de prueba
    
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Path + Certificado, Path + ClavePrivada)
    Debug.Print cms
    
    ' Llamar al web service para autenticar:
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.token
    Debug.Print "Sign:", WSAA.sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Exportación
    Set wDigDepFiel = CreateObject("wDigDepFiel")
    ' Setear tocken y sing de autorización (pasos previos)
    wDigDepFiel.token = WSAA.token
    wDigDepFiel.sign = WSAA.sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    wDigDepFiel.cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = wDigDepFiel.Conectar("https://testdia.afip.gov.ar/Dia/Ws/wDigDepFiel/wDigDepFiel.asmx") ' homologación
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    wDigDepFiel.Dummy
    Debug.Print "appserver status", wDigDepFiel.AppServerStatus
    Debug.Print "dbserver status", wDigDepFiel.DbServerStatus
    Debug.Print "authserver status", wDigDepFiel.AuthServerStatus
       
    tipo_agente = "PSAD" '"DESP"
    rol = "EXTE"
    nro_legajo = "0000000000000000"
    cuit_declarante = "20267565393"
    cuit_psad = "20267565393"
    cuit_ie = "20267565393"
    codigo = "000" ' carpeta completa, "001" carpeta adicional
    fecha_hora_acept = Format(Now(), "yyyy-MM-dd") & "T" & Format(Now(), "hh:mm:ss") & ".000000" ' "2010-06-07T00:23:51.750000"
    ticket = "1234"
    errCode = wDigDepFiel.AvisoRecepAcept(tipo_agente, rol, _
                          nro_legajo, cuit_declarante, cuit_psad, cuit_ie, _
                          codigo, fecha_hora_acept, ticket)
    Debug.Print wDigDepFiel.XmlResponse
       
    MsgBox wDigDepFiel.DescError, vbInformation, "AvisoRecepAcept Código Error: " & wDigDepFiel.CodError
    
    tipo_agente = "PSAD" ' "DESP"
    rol = "EXTE"
    nro_legajo = "0000000000000000" ' "1234567890123456"
    cuit_declarante = "20267565393"
    cuit_psad = "20267565393"
    cuit_ie = "20267565393"
    cuit_ata = "20267565393"
    codigo = "000" ' carpeta completa, "001" carpeta adicional
    ticket = "1234"
    url = "http://www.example.com"
    hashing = "db1491eda47d78532cdfca19c62875aade941dc2"
    
    ' inicializo aviso: limpio datos (familias)
    wDigDepFiel.IniciarAviso
    codigo = "02"
    cantidad = 1
    wDigDepFiel.AgregarFamilia codigo, cantidad
    codigo = "03"
    cantidad = 3
    wDigDepFiel.AgregarFamilia codigo, cantidad
    
    cantidad_total = 4

    errCode = wDigDepFiel.AvisoDigit(tipo_agente, rol, _
                         nro_legajo, cuit_declarante, cuit_psad, cuit_ie, cuit_ata, _
                         codigo, url, ticket, hashing, cantidad_total):
                         
    Debug.Print wDigDepFiel.XmlResponse
       
    MsgBox wDigDepFiel.DescError, vbInformation, "AvisoDigit Código: " & wDigDepFiel.CodError
                         
                             
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print wDigDepFiel.XmlRequest
    Debug.Assert False

End Sub
