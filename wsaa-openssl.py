import wsaa

import os,sys
from subprocess import Popen, PIPE
from base64 import b64encode

def sign_tra(tra,cert,privatekey):
    "Firmar PKCS#7 el TRA y devolver CMS (recortando los headers SMIME)"

    # Firmar el texto (tra)
    out = Popen(["openssl", "smime", "-sign", 
                 "-signer", cert, "-inkey", privatekey,
                 "-outform","DER", 
                 "-out", "cms.bin" , "-nodetach"], 
                stdin=PIPE,stdout=PIPE).communicate(tra)[0]
    out = open("cms.bin","rb").read()
    return b64encode(out)


tra = wsaa.create_tra("wsfex")
print tra

cms = sign_tra(tra,"reingart.crt","reingart.key")
print cms

open("tra.cms","w").write(cms)

ta = wsaa.call_wsaa(cms)
print ta

open("TA.xml","w").write(ta)
