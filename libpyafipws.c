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

#include <Python.h>
#include "libpyafipws.h"

/* Start-up the python interpreter */
CONSTRUCTOR static void initialize(void) {
    Py_SetProgramName("pyafipws");
    Py_Initialize();
    /* on linux, add the current directory so python can find the modules */
    PyRun_SimpleString("import sys, os");
    PyRun_SimpleString("sys.path.append(os.curdir)");
}

/* Tear down the python interpreter */
DESTRUCTOR static void finalize(void) {
    Py_Finalize();
}

#ifdef WIN32

/* Windows DLL Hook  */
BOOL WINAPI DllMain(HINSTANCE hInstance, DWORD dwReason, LPVOID lpReserved) {
    BOOL ret = TRUE;
    switch (dwReason) {
        case DLL_PROCESS_ATTACH: {
            initialize();
            break;
        }
        case DLL_PROCESS_DETACH: {
            finalize();
            break;
        }
    }
    return ret;
}

#endif

EXPORT int test() {
  PyRun_SimpleString("from time import time,ctime\n"
                     "print 'Today is',ctime(time())\n");
  return 0;
}

