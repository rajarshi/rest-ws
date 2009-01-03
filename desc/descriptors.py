from mod_python import apache
import SOAPpy, sys, string, StringIO
import elementtree.ElementTree as ET
from elementtree.ElementTree import XML

base = 'http://rguha.ath.cx/~rguha/cicc/rest/desc/descriptors'

def getSpecification(descClass):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/cdkws/services/Descriptors?wsdl')
    if descClass == 'all':
        descClasses = s.getAvailableDescriptorNames("all").data
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
    smiles = uriParts[-1]

    if req.method not in ['GET']:
        req.err_headers_out['Allow'] = 'GET'
        raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

    if uriParts[-1] == 'descriptors':
        req.content_type = 'text/xml'
        req.write(getSpecification('all'))        

    elif uriParts[-2] == 'descriptors' and uriParts[-1].startswith('org.openscience.cdk.qsar.descriptors.molecular'):
        req.content_type = 'text/xml'
        req.write(getSpecification(uriParts[-1]))

    ## here we assume that if descriptors is second last, then
    ## last must be the SMILES
    elif uriParts[-2] == 'descriptors': 
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
    elif uriParts[-2].startswith('org.openscience.cdk.qsar.descriptors.molecular'):
        try:
            descDoc = s.evaluateDescriptors( [uriParts[-2]], smiles )
        except Exception, e:
            req.content_type = 'text/plain'
            req.write(str(e))
            return apache.HTTP_BAD_REQUEST
        
        req.content_type = 'text/xml'
        req.write(descDoc)
    else:
        return apache.HTTP_BAD_REQUEST
 
        
    return apache.OK
