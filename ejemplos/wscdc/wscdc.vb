'<summary>
'EJEMPLO - Interfaz Libre PyAfipWs WSCDC
'</summary>
'<description>
' Interfaz PyAfipWs Web Service de Constatación de Comprobantes Emitidos
' Más info en: http://www.sistemasagiles.com.ar/trac/wiki/ConstatacionComprobantes
' 2013 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3
' Funcionamiento:
'   Solicita Ticket de Acceso (WSAA.LoginCMS)
'   Muestra estado de servidores (WSCDC.Dummy)
'   Verificar validez de comprobante (WSCDC.ConstatarComprobante)
'</description>
'<version>0.0.1</version>.
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

    Shared Sub Main(ByVal args As String())
		Dim WSAA As Object
		Dim Path As String
		Dim tra as string, cms as string, ta as string
		Dim wsdl as string, proxy as string, cache as string
		Dim certificado as string, claveprivada as string
		Dim ok

		Console.WriteLine("DEMO Interfaz PyAfipWs WSCDC para vb.net")
	  
		' Crear objeto interface Web Service Autenticación y Autorización
		WSAA = CreateObject("WSAA")
		Console.WriteLine(WSAA.Version)

		Try
			Console.WriteLine("Generar un Ticket de Requerimiento de Acceso (TRA) para WSCDC")
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

		Dim WSCDC As Object
		Dim cbte_modo, cuit_emisor, pto_vta, cbte_tipo, cbte_nro, cbte_fch, _
		    imp_total, cod_autorizacion, doc_tipo_receptor, doc_nro_receptor
		
		Console.WriteLine("Crear objeto interface Web Service de Constatación de Comprobantes")
		WSCDC = CreateObject("WSCDC")

		Try
			Console.WriteLine(WSCDC.Version)
			Console.WriteLine(WSCDC.InstallDir)

			' Setear tocken y sing de autorización (pasos previos)
			WSCDC.Token = WSAA.Token
			WSCDC.Sign = WSAA.Sign

			' CUIT del emisor (debe estar registrado en la AFIP)
			WSCDC.Cuit = "20267565393"

			' Conectar al Servicio Web de Facturación
			proxy = "" ' "usuario:clave@localhost:8000"
			wsdl = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL"
			cache = "" 'Path
			ok = WSCDC.Conectar(cache, wsdl, proxy) ' homologación

			REM ' mostrar bitácora de depuración:
			Console.WriteLine(WSCDC.DebugLog)

			REM ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
			WSCDC.Dummy()
			Console.WriteLine("appserver status" & WSCDC.AppServerStatus)
			Console.WriteLine("dbserver status" & WSCDC.DbServerStatus)
			Console.WriteLine("authserver status" & WSCDC.AuthServerStatus)
			   
			REM ' Establezco los valores de la factura a verificar:
            cbte_modo = "CAE"
            cuit_emisor = "20267565393"
            pto_vta = 4002
            cbte_tipo = 1
            cbte_nro = 109
            cbte_fch = "20131227"
            imp_total = "121.0"
            cod_autorizacion = "63523178385550"
            doc_tipo_receptor = 80
            doc_nro_receptor = "30628789661"
            ' Llamo al webservice para constatar
			ok = WSCDC.ConstatarComprobante(cbte_modo, cuit_emisor, pto_vta, cbte_tipo, _
                                    cbte_nro, cbte_fch, imp_total, cod_autorizacion, _
                                    doc_tipo_receptor, doc_nro_receptor)
			
			' Imprimo pedido y respuesta XML para depuración (errores de formato)
			Console.WriteLine(WSCDC.XmlRequest)
			Console.WriteLine(WSCDC.XmlResponse)

			Console.WriteLine("Resultado" & WSCDC.Resultado)
			Console.WriteLine("CAI", WSCDC.CAI)
			Console.WriteLine("CAE", WSCDC.CAE)
			Console.WriteLine("CAEA", WSCDC.CAEA)
			Console.WriteLine("Numero de comprobante:" & WSCDC.CbteNro)
			Console.WriteLine("EmisionTipo:" & WSCDC.EmisionTipo)

			MsgBox("Resultado:" & WSCDC.Resultado, vbInformation + vbOKOnly)
			
			If WSCDC.ErrMsg <> "" Then
				MsgBox(WSCDC.ErrMsg, vbExclamation, "Errores")
			End If

			If WSCDC.Obs <> "" Then
				MsgBox(WSCDC.Obs, vbExclamation, "Observaciones")
			End If
			
		Catch 
		
			' Muestro los errores
			If WSCDC.Traceback <> "" Then
				MsgBox(WSCDC.Traceback, vbExclamation, "Error")
			End If

		End Try
    End Sub
End Class
