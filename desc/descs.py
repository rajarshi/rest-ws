from mod_python import apache
import SOAPpy, sys, string, StringIO, base64
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XML

base = 'http://rguha.ath.cx/~rguha/cicc/rest/desc/descriptors'

def getSpecification(descClass, ctype):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/cdkws/services/Descriptors?wsdl')
    if descClass == 'all':
        descClasses = s.getAvailableDescriptorNames("all").data

        if ctype == 'text/plain':
            s = ""
            for className in descClasses:
                s += className+"\n"
            return s
        
        ET._namespace_map['http://www.w3.org/1999/xlink'] = 'xlink'
        root = ET.Element("specification-list")
        for className in descClasses:
            e = ET.SubElement(root, "specification-ref")
            e.set('{http://www.w3.org/1999/xlink}href', '%s/%s' % (base, className))
        tree = ET.ElementTree(root)

        output = StringIO.StringIO()
        tree.write(output)
        return output.getvalue()
    else:
       specs = s.getDescriptorSpecifications(descClass)
       return specs

def analyseURI(uriParts):
    smiles = None
    descName = None

    if uriParts[-1] == 'descriptors': 
        ## just get all desc specs
        smiles = None
        descName = None
        return descName, smiles

    if uriParts[-2] == 'descriptors':
        if uriParts[-1].startswith('org.openscience.cdk'):
            ## get spec for this descriptor
            smiles = None
            descName = uriParts[-1]
            return descName, smiles
        else: 
            ## get the links for descriptors for this SMILES
            smiles = uriParts[-1] ## we don't decode in this case
            descName = None
            return descName, smiles

    if uriParts[-3] == 'descriptors' and uriParts[-2].startswith('org.openscience.cdk'):
        ## specific desc for a smiles
        descName= uriParts[-2]
        try:
            smiles = base64.b64decode(uriParts[-1])
        except TypeError:
            smiles = 'INVALID'
        return descName, smiles

    return 'INVALID', 'INVALID'
    
def handler(req):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/cdkws/services/Descriptors?wsdl')

    if req.method not in ['GET']:
        req.err_headers_out['Allow'] = 'GET'
        raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

    uriParts = req.uri.split('/')
    descName, smiles = analyseURI(uriParts)

    if smiles == 'INVALID' or descName == 'INVALID':
        return apache.HTTP_BAD_REQUEST

    if not descName and not smiles:
        ## list specs for all descs
        req.content_type = 'text/xml'
        headers_in = req.headers_in
        try:
            accept = headers_in['Accept']
            if accept == 'text/plain': req.content_type = 'text/plain'
        except KeyError:
            pass
        req.write(getSpecification('all', req.content_type))
        return apache.OK

    if descName and not smiles:
        ## get spec for this descriptor
        req.content_type = 'text/xml'
        req.write(getSpecification(descName, req.content_type))
        return apache.OK

    if not descName and smiles:
        ## get all desc links for this SMILES (will be base64 encoded)
        descClasses = s.getAvailableDescriptorNames("all").data
        
        ET._namespace_map['http://www.w3.org/1999/xlink'] = 'xlink'
        root = ET.Element("descriptor-list")
        for className in descClasses:
            e = ET.SubElement(root, "descriptor-ref")
            e.set('{http://www.w3.org/1999/xlink}href', '%s/%s/%s' % (base, className, smiles))
        tree = ET.ElementTree(root)

        output = StringIO.StringIO()
        tree.write(output)

        req.content_type = 'text/xml'
        req.write(output.getvalue())
        return apache.OK

    if descName and smiles:
        ## eval this descriptor for this smiles, SMILES will have been decoded
        try:
            descDoc = s.evaluateDescriptors( descName, smiles )
        except Exception, e:
            req.content_type = 'text/plain'
            req.write(str(e))
            return apache.HTTP_BAD_REQUEST
        
        req.content_type = 'text/xml'
        req.write(descDoc)
        return apache.OK

    return apache.HTTP_NOT_FOUND
