#!/usr/bin/env python
import cgi, sys, time
DEBUG=True
if DEBUG: import cgitb; cgitb.enable()  # debug

form=cgi.FieldStorage()

print "Content-type: text/html\n"

print "HI!"
