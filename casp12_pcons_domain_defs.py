#!/usr/bin/env python3
from casp12.interface.pcons import pcons_domain_specifications, pcons_write_domain_files
from casp12.interface.targets import find_targets, guess_casp_experiment
from casp12.casp12_pcons_domains import read_target_selection
from sqlite3 import connect

'''
 Write pcons domain definition (ignore) interface into given CASP datadir
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
        description="Write pcons domain definition interface into CASP datadirs")
    parser.add_argument(
        "-db", nargs=1, metavar="file",
        help="Domain definition database")
    parser.add_argument(
        "-method", nargs=1, metavar="int",
        help="Domain partition method ID")
    parser.add_argument(
        "-targets", nargs=1, default=[None], metavar="str",
        help="Target selection [target1,target2,target3,etc.], default=None")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "files", nargs="*", metavar="PATH", help="Pathways to CASP data")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files

    # Set variables here
    sqlite_file = arguments.db[0]
    method = int(arguments.method[0])
    target_list = arguments.targets[0]
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

    # Check if selection is specified, otherwise run over all targets found
    if target_list is not None:
        target_list = read_target_selection(target_list)
    else:
        target_list = set(targets.keys())

    # Read domain definitions and write pcons ignore interface
    database = connect(sqlite_file)
    for target in target_list:
        ignore_residues = pcons_domain_specifications(target_casp[target],
                                                      target, database, method)
        print(ignore_residues)
        pcons_write_domain_files(targets[target], ignore_residues, method=method)


if __name__ == '__main__':
    main()
