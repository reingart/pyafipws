/* 
 * Ejemplo de Uso de Biblioteca LibPyAfipWs (.DLL / .so) para C # sharp
 * con Web Service Autenticación / Factura Electrónica AFIP
 * 2013 (C) Mariano Reingart <reingart@gmail.com>
 * Licencia: GPLv3
 * Requerimientos: scripts wsaa.py y libpyafipws.h / libpyafipws.c
 * Documentacion: 
 *  http://www.sistemasagiles.com.ar/trac/wiki/LibPyAfipWs
 *  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
 */

using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;


namespace ConsoleApplication1
{
    class Program
    {
        /* declaro el procedimiento externo exportado por la DLL */
        [DllImport("F:\\libpyafipws.dll")]
        private static extern string WSAA_CreateTRA(
              string service,
              long ttl
        );

        static void Main(string[] args)
        {
            /* llamo al método de la DLL para crear ticket de req. de acceso */
            string tra;
            tra = WSAA_CreateTRA("wsfe", 3600);
            Console.WriteLine("TRA = {0}", tra);
            Console.ReadLine();
            /* importante: en producción, revisar y liberar memoria alojada
             * para el string, ej: PYAFIPWS_Free(tra) */
        }
    }
}
