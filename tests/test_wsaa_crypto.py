import base64, subprocess

from pyafipws.wsaa import WSAA


def test_wsfev1_create_tra():
    wsaa = WSAA()
    tra = wsaa.CreateTRA(service="wsfe")
    # TODO: return string
    tra = tra.decode("utf8")
    # sanity checks:
    assert isinstance(tra, str)
    assert tra.startswith(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<loginTicketRequest version="1.0">'
        )
    assert '<uniqueId>' in tra
    assert '<expirationTime>' in tra
    assert tra.endswith('<service>wsfe</service></loginTicketRequest>')


def test_wsfev1_sign():
    wsaa = WSAA()
    tra = '<?xml version="1.0" encoding="UTF-8"?><loginTicketRequest version="1.0"/>'
    # TODO: use certificate and private key as fixture / PEM text (not files)
    cms = wsaa.SignTRA(tra, "reingart.crt", "reingart.key")
    # TODO: return string
    cms = cms.decode("utf8")
    # sanity checks:
    assert isinstance(cms, str)
    out = base64.b64decode(cms)
    assert tra.encode("utf8") in out