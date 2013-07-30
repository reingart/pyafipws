Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para generar Codigos de barra para facturas electronicas
' 2011 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim PyI25 As Object
    
    Dim PyEmail As Object
    
    Set PyEmail = CreateObject("PyEmail")
    
    Debug.Print PyEmail.Version
    
    ' Primer paso: conexión al servidor (por unica vez)
    servidor = "mail.sistemasagiles.com.ar"
    usuario = "mariano@nsis.com.ar"
    clave = ""
    ok = PyEmail.Conectar(servidor, usuario, clave)
    
    Debug.Print PyEmail.Traceback
    
    ok = PyEmail.Crear()
    
    ' Establesco From: y Reply-To:
    PyEmail.Remitente = "prueba@sistemasagiles.com.ar"
    PyEmail.ResponderA = "no.responder@sistemasagiles.com.ar"
    
    ' Agrego To:
    ok = PyEmail.AgregarDestinatario("reingart@gmail.com")
    ok = PyEmail.AgregarDestinatario("r.castrogiovani@gmail.com")
    
    ' Establezco el mensaje tanto en texto plano como en html con formato
    PyEmail.MensajeTexto = "Se envia factura electronica adjunta"
    PyEmail.MensajeHTML = "Se envia <b>factura electronica</b> adjunta"
    
    ' adjunto los archivos
    ok = PyEmail.Adjuntar("f:\ejemplos\pyfepdf\FACTURA.PDF")
    ok = PyEmail.Adjuntar("f:\ejemplos\pyfepdf\FACTURA.PDF")
    
    ' Envio el o los correos (repetir por cada FE)
    ok = PyEmail.Enviar()
 
    Debug.Print PyEmail.Traceback
End Sub
