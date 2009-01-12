from mod_python import apache
import SOAPpy, sys, string, StringIO, base64, urllib
import elementtree.ElementTree as ET
from elementtree.ElementTree import XML


baseUrl = 'http://rguha.ath.cx/~rguha/cicc/rest/desc/descriptors/org.openscience.cdk.qsar.descriptors.molecular.'
descs = {'ATSm1' : 'AutocorrelationDescriptorMass',
         'C1SP2' : 'CarbonTypesDescriptor',
         'AMR' : 'ALOGPDescriptor' }

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

    ## load the model and get a prediction
    from rpy import *

    makeDF = r("""
function( ..., names) 
{ 
df <- data.frame(...)
names(df) <- names
df
}
""")

    df = makeDF(1,2,3, names= ['a','b','c'])
#    r("""load('test-model.R')""")

    req.write(str(descriptors))
    return apache.OK
