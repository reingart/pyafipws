#!/usr/bin/python
# -*- coding: latin-1 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Py2Exe extension to build NSIS Installers"

# Based on py2exe/samples/extending/setup.py:
#   "A setup script showing how to extend py2exe."
#   Copyright (c) 2000-2008 Thomas Heller, Mark Hammond, Jimmy Retzlaff

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import sys
from py2exe.build_exe import py2exe


nsi_base_script = r"""\
; base.nsi

; WARNING: This script has been created by py2exe. Changes to this script
; will be overwritten the next time py2exe is run!

XPStyle on

Page license
Page directory
;Page components
Page instfiles

RequestExecutionLevel admin

LoadLanguageFile "${NSISDIR}\Contrib\Language files\English.nlf"
LoadLanguageFile "${NSISDIR}\Contrib\Language files\Spanish.nlf"

# set license page
LicenseText ""
LicenseData "licencia.txt"
LicenseForceSelection checkbox

; use the default string for the directory page.
DirText ""

Name "%(description)s"
OutFile "%(out_file)s"
;SetCompress off ; disable compression (testing)
SetCompressor /SOLID lzma
;InstallDir %(install_dir)s
InstallDir $PROGRAMFILES\%(install_dir)s

InstallDirRegKey HKLM "Software\%(reg_key)s" "Install_Dir"

VIProductVersion "%(product_version)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "%(name)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "%(description)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "%(company_name)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "%(product_version)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "%(copyright)s"
;VIAddVersionKey /LANG=${LANG_ENGLISH} "InternalName" "FileSetup.exe"

Section %(name)s
    ; uninstall old version

    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "UninstallString"
    StrCmp $R0 "" notistalled
    ExecWait '$R0 /S _?=$INSTDIR' 

notistalled:

    SectionIn RO
    SetOutPath $INSTDIR
    File /r dist\*.*
    IfFileExists $INSTDIR\\rece.ini.dist 0 +3
        IfFileExists $INSTDIR\\rece.ini +2 0
        CopyFiles $INSTDIR\\rece.ini.dist $INSTDIR\\rece.ini
    WriteRegStr HKLM SOFTWARE\%(reg_key)s "Install_Dir" "$INSTDIR"
    ; Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "DisplayName" "%(description)s (solo eliminar)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "UninstallString" "$INSTDIR\Uninst.exe"
    WriteUninstaller "Uninst.exe"
    ;To Register a DLL
    %(register_com_servers)s
    IfFileExists $INSTDIR\\pyrece.exe 0 +3
        ;create start-menu items
        CreateDirectory "$SMPROGRAMS\%(name)s"
        CreateShortCut "$SMPROGRAMS\%(name)s\PyRece.lnk" "$INSTDIR\pyrece.exe" "" "$INSTDIR\pyrece.exe" 0
        CreateShortCut "$SMPROGRAMS\%(name)s\Designer.lnk" "$INSTDIR\designer.exe" "" "$INSTDIR\designer.exe" 0
        ;CreateShortCut "$SMPROGRAMS\%(name)s\Uninstall.lnk" "$INSTDIR\Uninst.exe" "" "$INSTDIR\Uninst.exe" 0
  
SectionEnd

Section "Uninstall"
    ;To Unregister a DLL
    %(unregister_com_servers)s
    ;Delete Files

    ;Delete Uninstaller And Unistall Registry Entries
    Delete "$INSTDIR\Uninst.exe"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\%(reg_key)s"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s"
    RMDir "$INSTDIR"

SectionEnd

;--------------------------------

Function .onInit

    IfSilent nolangdialog

    ;Language selection dialog

    Push ""
    Push ${LANG_ENGLISH}
    Push English
    Push ${LANG_SPANISH}
    Push Spanish
    Push A ; A means auto count languages
           ; for the auto count to work the first empty push (Push "") must remain
    LangDLL::LangDialog "Installer Language" "Please select the language of the installer"

    Pop $LANGUAGE
    StrCmp $LANGUAGE "cancel" 0 +2
        Abort
        
nolangdialog:
        
FunctionEnd

"""

register_com_server = """\
    RegDLL "$INSTDIR\%s"
"""
unregister_com_server= """\
    UnRegDLL "$INSTDIR\%s"
"""

class build_installer(py2exe):
    # This class first builds the exe file(s), then creates a Windows installer.
    # You need NSIS (Nullsoft Scriptable Install System) for it.
    def run(self):
        # Clean up
        os.system("del /S /Q dist")
        # First, let py2exe do it's work.
        py2exe.run(self)

        lib_dir = self.lib_dir
        dist_dir = self.dist_dir
        comserver_files = self.comserver_files
        metadata = self.distribution.metadata

        # create the Installer, using the files py2exe has created.
        script = NSISScript(metadata,
                            lib_dir,
                            dist_dir,
                            self.windows_exe_files,
                            self.lib_files,
                            comserver_files)
        print "*** creating the nsis script***"
        script.create()
        print "*** compiling the nsis script***"
        script.compile()
        # Note: By default the final setup.exe will be in an Output subdirectory.
 

class NSISScript:
    def __init__(self,
                 metadata,
                 lib_dir,
                 dist_dir,
                 windows_exe_files = [],
                 lib_files = [],
                 comserver_files = []):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.name = metadata.get_name()
        self.description = metadata.get_name()
        self.version = metadata.get_version()
        self.copyright = metadata.get_author()
        self.url = metadata.get_url()
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.lib_files = [self.chop(p) for p in lib_files]
        self.comserver_files = [self.chop(p) for p in comserver_files if p.lower().endswith(".dll")]

    def chop(self, pathname):
        #print pathname, self.dist_dir
        #assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]
    
    def create(self, pathname="base.nsi"):
        self.pathname = pathname
        ofi = self.file = open(pathname, "w")
        ver = self.version
        if "-" in ver:
            ver = ver[:ver.index("-")]  
        rev = self.version.endswith("-full") and ".1" or ".0"
        ver= [c in '0123456789.' and c or ".%s" % (ord(c)-96) for c in ver]+[rev]
        ofi.write(nsi_base_script % {
            'name': self.name,
            'description': "%s version %s" % (self.description, self.version),
            'product_version': ''.join(ver),
            'company_name': self.url,
            'copyright': self.copyright,
            'install_dir': self.name,
            'reg_key': self.name,
            'out_file': "instalador-%s-%s.exe" % (self.name, self.version),
            'register_com_servers': ''.join([register_com_server % comserver for comserver in self.comserver_files]),
            'unregister_com_servers': ''.join([unregister_com_server % comserver for comserver in self.comserver_files]),
        })

    def compile(self, pathname="base.nsi"):
        os.startfile(pathname, 'compile')
        
        
class Target():
    def __init__(self, module, **kw):
        self.__dict__.update(kw)
        # for the version info resources (Properties -- Version)
        # convertir 1.21a en 1.21.1
        self.version = module.__version__[:-1]+"."+str(ord(module.__version__[-1])-96)
        self.description = module.__doc__
        self.company_name = "Sistemas Agiles"
        self.copyright = module.__copyright__
        self.name = "Interfaz PyAfipWs - %s" % os.path.basename(module.__file__).replace(".pyc", ".py")