Example:
--------

Merging two files with partially overlapping entries

1. simple append the files
```shell
 cat file1.bib > bfile.bib
 cat file2.bib >> bfile.bib
```

2. detect duplicates
```shell
 bibmanip.py bfile.bib duplicates -o dup.bib
```

3. cut these from the original file
```shell
 x=`bibmanip.py bfile.bib listkeys -p`
 bibmanip.py bfile.bib cutentries -o new.bib -d $x
```

4. merge the duplicates in dup.bib by hand (differences are highlighted)
5. combine the files
```shell
 cat dub.bib >> new.bib
```
