pyafipws
========

PyAfipWs contains Python modules to operate with web services regarding AFIP (Argentina's "IRS") and other government agencies, mainly related to electronic invoicing, several taxes and traceability.

Copyright 2008 - 2015 (C) Mariano Reingart [reingart@gmail.com](mailto:reingart@gmail.com) (creator and maintainter). All rights reserved.

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

 * [Python library][1] (a helper class for each webservice for easy use of their methods and attributes)
 * [PyAfipWs][7]: [OCX-like][2] Windows COM interface compatible with legacy programming languages (VB, VFP, Delphi, PHP, VB.NET, etc.)
 * [LibPyAfipWs][8]: [DLL/.so][3] compiled shared library (exposing python methods to C/C++/C#) 
 * [Console][4] (command line) tools using simplified input & ouput files 
 * [PyRece][5] GUI and [FacturaLibre][6] WEB apps as complete reference implementations
 * Examples for Visual Basic, Visual Fox Pro, Delphi, C, PHP. 
 * Minor code fragment samples for SAP (ABAP), PowerBuilder, Fujitsu Net Cobol, Clarion, etc.
 * Modules for [OpenERP][27] - [Tryton][28]
 
Features implemented:
---------------------

 * Supported alternate interchange formats: TXT (fixed lenght COBOL), CSV, DBF (Clipper/xBase/Harbour), XML, JSON, etc.
 * Full automation to request authentication and invoice authorization (CAE, COE, etc.)
 * Advanced XML manipulation, caching and proxy support.
 * Customizable PDF generation and visual designer (CSV templates)
 * Email, barcodes (PIL), installation (NSIS), configuration (.INI), debugging and other misc utilities

Web services supported so far:
------------------------------

AFIP:

 * [WSAA][10]: authorization & authentication, including digital cryptographic signature
 * [WSFEv1][11]: domestic market (electronic invoice) -[English][12]-
 * [WSMTXCA][22]: domestic market (electronic invoice) -detailing articles and barcodes-
 * [WSBFEv1][13]: tax bonus (electronic invoice)
 * [WSFEXv1][14]: foreign trade (electronic invoice) -[English][15]-
 * [WSCTG][16]: agriculture (grain traceability code)
 * [WSLPG][17]: agriculture (grain liquidation - invoice)
 * [wDigDepFiel][18]: customs (faithful depositary)
 * [WSCOC][19]: currency exchange operations autorization
 * [WSCDC][22]: invoice verification
 * [Taxpayers' Registe][26]: database to check sellers and buyers register

ARBA:

 * [COT][20]: Provincial Operation Transport Code (aka electronic Shipping note)

ANMAT/SEDRONAR/SENASA (SNT):

 * [TrazaMed][21]: National Medical Drug Traceability Program
 * [TrazaRenpre][24]: Controlled Chemical Precursors Traceability Program
 * [TrazaFito][25]: Phytosanitary Products Traceability Program

Installation Instructions:
--------------------------

## Quick-Start

On Ubuntu (GNU/Linux), you will need to install httplib2 and openssl binding.
Then you can download the compressed file, unzip it and use:

```
   sudo apt-get install python-httplib2 python-m2crypto
   wget https://pyafipws.googlecode.com/archive/default.zip
   unzip default.zip
   cd pyafipws-default
   sudo pip install -r requirements.txt
```

**Note:** M2Crypto is optional, the library will use OpenSSL directly (using
subprocess)

## Virtual environment (testing):

The following commands clone the repository, creates a virtualenv and install
the packages there (including the latest versions of the dependencies) to avoid
conflicts with other libraries:
```
   sudo apt-get install python-dev swig python-virtualenv mercurial python-pip libssl-dev
   hg clone https://code.google.com/p/pyafipws
   cd pyafipws
   virtualenv venv
   source venv/bin/activate
   pip install -r requirements.txt
```

## Dependency installation (development):

For SOAP webservices [PySimpleSOAP](https://code.google.com/p/pysimplesoap/) is
needed (spin-off of this library, inspired by the PHP SOAP extension):
```
    hg clone https://code.google.com/p/pysimplesoap/ 
    cd pysimplesoap
    hg update reingart
    sudo python setup.py install
``` 
For PDF generation, you will need the [PyFPDF](https://code.google.com/p/pyfpdf)
(PHP's FPDF library, python port):
```
    hg clone https://code.google.com/p/pyfpdf/ 
    cd pyfpdf
    sudo python setup.py install
```
For the GUI app, you will need [wxPython](http://www.wxpython.org/):
```
    sudo apt-get install wxpython
```
PythonCard is being replaced by [gui2py](https://code.google.com/p/gui2py/):
```
    hg clone https://code.google.com/p/gui2py/ 
    cd gui2py
    sudo python setup.py install
```
For the WEB app, you will need [web2py](http://www.web2py.com/).

On Windows, you can see available installers released for evaluation purposes on
[Downloads](https://code.google.com/p/pyafipws/downloads)

For more information see the source code installation steps in the 
[wiki](https://code.google.com/p/pyafipws/wiki/InstalacionCodigoFuente)


 [1]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaPython
 [2]: http://www.sistemasagiles.com.ar/trac/wiki/OcxFacturaElectronica
 [3]: http://www.sistemasagiles.com.ar/trac/wiki/DllFacturaElectronica
 [4]: http://www.sistemasagiles.com.ar/trac/wiki/HerramientaFacturaElectronica
 [5]: http://www.sistemasagiles.com.ar/trac/wiki/PyRece
 [6]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaLibre
 [7]: http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
 [8]: http://www.sistemasagiles.com.ar/trac/wiki/LibPyAfipWs
 [10]: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#ServicioWebdeAutenticaciónyAutorizaciónWSAA
 [11]: http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1
 [12]: https://code.google.com/p/pyafipws/wiki/WSFEv1
 [13]: http://www.sistemasagiles.com.ar/trac/wiki/BonosFiscales
 [14]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaExportacion
 [15]: https://code.google.com/p/pyafipws/wiki/WSFEX
 [16]: http://www.sistemasagiles.com.ar/trac/wiki/CodigoTrazabilidadGranos
 [17]: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
 [18]: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#wDigDepFiel:DepositarioFiel
 [19]: http://www.sistemasagiles.com.ar/trac/wiki/ConsultaOperacionesCambiarias
 [20]: http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCotArba
 [21]: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadMedicamentos
 [22]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaMTXCAService
 [23]: http://www.sistemasagiles.com.ar/trac/wiki/ConstatacionComprobantes
 [24]: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadPrecursoresQuimicos
 [25]: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosFitosanitarios
 [26]: http://www.sistemasagiles.com.ar/trac/wiki/PadronContribuyentesAFIP
 [27]: https://github.com/reingart/openerp_pyafipws
 [28]: https://github.com/tryton-ar/account_invoice_ar
 
