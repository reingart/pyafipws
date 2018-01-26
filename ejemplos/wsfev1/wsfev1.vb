'<summary>
'EJEMPLO - Interfaz Libre PyAfipWs WSFEv1
'</summary>
'<description>
' Interfaz PyAfipWs Web Service Factura Electrónica Mercado Interno
' Según RG2904 Artículo 4 Opción B (sin detalle, RG2485 Version 1)
' 2011, 2016 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3
' Funcionamiento:
'   Solicita Ticket de Acceso (WSAA.LoginCMS)
'   Muestra estado de servidores (WSFEv1.Dummy)
'   Obtiene último número de factura autorizado (WSFEv1.CompUltimoAutorizado)
'   Crea una Factura, agrega IVA, Tributo y Comprobantes Asociados (WSFEv1.CrearFactura et.al.)
'   Solicita CAE (WSFEv1.CAESolicitar)
'   Incluye reutilización de ticket de acceso (WSAA), persistiendo Token/Sign
' Compilación y ejecución (ej. con VB.net 2012):
'   c:\Windows\Microsoft.NET\Framework\v4.0.30319\vbc wsfev1.vb
'   wsfev1.exe
'</description>
'<version>0.0.2</version>.
'<platform>.NET Framework 1.1</platform>
'<disclaimer>
' This program is free software; you can redistribute it and/or modify
' it under the terms of the GNU General Public License as published by the
' Free Software Foundation; either version 3, or (at your option) any later
' version.
'
' This program is distributed in the hope that it will be useful, but
' WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
' or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
' for more details.
'</disclaimer>

Imports Microsoft.VisualBasic
Imports System

Public Class MainClass

    ' Declarar el componente WSAA y WSFEv1 como compartidos y privados para
    ' poder reutilizarlos en los distintos métodos (creados una sola vez)
    ' de esta forma, las instancias persistiran entre las distintas llamadas

    Private Shared WSAA As Object, WSFEv1 as Object

    Shared Sub Main(ByVal args As String())

        Console.WriteLine("DEMO Interfaz PyAfipWs WSFEv1 para vb.net")

        ' Crear objeto interface Web Service Autenticación y Autorización (TA)
        If WSAA is Nothing Then
            WSAA = CreateObject("WSAA")
        End If

        ' Autorizar dos facturas electrónicas para probar la reutilización TA
        ObtenerCAE
        ObtenerCAE
        
    End Sub

    Shared Sub Autenticar()
        Dim Path As String
        Dim tra as string, cms as string, ta as string
        Dim wsdl as string, proxy as string, cache as string = ""
        Dim certificado as string, claveprivada as string
                  
        Console.WriteLine(WSAA.Version)

        Try
            Console.WriteLine("Generar un Ticket de Requerimiento de Acceso (TRA) para WSFEv1")
            tra = WSAA.CreateTRA("wsfe")
            Console.WriteLine(tra)

            ' Especificar la ubicacion de los archivos certificado y clave privada
            Path = Environment.CurrentDirectory() + "\"
            ' Certificado: certificado es el firmado por la AFIP
            ' ClavePrivada: la clave privada usada para crear el certificado
            Certificado = "..\..\reingart.crt" ' certificado de prueba
            ClavePrivada = "..\..\reingart.key" ' clave privada de prueba

            Console.WriteLine("Generar el mensaje firmado (CMS)")
            cms = WSAA.SignTRA(tra, Path + Certificado, Path + ClavePrivada)
            Console.WriteLine(cms)

            Console.WriteLine("Llamar al web service para autenticar:")
            proxy = "" '"usuario:clave@localhost:8000"
            wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
            WSAA.Conectar(cache, wsdl, proxy) ' Homologación
            ta = WSAA.LoginCMS(cms) 

            ' Imprimir el ticket de acceso, ToKen y Sign de autorización
            MsgBox(WSAA.Token, vbInformation, "WSAA Token")
            MsgBox(WSAA.Sign, vbInformation, "WSAA Sign")

            ' Una vez obtenido, se puede usar el mismo token y sign por 12 horas
            ' (este período se puede cambiar)

        Catch 
            ' Muestro los errores
            If WSAA.Excepcion <> "" Then
                MsgBox(WSAA.Traceback, vbExclamation, WSAA.Excepcion)
            End If

        End Try

    End Sub

    Shared Sub ObtenerCAE()

        Dim wsdl as string, proxy as string, cache as string
        Dim concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, _
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, _
            imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, _
            fecha_serv_desde, fecha_serv_hasta, _
            moneda_id, moneda_ctz
        Dim fecha, cbte_nro
        Dim id, Desc, base_imp, alic, importe
        Dim cae
        Dim ok
        
        If WSFEv1 is Nothing Then
            Console.WriteLine("Crear objeto interface Web Service de Factura Electrónica de Mercado Interno")
            WSFEv1 = CreateObject("WSFEv1")
        End If

        Try
            Console.WriteLine(WSFEv1.Version)
            Console.WriteLine(WSFEv1.InstallDir)

            ' Generar un nuevo ticket de acceso si no existe o ha expirado;
            ' de lo contrario, se reutiliza el solicitado anteriormente
            ' (el objeto WSAA debe permanecer instanciado en memoria)
            If WSAA.Token = "" or WSAA.Sign = "" Then
                Autenticar
            Else If WSAA.Expirado Then
                Autenticar
            End If

            ' Setear tocken y sing de autorización (pasos previos)
            WSFEv1.Token = WSAA.Token
            WSFEv1.Sign = WSAA.Sign

            ' CUIT del emisor (debe estar registrado en la AFIP)
            WSFEv1.Cuit = "20267565393"

            ' Conectar al Servicio Web de Facturación
            proxy = "" ' "usuario:clave@localhost:8000"
            wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
            cache = "" 'Path
            ok = WSFEv1.Conectar(cache, wsdl, proxy) ' homologación

            REM ' mostrar bitácora de depuración:
            Console.WriteLine(WSFEv1.DebugLog)

            REM ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
            WSFEv1.Dummy()
            Console.WriteLine("appserver status" & WSFEv1.AppServerStatus)
            Console.WriteLine("dbserver status" & WSFEv1.DbServerStatus)
            Console.WriteLine("authserver status" & WSFEv1.AuthServerStatus)
               
            REM ' Establezco los valores de la factura a autorizar:
            tipo_cbte = 1
            punto_vta = 4002
            cbte_nro = WSFEv1.CompUltimoAutorizado(tipo_cbte, punto_vta)
            If cbte_nro = "" Then
                cbte_nro = 0                ' no hay comprobantes emitidos
            Else
                cbte_nro = CLng(cbte_nro)   ' convertir a entero largo
            End If
            fecha = Format(Now, "yyyyMMdd")
            concepto = 1
            tipo_doc = 80: nro_doc = "33693450239"
            cbte_nro = cbte_nro + 1
            cbt_desde = cbte_nro: cbt_hasta = cbte_nro
            imp_total = "122.00": imp_tot_conc = "0.00": imp_neto = "100.00"
            imp_iva = "21.00": imp_trib = "1.00": imp_op_ex = "0.00"
            fecha_cbte = fecha: fecha_venc_pago = ""
            ' Fechas del período del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = "": fecha_serv_hasta = ""
            moneda_id = "PES": moneda_ctz = "1.000"

            ok = WSFEv1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, _
                cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, _
                imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, _
                fecha_serv_desde, fecha_serv_hasta, _
                moneda_id, moneda_ctz)

            ' Agrego los comprobantes asociados:
            If False Then ' solo nc/nd
                REM tipo = 19
                REM pto_vta = 2
                REM nro = 1234
                REM ok = WSFEv1.AgregarCmpAsoc(tipo, pto_vta, nro)
            End If
                
            ' Agrego impuestos varios
            id = 99
            Desc = "Impuesto Municipal Matanza'"
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            ok = WSFEv1.AgregarTributo(id, Desc, base_imp, alic, importe)

            ' Agrego tasas de IVA
            id = 5 ' 21%
            base_imp = "100.00"
            importe = "21.00"
            ok = WSFEv1.AgregarIva(id, base_imp, importe)

            ' Habilito reprocesamiento automático (predeterminado):
            WSFEv1.Reprocesar = True

            ' Solicito CAE:
            CAE = WSFEv1.CAESolicitar()

            ' Imprimo pedido y respuesta XML para depuración (errores de formato)
            Console.WriteLine(WSFEv1.XmlRequest)
            Console.WriteLine(WSFEv1.XmlResponse)

            Console.WriteLine("Resultado" & WSFEv1.Resultado)
            Console.WriteLine("CAE", WSFEv1.CAE)
            Console.WriteLine("Numero de comprobante:" & WSFEv1.CbteNro)
            Console.WriteLine("Reprocesar:" & WSFEv1.Reprocesar)
            Console.WriteLine("Reproceso:" & WSFEv1.Reproceso)
            Console.WriteLine("EmisionTipo:" & WSFEv1.EmisionTipo)

            MsgBox("Resultado:" & WSFEv1.Resultado & " CAE: " & CAE & " Venc: " & WSFEv1.Vencimiento & " Reproceso: " & WSFEv1.Reproceso, vbInformation + vbOKOnly)
            
            If WSFEv1.ErrMsg <> "" Then
                MsgBox(WSFEv1.ErrMsg, vbExclamation, "Errores")
            End If

            If WSFEv1.Obs <> "" Then
                MsgBox(WSFEv1.Obs, vbExclamation, "Observaciones")
            End If
            
        Catch 
        
            ' Muestro los errores
            If WSFEv1.Traceback <> "" Then
                MsgBox(WSFEv1.Traceback, vbExclamation, "Error")
            End If

        End Try
    End Sub
End Class
