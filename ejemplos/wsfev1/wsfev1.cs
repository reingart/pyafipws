//<summary>
//EJEMPLO - Interfaz Libre PyAfipWs WSFEv1 C#
//</summary>
//<description>
// Interfaz PyAfipWs Web Service Factura Electrónica Mercado Interno
// Según RG2904 Artículo 4 Opción B (sin detalle, RG2485 Version 1)
// 2011 (C) Mariano Reingart <reingart@gmail.com> (original en VB.NET)
// Licencia: GPLv3
// Funcionamiento:
//   Solicita Ticket de Acceso (WSAA.LoginCMS)
//   Muestra estado de servidores (WSFEv1.Dummy)
//   Obtiene último número de factura autorizado (WSFEv1.CompUltimoAutorizado)
//   Crea una Factura, agrega IVA, Tributo y Comprobantes Asociados (WSFEv1.CrearFactura et.al.)
//   Solicita CAE (WSFEv1.CAESolicitar)
//</description>
//<version>0.0.1</version>.
//<platform>.NET Framework 1.1</platform>
//<disclaimer>
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by the
// Free Software Foundation; either version 3, or (at your option) any later
// version.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
// or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
// for more details.
//</disclaimer>

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using Microsoft.VisualBasic;


namespace ConsoleApplication2
{
    class Program
    {
        static void Main(string[] args)
        {
            
            string Path;
            string tra, cms, ta;
            string wsdl, proxy, cache="";
            string certificado, claveprivada;
            object ok;

            Console.WriteLine("DEMO Interfaz PyAfipWs WSFEv1 para vb.net");

       //' Crear objeto interface Web Service Autenticación y Autorización
            //WSAA = new object("WSAA");
            dynamic WSAA =Activator.CreateInstance(Type.GetTypeFromProgID("WSAA"));
            Console.WriteLine(WSAA.Version);

            try{
            Console.WriteLine("Generar un Ticket de Requerimiento de Acceso (TRA) para WSFEv1");

            tra = WSAA.CreateTRA("wsfe");
            Console.WriteLine(tra);

            // Especificar la ubicacion de los archivos certificado y clave privada
            Path = Environment.CurrentDirectory + "\\";

            // Certificado: certificado es el firmado por la AFIP
            // ClavePrivada: la clave privada usada para crear el certificado
            certificado = "..\\..\\reingart.crt" ; //certificado de prueba;
            claveprivada = "..\\..\\reingart.key"; // " clave privada de prueba;

            Console.WriteLine("Generar el mensaje firmado (CMS)");
            cms = WSAA.SignTRA(tra, certificado, claveprivada);
            Console.WriteLine(cms);

            Console.WriteLine("Llamar al web service para autenticar:");
            proxy = ""; //"usuario:clave@localhost:8000"
            wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl";
            WSAA.Conectar(cache, wsdl, proxy); // Homologación
            ta = WSAA.LoginCMS(cms);
            // Imprimir el ticket de acceso, ToKen y Sign de autorización
                ///MsgBox(WSAA.Token, vbInformation, "WSAA Token")
                ///MsgBox(WSAA.Sign, vbInformation, "WSAA Sign")
            }catch
            {
            
             if(WSAA.Excepcion != "")
                //MsgBox(WSAA.Traceback, vbExclamation, WSAA.Excepcion)
                Console.WriteLine(WSAA.Excepcion);
            
            }
            

            ////////////////////////////////////////////////
            
            object  concepto, tipo_doc, nro_doc, tipo_cbte;
            object  punto_vta,cbt_desde, cbt_hasta, imp_total;
            object  imp_tot_conc, imp_neto, imp_trib; 
            object  imp_op_ex, fecha_cbte, fecha_venc_pago;
            object  fecha_serv_desde, fecha_serv_hasta;
            object  moneda_id, moneda_ctz;
            object tipo, pto_vta, nro, fecha, cbte_nro;
            object id, Desc, base_imp, alic, importe;
            object CAE;
            long lcbte_nro;
            object imp_iva;
            
           

            Console.WriteLine("Crear objeto interface Web Service de Factura Electrónica de Mercado Interno");
            dynamic WSFEv1 = Activator.CreateInstance(Type.GetTypeFromProgID("WSFEv1"));

            try{
                Console.WriteLine(WSFEv1.Version);
                Console.WriteLine(WSFEv1.InstallDir);

                // Setear tocken y sing de autorización (pasos previos)
                WSFEv1.Token = WSAA.Token;
                WSFEv1.Sign = WSAA.Sign;

                // CUIT del emisor (debe estar registrado en la AFIP)
                WSFEv1.Cuit = "20267565393";

                // Conectar al Servicio Web de Facturación
                proxy = ""; // "usuario:clave@localhost:8000"
                wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL";
                cache = "" ;//Path
                ok = WSFEv1.Conectar(cache, wsdl, proxy); // homologación

            
                Console.WriteLine(WSFEv1.DebugLog);

                /// Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
                WSFEv1.Dummy();
                Console.WriteLine("appserver status" + WSFEv1.AppServerStatus);
                Console.WriteLine("dbserver status" + WSFEv1.DbServerStatus);
                Console.WriteLine("authserver status" + WSFEv1.AuthServerStatus);

                // Establezco los valores de la factura a autorizar:
                tipo_cbte = 1;
                punto_vta = 4002;
                cbte_nro = WSFEv1.CompUltimoAutorizado(tipo_cbte, punto_vta);
                if( cbte_nro == "")
                    lcbte_nro = 0;//                ' no hay comprobantes emitidos
                else
                    lcbte_nro = Convert.ToInt64(cbte_nro);   // convertir a entero largo
            
                fecha=DateTime.Now.ToString("yyyyMMdd");
                concepto = 1;
                tipo_doc = 80;
                nro_doc = "33693450239";
                lcbte_nro = lcbte_nro + 1;

                cbt_desde = lcbte_nro;
                cbt_hasta = lcbte_nro;
                imp_total = "122.00";
                imp_tot_conc = "0.00";
                imp_neto = "100.00";

                imp_iva = "21.00";

                imp_trib = "1.00";
                imp_op_ex = "0.00";
                fecha_cbte = fecha;
                fecha_venc_pago = "";
                // Fechas del período del servicio facturado (solo si concepto = 1?)
                fecha_serv_desde = "";
                fecha_serv_hasta = "";
                moneda_id = "PES";
                moneda_ctz = "1.000";

                ok = WSFEv1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                 cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, 
                 imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago,
                 fecha_serv_desde, fecha_serv_hasta,
                 moneda_id, moneda_ctz);

                //if (ok==false)
                //    Console.WriteLine("Ok false");

                // Agrego comprobantes Asociados

                // Agrego impuestos varios
                id = 99;
                Desc = "Impuesto Municipal Matanza";
                base_imp = "100.00";
                alic = "1.00";
                importe = "1.00";
                ok = WSFEv1.AgregarTributo(id, Desc, base_imp, alic, importe);

                // Agrego tasas de IVA
                id = 5;// 21%
                base_imp = "100.00";
                importe = "21.00";
                ok = WSFEv1.AgregarIva(id, base_imp, importe);

                // Habilito reprocesamiento automático (predeterminado):
                WSFEv1.Reprocesar = true;

                 // Solicito CAE:
                CAE = WSFEv1.CAESolicitar();

                // Imprimo pedido y respuesta XML para depuración (errores de formato)
                Console.WriteLine(WSFEv1.XmlRequest);
                Console.WriteLine(WSFEv1.XmlResponse);

                Console.WriteLine("Resultado" + WSFEv1.Resultado);
                Console.WriteLine("CAE", WSFEv1.CAE);
                Console.WriteLine("Numero de comprobante:" + WSFEv1.CbteNro);
                Console.WriteLine("Reprocesar:" + WSFEv1.Reprocesar);
                Console.WriteLine("Reproceso:" + WSFEv1.Reproceso);
                Console.WriteLine("EmisionTipo:" + WSFEv1.EmisionTipo);

                //MsgBox("Resultado:" & WSFEv1.Resultado & " CAE: " & CAE & " Venc: " & WSFEv1.Vencimiento & " Reproceso: " & WSFEv1.Reproceso, vbInformation + vbOKOnly)

                if( WSFEv1.ErrMsg != "")
                    // MsgBox(WSFEv1.ErrMsg, vbExclamation, "Errores")
                    Console.WriteLine(WSFEv1.ErrMsg);

                if(WSFEv1.Obs != "")
                    //MsgBox(WSFEv1.Obs, vbExclamation, "Observaciones")
                    Console.WriteLine(WSFEv1.Obs);
            }
            catch
            {
             // Muestro los errores
                if (WSFEv1.Traceback != "")
                    //MsgBox(WSFEv1.Traceback, vbExclamation, "Error")
                    Console.WriteLine(WSFEv1.Traceback);
            
            }

        Console.ReadKey();
        }
    }
}
