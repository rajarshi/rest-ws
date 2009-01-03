## Rajarshi Guha <rajarshi.guha@gmail.com>
## January 2009
##
## does PCA on a set of molecules, characterized by descriptors
## 
## The url is
## http://rguha.ath.cx/~rguha/cicc/rest/chemspace/default/mol1,mol2,mol3
##
## An alternative URL is of the form
## http://rguha.ath.cx/~rguha/cicc/rest/chemspace/default/N/mol1,mol2,mol3
##
## where N indicates the number of components to return. Cannot be less than 1
## if more than the valid number of components is requested, all are returned
##
## Right now, default indicates the default chemical space made up of
## ALogP, rot bonds, TPSA and MW. In the future other pre-defined chemical
## spaces might be made available.
##
## The result is the first 2 columns of the original data rotated into the PC
## space. Can be parsed and plotted via Javascript etc
##
## The return content type is based on the first element of the comma separated
## value of the Accept header. Currently text/plain and text/html are handled
## other wise HTTP_NOT_ACCEPTABLE is returned
##
## Browsers will get text/html by default
##
## Requires numpy, jsonlib

from mod_python import apache
import urllib, StringIO
from elementtree.ElementTree import ElementTree as ET
from elementtree.ElementTree import XML
from elementtree.ElementTree import Element, SubElement, tostring

descriptorBaseUrl = 'http://rguha.ath.cx/~rguha/cicc/rest/desc/descriptors/org.openscience.cdk.qsar.descriptors.molecular'

defaultChemicalSpace = { 'ALOGPDescriptor' : 'ALogP',
                        'RotatableBondsCountDescriptor' : 'nRotB',
                        'TPSADescriptor' : 'TPSA',
                        'WeightDescriptor' : 'MW' }

## this method needs to be robustified to handle
## descriptor calculation failures
def _getDescriptors(smiles):
    keys = defaultChemicalSpace.keys()
    vals = []
    for key in keys:
        dnames = defaultChemicalSpace[key]
        url = descriptorBaseUrl + '.' + key + '/' + smiles
        xml = ''.join(urllib.urlopen(url).readlines())
        root = XML(xml)
        values = root.findall('Descriptor')
        for value in values:
            if value.get('name') in dnames:
                vals.append(float(value.get('value')))
    return vals
    

def _getChemicalSpaceDocument(spaces):
    root = Element('chemicalSpaces')
    for space,desc,ndim in spaces:
        node = SubElement(root, 'chemicalSpace')
        node.set('name', space)
        node.set('description', desc)
        node.set('ndim', str(ndim))
        node.text = ""
    tree = ET(root)
    page = StringIO.StringIO()
    tree.write(page, encoding='UTF8')
    return page.getvalue()

def handler(req):
    uriParts = req.uri.split('/')

    tmp = uriParts.index('chemspace')
    if len(uriParts) == tmp+2: ## return the list of available spaces
        req.content_type = 'text/xml'
        req.write(_getChemicalSpaceDocument([('default', 'AlogP, TPSA, num rot bond, MW', 4)]))
        return apache.OK

    if len(uriParts) != tmp+3 and len(uriParts) != tmp+4:
        return apache.HTTP_NOT_FOUND

    spaceDef = uriParts[tmp+1]
    if spaceDef not in ['default']:
        return apache.HTTP_NOT_FOUND

    ## see if we have a number of components specified
    try:
        numComponent = int(uriParts[tmp+2])
        molecules = [x.strip() for x in ('/'.join(uriParts[ (tmp+3): ])).split(',')]
    except: ## wasn't a single number
        numComponent = 2
        molecules = [x.strip() for x in ('/'.join(uriParts[ (tmp+2): ])).split(',')]

    ## get descriptor values
    if len(molecules) < 3:
        return apache.HTTP_NOT_FOUND
    descriptors = []
    for molecule in molecules:
        data = _getDescriptors(molecule)
        descriptors.append(data)

    if numComponent > len(descriptors[0]): numComponent = len(descriptors[0])

    ## do PCA
    import pca
    import numpy

    data = numpy.asarray(descriptors)
    mean, pcs, norm_pcs, variances, positions, norm_positions = pca.pca(data, 'svd')
    
    centeredData = data - mean
    scores = numpy.dot(centeredData, numpy.transpose(pcs))
    scores2d = scores[:(scores.shape[0]), :numComponent]

    headers_in = req.headers_in
    try:
        accept = headers_in['Accept']
        accept = accept.split(',')
    except KeyError, e:
        ## we don't throw an exception, since at least one client
        ## (Google Spreadsheets) does not provide an Accept header
        accept = ['text/html']
        
    ctype = 'text/plain'
    page = ''

    if accept[0] == 'text/plain':
        ctype = 'text/plain'
        textarray = []
        for row in scores2d:
            textarray.append(' '.join([str(x) for x in row]))
        textarray = '\n'.join(textarray)
        page = textarray
    elif accept[0] == 'text/html':
        ctype = 'text/html'
        textarray = []
        for row in scores2d:
            textarray.append('<tr>'+''.join([ '<td>'+str(x)+'</td>\n' for x in row ])+'</tr>\n')
        page = '<html><body><table>'+'\n'.join(textarray)+'</table></body></html>'
    elif accept[0] == 'application/json':
        import jsonlib
        ctype = 'application/json'
        page = jsonlib.write(scores2d.tolist())
        
    else:
        return apache.HTTP_NOT_ACCEPTABLE

    req.content_type = ctype
    req.write(page)
    return apache.OK
    
