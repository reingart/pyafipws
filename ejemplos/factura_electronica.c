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
#endif

int main(int argc, char *argv[]) {
  char *tra, *cms, *ta;
  void *wsfev1;
  
  /* prueba generica */
  test();
  
  /* Generar ticket de requerimiento de acceso */
  tra = WSAA_CreateTRA("wsfe", 999);
  printf("TRA:\n%s\n", tra);
  /* Firmar criptograficamente el mensaje */
  cms = WSAA_SignTRA(tra, "reingart.crt", "reingart.key");
  printf("CMS:\n%s\n", cms);  
  /* Llamar al webservice y obtener el ticket de acceso */
  ta = WSAA_LoginCMS(cms);
  printf("TA:\n%s\n", ta);    
  
  /* Crear una objeto WSFEv1 (interfaz webservice factura electronica) */
  wsfev1 = PYAFIPWS_CreateObject("wsfev1", "WSFEv1");
  printf("wsfev1: %p\n", wsfev1);    /* si funiconó ok, no debe ser NULL! */  
  /* destruir el objeto */
  PYAFIPWS_DestroyObject(wsfev1);  


  return 0;
}

