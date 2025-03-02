import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ['PYTHONPATH'] = os.path.abspath(os.path.dirname(__file__))
import win32com.server.register
import pyqr

win32com.server.register.UseCommandLine(pyqr.PyQR)



