#!/usr/bin/env python
"""
This is quick and ugly and works only for me!

Parameters:
* bibtex-file
* tag
* view - one of 'citations','keys'

"""
import cgi, sys, time
from bibparse import *

SCRIPTNAME='cgibib.cgi'
DEBUG=True
if DEBUG: import cgitb; cgitb.enable()  # debug
form=cgi.FieldStorage()

def cgiify( p ):
    """
    p is a dictionary of parameters;
    the function returns a string in CGI-style
    """
    if not p:
        return ""

    rstring="?"
    for k in p.keys():
        rstring+="%s=%s&"%(k,p[k])
    return rstring

def get_cloud( bf, params=None ):
    tc = bf.get_tag_count()

    # sorted by value
    keys = sorted( tc, key=lambda x: tc[x]);
    font={}
    for i in range(len(keys)):
        t=keys[i]
        s="%+i"%( (i/float(len(keys)-1))*8-4 )
        font[t]=s

    r = '<div class="bt_tagcloud">\n'
    for t in sorted(tc.keys()):
        r += "<a href='%s'><FONT size=%s> %s </FONT></a>\n"%(SCRIPTNAME+cgiify(dict(params, **{'tag':t})),font[t],t)
    r+="</div>\n"
    return r

##-------------------------------------------

print "Content-type: text/html\n"
BIBFILE=form["bibtex-file"].value if form.has_key("bibtex-file") else "master.bib"

print "<HTML>\n<link rel='stylesheet' type='text/css'  href='local.css'>"
print "<BODY>"


print "Using file: %s"%BIBFILE
bib=BibtexFile( BIBFILE )
bib.parse()

print get_cloud( bib, {'bibtex-file':BIBFILE} )

print "<ul>"
for e in bib.bibentries:
    print "<li>%s</li>"%e.tohtml()
print "</ul>"


print "</BODY></HTML>"
