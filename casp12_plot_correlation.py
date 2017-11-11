#!/usr/bin/env python3
import sqlite3
from casp12.plots import convert_data, d2S, get_correlates, plot_correlates
from casp12.definitions import method_type
from casp12.database import get_method_id_and_name_from_type


'''
 Plot correlation data in quality assessment sqlite3 database
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
        "casp12_plot_correlation  Copyright (C) 2017  Robert Pilstål;",
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
        description="{one line to give a brief idea of what the program does.}")
    parser.add_argument(
        "-a", action="store_true", default=False, help="Prints nothing")
    parser.add_argument(
        "-d0", nargs=1, default=["3.0"], metavar="FLOAT",
        help="TMscore cutoff, default=3.0")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "database", nargs=1, metavar="DATABASE", help="SQLite3 database to use")
    parser.add_argument(
        "plot", nargs=1, metavar="FIGURE", help="Output filename for figure.")
    arguments = parser.parse_args(argv[1:])
    databasefile = arguments.database[0]

    # Set variables here
    database = sqlite3.connect(databasefile)
    outfile = arguments.plot[0]
    d0 = float(arguments.d0[0])

    # Get methods
    (method_ids, method_names) = get_method_id_and_name_from_type(database, ["qa", "compounder"])

    # Select correlates from database
    correlates = get_correlates(database, method_ids)

    # Convert to pandas table
    correlates = convert_data(correlates, method_names)

    # Convert SDA
    # to_convert = None
    # for (method_id, method_name) in zip(method_ids, method_names):
    #     if method_name == "CASP12_LGA_SDA":
    #         to_convert = method_id
    correlates = d2S(correlates, "CASP12_LGA_SDA", d0)

    # Plot the correlations
    (f, matrix) = plot_correlates(correlates)

    # Print correlation data to STDOUT
    print(matrix)

    # Save figure
    f.savefig(outfile)


if __name__ == '__main__':
    main()