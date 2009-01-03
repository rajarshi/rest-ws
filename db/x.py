def validCAS(casrn):
    x = ''.join(casrn.split('-')[:2])
    x = x[::-1]
    sum = 0
    for i in range(1, len(x)+1):
        sum = sum + int(x[i-1]) * i
    if sum % 10 == int(casrn[-1]):
        return True
    return False

def getbp(term):
    import urllib
    import re
    dat = ''.join(urllib.urlopen('http://www.chemspider.com/Search.aspx?q='+term))
    print dat

#print validCAS('7732-18-5')
print getbp('benzaldehyde')
