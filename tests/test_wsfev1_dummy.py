from pyafipws.wsfev1 import WSFEv1


def test_wsfev1_dummy():
    wsfev1 = WSFEv1()
    assert wsfev1.Conectar()
    wsfev1.Dummy()
    assert wsfev1.AppServerStatus == "OK"
    assert wsfev1.DbServerStatus == "OK"
    assert wsfev1.AuthServerStatus == "OK"
