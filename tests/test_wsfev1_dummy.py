from pyafipws.wsfev1 import WSFEv1
from pyafipws.wsaa import WSAA
import pytest
import os

__WSDL__ = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
__obj__ = WSFEv1()
__service__ = "wsfe"

CUIT = 20267565393
CERT = "reingart.crt"
PKEY = "reingart.key"
CACERT = "conf/afip_ca_info.crt"
CACHE = ""

pytestmark =pytest.mark.vcr


def test_wsfev1_dummy(auth):
    wsfev1 = auth
    wsfev1.Dummy()
    assert wsfev1.AppServerStatus == "OK"
    assert wsfev1.DbServerStatus == "OK"
    assert wsfev1.AuthServerStatus == "OK"
