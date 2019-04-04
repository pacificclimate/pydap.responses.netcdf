News
====

0.6.0
-----

*Release date: 2019-04-04*

* Changes to NetCDF 64-bit Offset Format to support files (without record variables) greater than 2 GiB.

0.5.4
-----

*Release date: 2019-03-15*

* Fixes bug in padding emission for variables with dtype short or char (or anything < 4 bytes)

0.5.3
-----

*Release date: 2019-03-11*

* Fixes bug where datasets without record variable fall into an infinite loop
