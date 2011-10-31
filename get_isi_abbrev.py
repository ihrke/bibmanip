#!/usr/bin/env python
"""
Get all ISI journal abbreviations and put them into bibtex
@string-variables.
"""

import urllib
import re
import sys

URL="http://www.efm.leeds.ac.uk/~mark/ISIabbr/"

pattern=re.compile( r"<DT>(.+?)<B><DD>(.+?)</B>", re.DOTALL )
for letter in [chr(x) for x in range(ord("A"), ord("Z")+1)]:
    f=urllib.urlopen( "%s/%s_abrvjt.html"%(URL,letter))
    content = f.read()
    f.close()
    
    ll=pattern.finditer(content)

    for m in ll:
        (lname,sname)=m.groups()
        lname=lname.strip().title()
        sname=sname.strip().replace(" ", "_")
        print "@string{ %s=\"%s\" }"%(sname,lname)

    
