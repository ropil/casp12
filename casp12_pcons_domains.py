#!/usr/bin/env python3
from casp12.interface.pcons import join_models, run_pcons, read_pcons, \
    write_scorefile, pcons_get_domain_file_name, pcons_get_model_file_name, \
    pcons_write_model_file, get_scorefile_name, which
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
def read_target_selection(selection):
    return set(selection.split(','))


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Run PCONS using domain definitions on CASP datadirs")
    parser.add_argument(
        "-d0", nargs=1, default=[3.0], metavar="float",
        help="D0 measure in score/distance conversions, default=3.0")
    parser.add_argument(
        "-db", nargs=1, metavar="file",
        help="Domain definition database")
    parser.add_argument(
        "-method", nargs=1, default=[None], metavar="str",
        help="Domain partition method name, default=None")
    parser.add_argument(
        "-pcons", nargs=1, default=["pcons"], metavar="str",
        help="Location of pcons binary, if not in path etc.")
    parser.add_argument(
        "-targets", nargs=1, default=[None], metavar="str",
        help="Target selection [target1,target2,target3,etc.], default=None")
    parser.add_argument(
        "-transform", action="store_false", default=True,
        help="Disable transform of distances (expect scores)")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "files", nargs="*", metavar="PATH", help="Pathways to CASP data")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files

    # Set variables here
    d0 = arguments.d0[0]
    pcons = arguments.pcons[0]
    sqlite_file = arguments.db[0]
    method = arguments.method[0]
    targets = {}
    target_list = arguments.targets[0]
    target_casp = {}
    transform = arguments.transform

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

    # Run PCONS for each target and domain, then join the PCONS models
    database = connect(sqlite_file)
    for target in target_list:
        casp = target_casp[target]
        domains = get_domain(casp, target, database)
        targetdir = targets[target]
        models = find_models(targetdir)
        print(models)
        pcons_write_model_file(targetdir, models)
        modelfile = pcons_get_model_file_name(targetdir)
        print(modelfile)
        length = get_length(casp, target, database)
        pcons_results = {}
        for domain in domains:
            ignorefile = pcons_get_domain_file_name(targetdir, domain,
                                                    method=method)
            # Run and parse results, keeping local scores only
            pcons_results[domain] = read_pcons(
                run_pcons(modelfile, length, d0=d0, ignore_file=ignorefile,
                          pcons_binary=pcons), transform_distance=transform,
                d0=3)[1]
        # Join the models here using joining function on the output
        print(pcons_results)
        joint_quality = join_models(pcons_results, length)
        # output the joint model using the output function and naming convention
        scorefile = get_scorefile_name(targetdir, method=method,
                                       partitioned=True)
        with open(scorefile, 'w') as outfile:
            write_scorefile(outfile, joint_quality[0], joint_quality[1], d0=d0)


if __name__ == '__main__':
    main()
