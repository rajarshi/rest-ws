from mod_python import apache
import SOAPpy, sys, string, StringIO, base64, urllib
import elementtree.ElementTree as ET
from elementtree.ElementTree import XML

import rpy2.robjects as ro
rinterp = ro.r

baseUrl = 'http://rguha.ath.cx/~rguha/cicc/rest/desc/descriptors/org.openscience.cdk.qsar.descriptors.molecular.'
descs = {'ATSm1' : 'AutocorrelationDescriptorMass',
         'C1SP2' : 'CarbonTypesDescriptor',
         'AMR' : 'ALOGPDescriptor' }

def _descDictToDataFrame(d):
    newd = {}
    for key in d.keys():
        newd[key] = ro.FloatVector([d[key]])
    return rinterp['data.frame'](**newd)

def handler(req):
    uriParts = req.uri.split('/')
    smiles = uriParts[-1]

    descriptors = {}

    ## get descriptors
    for key in descs.keys():
        descClass = descs[key]
        url = baseUrl + descClass + "/" + smiles
        doc = ''.join(urllib.urlopen(url).readlines())
        root = XML(doc)
        values = root.findall("Descriptor")
        for value in values:
            if value.attrib['name'] == key: descriptors[key] = float(value.attrib['value'])

    ## convert desc dict to data.frame
    descdf = _descDictToDataFrame(descriptors)

    ## load the model and get a prediction
    #rinterp("""load('/Users/rguha/src/rest-ws/predict/test-model.Rda')""")
    rinterp.load('/Users/rguha/src/rest-ws/predict/test-model.Rda')
    req.write(descdf.colnames().r_repr())
    return apache.OK
