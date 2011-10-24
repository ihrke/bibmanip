bibmanip
========

This is a script that handles some of the more common tasks I need to do with my bibtex-files. 

See

```shell
bibmanip -h
```

for a list of the available subcommands.


Notes
-----

bibmanip does not have a "real" parser. It relies purely on regular expressions, to parse the bibtex files and I had to add a some regex magic to get it to work. 

So far, it worked for all bibtex-files I used (and those came from citeulike, mendely, Papers (mac) and handwritten files).

I'm not sure that I didn't miss some specific example in which my regular expressions do not work though. Be warned!




