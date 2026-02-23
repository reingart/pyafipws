Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para
' Iniciar una declaracion jurada, dar de alta comprobantes de retetencion,
' consultar dj y cmp
' 2025 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim a122r As Object, ok As Variant
    Dim idp As Object
    ' Crear la interfaz COM
    Set a122r = CreateObject("WSA122r")
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set idp = CreateObject("WSIDP")
    
    Debug.Print a122r.Version
    Debug.Print a122r.InstallDir
    
    Debug.Print idp.Version
    Debug.Print idp.InstallDir
    
    ' Solicitar datos a ARBA
    cuit_agente = ""
    cit = ""
    client_id = ""
    secret = ""
    
    ' Consigo token para autenticarme
    token = idp.ObtenerToken(cuit_agente, cit, client_id, secret) ' Url por defecto homologacion
    
    Debug.Print ">> Token: ", token

    ' Seteo el token
    a122r.SetToken (token)
    
    ' Conecto al servidor de ARBA
    ok = a122r.Conectar() ' Url por defecto homologacion

    ' Inicio una DJ
    actividad_id = 6
    anio = 2026
    mes = 2
    quincena = 1
    ' ok = a122r.IniciarDj(cuit_agente, actividad_id, anio, mes, quincena)
    ' Debug.Print ">> ID de DJ iniciada: ", a122r.IdDj

    ' si no quiero iniciar una nueva dj consulto el Id por período
    consulta_dj = ""
    consulta_dj = a122r.ConsultarDj(cuit_agente, 0, actividad_id, anio, mes, quincena)
    
    Debug.Print ">> ID de DJ consultada: ", a122r.IdDj
    Debug.Print ">> Datos de la DJ consultda: ", consulta_dj

    ' Creo un Comprobante Interno
    cuit_contribuyente = "" ' Ingresar un cuit
    sucursal = "00002"
    alicuota = 1.75
    base_imponible = 90000
    importe_retencion = 1575
    razon_social_contribuyente = "" ' Relacionado al cuit
    fecha_operacion = "2026-02-03T00:00:00" ' Si no entra dentro del período de la DJ va a fallar
    n_transaccion_agente = 5
    
    ok = a122r.CrearComprobanteInterno(cuit_contribuyente, cuit_agente, sucursal, _
    alicuota, base_imponible, importe_retencion, razon_social_contribuyente, _
    fecha_operacion, n_transaccion_agente)
    
    ' Agrego la direccion (datos relacionados al cuit)
    calle = ""
    numero = ""
    piso = ""
    depto = ""
    codigo_postal = ""
    localidad = ""
    provincia = ""
    
    ok = a122r.AgregarDireccion(calle, numero, piso, depto, codigo_postal, _
    localidad, provincia)
    
    ' Doy de alta el comprobante
    ' ok = a122r.AltaComprobante(a122r.IdDj, cuit_agente)
    ' Debug.Print ">> Id Comprobante: ", a122r.IdComprobante
    
    ' Si no quiero dar de alta un nuevo comprobante consulto el Id por período
    ' y cuit del contribuyente
    estado = "TODOS"
    consulta_cmp = ""
    consulta_cmp = a122r.ConsultarComprobante(cuit_agente, 0, anio, mes, _
    quincena, cuit_contribuyente, estado)
    
    Debug.Print ">> Id Comprobante Consultado: ", a122r.IdComprobante

    ' Imprimo el comprobante en PDF
    ruta = a122r.InstallDir + "\cache\comp.pdf"
    id_comp = a122r.IdComprobante
    ok = a122r.ConsultarComprobantePdf(id_comp, ruta)
    
    If ok Then
            Debug.Print ">> PDF Generado En: ", ruta
    End If

    Debug.Print "------------ WSIDP DEBUG ------------"
    Debug.Print ">> Request IDP: ", idp.Request
    Debug.Print ">> Response IDP: "; idp.Response
    Debug.Print ">> Treaceback IDP: "; idp.Traceback
    Debug.Print ">> Excepcion IDP: "; idp.Excepcion
    Debug.Print "------------ WSA122R DEBUG ------------"
    Debug.Print ">> Request WSA122r: ", a122r.Request
    ' Debug.Print ">> Response WSA122r: "; a122r.Response
    Debug.Print ">> Traceback WSA122r: ", a122r.Traceback
    Debug.Print ">> Excepcion WSA122r: ", a122r.Excepcion
End Sub
