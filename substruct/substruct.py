from mod_python import apache
from pybel import *

def handler(req):
    req.content_type = 'text/plain'
    uriParts = req.uri.split('/')

    target = uriParts[-2]
    query = uriParts[-1]

    try:
        mol = readstring("smi", target)
    except IOError:
        return apache.HTTP_BAD_REQUEST

    try:
        pat = Smarts(query)
    except IOError:
        return apache.HTTP_BAD_REQUEST

    if pat.findall(mol):
        req.write('true')
    else:
        req.write('false')

    return apache.OK

