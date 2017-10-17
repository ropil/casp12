#!/usr/bin/env python3
from re import compile
from sqlite3 import connect
from casp12.database import get_or_add_method, save_or_dump
from casp12.interface.filesystem import find_all_files
from casp12.interface.casp import parse_lga_sda_summary, process_casp_sda


'''
 Parse all downloaded CASP12 LGA_SDA QA-files
 Copyright (C) 2017  Robert Pilstål

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.
'''


# Version and license information
def get_version_str():
    return "\n".join([
        "casp12_parse_lga_sda  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
    ])


# Library functions
def add_file(f, m, index):
    target = m.group(1)
    if target not in index:
        index[target] = []
    # Target -> file
    index[target].append(f)


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Parse all CASP_LGA_SDA-files found")
    parser.add_argument(
        "-casp", nargs=1, default=["12"], metavar="int",
        help="CASP integer experiment ID, default=12")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "directory", nargs=1, metavar="DIR", help="Directory in which to find files")
    parser.add_argument(
        "database", nargs=1, metavar="FILE",
        help="SQLite3 database file to store QA in")
    arguments = parser.parse_args(argv[1:])

    # Set variables here
    files = find_all_files(arguments.directory[0])
    m_summary_full = compile("(T.\d+)\.SUMMARY\.lga_sda\.txt\Z")
    m_summary_domain = compile("(T.\d+)-D(\d+)\.SUMMARY\.lga_sda\.txt\Z")
    m_model = compile("(T.\d+)TS(\d+)_(\d+)\.lga\Z")
    m_model_domain = compile("(T.\d+)TS(\d+)_(\d+)-D(\d+)\.lga\Z")
    casp = int(arguments.casp[0])
    databasefile = arguments.database[0]
    database = connect(databasefile)

    qa_method_name = "CASP{}_LGA_SDA".format(casp)
    qa_method_desc = "CASP{} LGA_SDA measure added by casp12_parse_lga_sda.py".format(casp)
    qa_method_type = "qa"

    qa_method = get_or_add_method(qa_method_name, qa_method_desc, qa_method_type, database)

    # Identify files
    summaries = {}
    domainsummaries = {}
    models = {}
    domainmodels = {}
    for f in files:
        m = m_model.search(f)
        if m:
            add_file(f, m, models)
            continue
        m = m_model_domain.search(f)
        if m:
            add_file(f, m, domainmodels)
            continue
        m = m_summary_full.search(f)
        if m:
            add_file(f, m, summaries)
            continue
        m = m_summary_domain.search(f)
        if m:
            add_file(f, m, domainsummaries)
            continue

    # Read summaries to get global scores
    globalscores = {}
    for target in summaries:
        with open(summaries[target][0], 'r') as infile:
            globalscores[target] = parse_lga_sda_summary(infile)

    # Parse all local score tables
    for target in models:
        for modelfile in models[target]:
            with open(modelfile, 'r') as infile:
                qa = process_casp_sda(infile, globalscores, qa_method, database)

    # Save database
    save_or_dump(database, databasefile)


if __name__ == '__main__':
    main()
