#!/usr/bin/env python3
from casp12.interface.pcons import run_pcons, read_pcons, \
    write_scorefile, pcons_write_model_file, get_scorefile_name, which
from casp12.interface.targets import find_targets, guess_casp_experiment, \
    find_models, get_length
from casp12.database import get_or_add_method, store_qa, store_models_and_servers, save_or_dump
from sqlite3 import connect

'''
 Run vanilla PCONS on a CASP dataset
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
        "casp12_pcons  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
    ])


# Library functions
def read_target_selection(selection):
    return set(selection.split(','))


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Run vanilla PCONS on CASP datadirs")
    parser.add_argument(
        "-d0", nargs=1, default=[3.0], metavar="float",
        help="D0 measure in score/distance conversions, default=3.0")
    parser.add_argument(
        "-db", nargs=1, metavar="file",
        help="database containing protein lengths")
    parser.add_argument(
        "-pcons", nargs=1, default=["pcons"], metavar="str",
        help="Location of pcons binary, if not in path etc.")
    parser.add_argument(
        "-targets", nargs=1, default=[None], metavar="str",
        help="Target selection [target1,target2,target3,etc.], default=None")
    parser.add_argument(
        "-transform", action="store_true", default=False,
        help="Transform of distances (default=expect scores)")
    parser.add_argument(
        "-write", action="store_true", default=False,
        help="Write out pcons text-files")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "files", nargs="*", metavar="PATH", help="Pathways to CASP data")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files

    # Method definition
    method_name = "vanilla"
    method_desc = "PCONS on full model, vanilla style"
    method_type_name = "qa"

    # Set variables here
    d0 = arguments.d0[0]
    pcons = arguments.pcons[0]
    sqlite_file = arguments.db[0]
    targets = {}
    target_list = arguments.targets[0]
    target_casp = {}
    transform = arguments.transform
    write = arguments.write

    pcons = which(pcons)

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

    # Insert vanilla method, if not found
    database = connect(sqlite_file)
    method = get_or_add_method(method_name, method_desc, method_type_name, database)

    # Run PCONS for each target
    for target in target_list:
        casp = target_casp[target]
        targetdir = targets[target]
        models = find_models(targetdir)
        # print(models)
        modelfile = pcons_write_model_file(targetdir, models)
        # print(modelfile)
        length = get_length(target, database)
        pcons_results = read_pcons(run_pcons(modelfile, total_len=length, d0=d0, pcons_binary=pcons), transform_distance=transform, d0=3)
        # Store new servers and models
        (servers, modeltuples, filenames, servermethods,
         model_id) = store_models_and_servers(target, pcons_results, database)
        # Store data in database directives here below
        for model in pcons_results[0]:
            thisid = model_id[modeltuples[model]]
            store_qa(thisid, pcons_results[0][model], pcons_results[1][model], method, database)
        # output the joint model using the output function and naming convention
        if write:
            scorefile = get_scorefile_name(targetdir, method=method, partitioned=False)
            with open(scorefile, 'w') as outfile:
                write_scorefile(outfile, pcons_results[0], pcons_results[1], d0=d0, transform=transform)

    # commit and close database
    save_or_dump(database, sqlite_file)


if __name__ == '__main__':
    main()
