from mod_python import apache
import SOAPpy, sys, string, StringIO, base64, urllib, os, os.path
import elementtree.ElementTree as ET
from elementtree.ElementTree import XML

import rpy2.robjects as ro
rinterp = ro.r

baseUrl = 'http://rguha.ath.cx/~rguha/cicc/rest/desc/descriptors/'
absolutePath = '/Users/rguha/src/rest-ws/predict'

class ModelDoc:
    def __init__(self, xml):
        self._xml = xml

    def getName(self):
        return self._name
    
    def getDescriptorDictionary(self):
        return self._descDict

    def getXML(self):
        return self._xml
    def setName(self, name):
        self._name = name

    def setDescriptorDictionary(self, d):
        self._descDict = d

    

def _descDictToDataFrame(d):
    newd = {}
    for key in d.keys():
        newd[key] = ro.FloatVector([d[key]])
    return rinterp['data.frame'](**newd)

def _getModelDoc(doclist, modelname):
    for i in doclist:
        if i.getName() == modelname: return i
    return None

def _getPrediction(model, encodedSmiles):
    descs = model.getDescriptorDictionary()
    descriptors = {}

    ## get descriptors
    for key in descs.keys():
        descClass = descs[key]
        url = baseUrl + descClass + "/" + encodedSmiles
        doc = ''.join(urllib.urlopen(url).readlines())
        root = XML(doc)
        values = root.findall("Descriptor")
        for value in values:
            if value.attrib['name'] == key: descriptors[key] = float(value.attrib['value'])

    ## convert desc dict to data.frame
    descdf = _descDictToDataFrame(descriptors)

    ## load the model and get a prediction
    #rinterp("""load('/Users/rguha/src/rest-ws/predict/test-model.Rda')""")
    ##rinterp.load('/Users/rguha/src/rest-ws/predict/test-model.Rda')
    
    return descriptors

def handler(req):

    ## load Manifest
    models = []
    root = ET.parse(os.path.join(absolutePath,"model.manifest"))
    modelElements = root.findall("model")
    for modelElement in modelElements:
        doc = ModelDoc(modelElement)
        doc.setName(modelElement.attrib['name'])
        
        descs = modelElement.findall("descriptors/descriptor")
        d = {}
        for desc in descs:
            d[desc.attrib['value']] = desc.attrib['class']
        doc.setDescriptorDictionary(d)
        models.append(doc)
        

    uriParts = req.uri.split('/')
    if uriParts[-1] == '': uriParts = uriParts[:-1]

    if uriParts[-1] == 'predict':
        req.content_type = 'text/plain'
        names = '\n'.join([x.getName() for x in models])
        req.write(names)
        return apache.OK

    if uriParts[-2] == 'predict':
        if uriParts[-1] in [x.getName() for x in models]:
            req.content_type = 'text/xml'
            frag = _getModelDoc(models, uriParts[-1]).getXML()
            req.write(ET.tostring(frag))
            return apache.OK
        else: return apache.HTTP_NOT_FOUND

    if uriParts[-3] == 'predict' and uriParts[-2] in [x.getName() for x in models]:
        ## get a prediction from this model
        predicted = _getPrediction(_getModelDoc(models, uriParts[-2]), uriParts[-1])
        
        req.content_type = 'text/plain'
        req.write(str(predicted))
        return apache.OK
    else: return apache.HTTP_NOT_FOUND

