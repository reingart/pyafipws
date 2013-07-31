pyafipws
========

PyAfipWs contains Python modules to operate with web services regarding AFIP (Argentina's "IRS") and other government agencies, mainly related to electronic invoicing, several taxes and traceability.

Copyright 2008 - 2013 (C) Mariano Reingart [reingart@gmail.com](mailto:reingart@gmail.com) (creator and maintainter). All rights reserved.

License: GPLv3+, with "commercial" exception available to include it and distribute with propietary programs

General Information:
--------------------

 * Main Project Site: https://code.google.com/p/pyafipws/ (mercurial repository)
 * Mirror: https://github.com/reingart/pyafipws (git repository)
 * User Manual: (http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs (Spanish)
 * Commercial Support: http://www.sistemasagiles.com.ar/ (Spanish)
 * Community Site: http://www.pyafipws.com.ar/ (Spanish)
 * Public Forum: http://groups.google.com/group/pyafipws

More information at [Python Argentina Magazine article](http://revista.python.org.ar/2/en/html/pyafip.html) (English) 
and [JAIIO 2012 paper](http://www.41jaiio.org.ar/sites/default/files/15_JSL_2012.pdf) (Spanish)

Project Structure:
------------------

 * Python library (a helper class for each webservice for easy use of their methods and attributes)
 * Windows COM interface compatible with legacy programming languages (VB, VFP, Delphi, PHP, VB.NET, etc.)
 * DLL/.so compiled shared library (exposing python methods to C/C++/C#) 
 * Command line (console) tools using simplified input & ouput files 
 * GUI and WEB apps as complete reference implementations
 * Examples for Visual Basic, Visual Fox Pro, Delphi, C, PHP. 
 * Minor code fragment samples for SAP (ABAP), PowerBuilder, Fujitsu Net Cobol, Clarion, etc.
 * OpenERP module (comming soon)
 
Features implemented:
---------------------

 * Supported alternate interchange formats: TXT (fixed lenght COBOL-like), CSV, DBF (Clipper/xBase/Harbour), XML, JSON, etc.
 * Full automation to request authentication and invoice authorization (CAE, COE, etc.)
 * Advanced XML manipulation, caching and proxy support.
 * Customizable PDF generation and visual designer (CSV templates)
 * Email, barcodes (PIL), installation (NSIS), configuration (.INI), debugging and other misc utilities

Web services supported so far:
------------------------------

 * WSAA: authorization & authentication, including digital cryptographic signature
 * WSFE and [WSFEv1](https://code.google.com/p/pyafipws/wiki/WSFEv1): domestic market (electronic invoice)
 * WSBFE: tax bonus (electronic invoice)
 * [WSFEX](https://code.google.com/p/pyafipws/wiki/WSFEX) and WSFEXv1: foreign trade (electronic invoice)
 * WSCTG: agriculture (grain traceability code)
 * WSLPG: agriculture (grain liquidation - invoice)
 * wDigDepFiel: customs (faithful depositary)
 * WSCOC: currency exchange operations autorization
 * COT ARBA: Provincial Operation Transport Code (aka electronic Shipping note)
 * TrazaMed ANMAT: National Medical Drug Traceability Program
 * Traza Renpre SEDRONAR: Controlled Chemical Precursors Traceability Program (comming soon)

Installation Instructions:
--------------------------

On Ubuntu (GNU/Linux), you will need to install the following dependencies:

httplib2 and openssl binding:

    apt-get install python-httplib2 python-m2crypto

For SOAP webservices you will need [PySimpleSOAP](https://code.google.com/p/pysimplesoap/) (spin-off of this library, inspired by the PHP SOAP extension):

    hg clone https://code.google.com/p/pysimplesoap/ 
    cd pysimplesoap
    hg update reingart
    sudo python setup.py install
    
For PDF generation, you will need the [PyFPDF](https://code.google.com/p/pyfpdf) (PHP's FPDF library, python port):

    hg clone https://code.google.com/p/pyfpdf/ 
    cd pyfpdf
    sudo python setup.py install

For the GUI app, you will need [wxPython](http://www.wxpython.org/):

    sudo apt-get install wxpython

PythonCard is being replaced by [gui2py](https://code.google.com/p/gui2py/):

    hg clone https://code.google.com/p/gui2py/ 
    cd gui2py
    sudo python setup.py install

For the WEB app, you will need [web2py](http://www.web2py.com/).

On Windows, you can see available installers released for evaluation purposes on [Downloads](https://code.google.com/p/pyafipws/downloads)
