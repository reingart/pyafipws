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
#include <frameobject.h>
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

/* test function to check if python & stdlib is installed ok */
EXPORT char *STDCALL test() {
  PyObject *ret, *pdict;
  pdict = PyDict_New();
  PyDict_SetItemString(pdict, "__builtins__", PyEval_GetBuiltins()); 
  ret = PyRun_String("from time import time,ctime", Py_single_input, pdict, pdict);
  ret = PyRun_String("'Today is %s' % ctime(time())", Py_eval_input, pdict, pdict);
  Py_XDECREF(pdict);
  if (ret == NULL) {
    return format_ex();
  } else {
    return cstr(PyObject_Str(ret));
  }  
}

/* cstr: utility function to convert a python string to c (uses malloc!) */
char *cstr(void *pStr) {
    char *ret;
    size_t len;
    
    /* get the string size, remeber to copy '\0' termination character */
    len = PyString_Size((PyObject*) pStr) + 1; 
    /* allocate memory for the c string */
    ret = (char *) malloc(len);
    if (ret) {
        /* copy the py string to c (note that it may have \0 characters */
        strncpy(ret, PyString_AsString((PyObject*) pStr), len);
    }
    return ret;
}

#define FMT "%s: %s - File %s, line %d, in %s"

/* format exception: simplified PyErr_PrintEx (to not write to stdout) */
char *format_ex(void) {
    char *buf;
    char *ex, *v, *filename, *name;
    int lineno;
    PyObject *exception, *value, *tb;
    PyTracebackObject *tb1;
    
    /* PyErr_PrintEx (pythonrun.c) */
    PyErr_Fetch(&exception, &value, &tb);
	if (exception == NULL) return NULL;
	PyErr_NormalizeException(&exception, &value, &tb);
	if (exception == NULL) return NULL;
    
    /* PyErr_Display (pythonrun.c) */
    ex = PyExceptionClass_Name(exception);
    if (ex == NULL){
        ex = "<no exception class name>";
    }
    
    if (value == NULL) {
        v = "<no exception value>";
    } else {
        v = PyString_AsString(PyObject_Str(value));
    }
    
    /* PyTracebackObject seems defined at frameobject.h, it should be included
       to avoid "error: dereferencing pointer to incomplete type"
    */
    tb1 = (PyTracebackObject *)tb;
    
    /* tb_printinternal (traceback.c) */
    filename = PyString_AsString(tb1->tb_frame->f_code->co_filename);
	lineno = tb1->tb_lineno;
    name = PyString_AsString(tb1->tb_frame->f_code->co_name);

    buf = (char *) malloc(2000);

    if (buf) {
        /* tb_displayline (traceback.c) */    
        PyOS_snprintf(buf, 2000, FMT, ex, v, filename, lineno, name);
    }
    
	Py_XDECREF(exception);
	Py_XDECREF(value);
	Py_XDECREF(tb);
	
	return buf;
}

/* CreateObject: import the module, instantiate the object and return the ref */
EXPORT void * STDCALL PYAFIPWS_CreateObject(char *module, char *name) {

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
EXPORT void STDCALL PYAFIPWS_DestroyObject(void * object) {

    Py_DECREF((PyObject *) object);
    
}

/* Get: generic method to get an attribute of an object (returns a string) */
EXPORT char * STDCALL PYAFIPWS_Get(void * object, char * name) {

    PyObject *pValue;
    char *ret=NULL;

    pValue = PyObject_GetAttrString((PyObject *) object, name);

    if (pValue) {
        ret = cstr(pValue);
        Py_DECREF(pValue);
    } else {
        PyErr_Print();
        fprintf(stderr,"GetAttr to %s failed\n", name);
    }

    return ret;    
}

/* Set: generic method to set an attribute of an object (string value) */
EXPORT bool STDCALL PYAFIPWS_Set(void * object, char * name, char * value) {

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

