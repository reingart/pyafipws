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
import sys

# modulos a compilar:

import pyafipws
import wsaa
import wsfev1, rece1
import wsfexv1, recex1
import wsmtx, recem
import wsctg11
import wslpg
import wscoc
import wscdc
import cot
import trazamed

# parametros para setup:
kwargs = {}

long_desc = ("Interfases, herramientas y aplicativos para Servicios Web"  
             "AFIP (Factura Electrónica, Granos, Aduana, etc.), "
             "ANMAT (Trazabilidad de Medicamentos), "
             "RENPRE (Trazabilidad de Precursores Químicos), "
             "ARBA (Remito Electrónico)")

data_files = [
    (".", ["licencia.txt", "rece.ini.dist", "geotrust.crt", "afip_ca_info.crt", ]),
    ("cache", glob.glob("cache/*")),
    ]


# build a one-click-installer for windows:
if 'py2exe' in sys.argv:
    import py2exe
    from nsis import build_installer, Target

    # includes for py2exe
    includes=['email.generator', 'email.iterators', 'email.message', 'email.utils']

    # optional modules:
    # required modules for shelve support (not detected by py2exe by default):
    for mod in ['socks', 'dbhash', 'gdbm', 'dbm', 'dumbdbm', 'anydbm']:
        try:
            __import__(mod)
            includes.append(mod)
        except ImportError:
            pass 

    # don't pull in all this MFC stuff used by the makepy UI.
    excludes=["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui"]

    # basic options for py2exe
    opts = { 
        'py2exe': {
            'includes': includes,
            'optimize': 2,
            'excludes': excludes,
            'dll_excludes': ["mswsock.dll", "powrprof.dll", "KERNELBASE.dll", 
                         "API-MS-Win-Core-LocalRegistry-L1-1-0.dll",
                         "API-MS-Win-Core-ProcessThreads-L1-1-0.dll",
                         "API-MS-Win-Security-Base-L1-1-0.dll"
                         ],
            'skip_archive': True,
            }
        }

    desc = "Instalador PyAfipWs %s"
    kwargs['com_server'] = []
    kwargs['console'] = []
    kwargs['windows'] = []
    
    # legacy webservices & utilities:
    if 'pyafipws' in globals():
        kwargs['com_server'] += ["pyafipws"]
        kwargs['console'] += ['rece.py', 'receb.py', 'recex.py', 'rg1361.py', 'wsaa.py', 'wsfex.py', 'wsbfe.py']

    # new webservices:
    if 'wsaa' in globals():
        kwargs['com_server'] += [Target(module=wsaa, modules='wsaa', create_exe=not wsaa.TYPELIB, create_dll=not wsaa.TYPELIB)]
        kwargs['console'] += [Target(module=wsaa, script="wsaa.py", dest_base="wsaa-cli")]
        if wsaa.TYPELIB:
            kwargs['windows'] += [Target(module=wsaa, script="wsaa.py", dest_base="wsaa")]
            data_files.append((".", ["wsaa.tlb"]))
            
        __version__ += (wsaa.HOMO and '-homo' or '-full')

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

    if 'wsfexv1' in globals():
        kwargs['com_server'] += [
            Target(module=wsfexv1, modules="wsfexv1", create_exe=True, create_dll=True)
            ]
        kwargs['console'] += [
            Target(module=wsfexv1, script='wsfexv1.py', dest_base="wsfexv1_cli"), 
            Target(module=recex1, script='recex1.py'), 
            ]
    
    if 'wsmtx' in globals():
        kwargs['com_server'] += [
            Target(module=wsmtx, modules="wsmtx", create_exe=True, create_dll=True)
            ]
        kwargs['console'] += [
            Target(module=wsmtx, script='wsmtx.py', dest_base="wsmtx_cli"), 
            Target(module=recem, script='recem.py'), 
            ]             
    
    if 'wsctg11' in globals():
        kwargs['com_server'] += [
            Target(module=wsctg11, modules="wsctg11"), 
            ]
        kwargs['console'] += [
            Target(module=wsctg11, script='wsctg11.py', dest_base="wsctg11_cli"),
            ]

    if 'wslpg' in globals():
        kwargs['com_server'] += [
            Target(module=wslpg, modules="wslpg"),
            ]
        kwargs['console'] += [
            Target(module=wslpg, script='wslpg.py', dest_base="wslpg_cli"),
            ]
        data_files.extend([
           "wslpg.ini", "wslpg_aut_test.xml",
           "liquidacion_form_c1116b_wslpg.csv",
           "liquidacion_form_c1116b_wslpg.png",
           "liquidacion_wslpg_ajuste_base.csv",
           "liquidacion_wslpg_ajuste_base.png",
           "liquidacion_wslpg_ajuste_debcred.csv",
           "liquidacion_wslpg_ajuste_debcred.png",
            ])
    
    if 'wscoc' in globals():
        kwargs['com_server'] += [
            Target(module=wscoc,modules="wscoc"),
            ]
        kwargs['console'] += [
            Target(module=wscoc, script='wscoc.py', dest_base="wscoc_cli"),
            ]

    if 'wscdc' in globals():
        kwargs['com_server'] += [
            Target(module=wscdc,modules="wscdc", create_exe=True, create_dll=True),
            ]
        kwargs['console'] += [
            Target(module=wscdc, script='wscdc.py', dest_base="wscdc_cli"),
            ]

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
        data_files.extend([
            "TB_20111111112_000000_20080124_000001.txt", 
            "TB_20111111112_000000_20080124_000001.xml",
            "TB_20111111112_000000_20101229_000001.txt", 
            "TB_20111111112_000000_20101229_000001.xml",
            ])    

    if 'trazamed' in globals():
        kwargs['com_server'] += [
            Target(module=trazamed, modules="trazamed", create_exe=not trazamed.TYPELIB, create_dll=not trazamed.TYPELIB),
            ]
        kwargs['console'] += [
            Target(module=trazamed, script='trazamed.py', dest_base="trazamed_cli"), 
            ]
        if wsaa.TYPELIB:
            kwargs['windows'] += [Target(module=trazamed, script="trazamed.py", dest_base="trazamed")]
            data_files.append((".", ["trazamed.tlb"]))

    # custom installer:
    kwargs['cmdclass'] = {"py2exe": build_installer}

    if sys.version_info > (2, 7):
        # add MSVCP90.dll path for py2exe
        sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
        data_files.extend([
            ("Microsoft.VC90.CRT", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\mfc*.*')),
            ("Microsoft.VC90.CRT", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\Microsoft.VC90.MFC.manifest')),
        ])

else:
    desc = "Paquete PyAfipWs %s"
    kwargs['package_dir'] = {'pyafipws': '.'}
    kwargs['packages'] = ['pyafipws']
    opts = {}


setup(name="PyAfipWs",
      version=__version__,
      description=desc,
      long_description=long_desc,
      author="Mariano Reingart",
      author_email="reingart@gmail.com",
      url="http://www.sistemasagiles.com.ar",
      license="GNU GPL v3",
      options=opts,
      data_files=data_files,
      **kwargs
      )

