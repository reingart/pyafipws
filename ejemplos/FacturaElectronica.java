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

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
