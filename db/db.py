from mod_python import apache
import SOAPpy
import psycopg2
import sys, string, operator


def procPubchem(uriparts):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/pws/services/Structure?wsdl')

    if 'cidinchi' in uriparts:
        start = uriparts.index('cidinchi')
        inchi = '/'.join(uriparts[(start+1):])
        if not inchi.startswith('InChI'): return None, None
        cid = s.getCIDByInChI(str(inchi))
        return 'text/plain', cid
    elif 'cidikey' in uriparts:
        ikey = uriparts[-1]
        if len(ikey) != 25: return None, None
        cid = s.getCIDByInChIKey(str(ikey))
        return 'text/plain', cid
    elif 'synonym' in uriparts:
        start = uriparts.index('synonym')
        ss = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/pws/services/Synonyms?wsdl')
        query = uriparts[start+1]
        smiles = ss.getSmilesBySynonym(query)
        if len(smiles) == 0 or smiles == None or smiles[0] == None:
            return 'text/plain', ""
        else: return 'text/plain', smiles[0]
    elif 'synmw' in uriparts:
        term = uriparts[-1].strip()
        con = psycopg2.connect('host=cheminfo.informatics.indiana.edu dbname=gnova user=gnovares')
        cursor = con.cursor()
        cursor.execute("select openeye_mw  from pubchem_compound, pubchem_synonym where lower(synonym) = '%s' and pubchem_synonym.cid = pubchem_compound.cid;" % (term))
	ret = cursor.fetchall()
        con.close()
        if not ret: return 'text/plain', '-1'
        else: return 'text/plain', str(ret[0][0])

    sim = 0
    try:
        sim = float(uriparts[-1])
        print sim
    except:
        ## not a similarity value
        return None, None


    smiles = uriparts[-2]
    cids = s.getCIDBySimilarity(smiles, sim, 20, 0)
    cids = '\n'.join(cids)
    return 'text/plain', cids

def getSimilarBy3D(nums):
    nums = [float(x.strip()) for x in nums]
    nhit = int(nums[0])
    radius = nums[1]
    x = ','.join([str(x) for x in nums[2:]])

    sql = """
select * from (
   select cid, momsim, 1.0/(1.0+cube_distance( ('%s')::cube, momsim )) as sim from pubchem_3d
   where cube_enlarge( ('%s'), %f, 12) @> momsim order by sim desc
   ) as foo limit %d;    
    """ % (x,x,radius,nhit)

    s = None
    try:
        s = SOAPpy.WSDL.Proxy('http://156.56.104.93:8888/pub3d/services/Pub3DQueryService?wsdl')
    except Exception, e:
	return (None, "Couldn't contact the service", e)

    try:
        cids = s.getQueryResult(sql)
        s.close()
    except Exception, e:
        s.close()
        return (None, "A problem performing the query", e)

    cids = cids.split('\n')
    dat = []
    for line in cids:
        line = line.split()
        if len(line) != 14: continue
        dat.append( ( int(line[0]), float(line[-1])) )
    dat = sorted(dat, key=operator.itemgetter(1))
    dat.reverse()
    return dat[:nhit]
    
def procChemSpider(parts):
    term = parts[-1]
    import urllib
    import re

    if parts[-2] == 'bp':
        dat = ''.join(urllib.urlopen('http://www.chemspider.com/Search.aspx?q='+term).readlines())
        from BeautifulSoup import BeautifulSoup as BS
        try:
            soup = BS(dat)
        except: pass
        propdiv = soup.find('div', {'class':'prop_page_content', 'id':'ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_RecordViewControl1_formview_predicted_properties_content'})
        if propdiv is None: return 'None'
        
        tds = propdiv.findAll('td', {'class':'prop_title'})
        trs = propdiv.findAll('td', {'class':re.compile('^prop_value')})
        i = 0
        for td in tds:
            if td.string is not None and td.string.find('Boiling Point') >= 0: break
            i += 1
        bp = 'None'
        if trs[i].string is not None:
            try:
                bp = float(trs[i].string.split()[0])
            except ValueError:
                bp = 'None'
        return str(bp)

    url = 'http://www.chemspider.com/Search.aspx?q='+term
    con = urllib.urlopen(url)
    data = ''.join(con.readlines())
    reg = re.compile('<span class="user_data_property_name">Specific Gravity:\s*</span>\s*([0-9]*\.[0-9]*)</div>')
    vals =  reg.findall(data)
    if vals: return str(vals[0])
    else: return "None"

def handler(req):
    s = SOAPpy.WSDL.Proxy('http://rguha.ath.cx:8080/pws/services/Struct3D?wsdl')
    
    ## uris should be of the form
    ## http://rguha.ath.cx/~rguha/cicc/rest/db/DBNAME/BLAH 
    ## depending on the DBNAME, the subsequent portions
    ## of the URI will have different meanings
    ## Right now we handle the 3D DB only
    
    ## second last component indicates output format
    ## last component should be InChI
    uriParts = req.uri.split('/')
    idx = uriParts.index('rest')

    dbname = uriParts[idx+2]
    if dbname not in ['pub3d', 'pubchem', 'cid2cas', 'chemspider']:
        return apache.HTTP_BAD_REQUEST

    if req.method not in ['GET']:
        req.err_headers_out['Allow'] = 'GET'
        raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

    if dbname == 'pubchem':
        type, ret = procPubchem(uriParts)

        if not type and not ret: return apache.HTTP_BAD_REQUEST
        
        req.content_type = type
        req.write(ret)
        return apache.OK

    elif dbname == 'chemspider':
        dens = procChemSpider(uriParts)
        req.content_type = 'text/plain'
        req.write(dens)
	return apache.OK

    elif dbname == 'cid2cas':
        def validCAS(casrn):
            x = ''.join(casrn.split('-')[:2])
            x = x[::-1]
            sum = 0
            for i in range(1, len(x)+1):
                sum = sum + int(x[i-1]) * i
            if sum % 10 == int(casrn[-1]):
                return True
            return False
            
        identifier = '/'.join(uriParts[(idx+3):])
        try:
            testid = int(identifier)
        except:
            return apache.HTTP_BAD_REQUEST
        
        con = psycopg2.connect('host=cheminfo.informatics.indiana.edu user=gnovares dbname=gnova')
        cursor = con.cursor()
        sql = """select synonym from pubchem_synonym  where 
	cid = '%s' and
	(synonym similar to '_-__-_' or
	synonym similar to '__-__-_' or
	synonym similar to '___-__-_' or
	synonym similar to '____-__-_' or
	synonym similar to '_____-__-_' or
	synonym similar to '______-__-_' or
	synonym similar to '_______-__-_');""" % (identifier)
        cursor.execute(sql)
        ret = cursor.fetchall()
        con.close()
        req.content_type = 'text/plain'
        casrn = ''
        if len(ret) > 0:
            casrn = '\n'.join(filter(validCAS, [x[0] for x in ret]))
        req.write(casrn)
        return apache.OK

    elif dbname == 'pub3d':
        identifier = '/'.join(uriParts[(idx+3):])
        wsCallWorked = False

        ## do we have a vector of 12 numbers?
        nums = identifier.split(',')
        if len(nums) == 14:
            req.content_type = 'text/plain'
            cids = getSimilarBy3D(nums)
	    if len(cids) == 3 and cids[0] == None:
                req.write('<div id="soapError"><i>%s</i><br><pre>%s</pre></div>' % (cids[1], str(cids[2])))
	        return apache.OK 
            ret = '\n'.join(['%s %s' % (x,y) for x,y in cids])
            req.write(ret)
            return apache.OK
                      
        
        try:
            struct = s.getStructureByInChIKey(identifier)
            req.content_type = 'text/plain'
            req.write(struct)
            wsCallWorked = True
        except Exception, e:
            pass
        
        try:
            struct = s.getStructureByInChI(identifier)
            req.content_type = 'text/plain'
            req.write(struct)
            wsCallWorked = True
        except Exception, e:
            pass

        if not wsCallWorked:
            try:
                struct = s.getStructureByCID(identifier)
                req.content_type = 'text/plain'
                req.write(struct)
                wsCallWorked = True
            except Exception, e:
                return apache.HTTP_NOT_FOUND
    else:
        return apache.HTTP_BAD_REQUEST        

    return apache.OK

    
