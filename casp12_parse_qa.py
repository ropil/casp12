#!/usr/bin/env python3
from re import compile
from sqlite3 import connect
from casp12.database import get_caspserver_method, get_caspserver_name, get_method_type, update_caspserver_method, get_or_add_method, save_or_dump
from casp12.interface.filesystem import find_all_files
from casp12.interface.casp import get_filename_info, process_casp_qa, QAError
from casp12.definitions import method_type


'''
 Parse all downloaded CASP QA-files
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
        "casp12_parse_qa  Copyright (C) 2017  Robert Pilstål;",
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
        description="Parse all CASP QA-files found")
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
    m_model = compile("(T.\d+)QA(\d+)_(\d+)\Z")
    casp = int(arguments.casp[0])
    databasefile = arguments.database[0]
    database = connect(databasefile)

    qa_method_type = "qa"

    # Identify files
    models = {}
    domainmodels = {}
    for f in files:
        m = m_model.search(f)
        if m:
            add_file(f, m, models)

    # Parse all local score tables
    for target in models:
        for modelfile in models[target]:
            (target, casp_method_type, server, model_name) = get_filename_info(modelfile)
            qa_method = get_caspserver_method(database, server)
            # This ugly hack will relink the CASP server to point to a QA method.
            # It will be removed when the database is properly rewritten.
            if qa_method is not None:
                qa_method_type_id = get_method_type(database, qa_method)
                if qa_method_type_id != method_type[qa_method_type]:
                    qa_method = None
            if qa_method is None:
                # Add method
                server_name = get_caspserver_name(database, server)
                qa_method = get_or_add_method(server_name, "", qa_method_type, database)
                update_caspserver_method(database, server, qa_method)
            with open(modelfile, 'r') as infile:
                try:
                    qa = process_casp_qa(infile, qa_method, database)
                except QAError:
                    print("Skipping {} : No QAs found".format(target))

    # Save database
    save_or_dump(database, databasefile)


if __name__ == '__main__':
    main()
