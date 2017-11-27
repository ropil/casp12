from pandas import DataFrame


def get_dataframe(data, column_names):
    """Format data into pandas frame

    :param data: Data table (iterable of iterables)
    :param column_names: iterable of column identifiers
    :return: Pandas Dataframe object
    """
    return DataFrame(data, columns=column_names)