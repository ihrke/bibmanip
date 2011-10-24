#!/usr/bin/env python
"""
Bibtex-manipulation program.

Example: Merging two files with partially overlapping entries
1) simple append the files
   $ cat file1.bib > bfile.bib
   $ cat file2.bib >> bfile.bib
2) detect duplicates
   $ bibmanip.py bfile.bib duplicates -o dup.bib
3) cut these from the original file
   $ x=`bibmanip.py bfile.bib listkeys -p`
   $ bibmanip.py bfile.bib cutentries -o new.bib -d $x
4) merge the duplicates in dup.bib by hand
5) combine the files
   $ cat dub.bib >> new.bib
"""
from bibparse import *
import glob
import string
import sys, re
import time
import inspect
from termcolor import *
import getopt
import subprocess

commands=["addtag", "splitbytag", "delfield", "matchpdf", "checkpdf", "stats",
          "compare", "cutentries", "duplicates", "listentries", "addentries",
          "sort"];

def __my_doc__(n=1):
    """Print the docstring of the calling function."""
    frame = inspect.stack()[n][0]
    return frame.f_globals[frame.f_code.co_name].__doc__

def addtag( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib addtag <regexp> tag1[tag2;tag3;...]
    
    The tag(s) are added for any entry that has a match for the regexp.
    """
    if len(args)<2:
        print __my_doc__()
        sys.exit();
    regex=args[0];
    tags=[t.strip() for t in args[1].split(";")];
    for e in bibfile.bibentries:
        if e.re_match( regex ):
            e.add_tag(tags);
            sys.stderr.write(">> %s -- %s\n"%(colored(e.key,"yellow"),colored(str(e.get_tags()), "green")));

    print bibfile

def delfield( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib [-r] [-m regex] [-o output] fieldname1 [fieldname2 ...]
    
    Delete the fieldname from any bibtex-entry.
    If regex is provided, only for entries that match.

    Options:
    * -r -- if provided, 'fieldname' is regarded as a regular expression;
            any fieldname that matches this regex is deleted
            Example: -r citeulike-.+ will match any fieldnames from the citeulike site
    * -m regex -- delete only fields in entries where the regex matches the entry
    * -o outfile -- redirect output to outfile; else it is written to stdout
    """
    
    try:
        opts,bargs=getopt.getopt( args, "rm:o:");
        opts=dict(opts);
        if len(bargs)<1:
            raise getopt.GetoptError(colored("ERROR: need at least one fieldname","red"))
        fields=bargs
        pattern=None;
        if opts.has_key("-m"):
            pattern=opts["-m"];
        field_is_re=False;
        if opts.has_key("-r"):
            field_is_re=True;
        outfile=None;
        if opts.has_key("-o"):
            outfile=opts["-o"];
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__();
        sys.exit()

    for e in bibfile.bibentries:
        if pattern and not e.re_match(pattern):
            continue
        if not field_is_re:
            for field in fields:
                if e.data.has_key(field):
                    del e.data[field];
                    sys.stderr.write(">> %s -- matches %s\n"%(colored(e.key, "red"),
                                                              colored(field,"yellow")));
        elif field_is_re:
            for field in fields:
                for k in e.data.keys():
                    if re.search( field, k, re.IGNORECASE ):
                        del e.data[k];
                        sys.stderr.write(">> %s -- matches %s\n"%(colored(e.key, "red"),
                                                                  colored(k,"yellow")));

    if outfile:
        bibfile.save(outfile);
    else:
        print bibfile

def matchpdf( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib matchpdf [-o outfile] [-C] [-e] [-s sep]
                                            [-i none|only|plus] pdfdirectory

    Look through all PDFs in pdfdirectory and match them to the entries in bibfile.bib.
    PDFs are assumed to be in

    Author1[_Author2_...]_Year[_Optional].pdf

    format (the underscore can be another separating character specified with -s).

    The matching is done as follows:
    * Authors are matched to the authors-string
    * Year is matched to the year-string
    * optional is currently ignored
    only if author and year can be found in the bibtex-entry is
    the pdf included.
    Entries that already have pdf-field are not considered except, when -e is provided.
    There is also an option to read the first page of each pdf-file and compare
    for the title. 

    Options
    * -o outfile -- redirect output to outfile; else it is written to stdout
    * -e -- match also entries with existing pdf-tag
    * -s sep -- character or string separating authors/year/optional
    * -C -- do not ignore case
    * -i none|only|plus -- use introspection of the PDF file: convert the first page
            to text and compare it to the title of each entry; may take a long time;
            requires pdftotext; only means that author/year inspection is not done
            plus means the pdf has to fulfill both author/year and pdf-introspection
    """
    try:
        opts,bargs=getopt.getopt( args, "o:es:Ci:");
        if len(bargs)<1:
            raise getopt.GetoptError(colored("ERROR: Need a directory for the PDF files","red"))
        pdfdir=bargs[0];
        opts=dict(opts);
        sepchar=opts["-s"] if opts.has_key("-s") else "_"
        outfile=opts["-o"] if opts.has_key("-o") else None
        ignorecase=False if opts.has_key("-C") else True
        introspectpdf=opts["-i"] if opts.has_key("-i") else "none"
        if introspectpdf not in ["none","only","plus"]:
            raise getopt.GetoptError(
                colored("ERROR: introspection must be 'none','only' or 'plus'","red"))
        match_existing=True if opts.has_key("-e") else False
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__()
        sys.exit()
    pdfs=glob.glob(os.path.join(pdfdir,"*.pdf"))
    pdfinfo=[]
    if introspectpdf in ["plus","only"]:
        sys.stderr.write(">> Introspecting, please wait...\n");
    for pdf in pdfs:
        (fname,ext)=os.path.splitext(os.path.basename(pdf))
        l=fname.split(sepchar)
        idx=[x.isdigit() for x in l].index( True )
        if introspectpdf in ["plus","only"]:
            p = subprocess.Popen(["pdftotext", '-f', '1', '-l', '1', pdf, "-"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            firstpage, err = p.communicate()
            firstpage=firstpage.translate(None,delchars).lower()
        else:
            firstpage=None
        pdfinfo.append( {'org':pdf, 'authors':l[0:idx], 'year':int(l[idx]),
                         'optional':l[(idx+1):] if idx<len(l) else [],
                         'pdfcontent':firstpage});

    reflags=re.IGNORECASE if ignorecase else None
    candidates={};
    for e in bibfile.bibentries:
        if not e.data.has_key("author") or not e.data.has_key("year"):
            sys.stderr.write(">> "+colored("WARNING: ", "green")+
                             "entry %s has no author or year\n"%(colored(e.key,"yellow")));
            continue
        if e.data.has_key("pdf") and not match_existing:
            continue
        for p in pdfinfo:
            if introspectpdf in ["none","plus"]:
                authormatch=[re.search(x,e.data["author"],reflags) for x in p["authors"]];
                if all( authormatch ) and str(p["year"])==e.data["year"].strip():
                    if introspectpdf=="none":
                        sys.stderr.write(">> Match by author/year %s: %s\n"%(
                            colored(e.key,"green"),
                            colored(p["org"],"yellow")))
                        if not candidates.has_key(e.key): candidates[e.key]=[];
                        candidates[e.key].append( p["org"]);
                    elif re.search(e.data["title"].translate(None,delchars).lower(),
                             p["pdfcontent"],re.DOTALL|re.IGNORECASE):
                        sys.stderr.write(">> Match by author/year/introspection %s: %s\n"%
                                         (colored(e.key,"green"),
                                          colored(p["org"],"yellow")))
                        if not candidates.has_key(e.key): candidates[e.key]=[];
                        candidates[e.key].append( p["org"]);
            elif introspectpdf=="only":
                if re.search(e.data["title"].translate(None,delchars).lower(),
                             p["pdfcontent"],re.DOTALL|re.IGNORECASE):
                    sys.stderr.write(">> Match by introspection only %s: %s\n"%
                                     (colored(e.key,"green"),
                                      colored(p["org"],"yellow")))
                    if not candidates.has_key(e.key): candidates[e.key]=[];                    
                    candidates[e.key].append( p["org"]);

    for c in candidates.keys():
        bibfile[c].data["pdf"]=";".join(candidates[c]);

    if outfile:
        bibfile.save(outfile)
    else:
        print bibfile



def duplicates( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib duplicates [-o outfile] [-c] [-p] [-l]

    Search for duplicates and write a new bibtex-file consisting of each of the
    duplicates plus a merged version for conflict resolution.
    A list of the found duplicate keys is printed which may be used with
    'cutentries' to remove and merge the resolved file.

    Options
    * -c -- colourize the output (nice for viewing, bad for editing, therefore
            off by default)
    * -o outfile -- redirect output to outfile; else it is written to stdout
    * -p -- print both original entries in addition to the merged one
    * -l -- print a list of the duplicate keys; no other output
    """
    try:
        opts,bargs=getopt.getopt( args, "o:cpl");
        opts=dict(opts);
        outfile=outfile=opts["-o"] if opts.has_key("-o") else None
        colourize=True if opts.has_key("-c") else False
        printorg=True if opts.has_key("-p") else False
        printlist=True if opts.has_key("-l") else False
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__();
        sys.exit()

    dupfile=BibtexFile( outfile );
    duplicates=[];
    for i in range(0,len(bibfile.bibentries)-1):
        for j in range(i+1,len(bibfile.bibentries)):
            if bibfile.bibentries[i].compare_by_title(bibfile.bibentries[j]):
                sys.stderr.write(">> Duplicate: %s -- %s\n"%(
                    colored(bibfile.bibentries[i].key, "yellow"),
                    colored(bibfile.bibentries[j].key, "green")) );
                duplicates.append( (bibfile.bibentries[i].key,bibfile.bibentries[j].key) );

    if printlist:
        print " ".join([ x for l in duplicates for x in l])
        return

    for d1,d2 in duplicates:
        dupfile.bibentries.append(BibtexEntryDuplicate([bibfile[d1],bibfile[d2]],
                                                       colourize=colourize))
        if printorg:
            dupfile.bibentries.append(bibfile[d1])
            dupfile.bibentries.append(bibfile[d2])

    if outfile:
        dupfile.save(outfile)
    else:
        print dupfile

def listentries( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib listentries [-o outfile] [-p] [-t type] [-r regex]

    Options
    * -p -- output only the keys separated by spaces (for use with
            e.g. cutentries; else mory fancy output
    * -t type -- output only the entries that are of type (e.g. article, book,...)
    * -r regex -- output only the entries that match the regex
    * -o outfile -- redirect output to outfile; else it is written to stdout    
    """
    try:
        opts,bargs=getopt.getopt( args, "o:pt:r:");
        opts=dict(opts);
        outfile = opts["-o"] if  opts.has_key("-o") else None
        fancy=True if opts.has_key("-p") else False
        etype=opts["-t"] if opts.has_key("-t") else None
        regex=opts["-r"] if opts.has_key("-r") else None
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__();
        sys.exit()

    for e in bibfile.bibentries:
        if etype and not e.btype==etype:
            continue
        if regex and not re.search( regex, e.org_content, re.DOTALL|re.IGNORECASE):
            continue
        if fancy:
            print ">> %s -- %s"%(e.key, " ".join(e.data["title"].split()))
        else:
            print "%s "%e.key,

def sort( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib sort [-o outfile] [-f field]

    Options
    * -f field -- sort the entries by field; default is to sort by key
    * -o outfile -- redirect output to outfile; else it is written to stdout    
    """
    try:
        opts,bargs=getopt.getopt( args, "o:f:");
        opts=dict(opts);
        outfile = opts["-o"] if  opts.has_key("-o") else None
        sortfield = opts["-f"] if  opts.has_key("-f") else None
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__();
        sys.exit()
        
       # keys=sorted( tags, key=lambda x: tags[x], reverse=True);
    if sortfield:
        sentries=sorted( bibfile.bibentries, key=lambda x: x.data[sortfield]
                         if x.data.has_key(sortfield) else "ZZZZ" )
    else:
        sentries=sorted( bibfile.bibentries, key=lambda x: x.key )

    bibfile.bibentries=sentries

    if outfile:
        bibfile.save(outfile)
    else:
        print bibfile
        
          
def addentries( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib addentries [-o outfile] [-p path/to/pdf.pdf]
                                              [-t tag1;tag2;...] [-s] <input-file|->

    Reads and appends the entries from <input-file> or from stdin when - is given.

    Options
    * -o outfile -- redirect output to outfile; else it is written to stdout
    * -p path/to/pdf.pdf -- use the provided pdf file (is used for all entries)
    * -t tag1;tag2;... -- use these tags
    * -s -- assume the file is sorted and put it at the appropriate place
    """
    try:
        opts,bargs=getopt.getopt( args, "o:p:t:s")
        if len(bargs)<1:
            raise getopt.GetoptError(colored("ERROR: Need an input","red"))
        infile=bargs[0];
        opts=dict(opts);
        outfile=opts["-o"] if opts.has_key("-o") else None
        tags=opts["-t"] if opts.has_key("-t") else []
        pdf=opts["-p"] if opts.has_key("-p") else None
        sorted=True if opts.has_key("-s") else False
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__();
        sys.exit()

    if infile=="-":
        mbib=BibtexFile()
        mbib.bibtexcontent=sys.stdin.read()
    else:
        mbib=BibtexFile(infile)
    mbib.parse()

    for e in mbib.bibcomments:
        bibfile.bibcomments.append(e)
    for e in mbib.bibstrings:
        bibfile.bibstrings.append(e)
    for e in mbib.bibentries:
        e.key=e.key.title()
        if sorted:
            keys=[e2.key for e2 in bibfile.bibentries]
            idx=len(keys)
            for i in range(len(keys)):
                if keys[i]>e.key:
                    idx=i
                    break
                
        if tags:
            e.add_tag( tags.split(";") )
        if pdf:
            e.data["pdf"]=pdf
        if sorted:
            bibfile.bibentries.insert(idx,e)
        else:
            bibfile.bibentries.append(e)

    if outfile:
        bibfile.save(outfile)
    else:
        print bibfile
  
def cutentries( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib cutentries [-o outfile] [-d] [-k] key1 [key2 key3 ...]

    Options
    * -d -- delete the keys (default)
    * -k -- keep the keys (and remove everything else)
    * -o outfile -- redirect output to outfile; else it is written to stdout    
    """
    try:
        opts,bargs=getopt.getopt( args, "dko:");
        opts=dict(opts);
        if len(bargs)<1:
            raise getopt.GetoptError(colored("ERROR: Need at least one key","red"))
        keys=bargs;
        outfile=None;
        if opts.has_key("-o"):
            outfile=opts["-o"];
        delkeys=True;
        if opts.has_key("-k"):
            delkeys=False;
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__();
        sys.exit()

    nlist=[]
    for e in bibfile.bibentries:
        if e.key in keys:
            if not delkeys: nlist.append(e)
        else:
            if delkeys: nlist.append(e)
    bibfile.bibentries=nlist;
    if outfile:
        bibfile.save(outfile);
    else:
        print bibfile
        


def compare( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib compare [-c key|title] [-p file1|file2|both] bibfile2.bib 

    Checks which citation key is present in either one of the to .bib files.
    If the optional argument 'bytitle' is given, the title is used
    (title converted to all lower-case, all non-alpha characters are deleted
    before comparison).
    
    Entries that are only available in the 1st file will by _yellow_.
    Entries that are only available in the 1st file will by _green_.
    Entries that are available in both files are _blue_.

    Arguments:
     * -c key|title -- compare using 'key' or 'title'
     * -p file1|file2|both -- print either 'file1', 'file2' or 'both' (default: both)
    """
    try:
        opts,bargs=getopt.getopt( args, "c:p:");
        opts=dict(opts);
        if len(bargs)<1:
            raise getopt.GetoptError(colored("ERROR: Need a 2nd bibfile for comparison","red"))
        matchkey="key";
        if opts.has_key("-c"):
            matchkey=opts["-c"];
        if matchkey!="key" and matchkey!="title":
            raise getopt.GetoptError( colored("ERROR: ","red")+
                                      "key %s not implemented"%colored(matchkey,"green") )
        printing="both";
        if opts.has_key("-p"):
            printing=opts["-p"];
        if printing!="file1" and printing!="file2" and printing!="both":
            raise getopt.GetoptError( colored("ERROR: ","red")+
                                      "printing %s not implemented"%colored(printing,"green") )
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__();
        sys.exit()

    cfile=bargs[0];
    if not os.path.exists(cfile):
        print colored("ERROR: ","red")+"%s does not exist"%colored(cfile,"green");
        sys.exit();
    bibfile2=BibtexFile(cfile);
    bibfile2.parse();

    keys={};
    titles={};

    # 1st file
    for e in bibfile.bibentries:
        keys[e.key]=1;
        if e.data.has_key("title"):
            tit=e.data["title"].translate(None, delchars);
            tit=tit.lower();
            titles[tit]={'file1':True, 'key1':e.key};
        else:
            print colored("WARNING: ","green")+" in file %s: %s has no title-field"%(
                colored(bibfile.bibfile, "yellow"), colored(e.key,"yellow"))

    # 2nd file
    for e in bibfile2.bibentries:
        if keys.has_key(e.key):
            keys[e.key]=3;
        else:
            keys[e.key]=2;
        if e.data.has_key("title"):
            tit=e.data["title"].translate(None, delchars);
            tit=tit.lower();
        else:
            print colored("WARNING: ","green")+" in file %s: %s has no title-field"%(
                colored(bibfile.bibfile, "yellow"), colored(e.key,"yellow"))
        if titles.has_key(tit):
            titles[tit]['file2']=True;
            titles[tit]['key2']=e.key;
        else:
            titles[tit]={'file2':True, 'key2':e.key};

    if matchkey=="key":
        for k in sorted( keys.keys()):
            if keys[k]==1:
                if printing=="file1" or printing=="both":
                    print ">> "+colored(k, "yellow")+" (in file1)"
            elif keys[k]==2:
                if printing=="file2" or printing=="both":
                    print ">> "+colored(k, "green")+" (in file2)"
            else:
                print ">> "+colored(k, "blue")+" (in both)"
    elif matchkey=="title":
        for k in (titles.keys()):
            if titles[k].has_key('file1') and titles[k].has_key('file2'):
                tit=" ".join(bibfile[titles[k]["key1"]].data["title"].split());
                if titles[k]['key1']==titles[k]['key2']:
                    print ">> %s -- %s"%(
                        colored(titles[k]['key1'],"blue"),
                        colored(tit, "blue") );
                else:
                    print ">> %s, %s -- %s"%(
                        colored(titles[k]['key1'],"yellow"),
                        colored(titles[k]['key2'],"green"),
                        colored(tit, "blue") );
            elif titles[k].has_key('file1'):
                if printing=="file1" or printing=="both":
                    tit=" ".join(bibfile[titles[k]["key1"]].data["title"].split());
                    print ">> %s -- %s"%(
                        colored(titles[k]['key1'],"yellow"),
                        colored(tit,"yellow"));
            elif titles[k].has_key('file2'):
                if printing=="file2" or printing=="both":
                    tit=" ".join(bibfile2[titles[k]["key2"]].data["title"].split());
                    print ">> %s -- %s"%(
                        colored(titles[k]['key2'],"green"),
                        colored(tit,"green"));
                


def checkpdf( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib checkpdf [-u|m pdfdir]

    Lists all entries containing a pdf and tells the status of the
    corresponding file.
    
    Options:
    * -u -- list all PDFs in pdfdir that are not matched in bibfile
    * -m -- list all PDFs in pdfdir that are matched in bibfile    
    """
    try:
        opts,bargs=getopt.getopt( args, "u:m:")
        opts=dict(opts)
        list_unmatched=opts["-u"] if opts.has_key("-u") else None
        list_matched=opts["-m"] if opts.has_key("-m") else None
        if list_unmatched and list_matched:
            raise getopt.GetoptError(colored("ERROR: choose either -u or -m","red"))
        if list_unmatched:
            pdfdir=list_unmatched
        elif list_matched:
            pdfdir=list_matched
        else:
            pdfdir=None
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__()
        sys.exit()

        
    if pdfdir:
        pdfs=glob.glob(os.path.join(pdfdir,"*.pdf"))
        m_pdfs=[ os.path.basename(e.get_pdf()) if e.get_pdf() else None for e in bibfile.bibentries ]
        for pdf in pdfs:
            pdf=os.path.basename(pdf)
            if list_unmatched and pdf not in m_pdfs:
                print "%s "%pdf,
            if list_matched and pdf in m_pdfs:
                print "%s "%pdf,
    else:
        for e in bibfile.bibentries:
            pdf=e.get_pdf();
            if pdf:
                status=colored("FAILED","red");
                if os.path.isfile(pdf):
                    status=colored("OK", "blue");
                print ">> %s -- %s (%s)"%(e.key,pdf,status)


def splitbytag( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib splitbytag [-u] [-a] outputdir

    Creates separate bibtex-files for each tag, each containing
    bibfile's entries belonging to each tag and all strings/comments.

    Options:
    * -u -- include untagged entry in 'notag.bib'
    * -a -- include all entries in 'all.bib'
    """
    try:
        opts,bargs=getopt.getopt( args, "ua")
        opts=dict(opts)
        untagged=True if opts.has_key("-u") else False
        alltag=True if opts.has_key("-a") else False
        if len(bargs)<1:
            raise getopt.GetoptError(colored("ERROR: need outputdir","red"))
        tagdir=bargs[0];        
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        print __my_doc__()
        sys.exit()

    if not os.path.exists(tagdir):
        os.makedirs(tagdir);
        sys.stderr.write(">> "+colored("creating tagdir","red")+": %s\n"%tagdir);

    open_files={};
    for e in bibfile.bibentries:
        tags=e.get_tags();
        if len(tags)<1 and untagged:
            tags.append("notag")
        if alltag:
            tags.append("all")
        for t in tags:
            if not open_files.has_key(t):
                sys.stderr.write(">> new file: %s\n"%colored(os.path.join(
                    tagdir,"%s.bib"%t),"yellow"));
                open_files[t]=BibtexFile(os.path.join(tagdir,"%s.bib"%t));
                open_files[t].bibcomments=bibfile.bibcomments;
                open_files[t].bibstrings=bibfile.bibstrings;
            open_files[t].bibentries.append(e)
            
    for (k,f) in open_files.iteritems():
        f.save();
    return bibfile

def stats( bibfile, args ):
    """
    Usage: bibmanip.py bibfile.bib stats

    Print some statistics about the bibtex-file.
    """
    print "File: %s"%colored(bibfile.bibfile, "red")
    print " Comments: %i"%len(bibfile.bibcomments)
    print " String  : %i"%len(bibfile.bibstrings)
    pdfentries=[1 if x.get_pdf() else 0 for x in bibfile.bibentries];
    print " Entries : %i (%i with pdf)"%(len(bibfile.bibentries),sum(pdfentries))
    print " Tags    :"
    tags=bibfile.get_tag_count();
    keys=sorted( tags, key=lambda x: tags[x], reverse=True);
    for t in keys:
        print "   %s (%i)"%(colored(t,"yellow"),tags[t])
    
### main file
if len(sys.argv)<3:
    print colored("Usage: %s bibfile.bib <command> [command_args]\n"%
                  sys.argv[0], "yellow",attrs=["bold"]);
    print "Available commands: "+colored(", ".join(commands), "green", attrs=["bold"])+"\n"
    for c in commands:
        print "==%s"%colored(c,color="green",attrs=["bold"])
        print eval(c).__doc__
    sys.exit();

bibfilename=sys.argv[1];
if not os.path.exists(bibfilename):
    print colored("ERROR: ","red")+"%s does not exist"%colored(bibfilename,"green");
    sys.exit();
command=sys.argv[2];
if not dict([(x,0) for x in commands]).has_key(command):
    print colored("ERROR","red")+" -- do not know command %s"%colored(command,"yellow")
    sys.exit();
    
args=sys.argv[3:];
bib=BibtexFile(bibfilename);
bib.parse();

# add a comment about the current operation
comment=BibtexComment("Modified by call: \'%s\' (%s)"%(" ".join(sys.argv),time.asctime()));
bib.bibcomments.append(comment);

# run the command
bib=eval("%s(bib,args)"%(command));


