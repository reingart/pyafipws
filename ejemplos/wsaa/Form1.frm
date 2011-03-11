VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "Interfaz PyAfipWs para WSAA"
   ClientHeight    =   6525
   ClientLeft      =   60
   ClientTop       =   345
   ClientWidth     =   9645
   LinkTopic       =   "Form1"
   ScaleHeight     =   6525
   ScaleWidth      =   9645
   StartUpPosition =   3  'Windows Default
   Begin VB.TextBox txtTraceback 
      Height          =   615
      Left            =   2040
      MultiLine       =   -1  'True
      TabIndex        =   35
      Top             =   5880
      Width           =   2655
   End
   Begin VB.TextBox txtInstallDir 
      BackColor       =   &H80000000&
      Height          =   285
      Left            =   7080
      Locked          =   -1  'True
      TabIndex        =   34
      Top             =   120
      Width           =   2175
   End
   Begin VB.TextBox txtVersion 
      BackColor       =   &H80000000&
      Height          =   285
      Left            =   2160
      Locked          =   -1  'True
      TabIndex        =   32
      Top             =   120
      Width           =   2175
   End
   Begin VB.TextBox txtCache 
      Height          =   285
      Left            =   2160
      TabIndex        =   29
      ToolTipText     =   "directorio para archivos temporales"
      Top             =   4320
      Width           =   2655
   End
   Begin VB.TextBox txtProxy 
      Height          =   285
      Left            =   2160
      TabIndex        =   27
      ToolTipText     =   "usuario:clave@servidor:puerto"
      Top             =   3960
      Width           =   2655
   End
   Begin VB.TextBox txtXmlRequest 
      Height          =   1335
      Left            =   6720
      MultiLine       =   -1  'True
      TabIndex        =   25
      Top             =   3720
      Width           =   2655
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
      Left            =   6720
      MultiLine       =   -1  'True
      TabIndex        =   17
      Top             =   5160
      Width           =   2655
   End
   Begin VB.TextBox txtSign 
      Height          =   285
      Left            =   2040
      MultiLine       =   -1  'True
      TabIndex        =   15
      Top             =   5520
      Width           =   2655
   End
   Begin VB.TextBox txtToken 
      Height          =   285
      Left            =   2040
      MultiLine       =   -1  'True
      TabIndex        =   13
      Top             =   5160
      Width           =   2655
   End
   Begin VB.ComboBox cboURL 
      Height          =   315
      ItemData        =   "Form1.frx":0000
      Left            =   2160
      List            =   "Form1.frx":000A
      TabIndex        =   11
      Text            =   "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
      Top             =   3600
      Width           =   2655
   End
   Begin VB.TextBox txtTTL 
      Height          =   285
      Left            =   2160
      TabIndex        =   8
      Text            =   "2400"
      Top             =   1200
      Width           =   1095
   End
   Begin VB.ComboBox cboService 
      Height          =   315
      ItemData        =   "Form1.frx":007A
      Left            =   2160
      List            =   "Form1.frx":0090
      TabIndex        =   7
      Text            =   "wsfe"
      Top             =   840
      Width           =   2655
   End
   Begin VB.TextBox txtClave 
      Height          =   285
      Left            =   2160
      TabIndex        =   6
      Text            =   "reingart.key"
      Top             =   2760
      Width           =   2655
   End
   Begin VB.TextBox txtCert 
      Height          =   285
      Left            =   2160
      TabIndex        =   5
      Text            =   "reingart.crt"
      Top             =   2400
      Width           =   2655
   End
   Begin VB.CommandButton btnAutenticar 
      Caption         =   "Autenticar"
      Height          =   375
      Left            =   2520
      TabIndex        =   0
      Top             =   4680
      Width           =   1695
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
      Top             =   4320
      Width           =   1575
   End
   Begin VB.Label Label11 
      Caption         =   "Proxy:"
      Height          =   255
      Left            =   360
      TabIndex        =   28
      Top             =   3960
      Width           =   1575
   End
   Begin VB.Label Label10 
      Caption         =   "XmlRequest:"
      Height          =   255
      Left            =   5520
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
      Top             =   3240
      Width           =   2895
   End
   Begin VB.Label Label6 
      Caption         =   "CMS (firma digital):"
      Height          =   255
      Left            =   120
      TabIndex        =   19
      Top             =   2040
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
      Left            =   5520
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
      Top             =   3600
      Width           =   1695
   End
   Begin VB.Label lbls 
      Caption         =   "segundos"
      Height          =   255
      Left            =   3480
      TabIndex        =   9
      Top             =   1200
      Width           =   735
   End
   Begin VB.Label Label3 
      Caption         =   "Tiempo de vida:"
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
      Top             =   2400
      Width           =   1575
   End
   Begin VB.Label lblClavePrivada 
      Caption         =   "Clave Privada"
      Height          =   255
      Left            =   360
      TabIndex        =   1
      Top             =   2760
      Width           =   1575
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub btnAutenticar_Click()

    On Error GoTo ManejoError
    
    Dim WSAA As Object
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Debug.Print Err.Description
    Set WSAA = CreateObject("WSAA")
    txtVersion.Text = WSAA.Version
    txtInstallDir.Text = WSAA.InstallDir
    DoEvents
    
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
    
    ' Llamar al web service para autenticar:
    'ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") ' Hologación
    Debug.Print Err.Description
    cache = txtCache.Text ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    wsdl = cboURL.Text ' homologación
    proxy = txtProxy.Text ' usar "usuario:clave@servidor:puerto"
    ok = WSAA.Conectar(cache, wsdl, proxy)
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

Private Sub Form_Load()
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    txtCert.Text = Path + "reingart.crt"
    txtClave.Text = Path + "reingart.key"
End Sub
