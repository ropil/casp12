#!/usr/bin/env python3
from casp12.interface.pcons import join_models, run_pcons, read_pcons, \
    write_scorefile, pcons_get_domain_file_name, pcons_get_model_file_name, \
    pcons_write_model_file, get_scorefile_name, which
from casp12.interface.targets import find_targets, guess_casp_experiment, \
    get_domain, find_models, get_length
from casp12.database import get_or_add_method, store_qa, store_qa_compounded, store_models_and_servers, save_or_dump
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
        "-domainmethod", nargs=1, metavar="int",
        help="Domain partition method ID, as stored in DB (.e. check DB)")
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
        "-write", action="store_true", default=False,
        help="Write out pcons text-files")
    parser.add_argument(
        "files", nargs="*", metavar="PATH", help="Pathways to CASP data")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files

    # Method definition
    method_name = "Simple Arithmetic"
    method_desc = "".join(["A simple method joining the domains expecting ",
                           "to be disjunct. The global score is formed by an ",
                           "arithmetic mean of the residue local scores, not ",
                           "counting any model gaps."])
    method_type_name = "compounder"

    # Set variables here
    d0 = arguments.d0[0]
    pcons = arguments.pcons[0]
    sqlite_file = arguments.db[0]
    domainmethod = int(arguments.domainmethod[0])

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

    # Determine method ID
    database = connect(sqlite_file)
    method = get_or_add_method(method_name, method_desc, method_type_name, database)
    vanilla_method = get_or_add_method("vanilla", "PCONS on full model, vanilla style", "qa", database)


    # Run PCONS for each target and domain, then join the PCONS models
    for target in target_list:
        casp = target_casp[target]
        (components, domains) = get_domain(target, domainmethod, database)
        targetdir = targets[target]
        models = find_models(targetdir)
        # print(models)
        modelfile = pcons_write_model_file(targetdir, models)
        # modelfile = pcons_get_model_file_name(targetdir)
        # print(modelfile)
        length = get_length(target, database, method=domainmethod)
        pcons_results = {}
        for (num, domain) in zip(components, domains):
            # This below could be stored in the database as a path object
            ignorefile = pcons_get_domain_file_name(targetdir, num,
                                                    method=domainmethod)
            # Run and parse results
            pcons_results[domain] = read_pcons(
                run_pcons(modelfile, total_len=length, d0=d0,
                          ignore_file=ignorefile, pcons_binary=pcons),
                transform_distance=transform, d0=3)
        # Store domain results in database here as QA and QAscores
        qas = {}
        (servers, modeltuples, filenames, servermethods,
         model_id) = store_models_and_servers(target, pcons_results[next(iter(pcons_results))], database)
        for domain in pcons_results:
            # this query could be dropped if we added this information to
            # get_domain, which is called above in the loop.
            query = 'SELECT domain.method, component.id FROM domain INNER JOIN component ON domain.id = component.domain WHERE domain.id = {}'.format(domain)
            (partition_method, component) = database.execute(query).fetchone()
            for model in pcons_results[domain][0]:
                qa = store_qa(model_id[modeltuples[model]], pcons_results[domain][0][model], pcons_results[domain][1][model], vanilla_method, database, component=component)
                # Initiate new empty lists of QA IDs if a new model is found
                if model not in qas:
                    qas[model] = []
                qas[model].append(qa)
        # Join the models here using joining function on the output
        # print(pcons_results)
        joint_quality = join_models(pcons_results, length)
        # Store joint results in database here as QAscores, QAcompound and QAjoin
        for model in joint_quality[0]:
            store_qa_compounded(model_id[modeltuples[model]], qas[model], joint_quality[0][model], joint_quality[1][model], method, database)

        # Commit database
        save_or_dump(database, sqlite_file)

        # output the joint model using the output function and naming convention
        if write:
            scorefile = get_scorefile_name(targetdir, method=method,
                                           partitioned=True)
            with open(scorefile, 'w') as outfile:
                write_scorefile(outfile, joint_quality[0], joint_quality[1],
                                d0=d0)


if __name__ == '__main__':
    main()
