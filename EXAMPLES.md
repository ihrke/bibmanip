Example:
--------

### Merging two files with partially overlapping entries ###

* concatenate the files

```shell
 cat file1.bib > bfile.bib
 cat file2.bib >> bfile.bib
```

* detect duplicates and output to dup.bib (output for merging)

```shell
 bibmanip.py bfile.bib duplicates -o dup.bib
```

* cut the duplicates from the original file (for concatenating after merging)

```shell
 x=`bibmanip.py bfile.bib listkeys -p`
 bibmanip.py bfile.bib cutentries -o new.bib -d $x
```

* merge the duplicates in dup.bib by hand (differences are highlighted)
* combine the files

```shell
 cat dub.bib >> new.bib
```
