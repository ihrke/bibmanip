#!/usr/bin/python
"""
* bibtex parser that does a  minimum of touching the bibtex file

BUGS & Issuses:
* don't know whether BibtexEntryDuplicates works with more than 2 entries in the list

Resolved:
* need a newline at end of file to work! [done]

"""

import re, sys, os
from termcolor import *
from cStringIO import StringIO
delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())

fieldsequence=["author", "editor", "year", "title", "booktitle", "journal", "publisher",
					"volume","number","pages", "month","day", "doi","url", "uri", "abstract","issn",
					"keywords","institution", "copyright", "lccn", "tags","pdf", "comment"]

class BibtexEntry:
	def __init__(self, type, key ):
		self.key = key;
		self.data = {};
		self.org_content="";
		self.btype = type;

	def get_authors(self):
		"""
		Split the author- and editor fields.  Returns a tuple
		(authors,editors), each entry is an ordered list of dictionaries
		possibly with the entries 'last', 'middle', 'first'.
		"""
		def _parse_author(e):
			## this is the last, first.middle. style
			if e.find(",")>0:
				l=e.split(",")
				last=l[0]
				rest=l[1:]
			## this is the "first middle lastname" style
			else:
				l=e.split(" ")
				last=l[len(l)-1]
				rest=l[0:(len(l)-1)]

			## rest is now a list of some stuff
			rest=" ".join( ((" ".join(rest)).replace("."," ")).split() )
			rest=re.sub( r"([A-Z])([A-Z])", r"\g<1> \g<2>", rest )
			l=rest.split()
			first = l[0] if len(l)>0 else None
			middle= ". ".join(l[1:]) if len(l)>1 else None
			return (first, middle, last)


		au=[];
		ed=[];
		if self.data.has_key("author"):
			r=" ".join(self.data["author"].split())
			r=r.split(" and ")
			for e in r:
				(first,middle,last)=_parse_author(e)
				au.append( {'last':last,'middle':middle,'first':first} )
		if self.data.has_key("editor"):
			r=self.data["editor"].replace("\n","").split(" and ")
			for e in r:
				(first,middle,last)=_parse_author(e)
				ed.append( {'last':last,'middle':middle,'first':first} )

		return (au if len(au)>0 else None, ed if len(ed)>0 else None)

	def compare_by_title(self, entry):
		"""return True if the title of self and entry BibtexEntry correspond"""
		if self.data.has_key("title"):
			stit=self.data["title"].translate(None, delchars);
		else:
			stit=None;
		if entry.data.has_key("title"):
			etit=entry.data["title"].translate(None, delchars);
		else:
			etit=None;
		return stit==etit

	def parse_fields(self):
		"""
		create the data-dict from org_content
		"""
		re_fields=re.compile(r"([\w-]+)\s*=\s*({.*?}|\".*?\"|\S*?)"
									"[\s*,]\s*(?=[\w-]+\s*=|\s*$)", re.DOTALL);
		fields=re_fields.finditer( self.org_content );
		for field in fields:
			lab=field.groups()[0].strip().lower();
			val=field.groups()[1].strip();
			if val[-1]==",":
				val=val[0:-1];
			if (val[0]=="\"" and val[-1]=="\"") or (val[0]=="{" and val[-1]=="}"):
				val=val[1:-1];
			#			val=re.sub("(.+)\s+,$", "\1", val );
			self.data[lab]=val;


	def _calc_tags(self):
		if not self.data.has_key("tags"):
			self.tags=[];
		else:
			sep=";"
			if ";" in self.data["tags"]:
				sep=";"
			elif "," in self.data["tags"]:
				sep=","
			self.tags=[z.replace("}","").replace("{","").strip()
						  for z in  self.data["tags"].split(sep)];

	def get_pdf(self):
		if self.data.has_key("pdf"):
			pdf=re.sub( r"[{\"](.*)[}\"]", r"\1", self.data["pdf"] );
			return pdf
		else:
			return None

	def get_tags(self):
		self._calc_tags();
		return self.tags
			
	def add_tag(self, tags):
		self._calc_tags();
		if isinstance(tags,list):
			self.tags=self.tags+tags;
		else:
			self.tags.append(tags);
		self.tags=list(set(self.tags));
		self.tags.sort();		
		self.data["tags"]="{%s}"%(";".join(self.tags));

	def re_match(self, pattern, re_flags=re.DOTALL, use_org_content=True):
		if re.search( pattern, self.org_content, re_flags ):
			return True;
		else:
			return False;

	def tohtml(self):
		result = StringIO()
		result.write("NOT IMPLEMENTED")
		return result.getvalue()

	def __str__(self):
		result = StringIO()

		result.write("@%s{%s,\n" % ( self.btype.lower().strip(), self.key.strip() ))

		keys=self.data.keys();

		for k in fieldsequence:
			if k in keys:
				result.write("  %s = {%s},\n" % ( k.strip(), self.data[k].strip() ))
				del keys[keys.index(k)]

		for k in keys:
			result.write("  %s = {%s},\n" % ( k.strip(), self.data[k].strip() ))

		result.write('}\n')

		return result.getvalue()

class BibtexEntryDuplicate:
	def __init__(self, entries, colourize=False, rm_linebreaks=True):
		self.entries=entries
		self.colourize=colourize
		self.rmlinebreaks=rm_linebreaks

	def _get_key_count(self):
		keys={};
		for e in self.entries:
			for k in e.data.keys():
				if keys.has_key(k):
					keys[k]+=1
				else:
					keys[k]=1
		return keys;
			
		
	def __str__(self):
		cols=['red','green','yellow','blue','magenta','cyan'];

		r = StringIO()

		for i in range(len(self.entries)):
			e=self.entries[i];
			if self.colourize:
				r.write(colored("@%s{%s,\n" %(e.btype.lower().strip(), e.key.strip() ),
									 cols[i %len(cols)]))
			else:
				r.write("#%i:@%s{%s,\n" % ( i+1,e.btype.lower().strip(), e.key.strip() ))
				
		keycounts=self._get_key_count();
		keys=sorted( keycounts, key=lambda x: keycounts[x], reverse=True);
		for k in keys:
			c=keycounts[k];
			tmp=self.entries[0].data[k].strip() if self.entries[0].data.has_key(k) else None;
			identical=all([ True if x.data.has_key(k) and x.data[k].strip()==tmp else False for x in self.entries]);
			for i in range(len(self.entries)):
				e=self.entries[i];
				if e.data.has_key(k):
					dat=e.data[k].strip()
					if self.rmlinebreaks:
						dat=" ".join(e.data[k].split());
					if self.colourize and c>1 and not identical:
						r.write(colored("  %s = {%s},\n"%( k, dat ),cols[i % len(cols)]) )
					elif not identical and c==1:
						r.write("  %s = {%s},\n"%(k,dat))
					else:
						r.write("  %s%s = {%s},\n"%( "#%i:"%(i+1) if c>1 and not identical else "",
															k, dat ))
				if identical: break

		r.write('}\n')

		return r.getvalue()	
		

class BibtexString:
	"""
	Defines bibtex-entries:
	  @string
	"""
	def __init__(self, label, value):
		self.label=label;
		self.value=value;
	def __str__(self):
		result = StringIO()
		result.write("@string{%s=\"%s\"}\n"%(self.label, self.value));
		return result.getvalue();

class BibtexComment:
	"""
	Defines bibtex-entries:
	  @comment
	"""
	def __init__(self, value ):
		self.value=value;
	def __str__(self):
		result = StringIO()
		result.write("@comment{%s}\n"%(self.value));
		return result.getvalue();

	

class BibtexFile:
	def __init__(self, fname=None):
		self.bibfile=fname;
		if self.bibfile and os.path.exists(fname):
			bib_file = open(self.bibfile, "r")
			self.bibtexcontent=bib_file.read();
			bib_file.close();
		else:
			self.bibtexcontent="";
		self.bibcomments=[];
		self.bibstrings=[];
		self.bibentries=[];
		self.tag_counts={};

	def save(self, fname=None):
		"""write to file"""
		if not fname:
			fname=self.bibfile;
		f=open(fname,"w");
		f.write(str(self));
		f.close();

	def get_tag_count(self):
		"""return dict with tag as key and count in file as val"""
		self.tag_counts={};
		for e in self.bibentries:
			for t in e.get_tags():
				if self.tag_counts.has_key(t):
					self.tag_counts[t]+=1;
				else:
					self.tag_counts[t]=1;
		return self.tag_counts;

	def __str__(self):
		r = StringIO();
		if len(self.bibcomments)>0:
			for c in self.bibcomments:
				r.write( str(c) );
			r.write("\n");
		if len(self.bibstrings)>0:			
			for l in self.bibstrings:
				r.write( str(l) );
			r.write("\n");
		if len(self.bibentries)>0:						
			for e in self.bibentries:
				r.write( str(e) );
			r.write("\n");			
		return r.getvalue();

	def __getitem__(self,key):
		"""allow indexing with bibtex-key"""
		for e in self.bibentries:
			if e.key==key:
				return e
		return None
	
	def parse(self):
		if len(self.bibtexcontent)<=0:
			bib_file = open(self.bibfile, "r")
			self.bibtexcontent=bib_file.read();
			bib_file.close();
		bf=self.bibtexcontent			

		# get all strings
		stringpattern=re.compile(r"@string{\s*([a-zA-Z0-9_-]+)\s*=\s*(.*?)\s*}(?=\s*@)", re.DOTALL);
		strings=stringpattern.finditer( bf );
		for s in strings:
			lab=s.groups()[0].strip();
			val=s.groups()[1].strip();
			self.bibstrings.append( BibtexString(lab,val.replace("\"","") ));

		# get all comments
		commentpattern=re.compile(r"@comment{(.*?)}(?=\s*@)", re.DOTALL);
		comments=commentpattern.finditer( bf );
		for c in comments:
			val=c.groups()[0].strip();
			self.bibcomments.append( BibtexComment(val) );

		# get the entries
		btentry=re.compile(r"@(article|book|inproceedings|incollection|booklet"
								 r"|conference|inbook|manual|misc|phdthesis|proceedings|"
								 r"mastersthesis|techreport|unpublished){(.+?),(.*?)}\s*(?=@|\s*$)",
								 re.DOTALL|re.IGNORECASE);
		btentries= re.finditer( btentry, bf );

		for entry in btentries:
			type=entry.groups()[0].strip();
			key=entry.groups()[1].strip();
			content=entry.groups()[2];

			current=BibtexEntry( type, key );
			current.org_content=content;
			current.parse_fields();

			self.bibentries.append( current );

## example usage
if __name__=="__main__":
	if len(sys.argv)<2:
		print "Usage: %s file.bib"%(sys.argv[0]);
		sys.exit()
		
	bib=BibtexFile(sys.argv[1]);
	bib.parse();
	print bib
