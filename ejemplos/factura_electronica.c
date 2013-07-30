/* 
 * Ejemplo de Uso de Biblioteca LibPyAfipWs (.DLL / .so)
 * con Web Service Autenticación / Factura Electrónica AFIP
 * 2013 (C) Mariano Reingart <reingart@gmail.com>
 * Licencia: GPLv3
 * Requerimientos: scripts wsaa.py y libpyafipws.h / libpyafipws.c
 * Documentacion: 
 *  http://www.sistemasagiles.com.ar/trac/wiki/LibPyAfipWs
 *  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
 */

#include "libpyafipws.h"

#if defined(__GNUC__)
#include <stdio.h>
#include <stdlib.h>
#endif

int main(int argc, char *argv[]) {
  BSTR tra, cms, ta;
  void *wsfev1;
  BSTR ret;
  bool ok;
  long nro;
  
  /* prueba generica, el valor devuelto no debería ser nulo */
  ret = test();
  printf("%s\n", ret);
  PYAFIPWS_Free(ret);
  if (ret == NULL) exit(1);
  
  /* Generar ticket de requerimiento de acceso */
  tra = WSAA_CreateTRA("wsfe", 999);
  printf("TRA:\n%s\n", tra);
  /* Firmar criptograficamente el mensaje */
  cms = WSAA_SignTRA((char*) tra, "reingart.crt", "reingart.key");
  printf("CMS:\n%s\n", cms);  
  /* Llamar al webservice y obtener el ticket de acceso */
  ta = WSAA_LoginCMS((char*) cms);
  printf("TA:\n%s\n", ta);
  
  /* Crear una objeto WSFEv1 (interfaz webservice factura electronica) */
  wsfev1 = PYAFIPWS_CreateObject("wsfev1", "WSFEv1");
  printf("crear wsfev1: %p\n", wsfev1);    /* si funcionó ok, no debe ser NULL! */  
  
  /* conectar al webservice (para produccion cambiar URL) */
  ok = WSFEv1_Conectar(wsfev1, "", "", "");
  printf("concetar: %s\n", ok ? "true" : "false");
  
  /* obtener datos genericos de la interfaz (version y ruta de instalación) */
  ret = PYAFIPWS_Get(wsfev1, "Version");
  printf("wsfev1 Version: %s\n", ret);
  free(ret);
  ret = PYAFIPWS_Get(wsfev1, "InstallDir");
  printf("wsfev1 InstallDir: %s\n", ret);
  free(ret);
  
  /* obtener el estado de los servidores (llama al ws) */
  ok = WSFEv1_Dummy(wsfev1);
  printf("llamar a dummy: %s\n", ok ? "true" : "false");
  /* obtener los atributos devueltos por AFIP */
  ret = PYAFIPWS_Get(wsfev1, "AppServerStatus");
  printf("dummy AppServerStatus: %s\n", ret);
  free(ret);
  ret = PYAFIPWS_Get(wsfev1, "DbServerStatus");
  printf("dummy DbServerStatus: %s\n", ret);
  free(ret);
  ret = PYAFIPWS_Get(wsfev1, "AuthServerStatus");
  printf("dummy AuthServerStatus: %s\n", ret);
  free(ret);

  /* establezco los datos para operar el webservice */
  ok = PYAFIPWS_Set(wsfev1, "Cuit", "20267565393");
  ok = WSFEv1_SetTicketAcceso(wsfev1, (char*) ta);  /* devuelto por WSAA_LoginCMS */

  /* obtengo el ultimo numero de comprobante generado */
  nro = WSFEv1_CompUltimoAutorizado(wsfev1, "1", "1");
  printf("ultimo comprobante: %ld\n", nro);

  /* destruir el objeto */
  PYAFIPWS_DestroyObject(wsfev1);  


  /* liberar la memoria adquirida para los valores devueltos de WSAA */
  PYAFIPWS_Free(ta);
  PYAFIPWS_Free(cms);
  PYAFIPWS_Free(tra);

  return 0;
}

