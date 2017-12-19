Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Certificación Electrónica de Granos
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
' 2014 (C) Mariano Reingart <reingart@gmail.com>


Sub Main()
    Dim WSAA As Object, WSLPG As Object
    Dim ok As Variant
    Dim ttl, cache, proxy
    
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
        
    ' Establecer tipo de certificación a autorizar
    tipo_certificado = "P"      '  cambiar P: primaria, R: retiro, T: transf, E: preexistente
        
    ' genero una certificación de ejemplo a autorizar (datos generales de cabecera):
    pto_emision = 99
    nro_orden = 1
    nro_planta = "1"
    nro_ing_bruto_depositario = "20267565393"
    titular_grano = "T"
    cuit_depositante = "20111111112"
    nro_ing_bruto_depositante = "123"
    cuit_corredor = "20222222223"
    cod_grano = 2
    campania = 1314
    datos_adicionales = "Prueba"
    
    ' Establezco los datos de cabecera
    ok = WSLPG.CrearCertificacionCabecera( _
            pto_emision, nro_orden, _
            tipo_certificado, nro_planta, _
            nro_ing_bruto_depositario, _
            titular_grano, _
            cuit_depositante, _
            nro_ing_bruto_depositante, _
            cuit_corredor, _
            cod_grano, campania, _
            datos_adicionales)

    Select Case tipo_certificado
        Case "P"
            ' datos del certificado depósito F1116A:
            nro_act_depositario = 29
            descripcion_tipo_grano = "SOJA"
            monto_almacenaje = 1: monto_acarreo = 2
            monto_gastos_generales = 3: monto_zarandeo = 4
            porcentaje_secado_de = 6: porcentaje_secado_a = 5
            monto_secado = 7: monto_por_cada_punto_exceso = 8
            monto_otros = 9:
            porcentaje_merma_volatil = 15: peso_neto_merma_volatil = 16
            porcentaje_merma_secado = 17: peso_neto_merma_secado = 18
            porcentaje_merma_zarandeo = 19: peso_neto_merma_zarandeo = 20
            peso_neto_certificado = 21: servicios_secado = 22
            servicios_zarandeo = 23: servicios_otros = 24
            servicios_forma_de_pago = 25
            
            ok = WSLPG.AgregarCertificacionPrimaria( _
                    nro_act_depositario, _
                    descripcion_tipo_grano, _
                    monto_almacenaje, monto_acarreo, _
                    monto_gastos_generales, monto_zarandeo, _
                    porcentaje_secado_de, porcentaje_secado_a, _
                    monto_secado, monto_por_cada_punto_exceso, _
                    monto_otros, _
                    porcentaje_merma_volatil, peso_neto_merma_volatil, _
                    porcentaje_merma_secado, peso_neto_merma_secado, _
                    porcentaje_merma_zarandeo, peso_neto_merma_zarandeo, _
                    peso_neto_certificado, servicios_secado, _
                    servicios_zarandeo, servicios_otros, _
                    servicios_forma_de_pago _
                    )
        
            ' Calidad por separado desde WSLPGv1.10
            analisis_muestra = 10: nro_boletin = 11: cod_grado = "F1"
            valor_grado = 1.02: valor_contenido_proteico = 1: valor_factor = 1
            ok = WSLPG.AgregarCalidad( _
                analisis_muestra, nro_boletin, cod_grado, _
                valor_grado, valor_contenido_proteico, valor_factor _
                )
                
            descripcion_rubro = "bonif": tipo_rubro = "B":
            porcentaje = 1: valor = 1
            ok = WSLPG.AgregarDetalleMuestraAnalisis( _
                descripcion_rubro, tipo_rubro, porcentaje, valor)
    
            nro_ctg = "123456": nro_carta_porte = 1000:
            porcentaje_secado_humedad = 1: importe_secado = 2:
            peso_neto_merma_secado = 3: tarifa_secado = 4:
            importe_zarandeo = 5: peso_neto_merma_zarandeo = 6:
            tarifa_zarandeo = 7: peso_neto_confirmado_definitivo = 8
            ok = WSLPG.AgregarCTG( _
                nro_ctg, nro_carta_porte, _
                porcentaje_secado_humedad, importe_secado, _
                peso_neto_merma_secado, tarifa_secado, _
                importe_zarandeo, peso_neto_merma_zarandeo, _
                tarifa_zarandeo, peso_neto_confirmado_definitivo)
    
        Case "R", "T":
            ' establezco datos del certificado retiro/transferencia F1116R/T:
            nro_act_depositario = 29
            cuit_receptor = "20400000000": fecha = "2014-11-26"
            nro_carta_porte_a_utilizar = "12345"
            cee_carta_porte_a_utilizar = "123456789012"
            ok = WSLPG.AgregarCertificacionRetiroTransferencia( _
                    nro_act_depositario, cuit_receptor, fecha, _
                    nro_carta_porte_a_utilizar, _
                    cee_carta_porte_a_utilizar)
            ' datos del certificado (los Null no se utilizan por el momento)
            peso_neto = 10000: coe_certificado_deposito = "123456789012"
            tipo_certificado_deposito = Null: nro_certificado_deposito = Null
            cod_localidad_procedencia = Null:  cod_prov_procedencia = Null
            campania = Null: fecha_cierre = Null
            ok = WSLPG.AgregarCertificado( _
                           tipo_certificado_deposito, _
                           nro_certificado_deposito, _
                           peso_neto, _
                           cod_localidad_procedencia, _
                           cod_prov_procedencia, _
                           campania, fecha_cierre, _
                           peso_neto, coe_certificado_deposito _
                            )
            
        Case "E":
            ' establezco datos del certificado preexistente:
            tipo_certificado_deposito_preexistente = 1: ' "R" o "T"
            nro_certificado_deposito_preexistente = "12345"
            cac_certificado_deposito_preexistente = "123456789012"
            fecha_emision_certificado_deposito_preexistente = "2014-11-26"
            peso_neto = 1000
            nro_planta = 1234
            ok = WSLPG.AgregarCertificacionPreexistente( _
                    tipo_certificado_deposito_preexistente, _
                    nro_certificado_deposito_preexistente, _
                    cac_certificado_deposito_preexistente, _
                    fecha_emision_certificado_deposito_preexistente, _
                    peso_neto, nro_planta)
    
    End Select

    ' cargar respuesta predeterminada de prueba (solo usar en evaluacion/testing)
    If Flase Then
        ok = WSLPG.LoadTestXML(WSLPG.InstallDir + "\tests\wslpg_cert_autorizar_resp.xml")
    End If

    ' Llamo al metodo remoto cgAutorizar:
    
    ok = WSLPG.AutorizarCertificacion()
    
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        
        Debug.Print "COE", WSLPG.COE
        
        MsgBox "COE: " & WSLPG.COE & vbCrLf, vbInformation, "Autorizar Liquidación:"
        
        ' Planta (opcional):
        Debug.Print "Nro. Planta", WSLPG.GetParametro("nro_planta")
        Debug.Print "Cuit Titular Planta", WSLPG.GetParametro("cuit_titular_planta")
        Debug.Print "Razon Titular Planta", WSLPG.GetParametro("razon_titular_planta")
    
        ' Resumen de pesos (si fue autorizada):
        Debug.Print "peso_bruto_certificado", WSLPG.GetParametro("peso_bruto_certificado")
        Debug.Print "peso_merma_secado", WSLPG.GetParametro("peso_merma_secado")
        Debug.Print "peso_merma_volatil", WSLPG.GetParametro("peso_merma_volatil")
        Debug.Print "peso_merma_zarandeo", WSLPG.GetParametro("peso_merma_zarandeo")
        Debug.Print "peso_neto_certificado", WSLPG.GetParametro("peso_neto_certificado")
    
        ' Resumen de servicios (si fue autorizada):
        Debug.Print "importe_iva", WSLPG.GetParametro("importe_iva")
        Debug.Print "servicio_gastos_generales", WSLPG.GetParametro("servicio_gastos_generales")
        Debug.Print "servicio_otros", WSLPG.GetParametro("servicio_otros")
        Debug.Print "servicio_total", WSLPG.GetParametro("servicio_total")
        Debug.Print "servicio_zarandeo", WSLPG.GetParametro("servicio_zarandeo")
        
        If WSLPG.ErrMsg <> "" Then
            Debug.Print "Errores", WSLPG.ErrMsg
            ' recorro y muestro los errores
            For Each er In WSLPG.Errores
                MsgBox er, vbExclamation, "Error"
            Next
        End If
        Debug.Print WSLPG.XmlRequest
        Debug.Print WSLPG.XmlResponse

    Else
        ' muestro el mensaje de error
        Debug.Print WSLPG.Traceback
        Debug.Print WSLPG.XmlRequest
        Debug.Print WSLPG.XmlResponse
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
    
End Sub
