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

# parametros para setup:
kwargs = {}

long_desc = ("Interfases, herramientas y aplicativos para Servicios Web"  
             "AFIP (Factura Electrónica, Granos, Aduana, etc.), "
             "ANMAT (Trazabilidad de Medicamentos), "
             "RENPRE (Trazabilidad de Precursores Químicos), "
             "ARBA (Remito Electrónico)")

data_files = [
    (".", ["licencia.txt", "geotrust.crt"]),
    ("cache", glob.glob("cache/*")),
    ]


# build a one-click-installer for windows:
if 'py2exe' in sys.argv:
    import py2exe
    from nsis import build_installer, Target

    # includes for py2exe
    includes=['email.generator', 'email.iterators', 'email.message', 'email.utils']

    # optional modules:
    for mod in ['socks']:
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
    
    # legacy webservices & utilities:
    if 'pyafipws' in globals():
        kwargs['com_server'] += ["pyafipws"]
        kwargs['console'] += ['rece.py', 'receb.py', 'recex.py', 'rg1361.py', 'wsaa.py', 'wsfex.py', 'wsbfe.py']

    # new webservices:
    if 'wsaa' in globals():
        kwargs['com_server'] += [Target(module=wsaa, modules='wsaa', create_exe=True, create_dll=True)]
        kwargs['console'] += [Target(module=wsaa, script="wsaa.py", dest_base="wsaa-cli")]
        if wsaa.TYPELIB:
            data_files.append((".", ["wsaa.tlb"]))
        __version__ += (wsaa.HOMO and '-homo' or '-full')

    if 'wsfev1' in globals():
        kwargs['com_server'] += [
            Target(module=wsfev1,modules="wsfev1", create_exe=True, create_dll=not wsfev1.TYPELIB)
            ]
        kwargs['console'] += [
            Target(module=wsfev1, script='wsfev1.py', dest_base="wsfev1_cli"), 
            Target(module=rece1, script='rece1.py'), 
            ]             
        if wsfev1.TYPELIB:
            data_files.append((".", ["wsfev1.tlb"]))
    
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

