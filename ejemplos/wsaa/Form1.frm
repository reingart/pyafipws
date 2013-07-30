VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "Ejemplo interactivo Interfaz PyAfipWs para WSAA"
   ClientHeight    =   6570
   ClientLeft      =   60
   ClientTop       =   345
   ClientWidth     =   9465
   LinkTopic       =   "Form1"
   ScaleHeight     =   6570
   ScaleWidth      =   9465
   StartUpPosition =   3  'Windows Default
   Begin VB.ComboBox cboWrapper 
      Height          =   315
      ItemData        =   "Form1.frx":0000
      Left            =   3840
      List            =   "Form1.frx":000D
      TabIndex        =   39
      Text            =   "httplib2"
      ToolTipText     =   "librería HTTP"
      Top             =   4320
      Width           =   975
   End
   Begin VB.TextBox txtCACert 
      BackColor       =   &H8000000F&
      Enabled         =   0   'False
      Height          =   285
      Left            =   1560
      TabIndex        =   37
      ToolTipText     =   "autoridad certificante (solo pycurl)"
      Top             =   4320
      Width           =   2295
   End
   Begin VB.TextBox txtTraceback 
      Height          =   615
      Left            =   1560
      MultiLine       =   -1  'True
      TabIndex        =   35
      Top             =   5880
      Width           =   3255
   End
   Begin VB.TextBox txtInstallDir 
      BackColor       =   &H00E0E0E0&
      Height          =   285
      Left            =   6720
      Locked          =   -1  'True
      TabIndex        =   34
      Top             =   120
      Width           =   2535
   End
   Begin VB.TextBox txtVersion 
      BackColor       =   &H00E0E0E0&
      Height          =   285
      Left            =   1560
      Locked          =   -1  'True
      TabIndex        =   32
      Top             =   120
      Width           =   3375
   End
   Begin VB.TextBox txtCache 
      Height          =   285
      Left            =   1560
      TabIndex        =   29
      ToolTipText     =   "directorio para archivos temporales"
      Top             =   3960
      Width           =   3255
   End
   Begin VB.TextBox txtProxy 
      Height          =   285
      Left            =   1560
      TabIndex        =   27
      ToolTipText     =   "usuario:clave@servidor:puerto"
      Top             =   3600
      Width           =   3255
   End
   Begin VB.TextBox txtXmlRequest 
      Height          =   1335
      Left            =   6120
      MultiLine       =   -1  'True
      TabIndex        =   25
      Top             =   3720
      Width           =   3255
   End
   Begin VB.TextBox txtCMS 
      Height          =   975
      Left            =   5760
      MultiLine       =   -1  'True
      TabIndex        =   23
      Top             =   2280
      Width           =   3615
   End
   Begin VB.TextBox txtTRA 
      Height          =   975
      Left            =   5760
      MultiLine       =   -1  'True
      TabIndex        =   21
      Top             =   840
      Width           =   3615
   End
   Begin VB.TextBox txtXmlResponse 
      Height          =   1335
      Left            =   6120
      MultiLine       =   -1  'True
      TabIndex        =   17
      Top             =   5160
      Width           =   3255
   End
   Begin VB.TextBox txtSign 
      Height          =   285
      Left            =   1560
      MultiLine       =   -1  'True
      TabIndex        =   15
      Top             =   5520
      Width           =   3255
   End
   Begin VB.TextBox txtToken 
      Height          =   285
      Left            =   1560
      MultiLine       =   -1  'True
      TabIndex        =   13
      Top             =   5160
      Width           =   3255
   End
   Begin VB.ComboBox cboURL 
      Height          =   315
      ItemData        =   "Form1.frx":002C
      Left            =   1560
      List            =   "Form1.frx":0036
      TabIndex        =   11
      Text            =   "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
      ToolTipText     =   "Dirección del WSDL (dehabilitado en homologación/testing)"
      Top             =   3240
      Width           =   3255
   End
   Begin VB.TextBox txtTTL 
      Height          =   285
      Left            =   1560
      TabIndex        =   8
      Text            =   "2400"
      ToolTipText     =   "Tiempo de vida (expiración)"
      Top             =   1200
      Width           =   1095
   End
   Begin VB.ComboBox cboService 
      Height          =   315
      ItemData        =   "Form1.frx":00A6
      Left            =   1560
      List            =   "Form1.frx":00BC
      TabIndex        =   7
      Text            =   "wsfe"
      ToolTipText     =   "webservice a utilizar"
      Top             =   840
      Width           =   2655
   End
   Begin VB.TextBox txtClave 
      Height          =   285
      Left            =   1560
      TabIndex        =   6
      Text            =   "reingart.key"
      ToolTipText     =   "Ruta completa a la clave privada PEM (.KEY)"
      Top             =   2400
      Width           =   3255
   End
   Begin VB.TextBox txtCert 
      Height          =   285
      Left            =   1560
      TabIndex        =   5
      Text            =   "reingart.crt"
      ToolTipText     =   "Ruta completa al Certificado X509 (.CRT)"
      Top             =   2040
      Width           =   3255
   End
   Begin VB.CommandButton btnAutenticar 
      Caption         =   "Autenticar"
      Default         =   -1  'True
      Height          =   375
      Left            =   2160
      TabIndex        =   0
      Top             =   4680
      Width           =   1695
   End
   Begin VB.Label Label15 
      Caption         =   "CA Cert:"
      Height          =   255
      Left            =   360
      TabIndex        =   38
      Top             =   4320
      Width           =   1095
   End
   Begin VB.Label Label14 
      Caption         =   "Traza:"
      Height          =   255
      Left            =   240
      TabIndex        =   36
      Top             =   5880
      Width           =   1695
   End
   Begin VB.Label Label13 
      Caption         =   "Directorio Instalación:"
      Height          =   255
      Left            =   5040
      TabIndex        =   33
      Top             =   120
      Width           =   1935
   End
   Begin VB.Label lblVersion 
      Caption         =   "Versión Interfaz:"
      Height          =   255
      Left            =   120
      TabIndex        =   31
      Top             =   120
      Width           =   1935
   End
   Begin VB.Label Label12 
      Caption         =   "Cache:"
      Height          =   255
      Left            =   360
      TabIndex        =   30
      Top             =   3960
      Width           =   1575
   End
   Begin VB.Label Label11 
      Caption         =   "Proxy:"
      Height          =   255
      Left            =   360
      TabIndex        =   28
      Top             =   3600
      Width           =   1575
   End
   Begin VB.Label Label10 
      Caption         =   "XmlRequest:"
      Height          =   255
      Left            =   5040
      TabIndex        =   26
      Top             =   3720
      Width           =   1695
   End
   Begin VB.Label Label9 
      Caption         =   "CMS:"
      Height          =   255
      Left            =   5040
      TabIndex        =   24
      Top             =   2280
      Width           =   1695
   End
   Begin VB.Label Label8 
      Caption         =   "TRA:"
      Height          =   255
      Left            =   5040
      TabIndex        =   22
      Top             =   840
      Width           =   1695
   End
   Begin VB.Label Label7 
      Caption         =   "LoginCMS:"
      Height          =   255
      Left            =   120
      TabIndex        =   20
      Top             =   2880
      Width           =   2895
   End
   Begin VB.Label Label6 
      Caption         =   "CMS (firma digital):"
      Height          =   255
      Left            =   120
      TabIndex        =   19
      Top             =   1680
      Width           =   2895
   End
   Begin VB.Label lblTRA 
      Caption         =   "Ticket de Requerimiento de Acceso:"
      Height          =   255
      Left            =   120
      TabIndex        =   18
      Top             =   480
      Width           =   2895
   End
   Begin VB.Label Label5 
      Caption         =   "XmlResponse:"
      Height          =   255
      Left            =   5040
      TabIndex        =   16
      Top             =   5160
      Width           =   1695
   End
   Begin VB.Label Label4 
      Caption         =   "Sign"
      Height          =   255
      Left            =   240
      TabIndex        =   14
      Top             =   5520
      Width           =   1695
   End
   Begin VB.Label lblToken 
      Caption         =   "Token"
      Height          =   255
      Left            =   240
      TabIndex        =   12
      Top             =   5160
      Width           =   1695
   End
   Begin VB.Label lblURL 
      Caption         =   "URL"
      Height          =   255
      Left            =   360
      TabIndex        =   10
      Top             =   3240
      Width           =   1695
   End
   Begin VB.Label lbls 
      Caption         =   "segundos"
      Height          =   255
      Left            =   2880
      TabIndex        =   9
      Top             =   1200
      Width           =   735
   End
   Begin VB.Label Label3 
      Caption         =   "TTL:"
      Height          =   255
      Left            =   360
      TabIndex        =   4
      Top             =   1200
      Width           =   1575
   End
   Begin VB.Label Label2 
      Caption         =   "Servicio:"
      Height          =   255
      Left            =   360
      TabIndex        =   3
      Top             =   840
      Width           =   1575
   End
   Begin VB.Label Label1 
      Caption         =   "Certificado:"
      Height          =   255
      Left            =   360
      TabIndex        =   2
      Top             =   2040
      Width           =   1575
   End
   Begin VB.Label lblClavePrivada 
      Caption         =   "Clave Privada"
      Height          =   255
      Left            =   360
      TabIndex        =   1
      Top             =   2400
      Width           =   1575
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Dim WSAA As Object

Private Sub btnAutenticar_Click()

    On Error GoTo ManejoError
            
    ' Generar un Ticket de Requerimiento de Acceso (TRA)
    tra = WSAA.CreateTRA(cboService.Text, CInt(txtTTL.Text))
    txtTRA.Text = tra
    DoEvents
    
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    
    ' Leo el contenido del certificado y clave privada
    Open Me.txtCert.Text For Input As #1
    cert = ""
    Do Until EOF(1)
        Line Input #1, li
        cert = cert + li + vbLf
    Loop
    Close #1
    Open Me.txtClave.Text For Input As #1
    clave = ""
    Do Until EOF(1)
        Line Input #1, li
        clave = clave + li + vbLf
    Loop
    Close #1
    
    ' Generar el mensaje firmado (CMS)
    Debug.Print Err.Description
    cms = WSAA.SignTRA(tra, cert, clave)
    txtCMS.Text = cms
    DoEvents
    
    Debug.Print "excepcion", WSAA.Excepcion
    If WSAA.Excepcion <> "" Then
        MsgBox WSAA.Excepcion, vbCritical, "Excepción"
        End
    End If
    
    ' Llamar al web service para autenticar:
    'ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") ' Hologación
    Debug.Print Err.Description
    cache = txtCache.Text ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    wsdl = cboURL.Text ' homologación
    proxy = txtProxy.Text ' usar "usuario:clave@servidor:puerto"
    wrapper = cboWrapper.Text ' libreria http (httplib2, urllib2, pycurl)
    cacert = txtCACert.Text ' certificado de la autoridad de certificante
    
    ok = WSAA.Conectar(cache, wsdl, proxy, wrapper, cacert)
    Me.txtVersion = WSAA.Version
    Debug.Print "excepcion", WSAA.Excepcion
    If WSAA.Excepcion <> "" Then
        MsgBox WSAA.Excepcion, vbCritical, "Excepción"
        Exit Sub
    ElseIf IsNull(ok) Then
        MsgBox "Ha ocurrido un error irrecuperable en WSAA!"
        Exit Sub
    ElseIf Not ok Then
        MsgBox "WSAA no pudo conectarse!"
        Exit Sub
    End If

    ta = WSAA.LoginCMS(cms) ' Producción

    txtXmlRequest.Text = WSAA.XmlRequest
    txtXmlResponse.Text = WSAA.XmlResponse
    
    txtTraceback.Text = WSAA.Traceback

    DoEvents
    
    Debug.Print "excepcion", WSAA.Excepcion
    If WSAA.Excepcion <> "" Then
        MsgBox WSAA.Excepcion, vbCritical, "Excepción"
    End If
    
    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign

    txtToken.Text = WSAA.Token
    txtSign.Text = WSAA.Sign
    
    If WSAA.Version >= "2.04a" Then
        If WSAA.Excepcion = "" Then
            ' Analizo el ticket de acceso (por defecto)
            MsgBox "Origen (Source): " & WSAA.ObtenerTagXml("source") & vbCrLf & _
               "Destino (Destination): " & WSAA.ObtenerTagXml("destination") & vbCrLf & _
               "ID Único: " & WSAA.ObtenerTagXml("uniqueId") & vbCrLf & _
               "Fecha de Generación: " & WSAA.ObtenerTagXml("generationTime") & vbCrLf & _
               "Fecha de Expiración: " & WSAA.ObtenerTagXml("expirationTime"), vbInformation, "Ticket de Acceso Gestionado OK!"
        Else
            ' No hay ticket de acceso, analizo la respuesta
            WSAA.AnalizarXml "XmlResponse"
            MsgBox "Servidor: " & WSAA.ObtenerTagXml("ns3:hostname")
        End If
    End If
    
    Exit Sub
ManejoError:
    ' If error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    'Debug.Print WSAA.XmlResponse
    Debug.Assert False
End Sub

Private Sub cboWrapper_Click()
    If cboWrapper.Text = "pycurl" Then
        txtCACert.Text = WSAA.InstallDir & "\geotrust.crt"
        txtCACert.Enabled = True
        txtCACert.BackColor = &H80000014
    Else
        txtCACert.Text = WSAA.InstallDir & "\geotrust.crt"
        txtCACert.Enabled = False
        txtCACert.BackColor = &H8000000F
    End If
End Sub

Private Sub Form_Load()
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    txtCert.Text = Path + "reingart.crt"
    txtClave.Text = Path + "reingart.key"
    
    On Error GoTo ManejoError
    Set WSAA = CreateObject("WSAA")

    ' deshabilito errores no manejados
    WSAA.LanzarExcepciones = False

    ' Crear objeto interface Web Service Autenticación y Autorización
    txtVersion.Text = WSAA.Version
    txtInstallDir.Text = WSAA.InstallDir
    
    ' Deshabilito URL para homologación
    If InStr(WSAA.Version, "Homo") > 0 Then
        cboURL.Locked = True
        cboURL.BackColor = &HE0E0E0
        txtProxy.Locked = True
        txtProxy.BackColor = &HE0E0E0
        txtCache.Locked = True
        txtCache.BackColor = &HE0E0E0
    End If
    DoEvents
    Exit Sub
ManejoError:
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    MsgBox "No está correctamente instalada la interfaz WSAA de PyAfipWs version 2.04 o superior." & vbCrLf & _
           "Esta aplicación puede no funcionar correctamente." & vbCrLf & _
           "Para más información: http://www.sistemasagiles.com.ar/", vbExclamation, "Advertencia:"
End Sub

