from pyafipws.wsfev1 import WSFEv1
from pyafipws.wsaa import WSAA
import pytest
import os

WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx"
CUIT = 20267565393
CERT = "reingart.crt"
PKEY = "reingart.key"
CACERT = "conf/afip_ca_info.crt"
CACHE = ""

pytestmark =pytest.mark.vcr

@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)



wsfev1 = WSFEv1()
@pytest.fixture(autouse=True)
def auth():
    wsaa=WSAA()
    wsfev1.Cuit = CUIT
    ta = wsaa.Autenticar("wsfe", CERT, PKEY)
    wsfev1.SetTicketAcceso(ta)
    wsfev1.Conectar(CACHE, WSDL)
    return wsfev1


def test_wsfev1_dummy(auth):
    wsfev1 = auth
    wsfev1.Dummy()
    assert wsfev1.AppServerStatus == "OK"
    assert wsfev1.DbServerStatus == "OK"
    assert wsfev1.AuthServerStatus == "OK"
