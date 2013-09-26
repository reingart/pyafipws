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

#ifdef WIN32
    #include "Shlwapi.h"
    /* sys.fronzenddlhandle emulation (set by DllMain) */
    HMODULE dllhandle;
#endif

/* Start-up the python interpreter */
CONSTRUCTOR static void initialize(void) {
    //Py_SetProgramName("libpyafipws");
    #ifdef WIN32
        char buf[2000], *b;
        unsigned long ok;
        PyObject *pSysPath, *pName;
       
        MessageBox(NULL, "Py_Initialize...", "LibPyAfipWs Initialize", 0);
        Py_Initialize();
        PyRun_SimpleString("import sys, os");
        PyRun_SimpleString("sys.stdout = open('stdout.txt', 'w')");
        PyRun_SimpleString("sys.stderr = open('stderr.txt', 'w')");
        /* on windows, add the base path of the .DLL */
        ok = GetModuleFileName(dllhandle, buf, sizeof(buf));
        MessageBox(NULL, buf, "LibPyAfipWs Initialize (module name)", 0);
        ok = PathRemoveFileSpec(buf);
        MessageBox(NULL, buf, "LibPyAfipWs Initialize (module path)", 0);
        pSysPath = PySys_GetObject("path");
        pName = PyString_FromString(buf);
        if (PyList_Insert(pSysPath, 0, pName))
            MessageBox(NULL, "PyList_Insert", "LibPyAfipWs Initialize", 0);
        Py_XDECREF(pName);   /* note that pSysPath is a Borrowed reference! */
        MessageBox(NULL, "done!", "LibPyAfipWs Initialize", 0);
    #else
        Py_Initialize();
        puts(Py_GetPath());
        /* on linux, add the current directory so python can find the modules */
        PyRun_SimpleString("import sys, os");
        PyRun_SimpleString("sys.path.append(os.curdir)");
        /* preliminary fix, it could not work on some cases and there could be 
           some security concerns. It should add the base path of the .so */
    #endif
}

/* Tear down the python interpreter */
DESTRUCTOR static void finalize(void) {
    MessageBox(NULL, "Py_Finalize...", "LibPyAfipWs Finalize", 0);
    Py_Finalize();
    MessageBox(NULL, "done!", "LibPyAfipWs Finalize", 0);
}

#ifdef WIN32

/* Windows DLL Hook  */
BOOL WINAPI DllMain(HINSTANCE hInstance, DWORD dwReason, LPVOID lpReserved) {
    BOOL ret = TRUE;
    switch (dwReason) {
        case DLL_PROCESS_ATTACH: {
            dllhandle = (HINSTANCE) hInstance;
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
EXPORT BSTR STDCALL test() {
  PyObject *pret, *pdict;
  BSTR ret = NULL;
  MessageBox(NULL, "iniciando pruebas...", "LibPyAfipWs Test!", 0);
  pdict = PyDict_New();
  PyDict_SetItemString(pdict, "__builtins__", PyEval_GetBuiltins()); 
  pret = PyRun_String("from time import time,ctime", Py_single_input, pdict, pdict);
  Py_XDECREF(pret);
  pret = PyRun_String("'Today is %s' % ctime(time())", Py_eval_input, pdict, pdict);
  if (pret == NULL) {
    ret = format_ex();
  } else {
    ret = cstr(PyObject_Str(pret));
  } 
  MessageBox(NULL, (char*)ret, "LibPyAfipWs Test!", 0);
  Py_XDECREF(pdict);
  Py_XDECREF(pret);
  return ret;
}


/* cstr: utility function to convert a python string to c (dyn. allocated) */
BSTR cstr(void *pStr) {
    BSTR ret;
    char *str;
    size_t len;
    
    /* get the string val/size, remember to copy '\0' termination character */
    len = PyString_Size((PyObject*) pStr) + 1; 
    str = PyString_AsString((PyObject*) pStr);

    #ifdef WIN32
        /* on windows, returns a automation string */
        ret = SysAllocStringByteLen(str, len);
    #else
        /* allocate memory for the c string */
        ret = (char *) malloc(len);
        if (ret) {
            /* copy the py string to c (note that it may have \0 characters */
            strncpy(ret, str, len);
        }
    #endif
    return ret;
}

#define FMT "%s: %s - File %s, line %d, in %s"

/* format exception: simplified PyErr_PrintEx (to not write to stdout) */
BSTR format_ex(void) {
    char buf[2000];
    BSTR ret;
    char *ex, *v, *filename="<internal>", *name="<C>";
    int lineno=-1;
    size_t len;
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
       tb is NULL if the failure is in the c-api (for example in PyImport_Import)
    */
    tb1 = (PyTracebackObject *)tb;
    
    /* tb_printinternal (traceback.c) */
    if (tb1) {
        filename = PyString_AsString(tb1->tb_frame->f_code->co_filename);
        lineno = tb1->tb_lineno;
        name = PyString_AsString(tb1->tb_frame->f_code->co_name);
    }

    /* tb_displayline (traceback.c) */    
    PyOS_snprintf(buf, sizeof(buf), FMT, ex, v, filename, lineno, name);

	Py_XDECREF(exception);
	Py_XDECREF(value);
	Py_XDECREF(tb);

	len = strlen(buf);
    #ifdef WIN32
        /* on windows, returns a automation string */
        ret = SysAllocStringByteLen(buf, len);
    #else
        /* allocate memory for the c string */
        ret = (char *) malloc(len);
        if (ret) {
            /* copy the py string to c (note that it may have \0 characters */
            strncpy(ret, buf, len);
        }
    #endif
    
    return ret;
}

/* CreateObject: import the module, instantiate the object and return the ref */
EXPORT void * STDCALL PYAFIPWS_CreateObject(char *module, char *name) {

    PyObject *pName, *pModule, *pClass, *pObject=NULL;

    pName = PyString_FromString(module);
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    //fprintf(stderr, "imported!\n");

    if (pModule != NULL) {
        pClass = PyObject_GetAttrString(pModule, name);
        if (pClass && PyCallable_Check(pClass)) {
            //fprintf(stderr, "pfunc!!!\n");
            pObject = PyObject_CallObject(pClass, NULL);
            //fprintf(stderr, "call!!!\n");
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
EXPORT BSTR STDCALL PYAFIPWS_Get(void * object, char * name) {
    PyObject *pValue;
    BSTR ret=NULL;

    pValue = PyObject_GetAttrString((PyObject *) object, name);

    if (pValue) {
        ret = cstr(pValue);
        Py_DECREF(pValue);
    } else {
        PyErr_Print();
        //fprintf(stderr,"GetAttr to %s failed\n", name);
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
        //fprintf(stderr,"GetAttr to %s failed\n", name);
        ok = false;
    } else {
        ok = true;
    }
    return ok;
}

/* deallocation function for libpyafipws string values */
EXPORT void STDCALL PYAFIPWS_Free(BSTR psz) {
    if (psz != (BSTR) NULL)
    #ifdef WIN32
        SysFreeString(psz);
    #else
        free(psz);
    #endif
}
