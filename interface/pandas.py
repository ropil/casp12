from pandas import concat, DataFrame, MultiIndex, Series
from numpy import arctanh
from ..internal.calculations import d2S


class MissingData(TypeError):
    pass


def get_dataframe(data, column_names):
    """Format data into pandas frame

    :param data: Data table (iterable of iterables)
    :param column_names: iterable of column identifiers
    :return: Pandas Dataframe object
    """
    return DataFrame(data, columns=column_names)


def join_dict_of_tables(tables):
    """Join a dictionary of Pandas DataFrames into a single DataFrame

    :param tables: dictionary with table names as keys and DataFrames as values
    :return: Pandas DataFrame with the joined tables
    """
    keys = list(tables.keys())
    return concat([tables[key] for key in keys], keys=keys)


def join_dict_of_tables_on_column(tables, column, source_type="table",
                                  skip=True):
    """Join a dictionary of Pandas DataFrames into one, transposing a select
       column from each DataFrame into a row of a new dataframe; transposing the
       data. The keys of the dictionary ends up in a new source column

    :param tables: dictionary with data source information as keys and pandas
                   DataFrames as values
    :param column: Column ID to select from DataFrames
    :param source_type: Name to use for index column name
    :param skip: silently skip tables with missing column data
    :return: Pandas DataFrame with selected column as rows from old dictionary
             and a list of skipped tables
    """
    # Split off this
    table_rows, skipped = select_column_from_tables_in_dictionary(tables,
                                                                  column,
                                                                  skip=skip)

    table = DataFrame(table_rows).transpose()

    return rename_index(table, source_type), skipped


def overwrite_column_with_value(dataframe, column, value):
    """Overwrite all entries in one column of a Pandas DataFrame with multiple
       copies of a single value

    :param dataframe: Pandas DataFrame to manipulate
    :param column: column ID to overwrite
    :param value: value to overwrite each column entry with
    :return: Pandas DataFrame of altered table
    """
    dataframe[column] = Series([value for x in range(len(dataframe.index))],
                               index=dataframe.index)
    return dataframe


def rename_index(dataframe, index_name, level=0):
    """Reset and rename Pandas DataFrame index column

    :param dataframe: Pandas DataFrame to reset and rename
    :param index_name: index name to use
    :param level: index level to reset, default is 0
    :return: new Pandas DataFrame
    """
    convert_name = level
    if type(convert_name) is int:
        if 'index' in dataframe or type(dataframe.index)  is MultiIndex:
            convert_name = "level_{}".format(convert_name)
        else:
            convert_name = "index"

    table = dataframe.reset_index(level=level)

    return table.rename(index=str, columns={convert_name: index_name})


def select_column_from_tables_in_dictionary(tables, column, skip=True):
    """Extract a dictionary of Pandas Series from Pandas DataFrames in a dict

    :param tables: dictionary with table ID as keys and DataFrames as values
    :param column: column name to select from DataFrames
    :param skip: if True (default), skip tables missing column; if false raise
                 exception MissingData
    :return: dictionary with table ID as keys and Pandas Series as values and
             list of skipped entries
    """
    table_rows = {}
    skipped = []
    for table in tables:
        if column in tables[table]:
            table_rows[table] = tables[table][column]
        elif skip:
            skipped.append(table)
        else:
            raise MissingData(table)

    return table_rows, skipped


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


def fischer_transform_dataframe(dataframe):
    """Apply numpy.arctanh as the Fischer z-transform to the whole dataframe

    :param dataframe: Pandas dataframe to apply transform to
    :return: Pandas DataFrame of transform
    """
    return dataframe.apply(arctanh)
