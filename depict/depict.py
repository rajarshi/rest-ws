## Rajarshi Guha <rajarshi.guha@gmail.com>
##
## Requires SOAPpy http://downloads.sourceforge.net/pywebsvcs/SOAPpy-0.12.0.tar.gz?modtime=1109072997&big_mirror=0

from mod_python import apache
import SOAPpy
import sys, string
import base64, bz2

def handler(req):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/cdkws/services/StructureDiagram?wsdl')
    
    ## uris should be of the form
    ## http://rguha.ath.cx/~rguha/cicc/rest/depict/SMILES
    uriParts = req.uri.split('/')
    smiles = uriParts[-1]

    if smiles[0:4] == 'Qlpo':
        bziped = base64.urlsafe_b64decode(smiles)
        smiles = bz2.decompress(bziped)
#    req.content_type='text/plain'
#    req.write(smiles)
#    return apache.OK

    if req.method not in ['GET']:
        req.err_headers_out['Allow'] = 'GET'
        raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

    png = None
    notSmiles = False
    try:
        png = s.getDiagram(smiles, int(200), int(200), float(0.9))
        png = base64.b64decode(png)
        req.content_type = 'image/png';
        req.write(png)
        return apache.OK
    except: ## maybe not a SMILES? Try syn lookup
        notSmiles = True

    if notSmiles:
        import urllib
        con = urllib.urlopen('http://rguha.ath.cx/~rguha/cicc/rest/db/pubchem/synonym/'+smiles)
        smiles = con.readlines()
        if len(smiles) != 1:
            return apache.HTTP_NOT_FOUND
        else: smiles = smiles[0].strip()
        png = s.getDiagram(smiles, int(200), int(200), float(0.9))
        png = base64.b64decode(png)
        req.content_type = 'image/png';
        req.write(png)
        return apache.OK
        

    
