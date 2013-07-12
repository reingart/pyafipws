/* 
 *  This file is part of PyAfipWs dynamical-link shared library
 *  Copyright (C) 2013 Mariano Reingart <reingart@gmail.com>
 *
 *  PyAfipWs is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  PyAfipWs is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with PyAfipWs.  If not, see <http://www.gnu.org/licenses/>.
 */

#if defined(__GNUC__)

#define EXPORT extern
#define STDCALL 
#define CONSTRUCTOR __attribute__((constructor))
#define DESTRUCTOR __attribute__((destructor))

#include <stdbool.h>

typedef char * BSTR ; 
#define SysAllocStringByteLen(psz,len) psz
#define SysFreeString(psz)  
#define MessageBox(hwnd,msg,title,flags) fprintf(stderr, "%s: %s", title, msg)

#else

#include <windows.h>
#define EXPORT 
//__declspec(dllexport)
#define STDCALL _stdcall
//__export
#define CONSTRUCTOR
#define DESTRUCTOR

BOOL WINAPI DllMain(HINSTANCE hInstance, DWORD dwReason, LPVOID lpReserved);

typedef int bool;
#define false 0
#define true 1

/* MessageBoxA and BSTR support */
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "Shlwapi.lib")

#define WIN32

#endif

/* Debugging and Internal functions */
EXPORT BSTR STDCALL test(void);
BSTR cstr(void *pStr);
BSTR format_ex(void);

/* PYAFIPWS: COM-like generic functions to instantiate python objects */
EXPORT void * STDCALL PYAFIPWS_CreateObject(char *module, char *name);
EXPORT void STDCALL PYAFIPWS_DestroyObject(void *object);
EXPORT BSTR STDCALL PYAFIPWS_Get(void *object, char *name);
EXPORT bool STDCALL PYAFIPWS_Set(void * object, char * name, char * value);
EXPORT void STDCALL PYAFIPWS_Free(BSTR psz);

/* WSAA: Autentication Webservice functions */
EXPORT BSTR STDCALL WSAA_CreateTRA(char *service, long ttl);
EXPORT BSTR STDCALL WSAA_SignTRA(char *tra, char *cert, char *privatekey);
EXPORT BSTR STDCALL WSAA_LoginCMS(char *cms);

/* WSFEv1: Electronic Invoice Webservice methods */
EXPORT bool STDCALL WSFEv1_Conectar(void *object, char *cache, char *wsdl, char *proxy);
EXPORT bool STDCALL WSFEv1_Dummy(void *object);
EXPORT bool STDCALL WSFEv1_SetTicketAcceso(void *object, char *ta);
EXPORT long STDCALL WSFEv1_CompUltimoAutorizado(void *object, char *tipo_cbte, char *punto_vta);
