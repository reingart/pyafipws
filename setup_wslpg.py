#!/usr/bin/python
# -*- coding: latin-1 -*-

# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para Liquidación Electrónica Primaria de Granos"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"

from distutils.core import setup
import py2exe
import glob, sys

# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils']

# required modules for shelve support (not detected by py2exe by defaultdel):
for lib in 'dbhash', 'gdbm', 'dbm', 'dumbdbm', 'anydbm':
    try:
        __import__(lib)
        includes.append(lib)
    except ImportError:
        pass

# don't pull in all this MFC stuff used by the makepy UI.
excludes=["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui"]

opts = { 
    'py2exe': {
    'includes':includes,
    'optimize':2,
    'excludes': excludes,
    'dll_excludes': ["mswsock.dll", "powrprof.dll", "KERNELBASE.dll", 
                     "API-MS-Win-Core-LocalRegistry-L1-1-0.dll",
                     "API-MS-Win-Core-ProcessThreads-L1-1-0.dll",
                     "API-MS-Win-Security-Base-L1-1-0.dll"
                     ],
    'skip_archive': True,
    }}

data_files = [
    (".", ["licencia.txt", "wslpg.ini", 
           "wslpg_aut_test.xml", "afip_ca_info.crt",
           "liquidacion_form_c1116b_wslpg.csv",
           "liquidacion_form_c1116b_wslpg.png",
           "liquidacion_wslpg_ajuste_base.csv",
           "liquidacion_wslpg_ajuste_base.png",
           "liquidacion_wslpg_ajuste_debcred.csv",
           "liquidacion_wslpg_ajuste_debcred.png",
          ]),
	("cache", glob.glob("cache/*")),
    ]

import wslpg, wsaa
from nsis import build_installer, Target

setup( 
    name="WSLPG",
    version=wslpg.__version__ + (wslpg.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs WSLPG",
    long_description=wslpg.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [Target(module=wsaa, modules='wsaa'),
                  Target(module=wslpg, modules="wslpg")],
    console=[Target(module=wslpg, script='wslpg.py', dest_base="wslpg_cli"), 
             Target(module=wsaa, script="wsaa.py", dest_base="wsaa-cli")
             ],
    #windows=[Target(module=wsaa, script="wsaa.py", dest_base="wsaa")],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
