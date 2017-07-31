#!/usr/bin/env python3
from casp12.files.targets import find_targets, guess_casp_experiment, pcons_domain_specifications, pcons_write_domain_file
from sqlite3 import connect

'''
 Write pcons domain definition (ignore) files into given CASP datadir
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
        "casp12_pcons_domain_defs  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
    ])


# Library functions


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Write pcons domain definition files into CASP datadirs")
    parser.add_argument(
        "-a", action="store_true", default=False, help="Prints nothing")
    parser.add_argument(
        "-db", nargs=1, metavar="file",
        help="Domain definition database")
    parser.add_argument(
        "-method", nargs=1, default=[None], metavar="str",
        help="Domain partition method name, default=None")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "files", nargs="*", metavar="PATH", help="Pathways to CASP data")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files

    # Set variables here
    sqlite_file = arguments.db[0]
    method = arguments.method[0]
    targets = {}
    target_casp = {}

    # Parse CASP experiments for targets
    for path in files:
        # Identify experiment
        casp = guess_casp_experiment(path)
        # Find targets in experiment
        newtargets = find_targets(path)
        # Assign casp experiment
        for target in newtargets:
            target_casp[target] = casp
        # Append target paths
        targets = {**targets, **newtargets}

    # Read domain definitions and write pcons ignore files
    database = connect(sqlite_file)
    for target in targets:
        ignore_residues = pcons_domain_specifications(target_casp[target], target, database)
        pcons_write_domain_file(targets[target], ignore_residues, method=method)


if __name__ == '__main__':
    main()
