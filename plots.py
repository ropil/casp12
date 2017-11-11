#!/usr/bin/env python3
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

def convert_data(correlates, method_names):
    # Format data into pandas frame
    return pandas.DataFrame([entry[1:] for entry in correlates],
                            columns=method_names)


def d2S(dataframe, method, d0):
    dataframe[method] = dataframe[method].apply(lambda x: 1.0 / (1.0 + (x / d0)**2))
    return dataframe


def get_models(database, target=None):
    query = "select id from model;"
    # Select only pertaining to a target if specified
    if target is not None:
        query = 'SELECT id FROM model WHERE target = "{}";'.format(target)
    return [entry[0] for entry in database.execute(query).fetchall()]


def get_correlates(database, methods, target=None):
    """ Get QA local scorecorrelates for a target over a set of methods

    :param database: sqlite3 database connection
    :param methods: list with integer method ID's
    :param target: Stirng with target identifier. if specified, only get
                   correlates pertaining to target
    :return: list of tuples with residue number as first element and local
                scores from all QA's found
    """
    # query = "select id, name from method where type = 2 or type = 3;"
    # methods = database.execute(query).fetchall()

    models = get_models(database, target=target)

    qa_query = "SELECT id FROM qa WHERE model = {} AND method = {} AND component IS NULL"
    score_query = "SELECT residue, score FROM lscore WHERE qa = {}"

    correlates = []
    for model in models:
        new_correlates = get_model_correlates(database, model, methods)
        if new_correlates is not None:
            correlates += new_correlates

    return correlates


def get_model_correlates(database, model, methods):
    """ Get correlates for a model, over specified methods

    :param database: sqlite3 connection
    :param model: integer model ID
    :param methods: list of integer method IDs
    :return: list of tuples with float correlates
    """
    qa_query = "SELECT id FROM qa WHERE model = {} AND method = {} AND component IS NULL"
    score_query = "SELECT residue, score FROM lscore WHERE qa = {}"

    selects = []
    froms = []
    ons = []
    previous = None
    skip = False
    # print("MODEL: {}".format(model))
    for (num, method_id) in enumerate(methods):
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
                ons.append(
                    "{}.residue = {}.residue".format(previous, tablename))
            previous = tablename
        else:
            # print("SKIPPING")
            skip = True
            break
    if skip:
        return None
    current_query = "SELECT {} FROM {} ON {};".format(", ".join(selects),
                                                      ", ".join(froms),
                                                      " AND ".join(ons))
    # print(current_query)
    return database.execute(current_query).fetchall()


def plot_correlates(correlates):
    # seaborn setting
    sns.set(style="white")

    # Get correlation matrix via pandas
    corrmatrix = correlates.corr()

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