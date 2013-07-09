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

/* CreateObject: import the module, instantiate the object and return the ref */
EXPORT void * PYAFIPWS_CreateObject(char *module, char *name) {

    PyObject *pName, *pModule, *pClass, *pObject=NULL;

    pName = PyString_FromString(module);
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    fprintf(stderr, "imported!\n");

    if (pModule != NULL) {
        pClass = PyObject_GetAttrString(pModule, name);
        if (pClass && PyCallable_Check(pClass)) {
            fprintf(stderr, "pfunc!!!\n");
            pObject = PyObject_CallObject(pClass, NULL);
            fprintf(stderr, "call!!!\n");
            Py_XDECREF(pClass);
        }
        Py_DECREF(pModule);
        return (void *) pObject;
    } else {
        return NULL;
    }
}

/* DestroyObject: decrement the reference to the module */
EXPORT void PYAFIPWS_DestroyObject(void * object) {

    Py_DECREF((PyObject *) object);
    
}

/* Get: generic method to get an attribute of an object (returns a string) */
EXPORT char * PYAFIPWS_Get(void * object, char * name) {

    PyObject *pValue;
    char *ret=NULL;

    pValue = PyObject_GetAttrString((PyObject *) object, name);

    if (pValue) {
        ret = PyString_AsString(pValue);
        Py_DECREF(pValue);
    } else {
        PyErr_Print();
        fprintf(stderr,"GetAttr to %s failed\n", name);
    }

    return ret;    
}

/* Set: generic method to set an attribute of an object (string value) */
EXPORT bool PYAFIPWS_Set(void * object, char * name, char * value) {

    PyObject *pValue;
    int ret;
    bool ok=false;

    pValue = PyString_FromString(value);
    ret = PyObject_SetAttrString((PyObject *) object, name, pValue);

    if (pValue) {
        Py_DECREF(pValue);
    }
    if (ret == -1) {
        PyErr_Print();
        fprintf(stderr,"GetAttr to %s failed\n", name);
        ok = false;
    } else {
        ok = true;
    }
    return ok;
}

