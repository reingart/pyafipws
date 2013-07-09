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

#define MODULE "wsfev1"


EXPORT char * WSFEv1_Conectar(void *object, char *cache, char *wsdl, char *proxy) {

    PyObject *pValue;
    char *ret = NULL;

    if (object != NULL) {

        pValue = PyObject_CallMethod((PyObject *)object, "Conectar", "(s)", cache, wsdl, proxy);
        fprintf(stderr, "conectar call!!!\n");
        if (pValue != NULL) {
                ret = PyString_AsString(pValue);
                Py_DECREF(pValue);
        } else {
            PyErr_Print();
            fprintf(stderr,"Call failed\n");
        }
    }
    return ret;
}


EXPORT char * WSFEv1_Dummy(void *object) {

    PyObject *pValue;
    char *ret = NULL;

    if (object != NULL) {

        pValue = PyObject_CallMethod((PyObject *)object, "Dummy", "");
        fprintf(stderr, "dummy call!!!\n");
        if (pValue != NULL) {
                ret = PyString_AsString(pValue);
                Py_DECREF(pValue);
        } else {
            PyErr_Print();
            fprintf(stderr,"Call failed\n");
        }
    }
    return ret;
}

