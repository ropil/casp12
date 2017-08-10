#!/usr/bin/env python3
from casp12.interface.pcons import join_models, run_pcons, read_pcons, \
    write_scorefile, pcons_get_domain_file_name, pcons_get_model_file_name, \
    pcons_write_model_file
from casp12.interface.targets import find_targets, guess_casp_experiment, \
    get_domain, find_models, get_length
from sqlite3 import connect

'''
 Run PCONS using domain definitions
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
        "casp12_pcons_domains  Copyright (C) 2017  Robert Pilstål;",
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
        description="Run PCONS using domain definitions on CASP datadirs")
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

    # Run PCONS for each target and domain, then join the PCONS models
    database = connect(sqlite_file)
    for target in targets:
        casp = target_casp[target]
        domains = get_domain(casp, target, database)
        targetdir = targets[target]
        models = find_models(targetdir)
        pcons_write_model_file(targetdir, models)
        modelfile = pcons_get_model_file_name(targetdir)
        length = get_length(casp, target, database)
        pcons_results = []
        for domain in domains:
            ignorefile = pcons_get_domain_file_name(targetdir, domain,
                                                         method=method)
            pcons_results.append(run_pcons(modelfile, length, d0=d0, ignore_file=ignorefile))
        # Join the models here using joining function on the output
        # output the joint model using the output function and naming convention

if __name__ == '__main__':
    main()
