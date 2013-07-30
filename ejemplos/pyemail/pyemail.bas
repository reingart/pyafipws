Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para generar Codigos de barra para facturas electronicas
' 2011 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim PyI25 As Object
    
    Dim PyEmail As Object
    
    Set PyEmail = CreateObject("PyEmail")
    
    ' Primer paso: conexión al servidor (por unica vez)
    servidor = "mail.sistemasagiles.com.ar"
    usuario = "no.responder@nsis.com.ar"
    clave = "1238478"
    ok = PyEmail.Conectar(servidor, usuario, clave)
    
    ' Envio el o los correos (repetir por cada FE)
    remitente = "no.responder@sistemasagiles.com.ar"
    destinatario = "reingart@gmail.com"
    mensaje = "Se envia factura electronica adjunta"
    archivo = "C:\FACTURA.PDF"
    
    ok = PyEmail.Enviar(remitente, motivo, destinatario, mensaje, archivo)
 
 
End Sub
