#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Creates a country database with ISO 2 and ISO 3 character codes, ISO number,
name and international dialing codes.

The data comes from three sources:

    * United Nations statistics
    * WorldAtlas.com
    * Wikipedia

This code merges data from the three sources, considering the UN data
to be most up-to-date (demonstrably so at the time of writing) and
applies some changes, such as renaming "Viet Nam" "Vietnam" and calling
the Vatican "HOLY SEE (VATICAN CITY STATE)" rather than just "Holy See"
which may bypass many.

In electing to use UN names where possible it is likely that some may not
be considered politically appropriate in some areas. We have chosen not to
impose our opinion and thus take the UN nomenclature without modification.

Based on screen-scraping, this is almost certainly going to break at some point
in the future. We will attempt to keep it updated.

Usage:
    ./build.py           # output csv to stdout
    ./build.py -t json   # output json to stdout
    ./build.py -v        # as above, but noise comes to stderr
    ./build.py -i        # as above, but ignore entities with no IDC
"""
import csv
import json
import sys
import re
import urllib2
from optparse import OptionParser

from tidylib import tidy_document
from BeautifulSoup import BeautifulSoup


# map countries as in Wikipedia to countries as in UN data
COUNTRY_MAPPINGS = {
    # 'WIKIPEDIA NAME': 'OUR DATA NAME (GENERALLY UN SOURCED)',
    'UNITED STATES': 'UNITED STATES OF AMERICA',
    'SAINT MARTIN (FRANCE)': 'SAINT-MARTIN (FRENCH PART)',

    'SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS':
    'SOUTH GEORGIA AND SOUTH S.S.',

    'CARIBBEAN NETHERLANDS': 'NETHERLANDS ANTILLES',
    'LAOS': "LAO PEOPLE'S DEMOCRATIC REPUBLIC",
    'BURMA': 'MYANMAR',
    'MICRONESIA, FEDERATED STATES OF': 'MICRONESIA (FEDERATED STATES OF)',
    'KOREA, NORTH': "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA",
    'KOREA, SOUTH': 'REPUBLIC OF KOREA',

    'CONGO, DEMOCRATIC REPUBLIC OF THE (ZAIRE)':
    'DEMOCRATIC REPUBLIC OF THE CONGO',

    'US VIRGIN ISLANDS': 'UNITED STATES VIRGIN ISLANDS',
    'MACAU': 'CHINA, MACAO SPECIAL ADMINISTRATIVE REGION',
    'FAROE ISLANDS': 'FAEROE ISLANDS',
    'EAST TIMOR': 'TIMOR-LESTE',
    'PALESTINIAN TERRITORIES': 'STATE OF PALESTINE',
    'VATICAN CITY STATE (HOLY SEE)': 'HOLY SEE (VATICAN CITY STATE)',
    u'SAINT BARTHÉLEMY': u'SAINT-BARTHÉLEMY',
    'SINT MAARTEN (NETHERLANDS)': 'SINT MAARTEN (DUTCH PART)',
    u'SÃO TOMÉ AND PRÍNCIPE': 'SAO TOME AND PRINCIPE',
    'SINT EUSTATIUS': 'BONAIRE, SAINT EUSTATIUS AND SABA',
}


#  countries that have no ISO3/2 or IDC
IGNORE_COUNTRIES = [
    '830',  # CHANNEL ISLANDS
    '680',  # SARK
]


def chunk(s, chunksize):
    """
    Return a list of s chunked into chunksize bits. e.g.

    chunk("abcdefgh", 2) -> ['ab', 'cd', 'ef', 'gh']
    """
    index = 0
    length = len(s)
    chunks = []
    while index < length:
        chunks.append(s[index:index+chunksize])
        index += chunksize
    return chunks


def fix_entities(s):
    """
    Process a string to replace HTML entities with their Unicode equivalents
    """
    return unicode(BeautifulSoup(s,
                                 convertEntities=BeautifulSoup.HTML_ENTITIES))


def download_un_data():
    page = urllib2.urlopen(
        "http://unstats.un.org/unsd/methods/m49/m49alpha.htm")
    # this page has mal-formed tags which break the parse, so let's fix those
    page, _ = tidy_document(page.read(), options={'numeric-entities': 1})
    soup = BeautifulSoup(page)

    table = soup.findAll('table',
                         attrs={'border': '0',
                                'cellpadding': '2',
                                'cellspacing': '0'}
                         )[0]

    rows = table.findAll('tr')[1:]

    country_dict = {}
    for row in rows:
        number, name, iso3 = [x.text for x in row.findAll('td')]
        if number in IGNORE_COUNTRIES:
            continue
        # fix a quirk or two
        if name == 'Viet Nam':
            name = 'Vietnam'
        if name == 'Holy See':
            name = 'Holy See (Vatican City State)'
        country_dict[iso3] = dict(number=number,
                                  name=fix_entities(name),
                                  iso3=iso3)

    return country_dict


def download_worldatlas_data():
    page = urllib2.urlopen("http://www.worldatlas.com/aatlas/ctycodes.htm")
    soup = BeautifulSoup(page)

    table = soup.findAll('table',
                         attrs={'width': '870',
                                'cellpadding': '0',
                                'cellspacing': '0'}
                         )[0]
    iso2_list = chunk(table.findAll('td')[0].text[2:], 2)
    iso3_list = chunk(table.findAll('td')[1].text[2:], 3)
    number_list = chunk(table.findAll('td')[2].text[3:], 3)

    # getting the countries a little more tedious
    s = table.findAll('td')[3].prettify()
    s = s.replace('<br />', '|')
    s = s.replace('\n', '')
    s = s.replace('</font>', '')
    s = s.replace('<font>', '')
    s = s[s.find('|'):]
    s = s.replace('</td>', '')
    name_list = [fix_entities(x.strip()) for x in s.split('|') if x.strip()]
    merged = zip(iso2_list, iso3_list, number_list, name_list)

    # now make a dict keyed on iso3
    keys = ['iso2', 'iso3', 'number', 'name']
    country_dict = {}
    for row in merged:
        country_dict[row[1]] = dict(zip(keys, row))

    return country_dict


def download_wikipedia_idc():
    """
    Download IDC list from wikipedia.
    """
    url = 'http://en.wikipedia.org/wiki/International_dialing_codes'
    req = urllib2.Request(url,
                          headers={'User-Agent':
                                   'Mozilla/5.0 (X11; U; Linux i686)'})
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page)
    rows = soup.findAll('table',
                        attrs={'class':
                               'wikitable sortable'})[0].findAll('tr')[1:]

    country_codes = {}
    for row in rows:
        country, numbers = [td.text for td in row.findAll('td')]
        country = fix_entities(country)
        numbers = re.sub('\[.*\]', '', numbers)
        numbers = [n.strip() for n in numbers.split(',')]
        numbers = [n[n.find('+'):] for n in numbers if n]
        country_codes[country.upper()] = numbers

    return country_codes


def reindex(dataset, key):
    """
    Take a dict of dicts and return a new dict keyed on the
    value of the named key in the data
    """
    newdict = {}
    for data in dataset.values():
        newdict[data[key]] = data

    return newdict


def blend_un_wad(und, wad):
    """
    Blend UN data (und) and World Atlas data (wad). WAD is larger and
    they disagree only in the ISO number so create new set with both.
    There has been found to be a discrepency in ISO3 code with Romania where
    the World Atlas appears wrong. There's also a discrepency with East Timor/
    Timor-Leste

    Therefore to merge UN into World Atlas:

    * if both UN and WA data are available for the ISO3 code, and the
      numbers differ, assign over the UN number.

    * if there is no UN data for the ISO3 code, check for a record of the
      same ISO Number code. If found, assign ISO3 and uppercase name

    We also user UN Names rather than WA names.

    Next we merge unique entries in the UN data into our blended set.
    """

    newdata = wad.copy()
    patched = []
    isonum = reindex(und, 'number')

    for iso3, data in newdata.items():
        PATCHED = False
        try:
            undata = und[iso3]
            unname = undata['name'].upper()
            if data['number'] != undata['number']:
                PATCHED = True
            if data['name'] != unname:
                PATCHED = True
            data['number'] = undata['number']
            data['name'] = unname
        except KeyError:
            # just in case ISO3 differs at the UN, check with the ISO number
            try:
                undata = isonum[data['number']]
                oldiso3 = iso3
                iso3 = undata['iso3']
                data['iso3'] = iso3
                data['name'] = undata['name'].upper()
                newdata[iso3] = data
                del(newdata[oldiso3])
                
                PATCHED = True
            except KeyError:
                # OK - there really is no UN entry for this country
                pass
        if PATCHED:
            patched.append(data)
        newdata[iso3] = data

    uniso3 = set(und.keys())
    blendiso3 = set(newdata.keys())
    missing_iso3 = list(uniso3 - blendiso3)

    for iso3 in missing_iso3:
        data = und[iso3]
        data['iso2'] = ''
        data['name'] = data['name'].upper()
        newdata[iso3] = data
        patched.append(data)

    return newdata, patched


def _split_numbers(numbers):
    """
    Receive a list of IDCs and IDC+region code and split into
    a dict to augment the country data.
    """
    result = {}
    # remove '+' prefix and split IDC from area code
    numbers = [x.replace('+', '').strip().split(' ') for x in numbers]
    idc = numbers[0][0]
    result['idc'] = idc

    if len(numbers[0]) > 1:
        region_codes = [x.pop(1) for x in numbers]
        regions = ['region_a', 'region_b', 'region_c', 'region_d']

        for rc in region_codes:
            result[regions.pop(0)] = rc

    return result


def map_numbers(data, country_codes, verbose=False):
    """
    Augments data with IDC codes. Change is in-place; function returns nothing.
    """
    byname = reindex(data, 'name')

    for country, numbers in country_codes.items():
        if country in COUNTRY_MAPPINGS:
            country = COUNTRY_MAPPINGS[country]
        try:
            data = byname[country]
            # Vatican is assigned +379 but does not use it, so remove
            # this solitary weird point
            if country == 'HOLY SEE (VATICAN CITY STATE)':
                numbers = ['+39 066']
            data.update(_split_numbers(numbers))
        except KeyError:
            possible_countries = [c for c in byname.keys()
                                  if c.find(country) >= 0]
            if len(possible_countries) == 1:
                data = byname[possible_countries[0]]
                data.update(_split_numbers(numbers))
                if verbose:
                    sys.stderr.write("{} --> {}\n"
                                     .format(country, possible_countries[0]))
            elif len(possible_countries) > 1:
                if verbose:
                    sys.stderr.write(u"Cannot find {}, possible matches: {}\n"
                                     .format(country, possible_countries))
            else:
                if verbose:
                    sys.stderr.write(u"Cannot find country: {}\n"
                                     .format(country))


def output_csv(data):
    """
    Write CSV to stdout
    """
    iso3list = data.keys()
    iso3list.sort()
    columns = ['number', 'iso3', 'iso2', 'name', 'idc',
               'region_a', 'region_b', 'region_c', 'region_d']
    try:
        writer = csv.writer(sys.stdout)
        writer.writerow(columns)
        for iso3 in iso3list:
            entry = data[iso3]
            writer.writerow([entry.get(c, '').encode('utf-8')
                             for c in columns])
    finally:
        sys.stdout.flush()


def make_dataset(format, verbose, ignore):
    und = download_un_data()
    wad = download_worldatlas_data()
    blend, patched = blend_un_wad(und, wad)
    country_codes = download_wikipedia_idc()
    map_numbers(blend, country_codes, verbose)

    if ignore:
        # strip out entries with no IDC
        iso3list = blend.keys()
        for iso3 in iso3list:
            if blend[iso3].get('idc', '') == '':
                del(blend[iso3])

    if format == 'csv':
        output_csv(blend)
    elif format == 'json':
        print(json.dumps(blend, indent=4))

    if verbose:
        for data in blend.values():
            sys.stderr.write(u"{}\t {}\t {}\n".format(data['iso2'],
                                                      data['iso3'],
                                                      data['name'],))

        sys.stderr.write("{} entities in database\n".format(len(blend)))
        sys.stderr.write("{} entities with numbers\n"
                         .format(len([x for x in blend.keys()
                                      if blend[x].get('idc', None)])))
        sys.stderr.write("{} patched entities\n".format(len(patched)))


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-v', '--verbose',
                      action='store_true',
                      default=False,
                      help='Show verbose output')
    parser.add_option('-i', '--ignore-no-idc',
                      action='store_true',
                      dest='ignore',
                      default=False,
                      help='Do not output countries for which we have '
                           'no IDC')
    parser.add_option('-t', '--format',
                      action='store',
                      choices=['csv', 'json'],
                      default='csv',
                      help='Output format: json or csv (default)')

    options, args = parser.parse_args()
    make_dataset(options.format, options.verbose, options.ignore)
