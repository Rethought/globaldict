GlobalDict
==========

In needing to find an authoritative source of countries and dialing codes I ran
into an interesting problem. One might imagine a single authoritative source,
and maybe a nice United Nations or ITU downloadable CSV file kept up to date
and in good shape, but it seems it's a little tricky. Plenty of people have been
very generous in posting databases but not all are up to date.

This package attempts to create a database based on a number of sources to
achieve what we hope is a reasonable starter point.

Other databases exist on the web in various forms, and a few of them are
in handy machine readable form. However it is not common to find a datasource
that is either complete and authoritative or has associated code that can
regenerate the database from original sources. This package aims to do that.

The data available are:

Country name
Formal name
ISO 316-1 2 letter country code
ISO 316-1 3 letter country code
ISO 316-1 number
ITU-T international dialing code
ITU-T area code (e.g. for countries in North American Numbering system where
one dials +1 xxx, we term xxx the area code)

Local changes
-------------

UN names are used in preference to others where possible, but we have chosen
to ignore the UNstats.un.org spelling of "Viet Nam" in favour of "Vietnam".


Telephone numbers
-----------------

The output data contains IDCs and for countries/territories in the North
American Numbering Plan Area we include the area code in the field
'Region X' where X is A through D on account of some territories sharing
and IDC with others and having a limited set of area codes that, together
with the IDC, identify the country.

Completeness and beauty
-----------------------

The data have obvious holes and come with no guarantee of completeness. We
do intend to continue building the dataset and plugging holes with the aim
of ensuring that the set is always regenerable from the source material.

This code is also not beautiful and, contrary to our normal practice, comes
with no tests so its correct functioning is not certain at the lowest level.

Data sources
------------

* http://unstats.un.org/unsd/methods/m49/m49alpha.htm
* http://www.worldatlas.com/aatlas/ctycodes.htm 
  * some of the country numbers disagree with the UN site so we consider the UN site to be more authoritative
* https://en.wikipedia.org/wiki/List_of_country_calling_codes

* http://www.famfamfam.com/lab/icons/flags/
  * flags of the world

We believe it to be acceptable to draw on these sources but would invite
site owners to contact one of the contributors in the event that this has been
mis-understood.

Usage
=====

The file `requirements.txt` contains the Python dependencies. These may, in
turn, depend on other libraries which may or may not already be present on your
system. YMMV.

Install the requirements then run::

  $ python build.py > numbers.csv

For JSON output::

  $ python build.py -t json > numbers.json

To see some logging, you can make this verbose::

  $ python build.py -v

To ignore all entities for which we've not ascertained an IDC::

  $ python build.py -i

A note on politics
==================

In electing to use UN names where possible it is likely that some may not
be considered politically appropriate in some areas. We have chosen not to
impose our opinion and thus take the UN nomenclature without modification.
