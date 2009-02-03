import urllib2
import urllib

url = 'http://rguha.ath.cx/~rguha/cicc/rest/substruct/'
values = {'target' : 'CCC(=O)CC,c1ccccc1,C(=O)CC(=O)COC', 'query' : 'c' }
data = urllib.urlencode(values)
req = urllib2.Request(url, data)
response = urllib2.urlopen(req)
the_page = response.read()

print the_page
