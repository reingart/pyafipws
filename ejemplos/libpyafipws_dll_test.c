/* 
 * Ejemplo de Uso de Biblioteca LibPyAfipWs.DLL en windows
 * con Web Service Autenticación / Factura Electrónica AFIP
 * 2013 (C) Mariano Reingart <reingart@gmail.com>
 * Licencia: GPLv3
 * Requerimientos: scripts wsaa.py y libpyafipws.h / libpyafipws.c
 * Documentacion: 
 *  http://www.sistemasagiles.com.ar/trac/wiki/LibPyAfipWs
 *  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
 */

#include "libpyafipws.h"

#include <windows.h>

int main(int argc, char *argv[]) {
  BSTR tra, cms, ta, ret;
  void *wsfev1;
  bool ok;
  long nro;
  HINSTANCE hPyAfipWsDll;
  FARPROC lpFunc, lpFree;

  /* cargo la librería y obtengo la referencia (poner ruta completa) */
  hPyAfipWsDll = LoadLibrary("..\\LIBPYAFIPWS.DLL");
  if (hPyAfipWsDll != NULL) {
    /* obtengo los punteros a las funciones exportadas en la librería */
    lpFunc = GetProcAddress(hPyAfipWsDll , "WSAA_CreateTRA");
    lpFree = GetProcAddress(hPyAfipWsDll , "PYAFIPWS_Free");
    if (lpFunc != (FARPROC) NULL) {
        /* llamo al método de la DLL para crear el ticket de req. de acceso */
        tra = (*lpFunc)("wsfe", (long)3600);
        printf("TRA: %s\n", tra);
        /* libero la memoria alojada por el string devuelto */
        (*lpFree)(tra);
    }
  }
  FreeLibrary(hPyAfipWsDll);
}
