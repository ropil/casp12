#!/usr/bin/env python3
import numpy
import seaborn
from scipy.stats import kendalltau
from sqlite3 import connect

# Seaborn settings
seaborn.set(style="ticks")

'''
 Generate hexagonal distribution plot for a set of CASP partitions
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
        "casp12_plot_partdistribution  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
    ])


# Library functions
def read_data(database):
    domains = {}
    for (casp, target, domain, dlen, nseg) in database.execute("SELECT casp, target, domain, dlen, nseg FROM domain_size ORDER BY casp, target, dlen DESC;"):
        if casp not in domains:
            domains[casp] = {}
        if target not in domains[casp]:
            domains[casp][target] = []
        domains[casp][target].append((domain, dlen, nseg))
    return domains


def get_sorted_lists(targets, sort_index=1, top_num=2, data_index=1):
    toprange = range(top_num)
    sorted_tuples = [[] for i in toprange]
    for target in targets:
        # sort the target domains in-place
        targets[target].sort(key=lambda domain: domain[sort_index])
        for i in toprange:
            # sequentially build the lists
            sorted_tuples[i].append(targets[target][i][data_index])
    return sorted_tuples


def plot_seaborn_hexbin(a, b):
    x = numpy.array(a)
    y = numpy.array(b)
    return seaborn.jointplot(x, y, kind="hex", stat_func=kendalltau, color="#4CB391")


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from os.path import basename
    from sys import argv
    parser = ArgumentParser(
        description="Generate hexagonal distribution plot for a set of CASP" +
                    " partitions.")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "files", nargs="*", metavar="FILE", help="databases to read")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files

    # Set variables here

    # Parse STDIN or interface
    for f in files:
        with connect(f) as database:
            data = read_data(database)
            prefix = ".".join(basename(f).split(".")[:-1])
            for experiment in data:
                plot = plot_seaborn_hexbin(*get_sorted_lists(data[experiment], data_index=1)[0:2])
                plot.savefig(prefix + "_{}_hexbin_dlen.png".format(experiment))
                plot = plot_seaborn_hexbin(
                    *get_sorted_lists(data[experiment], data_index=2)[0:2])
                plot.savefig(prefix + "_{}_hexbin_nseg.png".format(experiment))



if __name__ == '__main__':
    main()
