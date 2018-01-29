from ..database import get_correlates, get_local_correlates_with_model_id, query_global_correlates, query_global_correlates_proper
from .pandas import get_dataframe
from ..internal.data import remove_residue_column, remove_model_column, collapse_dictionary_to_list_of_tuples


def correlate_methods(methods_ids, methods_id2name, database, targets=None):
    """Defaults to correlate_methods_local

    :param methods_ids: list of method integer identifiers
    :param methods_id2name: dictionary with method ID as keys and name as values
    :param database: sqlite3 database connection
    :return: pandas dataframe
    """
    return correlate_methods_local(methods_ids, methods_id2name, database, targets=targets)


def correlate_methods_local(methods_ids, methods_id2name, database, targets=None):
    """Get plotting ready Pandas dataframe with method local correlates

    :param methods_ids: list of method integer identifiers
    :param methods_id2name: dictionary with method ID as keys and name as values
    :param database: sqlite3 database connection
    :return: pandas dataframe
    """
    methods = sorted(list(methods_ids))
    names = [methods_id2name[method] for method in methods]
    correlates = remove_residue_column(get_correlates(database, methods, target=targets))
    return get_dataframe(correlates, names)


def correlate_methods_local_on_models(methods_ids, methods_id2name, database, targets=None):
    """Get plotting ready Pandas dataframe with method local correlates

    :param methods_ids: list of method integer identifiers
    :param methods_id2name: dictionary with method ID as keys and name as values
    :param database: sqlite3 database connection
    :return: pandas dataframe
    """
    methods = sorted(list(methods_ids))
    names = [methods_id2name[method] for method in methods]
    correlates_dict = get_local_correlates_with_model_id(database, methods, target=targets)
    #removing residue column
    # for model in correlates_dict:
    #     correlates_dict[model] = remove_residue_column(correlates_dict[model])
    # correlate_list = collapse_dictionary_to_list_of_tuples(correlates_dict)
    # correlates = get_dataframe(correlate_list, ['Model'] + names)
    for model in correlates_dict:
        correlates_dict[model] = get_dataframe(remove_residue_column(correlates_dict[model]), names)
    return correlates_dict


def correlate_methods_global(methods_ids, methods_id2name, database, targets=None):
    """Get plotting ready Pandas dataframe with method global correlates

    :param methods_ids: list of method integer identifiers
    :param methods_id2name: dictionary with method ID as keys and name as values
    :param database: sqlite3 database connection
    :param targets: iterable with target text string names, for selection over
                    subset of targets
    :return: pandas dataframe
    """
    methods = sorted(list(methods_ids))
    names = [methods_id2name[method] for method in methods]
    query = query_global_correlates(methods, targets=targets)
    correlates = remove_model_column(database.execute(query).fetchall())
    return get_dataframe(correlates, names)


def correlate_methods_global_proper(methods_ids, methods_id2name, database, targets=None):
    """Get plotting ready Pandas dataframe with method global correlates

    :param methods_ids: list of method integer identifiers
    :param methods_id2name: dictionary with method ID as keys and name as values
    :param database: sqlite3 database connection
    :param targets: iterable with target text string names, for selection over
                    subset of targets
    :return: pandas dataframe
    """
    methods = sorted(list(methods_ids))
    names = [methods_id2name[method] for method in methods]
    query = query_global_correlates_proper(methods, targets=targets)
    correlates = database.execute(query).fetchall()
    return get_dataframe(correlates, ["Target", "Model"] + names)