#!/usr/bin/env python3
import sqlite3
import numpy
import pandas
import seaborn as sns
import matplotlib.pyplot as plt


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
def get_correlates(database):
    query = "select id, name from method where type = 2 or type = 3;"
    methods = database.execute(query).fetchall()

    query = "select id from model;"
    models = [entry[0] for entry in database.execute(query).fetchall()]

    qa_query = "SELECT id FROM qa WHERE model = {} AND method = {} AND component IS NULL"
    score_query = "SELECT residue, score FROM lscore WHERE qa = {}"

    correlates = []
    for model in models:
        selects = []
        froms = []
        ons = []
        previous = None
        skip = False
        # print("MODEL: {}".format(model))
        for (num, (method_id, method_name)) in enumerate(methods):
            tablename = "t{}".format(num)
            qa = database.execute(qa_query.format(model, method_id)).fetchone()
            if qa is not None:
                # print("TABLE NUM: {}, METHOD ID: {}".format(num, method_id))
                qa = qa[0]
                if previous is None:
                    selects.append("{}.residue".format(tablename))
                selects.append("{}.score".format(tablename))
                froms.append("({}) AS {}".format(score_query.format(qa), tablename))
                if previous is not None:
                    ons.append("{}.residue = {}.residue".format(previous, tablename))
                previous = tablename
            else:
                # print("SKIPPING")
                skip = True
                break
        if skip:
            continue
        current_query = "SELECT {} FROM {} ON {};".format(", ".join(selects), ", ".join(froms), " AND ".join(ons))
        # print(current_query)
        correlates += database.execute(current_query).fetchall()

    return correlates, methods


def plot_correlates(correlates, methods):
    # seaborn setting
    sns.set(style="white")

    # Format data into pandas frame
    data = pandas.DataFrame([entry[1:] for entry in correlates],
                            columns=[method[1] for method in methods])

    # Get correlation matrix via pandas
    corrmatrix = data.corr()

    # Generate a mask for the upper triangle
    mask = numpy.zeros_like(corrmatrix, dtype=numpy.bool)
    mask[numpy.triu_indices_from(mask)] = True

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(11, 9))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corrmatrix, mask=mask, cmap=cmap, vmax=.3, center=0,
                    square=True, linewidths=.5, cbar_kws={"shrink": .5})
    return (f, corrmatrix)


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="{one line to give a brief idea of what the program does.}")
    parser.add_argument(
        "-a", action="store_true", default=False, help="Prints nothing")
    parser.add_argument(
        "-t", nargs=1, default=["nothing"], metavar="TEXT",
        help="What to print")
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

    # Select correlates from database
    (correlates, methods) = get_correlates(database)

    # Plot the correlations
    (f, matrix) = plot_correlates(correlates, methods)

    # Print correlation data to STDOUT
    print(matrix)

    # Save figure
    f.savefig(outfile)


if __name__ == '__main__':
    main()