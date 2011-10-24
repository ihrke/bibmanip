bibmanip
========

This is a script that handles some of the more common tasks I need to do with my bibtex-files. 

See

```shell
bibmanip -h
```

for a list of the available subcommands (this list is also in HELP.txt).

For some examples, see [Examples](Examples.md).

Things to know
--------------

I have some functionality for "tags" which I use pretty much as citeulike does. 
Any bibtex-entry may have a field 

```
tags={tag1;tag2;tag3}
```

and the scripts can operate on them (e.g., split a master.bib file into separate tag1.bib, tag2.bib, ... files)


Notes
-----

bibmanip does not have a "real" parser. It relies purely on regular expressions, to parse the bibtex files and I had to add a some regex magic to get it to work. 

So far, it worked for all bibtex-files I used (and those came from citeulike, mendely, Papers (mac) and handwritten files).

I'm not sure that I didn't miss some specific example in which my regular expressions do not work though. Be warned!




