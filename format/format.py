from mod_python import apache
import SOAPpy
import sys, string
from openbabel import *

def handler(req):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/cdkws/services/StructureDiagram?wsdl')
    
    ## uris should be of the form
    ## http://rguha.ath.cx/~rguha/cicc/rest/format/TARGET_FORMAT/SMILES_STRING
    uriParts = req.uri.split('/')
    smiles = uriParts[-1]

    if uriParts[-2] not in ['inchi', 'inchikey', 'sdf', 'can']:
        return apache.HTTP_BAD_REQUEST
    
    if req.method not in ['GET']:
        req.err_headers_out['Allow'] = 'GET'
        raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

    mol = OBMol()
    obc = OBConversion()
    if uriParts[-2] == 'inchi':
        obc.SetInAndOutFormats("smi", "inchi")
    elif uriParts[-2] == 'inchikey':
        obc.SetInAndOutFormats("smi", "inchi")
        obc.AddOption("K", OBConversion.OUTOPTIONS)
    elif uriParts[-2] == 'sdf':
        obc.SetInAndOutFormats('smi', 'sdf')
    elif uriParts[-2] == 'can':
        obc.SetInAndOutFormats('smi', 'can')
        
    obc.ReadString(mol, smiles)
    ret = obc.WriteString(mol)
    
    req.content_type = 'text/plain';
    req.write(ret)
    return apache.OK

    
