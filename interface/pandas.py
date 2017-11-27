from pandas import DataFrame
from ..internal.calculations import d2S


def get_dataframe(data, column_names):
    """Format data into pandas frame

    :param data: Data table (iterable of iterables)
    :param column_names: iterable of column identifiers
    :return: Pandas Dataframe object
    """
    return DataFrame(data, columns=column_names)


def score_column(dataframe, column, d0):
    """Convert distance to TM-like score within a Pandas dataframe

    :param dataframe: a pandas dataframe
    :param method: dataframe column ID (method name)
    :param d0: float conversion parameter
    :return: handle to converted dataframe
    """
    dataframe[column] = dataframe[column].apply(d2S, args=(d0,))
    return dataframe


def score_columns(dataframe, columns, d0):
    """Convert distances to TM-like score for multiple columns in Pandas frame

    :param dataframe: a pandas dataframe
    :param columns: list of column identifiers
    :param d0: float conversion parameter
    :return: handle to converted dataframe
    """
    converted = dataframe
    for column in columns:
        converted = score_column(converted, column, d0)
    return converted