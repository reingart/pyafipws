Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Liquidación Primaria Electrónica de Granos
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
' 2013 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSLPG As Object
    Dim ok As Variant
    
    ttl = 2400 ' tiempo de vida en segundos
    cache = "" ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    proxy = "" ' usar "usuario:clave@servidor:puerto"

    Certificado = App.Path & "\..\..\reingart.crt"   ' certificado es el firmado por la afip
    ClavePrivada = App.Path & "\..\..\reingart.key"  ' clave privada usada para crear el cert.
        
    Token = ""
    Sign = ""
    
    Set WSAA = CreateObject("WSAA")
    Debug.Print WSAA.InstallDir
    tra = WSAA.CreateTRA("wslpg", ttl)
    Debug.Print tra
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Certificado, ClavePrivada)
    Debug.Print cms
    
    wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" ' homologación
    ok = WSAA.Conectar(cache, wsdl, proxy)
    ta = WSAA.LoginCMS(cms) 'obtener ticket de acceso
    
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Crear objeto interface Web Service de Liquidación Primaria de Granos
    Set WSLPG = CreateObject("WSLPG")
    Debug.Print WSLPG.Version
    Debug.Print WSLPG.InstallDir
    ' Setear tocken y sing de autorización (pasos previos)
    WSLPG.Token = WSAA.Token
    WSLPG.Sign = WSAA.Sign
    ' CUIT (debe estar registrado en la AFIP)
    WSLPG.cuit = "20267565393"
    
    ' Conectar al Servicio Web
    ok = WSLPG.Conectar("", "", "") ' homologación
    If Not ok Then
        Debug.Print WSLPG.Traceback
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    ok = WSLPG.Dummy()
    If Not ok Then
        ' muestro el mensaje de error
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    Else
        Debug.Print "appserver status", WSLPG.AppServerStatus
        Debug.Print "dbserver status", WSLPG.DbServerStatus
        Debug.Print "authserver status", WSLPG.AuthServerStatus
    End If
    
    ' Consulto las campanias (usando dos puntos como separador)
    For Each parametro In WSLPG.ConsultarCampanias(":")
        Debug.Print parametro ' devuelve un string ": codigo : descripcion :"
    Next
    
    ' Busco una localidad (para verificar que la tabla temporal esté en cache ok
    ' nota: solo reconstruye la bd local (llama a AFIP) si el tercer parámetro es True
    Debug.Assert WSLPG.BuscarLocalidades(11, 7295, False) = "LA AGUADA DE LAS ANIMAS"
    
    ' obtengo el último número de orden registrado
    ok = WSLPG.ConsultarUltNroOrden()
    If ok Then
        nro_orden = WSLPG.NroOrden + 1   ' uso el siguiente
        ' NOTA: es recomendable llevar internamente el control del numero de orden
        '       (ya que sirve para recuperar datos de una liquidación ante AFIP)
        '       ver documentación oficial de AFIP, sección "Tratamiento Nro Orden"
    Else
        ' revisar el error, posiblemente no se pueda continuar
        Debug.Print WSLPG.Traceback
        Debug.Print WSLPG.ErrMsg
        MsgBox "No se pudo obtener el último número de orden!"
        nro_orden = 1                    ' uso el primero
    End If
    
    pto_emision = 1  ' agregado v1.1
    cuit_comprador = "20400000000" ' Exportador
    nro_act_comprador = 40: nro_ing_bruto_comprador = "23000000000"
    cod_tipo_operacion = 1
    es_liquidacion_propia = "N": es_canje = "N"
    cod_puerto = 14: des_puerto_localidad = "DETALLE PUERTO"
    cod_grano = 31
    cuit_vendedor = "23000000019": nro_ing_bruto_vendedor = "23000000019"
    actua_corredor = "S": liquida_corredor = "S": cuit_corredor = "20267565393"
    comision_corredor = 1: nro_ing_bruto_corredor = "20267565393"
    fecha_precio_operacion = "2013-02-07"
    precio_ref_tn = 2000
    cod_grado_ref = "G1"
    cod_grado_ent = "G1"
    factor_ent = 98
    precio_flete_tn = 10
    cont_proteico = 20
    alic_iva_operacion = 10.5
    campania_ppal = 1213
    cod_localidad_procedencia = 3
    cod_provincia_procedencia = 1  ' agregado v1.1
    datos_adicionales = "DATOS ADICIONALES"
       
    ' establezco un parámetro adicional (antes de llamar a CrearLiquidacion)
    ' nuevos parámetros WSLPGv1.1:
    '' ok = WSLPG.SetParametro("peso_neto_sin_certificado", 1000)
    ' nuevos parámetros WSLPGv1.3:
    '' ok = WSLPG.SetParametro("cod_prov_procedencia_sin_certificado", 12)
    '' ok = WSLPG.SetParametro("cod_localidad_procedencia_sin_certificado", 5544)
       
    ok = WSLPG.CrearLiquidacion(nro_orden, cuit_comprador, _
                               nro_act_comprador, nro_ing_bruto_comprador, _
                               cod_tipo_operacion, _
                               es_liquidacion_propia, es_canje, _
                               cod_puerto, des_puerto_localidad, cod_grano, _
                               cuit_vendedor, nro_ing_bruto_vendedor, _
                               actua_corredor, liquida_corredor, cuit_corredor, _
                               comision_corredor, nro_ing_bruto_corredor, _
                               fecha_precio_operacion, _
                               precio_ref_tn, cod_grado_ref, cod_grado_ent, _
                               factor_ent, precio_flete_tn, cont_proteico, _
                               alic_iva_operacion, campania_ppal, _
                               cod_localidad_procedencia, _
                               datos_adicionales, _
                               pto_emision, cod_provincia_procedencia)
    
    ' Agergo un certificado de Depósito a la liquidación (opcional):
    
    tipo_certificado_dposito = 5
    nro_certificado_deposito = "555501200729"
    peso_neto = 1000
    cod_localidad_procedencia = 3
    cod_prov_procedencia = 1
    campania = 1213
    fecha_cierre = "2013-01-13"
                
    ok = WSLPG.AgregarCertificado(tipo_certificado_dposito, _
                           nro_certificado_deposito, _
                           peso_neto, _
                           cod_localidad_procedencia, _
                           cod_prov_procedencia, _
                           campania, _
                           fecha_cierre)
    
    ' Agrego deducciones (opcional):
    
    codigo_concepto = "OD"
    detalle_aclaratorio = "FLETE"
    dias_almacenaje = "0"
    precio_pkg_diario = "0.00"
    comision_gastos_adm = "0.00"
    base_calculo = "1000.00"
    alicuota = "21.00"

    ok = WSLPG.AgregarDeduccion(codigo_concepto, detalle_aclaratorio, _
                               dias_almacenaje, precio_pkg_diario, _
                               comision_gastos_adm, base_calculo, _
                               alicuota)
    
    ' Agrego retenciones (opcional):
    
    codigo_concepto = "RI"
    detalle_aclaratorio = "DETALLE DE IVA"
    base_calculo = 1000
    alicuota = 10.5

    ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
    
    codigo_concepto = "RG"
    detalle_aclaratorio = "DETALLE DE GANANCIAS"
    base_calculo = 1000
    alicuota = 0
    
    ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
               
    ' Cargo respuesta de prueba según documentación de AFIP (Ejemplo 1)
    ' (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
    ''WSLPG.LoadTestXML ("wslpg_aut_test.xml")
               
    ' llamo al webservice con los datos cargados:
    
    ok = WSLPG.AutorizarLiquidacion()
            
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        
        Debug.Print "COE", WSLPG.COE
        Debug.Print "COEAjustado", WSLPG.COEAjustado
        Debug.Print "TootalDeduccion", WSLPG.TotalDeduccion
        Debug.Print "TotalRetencion", WSLPG.TotalRetencion
        Debug.Print "TotalRetencionAfip", WSLPG.TotalRetencionAfip
        Debug.Print "TotalOtrasRetenciones", WSLPG.TotalOtrasRetenciones
        Debug.Print "TotalNetoAPagar", WSLPG.TotalNetoAPagar
        Debug.Print "TotalIvaRg2300_07", WSLPG.TotalIvaRg2300_07
        Debug.Print "TotalPagoSegunCondicion", WSLPG.TotalPagoSegunCondicion
        
        ' obtengo los datos adcionales desde losparametros de salida:
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        Debug.Print "subtotal", WSLPG.GetParametro("subtotal")
        Debug.Print "primer importe_retencion", WSLPG.GetParametro("retenciones", 0, "importe_retencion")
        Debug.Print "segundo importe_retencion", WSLPG.GetParametro("retenciones", 1, "importe_retencion")
        Debug.Print "primer importe_deduccion", WSLPG.GetParametro("deducciones", 0, "importe_deduccion")
        
        
        MsgBox "COE: " & WSLPG.COE & vbCrLf, vbInformation, "Autorizar Liquidación:"
        If WSLPG.ErrMsg <> "" Then
            Debug.Print "Errores", WSLPG.ErrMsg
            ' recorro y muestro los errores
            For Each er In WSLPG.Errores
                MsgBox er, vbExclamation, "Error"
            Next
        End If
        
        ' GENERACIÓN DEL FORMULARIO C 1116 B EN PDF:
        ok = WSLPG.CrearPlantillaPDF("A4", "portrait")  ' IMPORTANTE: realizar como primer paso!
        ok = WSLPG.CargarFormatoPDF(WSLPG.InstallDir & "\liquidacion_form_c1116b_wslpg.csv")
        
        ' agrego datos fijos y campos adicionales
        ok = WSLPG.AgregarDatoPDF("formulario", "Form. C 1116 B (prueba)")
        ok = WSLPG.AgregarDatoPDF("fondo", WSLPG.InstallDir & "\liquidacion_form_c1116b_wslpg.png")
        ok = WSLPG.AgregarDatoPDF("nombre_comprador", "NOMBRE 1")
        ok = WSLPG.AgregarDatoPDF("domicilio1_comprador", "DOMICILIO 1")
        ok = WSLPG.AgregarDatoPDF("domicilio2_comprador", "DOMICILIO 1")
        ok = WSLPG.AgregarDatoPDF("localidad_comprador", "LOCALIDAD 1")
        ok = WSLPG.AgregarDatoPDF("iva_comprador", "R.I.")
        ok = WSLPG.AgregarDatoPDF("nombre_vendedor", "NOMBRE 2")
        ok = WSLPG.AgregarDatoPDF("domicilio1_vendedor", "DOMICILIO 2")
        ok = WSLPG.AgregarDatoPDF("domicilio2_vendedor", "DOMICILIO 2")
        ok = WSLPG.AgregarDatoPDF("localidad_vendedor", "LOCALIDAD 2")
        ok = WSLPG.AgregarDatoPDF("iva_vendedor", "R.I.")
        ok = WSLPG.AgregarDatoPDF("nombre_corredor", "NOMBRE 3")
        ok = WSLPG.AgregarDatoPDF("domicilio_corredor", "DOMICILIO 3")
        ok = WSLPG.AgregarDatoPDF("art_27", "Art. 27 inc. ...................")
        ok = WSLPG.AgregarDatoPDF("forma_pago", "Forma de Pago: 1234 pesos ..")
        ok = WSLPG.AgregarDatoPDF("constancia", "Por la presente dejo constancia...")
        ok = WSLPG.AgregarDatoPDF("lugar_y_fecha", "")
    
        ' genero el PDF y lo muestro
        ok = WSLPG.ProcesarPlantillaPDF(2)
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.Excepcion
        End If
        ok = WSLPG.GenerarPDF(App.Path & "\form1116b.pdf")
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.Excepcion
        End If
        ok = WSLPG.MostrarPDF(App.Path & "\form1116b.pdf", False)

    Else
        ' muestro el mensaje de error
        Debug.Print WSLPG.Traceback
        Debug.Print WSLPG.XmlRequest
        Debug.Print WSLPG.XmlResponse
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
    
    ' consulto una liquidacion
    COE = WSLPG.COE
    ok = WSLPG.ConsultarLiquidacion(pto_emision, nro_orden, COE)
    If ok Then
        MsgBox "COE:" & WSLPG.COE & vbCrLf & "Estado: " & WSLPG.Estado & vbCrLf, vbInformation, "Consultar Liquidación:"
        For Each er In WSLPG.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error"
        Next
        
        ' muestro los resultados devueltos por el webservice:
        Debug.Print "COE", WSLPG.COE
        Debug.Print "COEAjustado", WSLPG.COEAjustado
        Debug.Print "TootalDeduccion", WSLPG.TotalDeduccion
        Debug.Print "TotalRetencion", WSLPG.TotalRetencion
        Debug.Print "TotalRetencionAfip", WSLPG.TotalRetencionAfip
        Debug.Print "TotalOtrasRetenciones", WSLPG.TotalOtrasRetenciones
        Debug.Print "TotalNetoAPagar", WSLPG.TotalNetoAPagar
        Debug.Print "TotalIvaRg2300_07", WSLPG.TotalIvaRg2300_07
        Debug.Print "TotalPagoSegunCondicion", WSLPG.TotalPagoSegunCondicion
        
        ' obtengo los datos adcionales desde losparametros de salida:
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        Debug.Print "precio_operacion", WSLPG.GetParametro("precio_operacion")
        Debug.Print "total_peso_neto", WSLPG.GetParametro("total_peso_neto")
        Debug.Print "primer importe_retencion", WSLPG.GetParametro("retenciones", 0, "importe_retencion")
        Debug.Print "segundo importe_retencion", WSLPG.GetParametro("retenciones", 1, "importe_retencion")
        Debug.Print "primer importe_deduccion", WSLPG.GetParametro("deducciones", 0, "importe_deduccion")
        Debug.Print "primer nro certificado", WSLPG.GetParametro("certificados", 0, "nro_certificado_deposito")
        
    End If
    
    ' asocio la liquidación previamente emitida a un contrato (asociarLiquidacionAContrato):
    
    nro_contrato = 27
    
    ok = WSLPG.AsociarLiquidacionAContrato(COE, nro_contrato, cuit_comprador, cuit_vendedor, cuit_corredor, cod_grano)
    For Each er In WSLPG.Errores
        Debug.Print er
        MsgBox er, vbExclamation, "Error"
    Next
    Debug.Print WSLPG.COE   ' devuelve el COE ajustado
    Debug.Print WSLPG.Estado ' debería ser "AC"
    
    ' consulto las liquidaciones relacionadas a un contrato (liquidacionPorContratoConsultar):
    
    ok = WSLPG.ConsultarLiquidacionesPorContrato(nro_contrato, cuit_comprador, cuit_vendedor, cuit_corredor, cod_grano)
    Do
        If WSLPG.COE = "" Then Exit Do
        ' si existe COE relacionado, lo muestro:
        Debug.Print WSLPG.COE
        ' leo la próxima liquidación:
        ok = WSLPG.LeerDatosLiquidacion()
    Loop Until ok = ""
    
    ' anulo una liquidacion
    
    'COE = "330100000357"     ' nro ejemplo AFIP
    COE = WSLPG.AnularLiquidacion(COE)
    If COE <> "" Then
        MsgBox "Resultado: " & WSLPG.Resultado & vbCrLf, vbInformation, "AnularLiquidación:"
        For Each er In WSLPG.Errores
            MsgBox er, vbExclamation, "Error"
        Next
    End If
    
End Sub
