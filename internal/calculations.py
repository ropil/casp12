def d2S(dataframe, column, d0):
    """Convert distance to TM-like score within a Pandas dataframe

    :param dataframe: a pandas dataframe
    :param method: dataframe column ID (method name)
    :param d0: float conversion parameter
    :return: handle to converted dataframe
    """
    dataframe[column] = dataframe[column].apply(lambda x: 1.0 / (1.0 + (x / d0)**2))
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
        converted = d2S(converted, column, d0)
    return converted
