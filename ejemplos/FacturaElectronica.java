/* Ejemplo de Uso de Interfaz PyAfipWs para JAVA (componentes DLL en Windows)
   con Web Service Autenticación / Factura Electrónica AFIP (mercado interno)
   2014 (C) Mariano Reingart <reingart@gmail.com> Licencia: GPLv3
   
   Requerimientos: 
    * wsaa.py y wsfev1.py registrados (último instalador PyAfipWs homologación)
   
   Dependencias: 
    * JACOB - Java COM Bridge: http://sourceforge.net/projects/jacob-project/
   
   IMPORTANTE: 
    * Renombrar jacob-1.18-M2-x64.dll o jacob-1.18-M2-x86.dll -> jacob.dll
    * Mover jacob.dll al directorio windows\system o junto a esta clase
    * Agregar jacob.jar al CLASSPATH, ej SET CLASSPATH=Z:\ruta\jacob.jar;.
   
   Documentacion: 
    http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
    http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
*/

import com.jacob.activeX.ActiveXComponent;
import com.jacob.com.Dispatch;
import com.jacob.com.LibraryLoader;
import com.jacob.com.Variant;
import java.text.SimpleDateFormat;
import java.util.Date;

public class FacturaElectronica {

    public static void main(String[] args) {
        try {

            LibraryLoader.loadJacobLibrary();
            
            /* Crear objeto WSAA: Web Service de Autenticación y Autorización */
            ActiveXComponent wsaa = new ActiveXComponent("WSAA");
            
            System.out.println(Dispatch.get(wsaa, "InstallDir").toString() + 
                               Dispatch.get(wsaa, "Version").toString()
                              );
                        
            /* Solicitar Ticket de Acceso a AFIP (cambiar URL producción) */
            String wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms";
            String userdir = System.getProperty("user.dir");
            Dispatch.call(wsaa, "Autenticar", 
                                new Variant("wsfe"), 
                                new Variant(userdir + "/reingart.crt"), 
                                new Variant(userdir + "/reingart.key"), 
                                new Variant(wsdl));
            String excepcion =  Dispatch.get(wsaa, "Excepcion").toString();
            System.out.println("Excepcion: " + excepcion);
            String token = Dispatch.get(wsaa, "Token").toString();
            String sign = Dispatch.get(wsaa, "Sign").toString();
            System.out.println("Token: " + token +  "Sign: " + sign);
            
            /* Instanciar WSFEv1: WebService de Factura Electrónica version 1 */

            ActiveXComponent wsfev1 = new ActiveXComponent("WSFEv1");

            /* Establecer parametros de uso: */
            Dispatch.put(wsfev1, "Cuit", new Variant("20267565393"));
            Dispatch.put(wsfev1, "Token", new Variant(token));
            Dispatch.put(wsfev1, "Sign", new Variant(sign));

            /* Conectar al websrvice (cambiar URL para producción) */
            wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL";
            Dispatch.call(wsfev1, "Conectar", 
                                  new Variant(""), 
                                  new Variant(wsdl));

            /* Consultar último comprobante autorizado en AFIP */
            String tipo_cbte = "1";
            String pto_vta = "1";
            Variant ult = Dispatch.call(wsfev1, "CompUltimoAutorizado", 
                                                new Variant(tipo_cbte), 
                                                new Variant(pto_vta));
            System.out.println("Ultimo comprobante: " + ult.toString());
            excepcion =  Dispatch.get(wsfev1, "Excepcion").toString();
            System.out.println("Excepcion: " + excepcion);

            /* CAE */             
            String fecha = new SimpleDateFormat("yyyyMMdd").format(new Date());
            String concepto = "1";
            String tipo_doc = "80", nro_doc = "33693450239";
            int cbte_nro = Integer.parseInt(ult.toString()) + 1,
                cbt_desde = cbte_nro,
                cbt_hasta = cbte_nro;
            String imp_total = "124.00";
            String imp_tot_conc = "2.00";
            String imp_neto = "100.00";
            String imp_iva = "21.00", imp_trib = "1.00", imp_op_ex = "0.00";
            String fecha_cbte = fecha, fecha_venc_pago = "";
            /* Fechas período del servicio facturado (solo si concepto> 1) */
            String fecha_serv_desde = "", fecha_serv_hasta = "";
            String moneda_id = "PES", moneda_ctz = "1.000";

            Variant ok = Dispatch.call(wsfev1, "CrearFactura",
                new Variant(concepto), new Variant(tipo_doc), 
                new Variant(nro_doc), new Variant(tipo_cbte), 
                new Variant(pto_vta), 
                new Variant(cbt_desde), new Variant(cbt_hasta), 
                new Variant(imp_total), new Variant(imp_tot_conc), 
                new Variant(imp_neto), new Variant(imp_iva), 
                new Variant(imp_trib), new Variant(imp_op_ex), 
                new Variant(fecha_cbte), new Variant(fecha_venc_pago), 
                new Variant(fecha_serv_desde), new Variant(fecha_serv_hasta),
                new Variant(moneda_id), new Variant(moneda_ctz));
            
            /* Agrego los comprobantes asociados: */ 
            if (false) { /* solo nc/nd */
                Variant cbte_asoc_tipo = new Variant("19"), 
                        cbte_asoc_pto_vta = new Variant("2"), 
                        cbte_asoc_nro = new Variant("1234");
                Dispatch.call(wsfev1, "AgregarCmpAsoc",
                              cbte_asoc_tipo, cbte_asoc_pto_vta, cbte_asoc_nro);
            }
                
            /* Agrego impuestos varios */
            Variant tributo_id = new Variant(4),
                    tributo_desc = new Variant("Impuestos internos"),
                    tributo_base_imp = new Variant("100.00"),
                    tributo_alic = new Variant("1.00"),
                    tributo_importe = new Variant("1.00");
            Dispatch.call(wsfev1, "AgregarTributo", 
                          tributo_id, tributo_desc, tributo_base_imp, 
                          tributo_alic, tributo_importe);

            /* Agrego tasas de IVA */
            Variant iva_id = new Variant(5), /* 21% */
                    iva_base_imp = new Variant("100.00"),
                    iva_importe = new Variant("21.00");
            Dispatch.call(wsfev1, "AgregarIva", 
                          iva_id, iva_base_imp, iva_importe);
            
            /* Habilito reprocesamiento automático (predeterminado): */
            Dispatch.put(wsfev1, "Reprocesar", new Variant(true));

            /* Solicito CAE (llamando al webservice de AFIP): */
            Variant cae = Dispatch.call(wsfev1, "CAESolicitar");

            /* Mostrar mensajes XML enviados y recibidos (depuración) */            
            System.out.println("XmlRequest: " +
                               Dispatch.get(wsfev1, "XmlRequest").toString());
            System.out.println("XmlResponse: " +
                               Dispatch.get(wsfev1, "XmlResponse").toString());

            excepcion =  Dispatch.get(wsfev1, "Excepcion").toString();
            System.out.println("Excepcion: " + excepcion);

            String errmsg =  Dispatch.get(wsfev1, "ErrMsg").toString();
            System.out.println("ErrMsg: " + errmsg);
            String obs =  Dispatch.get(wsfev1, "Obs").toString();
            System.out.println("Obs: " + obs);
           
            /* datos devueltos */
            System.out.println("CAE: " + cae.toString());
            String resultado = Dispatch.get(wsfev1, "Resultado").toString();
            System.out.println("Resultado: " + resultado);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
