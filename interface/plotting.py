from ..database import get_correlates
from .pandas import get_dataframe
from ..internal.data import remove_residue_column


def correlate_methods(methods_ids, methods_id2name, database):
    """Get plotting ready Pandas dataframe with method local correlates

    :param methods_ids: list of method integer identifiers
    :param methods_id2name: dictionary with method ID as keys and name as values
    :param database: sqlite3 database connection
    :return: pandas dataframe
    """
    methods = sorted(list(methods_ids))
    names = [methods_id2name[method] for method in methods]
    correlates = remove_residue_column(get_correlates(database, methods))
    return get_dataframe(correlates, names)