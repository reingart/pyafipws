#!/usr/bin/python
# -*- coding: latin-1 -*-

# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"

from distutils.core import setup
import sys

if 'py2exe' in sys.argv:
    import py2exe

from __init__ import __version__

# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils']

opts = { 
    'py2exe': {
    'includes': includes,
    'optimize': 2}
    }

kwargs = {}

long_desc = ("Interfases, herramientas y aplicativos para Servicios Web"  
             "AFIP (Factura Electrónica, Granos, Aduana, etc.), "
             "ANMAT (Trazabilidad de Medicamentos), "
             "RENPRE (Trazabilidad de Precursores Químicos), "
             "ARBA (Remito Electrónico)")

if 'py2exe' in sys.argv:
    desc = "Instalador PyAfipWs %s"
    kwargs['com_server'] = ["pyafipws"]
    kwargs['console'] = ['rece.py', 'receb.py', 'recex.py', 'rg1361.py', 'wsaa.py', 'wsfex.py', 'wsbfe.py']
else:
    desc = "Paquete PyAfipWs %s"
    kwargs['package_dir'] = {'pyafipws': '.'}
    kwargs['packages'] = ['pyafipws']


setup(name="PyAfipWs",
      version=__version__,
      description=desc,
      long_description=long_desc,
      author="Mariano Reingart",
      author_email="reingart@gmail.com",
      url="http://www.sistemasagiles.com.ar",
      license="GNU GPL v3",
      options=opts,
      **kwargs
      )

