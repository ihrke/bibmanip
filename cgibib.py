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
BYTAG=form["tag"].value if form.has_key("tag") else None
ENTRY=form["entry"].value if form.has_key("entry") else None

print "<HTML>\n<link rel='stylesheet' type='text/css'  href='local.css'>"
print "<BODY>"

bib=BibtexFile( BIBFILE )
bib.parse()
params={'bibtex-file':BIBFILE};

if ENTRY:
    print "<H1>%s</H1>"%(ENTRY)
    print "<div id='bibfile'>Using file: %s</div>"%BIBFILE
    print "<div id='citation'>%s</div>"%bib[ENTRY].tohtml()
    print "<pre>%s</pre>"%(bib[ENTRY])
else:
    if BYTAG:
        print "<H1>Tag: %s</H1>"%BYTAG
    else:
        print "<H1>All Entries</H1>"

    print "<div id='bibfile'>Using file: %s</div>"%BIBFILE
    print get_cloud( bib, {'bibtex-file':BIBFILE} )

    print "<div id='entrylist'><ul>"
    for e in bib.bibentries:
        if BYTAG and not BYTAG in e.get_tags():
            continue
        print "<li><a id='entrylink' href='%s'>%s</a>"%(cgiify(dict(params, **{'entry':e.key})),e.tohtml())
        if len( e.get_tags())>0:
            print "<br>"
        print "<span id='taglist'>"
        for t in e.get_tags():
            print "<a href='%s'>%s</a>"%(cgiify(dict(params,**{'tag':t})),t)
        print "</span>"
        if e.get_pdf():
            print "<a id='pdf' href='%s'>[PDF]</a>"%(e.get_pdf())
        if e.data.has_key("url"):
            print "<a id='url' href='%s'>[URL]</a>"%(e.data["url"])
        print "<form>new tag: <input type='text' name='newtag'>"
        params["key"]=e.key
        for p in params.keys():
            print "<input type='hidden' name='%s' value='%s'>"%(p,params[p])
        print "</form>"
        print "</li>"
    print "</ul></div>"


print "</BODY></HTML>"


