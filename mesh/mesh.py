from mod_python import apache
import SOAPpy
import sys, string, operator
import urllib
import elementtree.ElementTree as ET
from elementtree.ElementTree import XML

def handler(req):
    url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id='
    
    ## uris should be of the form
    ## http://rguha.ath.cx/~rguha/cicc/rest/depict/SMILES
    uriParts = req.uri.split('/')
    ids = ','.join([x.strip() for x in uriParts[-1].split(',')])
    url = url+ids

    if req.method not in ['GET']:
        req.err_headers_out['Allow'] = 'GET'
        raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

    result = ''
    headingCounts = {}
    narticle = 0
    
    data = ''.join(urllib.urlopen(url).readlines())
    doc = XML(data)
    for article in doc.findall('PubmedArticle'):
        narticle += 1
        for mh in article.findall('MedlineCitation/MeshHeadingList/MeshHeading/DescriptorName'):
            if mh.text in headingCounts.keys():
                headingCounts[mh.text] += 1
            else:
                headingCounts[mh.text] = 1

    ## most frequent first
    headingCounts = sorted(headingCounts.items(), key = operator.itemgetter(1), reverse=True)
    for key,item in headingCounts:
        result += '%s # %d/%d\n' % (key, item, narticle)
    
    req.content_type = 'text/plain';
    req.write(result)
    return apache.OK

    
