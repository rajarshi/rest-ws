import psycopg2
import urllib
from mod_python import apache

def handler(req):
    uriParts = req.uri.split('/')
    if 'getAllAids' in uriParts:
        content_type, return_value = getAllAids()
        if not return_value: return apache.HTTP_ERROR
    elif 'aidQuery' in uriParts:
        pos = uriParts.index('aidQuery')
        if len(uriParts) < pos+2: return apache.HTTP_NOT_FOUND
        aid = uriParts[pos+1]
        if aid == uriParts[-1]: termtype = 'all'
        else:
            termtype = uriParts[pos+2]
            if termtype not in ['functional', 'pathway', 'component']:
                return apache.HTTP_NOT_FOUND
        content_type, return_value = getAidDetails(aid, termtype)
        if not return_value: return apache.HTTP_NOT_FOUND
        
    req.content_type = content_type
    req.write(return_value)
    return apache.OK

def getAllAids():
    con = psycopg2.connect("dbname='gnova' user='gnovares' host='cheminfo.informatics.indiana.edu'")
    cursor = con.cursor()
    cursor.execute("select distinct aid from pubchem_aidgo")
    results = '\n'.join([ str(x[0]) for x in cursor.fetchall() ])
    cursor.close()
    con.close()
    return 'text/plain', results

def getAidDetails(aid, termtype):
    con = psycopg2.connect("dbname='gnova' user='gnovares' host='cheminfo.informatics.indiana.edu'")
    cursor = con.cursor()
    cursor.execute("select * from pubchem_aidgo where aid = %s order by score desc" % (aid))
    results = cursor.fetchall()
    ret = []
    for row in results:
        ret.append('\t'.join([str(x) for x in row[2:]]))
    cursor.close()
    con.close()
    return 'text/plain', '\n'.join(ret)
