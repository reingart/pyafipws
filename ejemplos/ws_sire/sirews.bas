Attribute VB_Name = "Modulo1"
' Ejemplo de Uso de Interface COM con Web Service SIRE Certificado de Retencion electronica AFIP
' para Visual Basic 5.0 o superior (VB5 o VB6)
' Documentación: http://www.sistemasagiles.com.ar/trac/wiki/SIRE_CertificadoRetencionElectronica
' 2020 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim WSAA As Object, WSSIRE As Object
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    Debug.Print WSAA.version
    If WSAA.version < "2.07" Then
        MsgBox "Debe instalar una versión más actualizada de PyAfipWs WSAA!"
        End
    End If
            
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    crt = Path + "..\..\reingart.crt" ' certificado de prueba
    Key = Path + "..\..\reingart.key" ' clave privada de prueba
    url_wsaa = "" ' cambiar en producción
    
    ta = WSAA.Autenticar("sire-ws", crt, Key, url_wsaa)
    If ta = "" Then
        MsgBox WSAA.Excepcion, vbCritical, "No se puede gestionar el Ticket de Acceso"
        End
    End If
             
    ' Crear objeto interface Web Service de Constatación de Comprobantes emitidos
    Set WSSIRE = CreateObject("WSSIREc2005")
    Debug.Print WSSIRE.version
    If WSAA.version < "1.12" Then
        MsgBox "Debe instalar una versión mas actualizada de PyAfipWs WSSIRE!"
        End
    End If
    'Debug.Print WSSIRE.InstallDir
    
    ' Setear tocken y sing de autorización (pasos previos)
    WSSIRE.Token = WSAA.Token
    WSSIRE.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSSIRE.Cuit = "20267565393"
    
    ' deshabilito errores no manejados
    WSSIRE.LanzarExcepciones = False
    
    ' Conectar al Servicio Web
    proxy = "" ' "usuario:clave@localhost:8000"
    wsdl = "https://ws-aplicativos-reca.homo.afip.gob.ar/sire/ws/v1/c2005/2005?wsdl"
    cache = "" 'Path
    wrapper = "" ' libreria http (httplib2, urllib2, pycurl)
    cacert = WSAA.InstallDir & "\afip_ca_info.crt" ' certificado de la autoridad de certificante (solo pycurl)
    
    ok = WSSIRE.Conectar(cache, wsdl, proxy, wrapper, cacert) ' homologación
    If Not ok Then
        MsgBox WSSIRE.Traceback, vbCritical, WSCDC.Excepcion
        End
    End If
        
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    ok = WSSIRE.Dummy()
    Debug.Print "appserver status", WSSIRE.AppServerStatus
    Debug.Print "dbserver status", WSSIRE.DbServerStatus
    Debug.Print "authserver status", WSSIRE.AuthServerStatus

    version = 100
    impuesto = 216
    regimen = 831
    fecha_retencion = "2019-11-26T11:22:00.969-03:00"
    importe_retencion = 0
    importe_base_calculo = 0
    regimen_exclusion = False
    tipo_comprobante = 1
    fecha_comprobante = "2019-11-26T11:22:00.969-03:00"
    importe_comprobante = 0
    cuit_retenido = "30500010912"
    fecha_retencion_certificado_original = "2019-11-26T11:22:00.969-03:00"
    codigo_trazabilidad = Null
    condicion = 1 ' 1: Inscripto , 2: No inscriptio
    imposibilidad_retencion = False
    motivo_no_retencion = Null
    porcentaje_exclusion = Null
    fecha_publicacion = Null
    numero_comprobante = "99999-99999999"
    coe = None
    coe_original = Null
    cae = Null
    motivo_emision_nota_credito = Null
    numero_certificado_original = Null
    importe_certificado_original = Null
    motivo_anulacion = Null
    
    ok = WSSIRE.Emitir(version, impuesto, regimen, fecha_retencion, importe_retencion, importe_base_calculo, _
                regimen_exclusion, tipo_comprobante, fecha_comprobante, importe_comprobante, _
                cuit_retenido, fecha_retencion_certificado_original, codigo_trazabilidad, condicion, _
                imposibilidad_retencion, motivo_no_retencion, porcentaje_exclusion, fecha_publicacion, _
                numero_comprobante, coe, coe_original, cae, motivo_emision_nota_credito, _
                numero_certificado_original, importe_certificado_original, motivo_anulacion)
                
    Debug.Print "XMLRequest: ", WSSIRE.XMLRequest
    Debug.Print "XMLResponse: ", WSSIRE.XMLResponse
    
    Debug.Print "Traceback: ", WSSIRE.Traceback
                
    If ok Then
        Debug.Print "CertificadoNro: ", WSSIRE.CertificadoNro
        Debug.Print "CodigoSeguridad: ", WSSIRE.CodigoSeguridad
    End If
End Sub
