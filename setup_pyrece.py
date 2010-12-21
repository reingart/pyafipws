# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"""
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005/04/05 18:44:54 $"
"""
__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
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

setup( name = "PyRece",
       data_files = [ (".", pycard_resources),
                      (".",["logo.png",]) ],
       options=opts,
       **{buildstyle: ["pyrece.py"]}
       )