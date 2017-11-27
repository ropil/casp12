#!/usr/bin/env python3
import numpy
import seaborn as sns
import matplotlib.pyplot as plt
from .database import get_model_correlates as database_get_model_correlates
from .database import get_correlates as database_get_correlates
from .database import get_models as database_get_models
from internal.calculations import d2S as calc_d2S
from internal.data import remove_residue_column
from interface.pandas import get_dataframe


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
    """Legacy stateful function; uses interface/pandas.py and internal/data.py

    :param correlates: iterable of iterables with correlation data, including
                       first residue column
    :param method_names: list of method names, used for columns
    :return: Pandas Dataframe
    """
    return get_dataframe(remove_residue_column(correlates), method_names)


def d2S(dataframe, method, d0):
    """Legacy interface, moved to internal/data.py

    """
    return calc_d2S(dataframe, method, d0)


def get_models(database, target=None):
    """Legacy interface, moved to database.py

    """
    return database_get_models(database, target=target)


def get_correlates(database, methods, target=None):
    """Legacy interface, moved to database.py

    """
    return database_get_correlates(database, methods, target=target)


def get_model_correlats(database, model, methods):
    """Legacy interface, moved to database.py

    """
    return database_get_model_correlates(database, model, methods)


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