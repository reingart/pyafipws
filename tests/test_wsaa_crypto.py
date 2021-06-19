import base64, subprocess

from past.builtins import basestring

from pyafipws.wsaa import WSAA

import pytest


@pytest.fixture
def key_and_cert():
    KEY = "reingart.key"
    CERT = "reingart.crt"
    return [KEY, CERT]


def test_wsaa_create_tra():
    wsaa = WSAA()
    tra = wsaa.CreateTRA(service="wsfe")

    # sanity checks:
    assert isinstance(tra, basestring)
    assert tra.startswith(
        '<?xml version="1.0" encoding="UTF-8"?>' '<loginTicketRequest version="1.0">'
    )
    assert "<uniqueId>" in tra
    assert "<expirationTime>" in tra
    assert "<generationTime>" in tra
    assert tra.endswith("<service>wsfe</service></loginTicketRequest>")


def test_wsaa_sign():
    wsaa = WSAA()
    tra = '<?xml version="1.0" encoding="UTF-8"?><loginTicketRequest version="1.0"/>'
    # TODO: use certificate and private key as fixture / PEM text (not files)
    cms = wsaa.SignTRA(tra, "reingart.crt", "reingart.key")
    # TODO: return string
    if not isinstance(cms, str):
        cms = cms.decode("utf8")
    # sanity checks:
    assert isinstance(cms, str)
    out = base64.b64decode(cms)
    assert tra.encode("utf8") in out


def test_wsaa_sign_tra(key_and_cert):
    wsaa = WSAA()

    tra = wsaa.CreateTRA("wsfe")
    sign = wsaa.SignTRA(tra, key_and_cert[1], key_and_cert[0])

    assert isinstance(sign, str)
    assert sign.startswith("MIIG+")


def test_wsaa_sign_tra_inline(key_and_cert):
    wsaa = WSAA()

    tra = wsaa.CreateTRA("wsfe")
    sign = wsaa.SignTRA(tra, key_and_cert[1], key_and_cert[0])

    sign_2 = wsaa.SignTRA(
        tra, open(key_and_cert[1]).read(), open(key_and_cert[0]).read()
    )

    assert isinstance(sign, str)
    assert sign.startswith("MIIG+")

    assert isinstance(sign_2, str)
    assert sign_2.startswith("MIIG+")
