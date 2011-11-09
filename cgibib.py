#!/usr/bin/env python
import cgi, sys, time
from bibparse import *

DEBUG=True
if DEBUG: import cgitb; cgitb.enable()  # debug
form=cgi.FieldStorage()

print "Content-type: text/html\n"

BIBFILE=form["bibtex-file"].value if form.has_key("bibtex-file") else "master.bib"

print "Using file: %s"%BIBFILE
bib=BibtexFile( BIBFILE )
bib.parse()
print "<ul>"
for e in bib.bibentries:
    print "<li>%s</li>"%e.key
print "</ul>"
