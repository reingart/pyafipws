#!/usr/bin/python
# -*- coding: latin-1 -*-

# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008-2013 Mariano Reingart"

from __init__ import __version__

from distutils.core import setup
import glob
import os
import sys

# modulos a compilar y empaquetar (comentar si no se desea incluir):

import pyafipws
import pyrece
import wsaa
import wsfev1, rece1
import wsfexv1, recex1
import wsbfev1, receb1
import wsmtx, recem
import pyfepdf, pyemail, pyi25
import wsctg11
import wslpg
import wscoc
import wscdc
import cot
import trazamed
import trazarenpre

# herramientas opcionales a compilar y empaquetar:
try:
    import designer     
except ImportError:
    # el script pyfpdf/tools/designer.py no esta disponible:
    print "IMPORTANTE: no se incluye el diseñador de plantillas PDF"

# parametros para setup:
kwargs = {}

long_desc = ("Interfases, herramientas y aplicativos para Servicios Web"  
             "AFIP (Factura Electrónica, Granos, Aduana, etc.), "
             "ANMAT (Trazabilidad de Medicamentos), "
             "RENPRE (Trazabilidad de Precursores Químicos), "
             "ARBA (Remito Electrónico)")

data_files = [
    (".", ["licencia.txt",]),
    ("conf", ["conf/rece.ini", "conf/geotrust.crt", "conf/afip_ca_info.crt", ]),
    ("cache", glob.glob("cache/*")),
    ]


# build a one-click-installer for windows:
if 'py2exe' in sys.argv:
    import py2exe
    from nsis import build_installer, Target

    # includes for py2exe
    includes=['email.generator', 'email.iterators', 'email.message', 'email.utils',  'email.mime.text', 'email.mime.application', 'email.mime.multipart']

    # optional modules:
    # required modules for shelve support (not detected by py2exe by default):
    for mod in ['socks', 'dbhash', 'gdbm', 'dbm', 'dumbdbm', 'anydbm']:
        try:
            __import__(mod)
            includes.append(mod)
        except ImportError:
            pass 

    # don't pull in all this MFC stuff used by the makepy UI.
    excludes=["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui",
              "Tkconstants","Tkinter","tcl",
              "_imagingtk", "PIL._imagingtk", "ImageTk", "PIL.ImageTk", "FixTk",
             ]

    # basic options for py2exe
    opts = { 
        'py2exe': {
            'includes': includes,
            'optimize': 0,
            'excludes': excludes,
            'dll_excludes': ["mswsock.dll", "powrprof.dll", "KERNELBASE.dll", 
                         "API-MS-Win-Core-LocalRegistry-L1-1-0.dll",
                         "API-MS-Win-Core-ProcessThreads-L1-1-0.dll",
                         "API-MS-Win-Security-Base-L1-1-0.dll"
                         ],
            'skip_archive': True,
            }
        }

    desc = "Instalador PyAfipWs"
    kwargs['com_server'] = []
    kwargs['console'] = []
    kwargs['windows'] = []
    
    # legacy webservices & utilities:
    if 'pyafipws' in globals():
        kwargs['com_server'] += ["pyafipws"]
        kwargs['console'] += ['rece.py', 'receb.py', 'recex.py', 'rg1361.py', 'wsaa.py', 'wsfex.py', 'wsbfe.py']

    # visual application
    if 'pyrece' in globals():
        # find pythoncard resources, to add as 'data_files'
        pycard_resources=[]
        for filename in os.listdir('.'):
            if filename.find('.rsrc.')>-1:
                pycard_resources+=[filename]

        kwargs['console'] += [
            Target(module=pyrece, script="pyrece.py", dest_base="pyrece_consola"),
            ]
        kwargs['windows'] += [
            Target(module=pyrece, script='pyrece.py'),
            ]
        data_files += [
            (".", [
            "C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll",
            "C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll",
            ]), 
            ("plantillas", ["plantillas/logo.png", ]),
            ("datos", ["datos/facturas.csv", "datos/facturas.json", "datos/facturas.txt", ])
            ]
        data_files.append((".", pycard_resources))


    # new webservices:
    if 'wsaa' in globals():
        kwargs['com_server'] += [Target(module=wsaa, modules='wsaa', create_exe=not wsaa.TYPELIB, create_dll=not wsaa.TYPELIB)]
        kwargs['console'] += [Target(module=wsaa, script="wsaa.py", dest_base="wsaa-cli")]
        if wsaa.TYPELIB:
            kwargs['windows'] += [Target(module=wsaa, script="wsaa.py", dest_base="wsaa")]
            data_files.append((".", ["wsaa.tlb"]))
            
        __version__ += (wsaa.HOMO and '-homo' or '-full')
        __version__ += "+wsaa"

    if 'wsfev1' in globals():
        kwargs['com_server'] += [
            Target(module=wsfev1, modules="wsfev1", create_exe=not wsfev1.TYPELIB, create_dll=not wsfev1.TYPELIB)
            ]
        kwargs['console'] += [
            Target(module=wsfev1, script='wsfev1.py', dest_base="wsfev1_cli"), 
            Target(module=rece1, script='rece1.py'), 
            ]             
        if wsfev1.TYPELIB:
            kwargs['windows'] += [Target(module=wsaa, script="wsfev1.py", dest_base="wsfev1")]
            data_files.append((".", ["wsfev1.tlb"]))
        __version__ += "+wsfev1"

    if 'wsfexv1' in globals():
        kwargs['com_server'] += [
            Target(module=wsfexv1, modules="wsfexv1", create_exe=True, create_dll=True)
            ]
        kwargs['console'] += [
            Target(module=wsfexv1, script='wsfexv1.py', dest_base="wsfexv1_cli"), 
            Target(module=recex1, script='recex1.py'), 
            ]
        __version__ += "+wsfexv1"

    if 'wsbfev1' in globals():
        kwargs['com_server'] += [
            Target(module=wsfexv1, modules="wsbfev1", create_exe=True, create_dll=True)
            ]
        kwargs['console'] += [
            Target(module=wsbfev1, script='wsbfev1.py', dest_base="wsbfev1_cli"), 
            Target(module=receb1, script='receb1.py'), 
            ]
        __version__ += "+wsfexv1"
    
    if 'wsmtx' in globals():
        kwargs['com_server'] += [
            Target(module=wsmtx, modules="wsmtx", create_exe=True, create_dll=True)
            ]
        kwargs['console'] += [
            Target(module=wsmtx, script='wsmtx.py', dest_base="wsmtx_cli"), 
            Target(module=recem, script='recem.py'), 
            ]             
        __version__ += "+wsmtx"

    if 'pyfepdf' in globals():
        kwargs['com_server'] += [
            Target(module=pyfepdf, modules="pyfepdf", create_exe=False, create_dll=True),
            Target(module=pyemail, modules="pyemail", create_exe=False, create_dll=True),
            Target(module=pyi25, modules="pyi25", create_exe=False, create_dll=True),
            ]
        kwargs['console'] += [
            Target(module=pyfepdf, script='pyfepdf.py', dest_base="pyfepdf"), 
            Target(module=pyemail, script='pyemail.py', dest_base="pyemail"),
            Target(module=pyi25, script='pyi25.py', dest_base="pyi25"),
            ]
        kwargs['windows'] += [
            Target(module=pyfepdf, script="pyfepdf.py", dest_base="pyfepdf_com"),
            Target(module=pyemail, script="pyemail.py", dest_base="pyemail_com"),
            Target(module=pyi25, script="pyi25.py", dest_base="pyi25_com"),
            ]
        data_files += [
            ("plantillas", ["plantillas/factura.csv", 'plantillas/fpdf.png']),
            ]
        __version__ += "+pyfepdf"

    if 'designer' in globals():
        kwargs['windows'] += [
            Target(module=designer, script="designer.py", dest_base="designer"),
            ]
            
    if 'wsctg11' in globals():
        kwargs['com_server'] += [
            Target(module=wsctg11, modules="wsctg11"), 
            ]
        kwargs['console'] += [
            Target(module=wsctg11, script='wsctg11.py', dest_base="wsctg11_cli"),
            ]
        __version__ += "+wsctg11"

    if 'wslpg' in globals():
        kwargs['com_server'] += [
            Target(module=wslpg, modules="wslpg"),
            ]
        kwargs['console'] += [
            Target(module=wslpg, script='wslpg.py', dest_base="wslpg_cli"),
            ]
        data_files += [
            ("conf", ["conf/wslpg.ini"]),
            ("plantillas", [ 
               "plantillas/liquidacion_form_c1116b_wslpg.csv",
               "plantillas/liquidacion_form_c1116b_wslpg.png",
               "plantillas/liquidacion_wslpg_ajuste_base.csv",
               "plantillas/liquidacion_wslpg_ajuste_base.png",
               "plantillas/liquidacion_wslpg_ajuste_debcred.csv",
               "plantillas/liquidacion_wslpg_ajuste_debcred.png",
                ]),
            ]
        __version__ += "+wslpg"
    
    if 'wscoc' in globals():
        kwargs['com_server'] += [
            Target(module=wscoc,modules="wscoc"),
            ]
        kwargs['console'] += [
            Target(module=wscoc, script='wscoc.py', dest_base="wscoc_cli"),
            ]
        __version__ += "+wscoc"

    if 'wscdc' in globals():
        kwargs['com_server'] += [
            Target(module=wscdc,modules="wscdc", create_exe=True, create_dll=True),
            ]
        kwargs['console'] += [
            Target(module=wscdc, script='wscdc.py', dest_base="wscdc_cli"),
            ]
        __version__ += "+wscdc"

    if 'cot' in globals():
        kwargs['com_server'] += [
            Target(module=cot,modules="cot")
            ]
        kwargs['console'] += [
            Target(module=cot, script='cot.py', dest_base="cot_cli")
            ]
        kwargs['windows'] += [
            Target(module=cot, script='cot.pyw', dest_base="cot_win"), 
            ]
        data_files += [("datos", [
            "datos/TB_20111111112_000000_20080124_000001.txt", 
            "datos/TB_20111111112_000000_20080124_000001.xml",
            "datos/TB_20111111112_000000_20101229_000001.txt", 
            "datos/TB_20111111112_000000_20101229_000001.xml",
            ])]
        __version__ += "+cot"

    if 'trazamed' in globals():
        kwargs['com_server'] += [
            Target(module=trazamed, modules="trazamed", create_exe=not trazamed.TYPELIB, create_dll=not trazamed.TYPELIB),
            ]
        kwargs['console'] += [
            Target(module=trazamed, script='trazamed.py', dest_base="trazamed_cli"), 
            ]
        if trazamed.TYPELIB:
            kwargs['windows'] += [Target(module=trazamed, script="trazamed.py", dest_base="trazamed")]
            data_files.append((".", ["trazamed.tlb"]))
        __version__ += "+trazamed"

    if 'trazarenpre' in globals():
        kwargs['com_server'] += [
            Target(module=trazamed, modules="trazarenpre", create_exe=not trazarenpre.TYPELIB, create_dll=not trazarenpre.TYPELIB),
            ]
        kwargs['console'] += [
            Target(module=trazarenpre, script='trazarenpre.py', dest_base="trazarenpre_cli"), 
            ]
        if trazarenpre.TYPELIB:
            kwargs['windows'] += [Target(module=trazarenpre, script="trazarenpre.py", dest_base="trazarenpre")]
            data_files.append((".", ["trazarenpre.tlb"]))
        __version__ += "+trazarenpre"

    # custom installer:
    kwargs['cmdclass'] = {"py2exe": build_installer}

    if sys.version_info > (2, 7):
        # add MSVCP90.dll path for py2exe
        sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
        data_files += [
            ("Microsoft.VC90.CRT", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\mfc*.*')),
            ("Microsoft.VC90.CRT", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\Microsoft.VC90.MFC.manifest')),
            ]

else:
    desc = "Paquete PyAfipWs"
    kwargs['package_dir'] = {'pyafipws': '.'}
    kwargs['packages'] = ['pyafipws']
    opts = {}


setup(name="PyAfipWs",
      version=__version__,
      description=desc,
      long_description=long_desc,
      author="Mariano Reingart",
      author_email="reingart@gmail.com",
      url="https://code.google.com/p/pyafipws/" if 'register' in sys.argv 
          else "http://www.sistemasagiles.com.ar",
      license="GNU GPL v3",
      options=opts,
      data_files=data_files,
            classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Intended Audience :: End Users/Desktop",
            "Intended Audience :: Financial and Insurance Industry",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            #"Programming Language :: Python :: 3.2",
            "Operating System :: OS Independent",
            "Operating System :: Microsoft :: Windows",
            "Natural Language :: Spanish",
            "Topic :: Office/Business :: Financial :: Point-Of-Sale",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Software Development :: Object Brokering",
      ],
      keywords="webservice electronic invoice pdf traceability",
      **kwargs
      )

