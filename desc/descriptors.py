from mod_python import apache
import SOAPpy, sys, string, StringIO
import elementtree.ElementTree as ET
from elementtree.ElementTree import XML

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
   
def handler(req):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/cdkws/services/Descriptors?wsdl')

    uriParts = req.uri.split('/')
    smiles = '/'.join(uriParts[-1])

    if req.method not in ['GET']:
        req.err_headers_out['Allow'] = 'GET'
        raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

    smiles = None
    descriptor = None

    
    # get all available descriptors
    if uriParts[-1] == 'descriptors':
        req.content_type = 'text/xml'
        headers_in = req.headers_in
        try:
            accept = headers_in['Accept']
            if accept == 'text/plain': req.content_type = 'text/plain'
        except KeyError:
            pass
        req.write(getSpecification('all', req.content_type))
        return apache.OK

    # get all available molecular descriptors
    if uriParts[-2] == 'descriptors' and uriParts[-1].startswith('org.openscience.cdk.qsar.descriptors.molecular'):
        req.content_type = 'text/xml'
        req.write(getSpecification(uriParts[-1]))
        return apache.OK
    
    ## here we assume that if descriptors is second last, then
    ## last must be the SMILES
    descIdx = uriParts.index('descriptors')
    if not uriParts[descIdx+1].startswith('org.openscience'): # all descriptors for the SMILES
        smiles = '/'.join(uriParts[(descIdx+1):])
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

    ## here we assume that if the package name is second last, then
    ## last must be the SMILES       
    else:
        smiles = '/'.join(uriParts[(descIdx+2):])        
        try:
            descDoc = s.evaluateDescriptors( [uriParts[descIdx+1]], smiles )
        except Exception, e:
            req.content_type = 'text/plain'
            req.write(str(e))
            return apache.HTTP_BAD_REQUEST
        
        req.content_type = 'text/xml'
        req.write(descDoc)
        
    return apache.OK
