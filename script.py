import ktuhfm
from google.appengine.ext import db
import urllib

f = urllib.urlopen("http://www2.hawaii.edu/~dwilkie/whitelist.txt")
whitelist = f.readlines()[0].split()
for line in whitelist:
    print line
    w = ktuhfm.Whitelist.add(line)
    w.put()