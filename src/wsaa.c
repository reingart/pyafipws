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

#define MODULE "wsaa"

EXPORT BSTR STDCALL WSAA_CreateTRA(char * service, long ttl) {

    PyObject *pName, *pModule, *pFunc;
    PyObject *pArgs, *pValue;
    BSTR ret=NULL;

    pName = PyString_FromString("wsaa");
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        
        pArgs = PyTuple_New(2);
        pValue = PyString_FromString((char*)service);
        if (!pValue) {
            Py_DECREF(pArgs);
            Py_DECREF(pModule);
            MessageBox(NULL, "Cannot convert argument 1", "WSAA_CreateTRA", 0);
            return NULL;
        }
        PyTuple_SetItem(pArgs, 0, pValue);
        pValue = PyInt_FromLong(ttl);
        if (!pValue) {
            Py_DECREF(pArgs);
            Py_DECREF(pModule);
            MessageBox(NULL, "Cannot convert argument 2", "WSAA_CreateTRA", 0);
            return NULL;
        }
        PyTuple_SetItem(pArgs, 1, pValue);

        pFunc = PyObject_GetAttrString(pModule, "create_tra");

        if (pFunc && PyCallable_Check(pFunc)) {
            MessageBox(NULL, "pfunc!!!", "WSAA_CreateTRA", 0);
            pValue = PyObject_CallObject(pFunc, pArgs);
            MessageBox(NULL, "call!!!", "WSAA_CreateTRA", 0);
            Py_DECREF(pArgs);
            if (pValue != NULL) {
                ret = cstr(pValue);
                Py_DECREF(pValue);
            }
            else {
                ret = format_ex();
                MessageBox(NULL, (char*)ret, "WSAA_CreateTRA: Call failed", 0);
            }
        }
        else {
            if (PyErr_Occurred())
                ret = format_ex();
            MessageBox(NULL, (char*)ret, "WSAA_CreateTRA: Cannot find function", 0);
        }
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    }
    else {
        if (PyErr_Occurred()) {
            ret = format_ex();
            }
        MessageBox(NULL, (char*)ret, "WSAA_CreateTRA: Failed to load module", 0);
    }
    return ret;
}

EXPORT BSTR STDCALL WSAA_SignTRA(char *tra, char *cert, char *privatekey) {

    PyObject *pName, *pModule, *pFunc;
    PyObject *pArgs, *pValue;
    BSTR ret=NULL;

    pName = PyString_FromString("wsaa");
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    //fprintf(stderr, "imported!\n");

    if (pModule != NULL) {
        
        pArgs = PyTuple_New(3);

        pValue = PyString_FromString(tra);
        if (!pValue) {
            Py_DECREF(pArgs);
            Py_DECREF(pModule);
            //fprintf(stderr, "Cannot convert argument\n");
            return NULL;
        }
        PyTuple_SetItem(pArgs, 0, pValue);
        pValue = PyString_FromString(cert);
        if (!pValue) {
            Py_DECREF(pArgs);
            Py_DECREF(pModule);
            //fprintf(stderr, "Cannot convert argument\n");
            return NULL;
        }
        PyTuple_SetItem(pArgs, 1, pValue);
        pValue = PyString_FromString(privatekey);
        if (!pValue) {
            Py_DECREF(pArgs);
            Py_DECREF(pModule);
            //fprintf(stderr, "Cannot convert argument\n");
            return NULL;
        }
        PyTuple_SetItem(pArgs, 2, pValue);

        pFunc = PyObject_GetAttrString(pModule, "sign_tra");

        if (pFunc && PyCallable_Check(pFunc)) {
            //fprintf(stderr, "pfunc!!!\n");
            pValue = PyObject_CallObject(pFunc, pArgs);
            //fprintf(stderr, "call!!!\n");
            Py_DECREF(pArgs);
            if (pValue != NULL) {
                ret = cstr(pValue);
                Py_DECREF(pValue);
            }
            else {
                PyErr_Print();
                //fprintf(stderr,"Call failed\n");
            }
        }
        else {
            if (PyErr_Occurred())
                PyErr_Print();
            //fprintf(stderr, "Cannot find function");
        }
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    }
    else {
        PyErr_Print();
        //fprintf(stderr, "Failed to load module\n");
    }
    return ret;
}


EXPORT BSTR STDCALL WSAA_LoginCMS(char *cms) {

    PyObject *pName, *pModule, *pFunc;
    PyObject *pArgs, *pValue;
    BSTR ret = NULL;
    char *argv[] = {"libpyafipws", "--trace"};

    PySys_SetArgv(2, argv);

    pName = PyString_FromString("wsaa");
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    //fprintf(stderr, "imported!\n");

    if (pModule != NULL) {
        
        pArgs = PyTuple_New(1);

        pValue = PyString_FromString(cms);
        if (!pValue) {
            Py_DECREF(pArgs);
            Py_DECREF(pModule);
            //fprintf(stderr, "Cannot convert argument\n");
            return NULL;
        }
        PyTuple_SetItem(pArgs, 0, pValue);

        pFunc = PyObject_GetAttrString(pModule, "call_wsaa");

        if (pFunc && PyCallable_Check(pFunc)) {
            //fprintf(stderr, "pfunc!!!\n");
            pValue = PyObject_CallObject(pFunc, pArgs);
            //fprintf(stderr, "call!!!\n");
            Py_DECREF(pArgs);
            if (pValue != NULL) {
                ret = cstr(pValue);
                Py_DECREF(pValue);
            }
            else {
                PyErr_Print();
                //fprintf(stderr,"Call failed\n");
            }
        }
        else {
            if (PyErr_Occurred())
                PyErr_Print();
            //fprintf(stderr, "Cannot find function");
        }
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    }
    else {
        PyErr_Print();
        //fprintf(stderr, "Failed to load module\n");
    }
    return ret;
}
