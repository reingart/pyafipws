#!/usr/bin/python
# -*- coding: utf8 -*-

# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs"
from __future__ import print_function
from __future__ import absolute_import

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008-2016 Mariano Reingart"

from distutils.core import setup
import glob
import os
import subprocess
import warnings
import sys

__version__ = "3.10.3028"

HOMO = True

# build a one-click-installer for windows:
import py2exe
from pyafipws.nsis import build_installer, Target

# modulos a compilar y empaquetar (comentar si no se desea incluir):

#import pyafipws
#import pyrece
from pyafipws import wsaa
from pyafipws import wsfev1, rece1, rg3685
#import wsfexv1, recex1
#import wsbfev1, receb1
#import wsmtx, recem
#import wsct, recet
#import wsfecred
#import ws_sr_padron
#from pyafipws import pyfepdf
#import pyemail
#import pyi25
#from pyafipws import pyqr
#import ws_sire
#import wsctg
#import wslpg
#import wsltv
#import wslum
#import wslsp
#import wsremcarne
#import wsremharina
#import wsremazucar
#import wscoc
#import wscdc
#import cot
#import iibb
#import trazamed
#import trazaprodmed
#import trazarenpre
#import trazafito
#import trazavet
#import padron
#import sired

data_files = [
    (".", ["licencia.txt",]),
    ("conf", ["conf/rece.ini", "conf/geotrust.crt", "conf/afip_ca_info.crt", ]),
    ("cache", glob.glob("cache/*")),
    ]

# herramientas opcionales a compilar y empaquetar:
try:
    if 'pyfepdf' in globals() or 'pyrece' in globals():
        import designer     
except ImportError:
    # el script pyfpdf/tools/designer.py no esta disponible:
    print("IMPORTANTE: no se incluye el diseñador de plantillas PDF")

# parametros para setup:
kwargs = {}

# incluyo mis certificados para homologación (si existen)
if os.path.exists("reingart.crt"):
    data_files.append(("conf", ["reingart.crt", "reingart.key"]))
    
if sys.version_info > (2, 7):
    # add "Microsoft Visual C++ 2008 Redistributable Package (x86)"
    if os.path.exists(r"c:\Program Files\Mercurial"):
        data_files += [(
            ".", glob.glob(r'c:\Program Files\Mercurial\msvc*.dll') +
                    glob.glob(r'c:\Program Files\Mercurial\Microsoft.VC90.CRT.manifest'),
            )]
    # fix permission denied runtime error on win32com.client.gencache.GenGeneratePath
    # (expects a __init__.py not pyc, also dicts.dat pickled or _LoadDicts/_SaveDicts will fail too)
    # NOTE: on windows 8.1 64 bits, this is stored in C:\Users\REINGART\AppData\\Local\Temp\gen_py\2.7
    from win32com.client import gencache
    gen_py_path = gencache.GetGeneratePath() or "C:\Python27\lib\site-packages\win32com\gen_py"
    data_files += [(
            r"win32com\gen_py", 
            [os.path.join(gen_py_path, "__init__.py"),
                os.path.join(gen_py_path, "dicts.dat")],
            )]
    
    sys.path.insert(0, r"C:\Python27\Lib\site-packages\pythonwin")
    WX_DLL = (
        ".", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\mfc*.*') +
                glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\Microsoft.VC90.MFC.manifest'),
        )
else:
    WX_DLL = (".", [
        "C:\python25\Lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll",
        "C:\python25\MSVCR71.dll",
        "C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll",
        ])

# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils',  'email.mime.text', 'email.mime.application', 'email.mime.multipart']
if 'pyi25' in globals() or 'pyfepdf' in globals() or 'pyqr' in globals():
    includes.extend(["PIL.Image", "PIL.ImageFont", "PIL.ImageDraw"])

includes.append("dbf")

# cryptography:
includes.append("cffi")

# win32 COM
includes.extend(["win32com.server.policy"])

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
                        "tcl85.dll", "tk85.dll",
                        # Windows 8.1 DLL:
                        "CRYPT32.dll", "WLDAP32.dll",
                        "api-ms-win-core-delayload-l1-1-1.dll",
                        "api-ms-win-core-errorhandling-l1-1-1.dll",
                        "api-ms-win-core-handle-l1-1-0.dll",
                        "api-ms-win-core-heap-l1-2-0.dll",
                        "api-ms-win-core-heap-obsolete-l1-1-0.dll",
                        "api-ms-win-core-libraryloader-l1-2-0.dll",
                        "api-ms-win-core-localization-obsolete-l1-2-0.dll",
                        "api-ms-win-core-processthreads-l1-1-2.dll",
                        "api-ms-win-core-profile-l1-1-0.dll",
                        "api-ms-win-core-registry-l1-1-0.dll",
                        "api-ms-win-core-string-l1-1-0.dll",
                        "api-ms-win-core-string-obsolete-l1-1-0.dll",
                        "api-ms-win-core-synch-l1-2-0.dll",
                        "api-ms-win-core-sysinfo-l1-2-1.dll",
                        "api-ms-win-security-base-l1-2-0.dll",
                        ],
        'skip_archive': True,
        }
    }

desc = "Instalador PyAfipWs"
kwargs['com_server'] = []
kwargs['console'] = []
kwargs['windows'] = []

# add 32bit or 64bit tag to the installer name
import platform



# new webservices:
if 'wsaa' in globals():
    kwargs['windows'] += [Target(module=wsaa, script="wsaa.py", dest_base="wsaa_com")]
    kwargs['console'] += [Target(module=wsaa, script="wsaa.py", dest_base="wsaa")]
    if wsaa.TYPELIB:
        data_files.append(("typelib", ["typelib/wsaa.tlb"]))
        
    HOMO &= wsaa.HOMO

if 'wsfev1' in globals():
    kwargs['windows'] += [Target(module=wsfev1, script="wsfev1.py", dest_base="wsfev1_com")]
    kwargs['console'] += [
        Target(module=wsfev1, script='wsfev1.py', dest_base="wsfev1"),
        Target(module=rece1, script='rece1.py'), 
        #Target(module=rg3685, script='rg3685.py'), 
        ]             
    if wsfev1.TYPELIB:
        data_files.append(("typelib", ["typelib/wsfev1.tlb"]))

    HOMO &= wsfev1.HOMO

if 'wsfexv1' in globals():
    kwargs['com_server'] += [
        Target(module=wsfexv1, modules="wsfexv1", create_exe=True, create_dll=True)
        ]
    kwargs['console'] += [
        Target(module=wsfexv1, script='wsfexv1.py', dest_base="wsfexv1_cli"), 
        Target(module=recex1, script='recex1.py'), 
        ]
    
    HOMO &= wsfexv1.HOMO

if 'wsbfev1' in globals():
    kwargs['com_server'] += [
        Target(module=wsbfev1, modules="wsbfev1", create_exe=True, create_dll=True)
        ]
    kwargs['console'] += [
        Target(module=wsbfev1, script='wsbfev1.py', dest_base="wsbfev1_cli"), 
        Target(module=receb1, script='receb1.py'), 
        ]
    
    HOMO &= wsbfev1.HOMO

if 'wsmtx' in globals():
    kwargs['com_server'] += [
        Target(module=wsmtx, modules="wsmtx", create_exe=True, create_dll=True)
        ]
    kwargs['console'] += [
        Target(module=wsmtx, script='wsmtx.py', dest_base="wsmtx_cli"), 
        Target(module=recem, script='recem.py'), 
        ]             
    
    HOMO &= wsmtx.HOMO

if 'wsct' in globals():
    kwargs['com_server'] += [
        Target(module=wsct, modules="wsct", create_exe=True, create_dll=True)
        ]
    kwargs['console'] += [
        Target(module=wsct, script='wsct.py', dest_base="wsct_cli"), 
        Target(module=recet, script='recet.py'), 
        ]
    
    HOMO &= wsct.HOMO

if 'wsfecred' in globals():
    kwargs['com_server'] += [
        Target(module=wsfecred, modules="wsfecred"),
        ]
    kwargs['console'] += [
        Target(module=wsfecred, script='wsfecred.py', dest_base="wsfecred_cli"),
        ]
    data_files += [
        ]
    
    HOMO &= wsfecred.HOMO

if 'ws_sire' in globals():
    kwargs['com_server'] += [
        Target(module=ws_sire, modules="ws_sire"),
        ]
    kwargs['console'] += [
        Target(module=ws_sire, script='ws_sire.py', dest_base="ws_sire_cli"),
        ]
    data_files += [
        ]
    
    HOMO &= ws_sire.HOMO

if 'pyfepdf' in globals():
    kwargs['com_server'] += [
        Target(module=pyfepdf, modules="pyfepdf", create_exe=True, create_dll=True),
        ]
    kwargs['console'] += [
        Target(module=pyfepdf, script='pyfepdf.py', dest_base="pyfepdf_cli"), 
        ]
    #kwargs['windows'] += [
    #    Target(module=pyfepdf, script="pyfepdf.py", dest_base="pyfepdf_com"),
    #    ]
    data_files += [
        WX_DLL, 
        ("plantillas", ["plantillas/logo.png", "plantillas/afip.png",
                        "plantillas/factura.csv",
                        "plantillas/recibo.csv"]),
        ]
    
    HOMO &= pyfepdf.HOMO

if 'pyemail' in globals():
    kwargs['com_server'] += [
        Target(module=pyemail, modules="pyemail", create_exe=False, create_dll=True),
        ]
    kwargs['console'] += [
        Target(module=pyemail, script='pyemail.py', dest_base="pyemail"),
        ]
    kwargs['windows'] += [
        Target(module=pyemail, script="pyemail.py", dest_base="pyemail_com"),
        ]
    data_files += [
        ]
    

if 'pyi25' in globals():
    kwargs['com_server'] += [
        Target(module=pyi25, modules="pyi25", create_exe=False, create_dll=True),
        ]
    kwargs['console'] += [
        Target(module=pyi25, script='pyi25.py', dest_base="pyi25"),
        ]
    kwargs['windows'] += [
        Target(module=pyi25, script="pyi25.py", dest_base="pyi25_com"),
        ]
    data_files += [
        ]
    

if 'pyqr' in globals():
    kwargs['com_server'] += [
        Target(module=pyqr, modules="pyqr", create_exe=False, create_dll=True),
        ]
    kwargs['console'] += [
        Target(module=pyqr, script='pyqr.py', dest_base="pyqr"),
        ]
    kwargs['windows'] += [
        Target(module=pyqr, script="pyqr.py", dest_base="pyqr_com"),
        ]
    data_files += [
        ]
    
        
if 'wsctg' in globals():
    kwargs['com_server'] += [
        Target(module=wsctg, modules="wsctg"), 
        ]
    kwargs['console'] += [
        Target(module=wsctg, script='wsctg.py', dest_base="wsctg_cli"),
        ]
    
    HOMO &= wsctg.HOMO

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
   
    HOMO &= wslpg.HOMO

if 'wsltv' in globals():
    kwargs['com_server'] += [
        Target(module=wsltv, modules="wsltv"),
        ]
    kwargs['console'] += [
        Target(module=wsltv, script='wsltv.py', dest_base="wsltv_cli"),
        ]
    data_files += [
        ("conf", ["conf/wsltv.ini"]),
        ("plantillas", [ 
            ]),
        ]
   
    HOMO &= wsltv.HOMO

if 'wslum' in globals():
    kwargs['com_server'] += [
        Target(module=wslum, modules="wslum"),
        ]
    kwargs['console'] += [
        Target(module=wslum, script='wslum.py', dest_base="wslum_cli"),
        ]
    data_files += [
        ("conf", ["conf/wslum.ini"]),
        ]
   
    HOMO &= wslum.HOMO

if 'wslsp' in globals():
    kwargs['com_server'] += [
        Target(module=wslsp, modules="wslsp"),
        ]
    kwargs['console'] += [
        Target(module=wslsp, script='wslsp.py', dest_base="wslsp_cli"),
        ]
    data_files += [
        ("conf", ["conf/wslsp.ini"]),
        ]
  
    HOMO &= wslsp.HOMO

if 'wsremcarne' in globals():
    kwargs['com_server'] += [
        Target(module=wsremcarne, modules="wsremcarne"),
        ]
    kwargs['console'] += [
        Target(module=wsremcarne, script='wsremcarne.py', dest_base="wsremcarne_cli"),
        ]
    data_files += [
        ("conf", ["conf/wsremcarne.ini"]),
        ]
   
    HOMO &= wsremcarne.HOMO

if 'wsremharina' in globals():
    kwargs['com_server'] += [
        Target(module=wsremharina, modules="wsremharina"),
        ]
    kwargs['console'] += [
        Target(module=wsremharina, script='wsremharina.py', dest_base="wsremharina_cli"),
        ]
    data_files += [
        ("conf", ["conf/wsremharina.ini"]),
        ]
   
    HOMO &= wsremharina.HOMO

if 'wsremazucar' in globals():
    kwargs['com_server'] += [
        Target(module=wsremazucar, modules="wsremazucar"),
        ]
    kwargs['console'] += [
        Target(module=wsremazucar, script='wsremazucar.py', dest_base="wsremazucar_cli"),
        ]
    data_files += [
        ("conf", ["conf/wsremazucar.ini"]),
        ]
   
    HOMO &= wsremazucar.HOMO

if 'wscoc' in globals():
    kwargs['com_server'] += [
        Target(module=wscoc,modules="wscoc"),
        ]
    kwargs['console'] += [
        Target(module=wscoc, script='wscoc.py', dest_base="wscoc_cli"),
        ]
   
    HOMO &= wscoc.HOMO

if 'wscdc' in globals():
    kwargs['com_server'] += [
        Target(module=wscdc,modules="wscdc", create_exe=True, create_dll=True),
        ]
    kwargs['console'] += [
        Target(module=wscdc, script='wscdc.py', dest_base="wscdc_cli"),
        ]
   
    HOMO &= wscdc.HOMO

if 'ws_sr_padron' in globals():
    kwargs['com_server'] += [
        Target(module=ws_sr_padron,modules="ws_sr_padron", create_exe=True, create_dll=True),
        ]
    kwargs['console'] += [
        Target(module=ws_sr_padron, script='ws_sr_padron.py', dest_base="ws_sr_padron_cli"),
        ]
  
    HOMO &= ws_sr_padron.HOMO

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
        ]), ("conf", ["conf/arba.crt"])]
  
    HOMO &= cot.HOMO

if 'iibb' in globals():
    kwargs['com_server'] += [
        Target(module=iibb,modules="iibb")
        ]
    kwargs['console'] += [
        Target(module=iibb, script='iibb.py', dest_base="iibb_cli")
        ]
    data_files += [("conf", ["conf/arba.crt"])]
  
    HOMO &= iibb.HOMO
    
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
   
    HOMO &= trazamed.HOMO

if 'trazaprodmed' in globals():
    kwargs['com_server'] += [
        Target(module=trazaprodmed, modules="trazaprodmed", create_exe=not trazaprodmed.TYPELIB, create_dll=not trazaprodmed.TYPELIB),
        ]
    kwargs['console'] += [
        Target(module=trazaprodmed, script='trazaprodmed.py', dest_base="trazaprodmed_cli"), 
        ]
   
    HOMO &= trazaprodmed.HOMO

if 'trazarenpre' in globals():
    kwargs['com_server'] += [
        Target(module=trazarenpre, modules="trazarenpre", create_exe=not trazarenpre.TYPELIB, create_dll=not trazarenpre.TYPELIB),
        ]
    kwargs['console'] += [
        Target(module=trazarenpre, script='trazarenpre.py', dest_base="trazarenpre_cli"), 
        ]
    if trazarenpre.TYPELIB:
        kwargs['windows'] += [Target(module=trazarenpre, script="trazarenpre.py", dest_base="trazarenpre")]
        data_files.append((".", ["trazarenpre.tlb"]))
   
    HOMO &= trazarenpre.HOMO

if 'trazafito' in globals():
    kwargs['com_server'] += [
        Target(module=trazafito, modules="trazafito", create_exe=True, create_dll=False),
        ]
    kwargs['console'] += [
        Target(module=trazafito, script='trazafito.py', dest_base="trazafito_cli"), 
        ]
   
    HOMO &= trazafito.HOMO

if 'trazavet' in globals():
    kwargs['com_server'] += [
        Target(module=trazavet, modules="trazavet", create_exe=True, create_dll=False),
        ]
    kwargs['console'] += [
        Target(module=trazavet, script='trazavet.py', dest_base="trazavet_cli"), 
        ]
   
    HOMO &= trazavet.HOMO

if 'padron' in globals():
    kwargs['com_server'] += [
        Target(module=padron, modules="padron", create_exe=True, create_dll=True),
        ]

    kwargs['console'] += [
        Target(module=padron, script='padron.py', dest_base="padron_cli"), 
        ]
    if os.path.exists("padron.db"):
        data_files += [(".", [
            "padron.db", 
            ])]
   
    #HOMO &= padron.HOMO

if 'sired' in globals():
    kwargs['com_server'] += [
        Target(module=sired, modules="sired", create_exe=True, create_dll=True),
        ]
    kwargs['console'] += [
        Target(module=sired, script='sired.py', dest_base="sired_cli"), 
        ]
   

# custom installer:
kwargs['cmdclass'] = {"py2exe": build_installer}

# add certification authorities (newer versions of httplib2)
import httplib2
data_files += [("httplib2",
    [os.path.join(os.path.dirname(httplib2.__file__), "cacerts.txt")])]

# add certification authorities (newer versions of httplib2)
try:
    import certifi
    data_files += [("certifi", [certifi.where()])]
except ImportError:
    pass

# agrego tag de homologación (testing - modo evaluación):


# agrego ejemplos
##if HOMO:
##     data_files += [("ejemplos", glob.glob("ejemplos/*"))]


long_desc = ("Interfases, herramientas y aplicativos para Servicios Web"  
             "AFIP (Factura Electrónica, Granos, Aduana, etc.), "
             "ANMAT (Trazabilidad de Medicamentos), "
             "RENPRE (Trazabilidad de Precursores Químicos), "
             "ARBA (Remito Electrónico)")


setup(name="PyAfipWs",
      version=__version__,
      description=desc,
      long_description=long_desc,
      author="Mariano Reingart",
      author_email="reingart@gmail.com",
      url="http://www.sistemasagiles.com.ar",
      license="GNU GPL v3+",
      options=opts,
      data_files=data_files,
            classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Intended Audience :: End Users/Desktop",
            "Intended Audience :: Financial and Insurance Industry",
            "License :: OSI Approved :: GNU Lesser General Public License v3 (GPLv3)",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.9",
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

