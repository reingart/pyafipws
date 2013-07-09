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
#define CONSTRUCTOR __attribute__((constructor))
#define DESTRUCTOR __attribute__((destructor))

#include <stdbool.h>

#else

#include <windows.h>
#define EXPORT __declspec(dllexport) 
#define CONSTRUCTOR
#define DESTRUCTOR

BOOL WINAPI DllMain(HINSTANCE hInstance, DWORD dwReason, LPVOID lpReserved);

typedef int bool;
#define false 0
#define true 1

#define WIN32

#endif

EXPORT int test(void);
char *cstr(void *pStr);

/* PYAFIPWS: COM-like generic functions to instantiate python objects */
EXPORT void * PYAFIPWS_CreateObject(char *module, char *name);
EXPORT void PYAFIPWS_DestroyObject(void *object);
EXPORT char * PYAFIPWS_Get(void *object, char *name);
EXPORT bool PYAFIPWS_Set(void * object, char * name, char * value);

/* WSAA: Autentication Webservice functions */
EXPORT char * WSAA_CreateTRA(const char *service, long ttl);
EXPORT char * WSAA_SignTRA(char *tra, char *cert, char *privatekey);
EXPORT char * WSAA_LoginCMS(char *cms);

/* WSFEv1: Electronic Invoice Webservice methods */
EXPORT bool WSFEV1_Conectar(void *object, char *cache, char *wsdl, char *proxy);
EXPORT bool WSFEV1_Dummy(void *object);
EXPORT bool WSFEv1_SetTicketAccesso(void *object, char *ta);

