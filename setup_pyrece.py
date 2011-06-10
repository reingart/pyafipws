# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"""
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005/04/05 18:44:54 $"
"""
__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"

from distutils.core import setup
import py2exe
import sys

if sys.platform == 'darwin':
    import py2app
    buildstyle = 'app'
else:
    import py2exe
    buildstyle = 'windows'

# find pythoncard resources, to add as 'data_files'
import os
pycard_resources=[]
for filename in os.listdir('.'):
    if filename.find('.rsrc.')>-1:
        pycard_resources+=[filename]

# includes for py2exe
includes=[]
for comp in ['button','image','staticbox','radiogroup', 'imagebutton',
            'statictext','textarea','textfield','passwordfield', 'checkbox',
             'tree','multicolumnlist','list','gauge','choice',
            ]:
    includes += ['PythonCard.components.'+comp]
print 'includes',includes

includes+=['email.generator', 'email.iterators', 'email.message', 'email.utils']

opts = { 
    'py2exe': {
    'includes':includes,
    'optimize':2}
    }

import pyrece, pyfpdf_hg.designer
from nsis import build_installer, Target

import glob
data_files = [
    (".", ["wsfev1_wsdl.xml","wsfev1_wsdl_homo.xml", "licencia.txt",
            "C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll",
            "C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll",
            "logo.png", 
            "rece.ini.dist", "factura.csv", 
            "facturas.csv", "facturas.json", "facturas.txt", "entrada.txt"]),
    ("cache", glob.glob("cache/*")),
    ]


setup( name = "PyRece",
       version=pyrece.__version__ + (pyrece.HOMO and '-homo' or '-full'),
       description="PyRece %s" % pyrece.__version__,
       long_description=pyrece.__doc__,
       author="Mariano Reingart",
       author_email="reingart@gmail.com",
       url="http://www.sistemasagiles.com.ar",
       license="GNU GPL v3",
       data_files = [ (".", pycard_resources),
                      (".",["logo.png",]) ] + data_files,
       options=opts,
       cmdclass = {"py2exe": build_installer},
       **{buildstyle: [Target(module=pyrece, script='pyrece.py'),
                       Target(module=pyfpdf_hg.designer, script='pyfpdf_hg/designer.py')],
          'console': [Target(module=pyrece, script="pyrece.py", dest_base="pyrece_consola")]
        }
       )

