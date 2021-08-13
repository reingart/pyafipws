#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Test para pyemail"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

from pyafipws.pyemail import PyEmail, main
import pytest
import traceback
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import sys, os
import smtplib
from configparser import SafeConfigParser

pytestmark = [pytest.mark.dontusefix]

pyemail = PyEmail()
config = SafeConfigParser()
config.read("rece.ini")
conf_mail = dict(config.items("MAIL"))

def test_Connectar_Enviar(mocker):
    """Test de conexion"""
    mocker.patch("smtplib.SMTP")
    pyemail.Conectar(
            conf_mail["servidor"],
            conf_mail["usuario"],
            conf_mail["clave"],
            25,
        )
    pyemail.Enviar(
        conf_mail["remitente"], "prueba", "check@gmail.com", None
    )

    pyemail.Salir() 

    smtplib.SMTP.assert_called_with(conf_mail["servidor"], 25)

def test_Crear():
    ok =pyemail.Crear()
    assert ok


def test_Agreagar_Destinatario():
    ok =pyemail.AgregarDestinatario("test@gmail.com")
    assert ok

def test_AgregarCC():
    ok =pyemail.AgregarCC("test@gmail.com")
    assert ok

def test_AgregarBCC():
    ok =pyemail.AgregarBCC("test@gmail.com")
    assert ok

def test_Adjuntar():
    ok =pyemail.Adjuntar("test@gmail.com")
    assert ok

def test_main(mocker):
    """Test de funcion main"""
    mocker.patch("smtplib.SMTP")
    sys.argv = []
    sys.argv.append("/debug")
    sys.argv.append("prueba")
    sys.argv.append("test@gmail.com")
    sys.argv.append("")
    main()

    smtplib.SMTP.assert_called_with(conf_mail["servidor"], 25)

def test_main_prueba(mocker):

    mocker.patch("smtplib.SMTP")
    sys.argv = []
    sys.argv.append("/prueba")
    sys.argv.append("user@gmail.com")
    sys.argv.append("pass123")
    main()

    smtplib.SMTP.assert_called_with('smtp.gmail.com', 587)