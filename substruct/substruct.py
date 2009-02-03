from mod_python import apache
from mod_python import util
from pybel import *

def handle_get(uriParts):
    target = uriParts[-2]
    query = uriParts[-1]

    try:
        mol = readstring("smi", target)
    except IOError:
        raise RuntimeError

    try:
        pat = Smarts(query)
    except IOError:
        raise RuntimeError

    if pat.findall(mol):
        return "true"
    else:
        return "false"

def handle_post(req):
    fd = util.FieldStorage(req)
    query = fd['query']
    targets = fd['target']
    if targets == "": raise RuntimeError
    targets = [x.strip() for x in targets.split(",")]

    try:
        pat = Smarts(query)
    except IOError:
        raise RuntimeError

    result = []
    for target in targets:
        try:
            mol = readstring("smi", target)
            if pat.findall(mol): result.append("true")
            else: result.append("false")
        except IOError:
            result.append("fail")

    return '\n'.join(result)
  
def handler(req):
    req.content_type = 'text/plain'
    uriParts = req.uri.split('/')

    if req.method == 'GET':
        try:
            value = handle_get(uriParts)
            req.write(value)
        except RuntimeError:
            return apache.HTTP_BAD_REQUEST
    elif req.method == 'POST':
        try:
            values = handle_post(req)
            req.write(values)
        except RuntimeError: return apache.HTTPD_BAD_REQUEST
    
    return apache.OK


