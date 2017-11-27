def get_method_id_dictionaries(ids, names):
    """Zip method ids and names into dictionaries for fast lookups

    :param ids: list of IDs
    :param names: list of names
    :return: tuple of two dictionaries
             1) dictionary of method names with id's as keys
             2) dictionary of method id's with names as keys
    """
    id2name = {}
    name2id = {}
    for (method_id, method_name) in zip(ids, names):
        id2name[method_id] = method_name
        name2id[method_name] = method_id
    return id2name, name2id


def get_method_names_from_id_dict(methods, id2names):
    """Get a list of method names from ID to name dictionary

    :param methods: list of method ID's
    :param id2names: dictionary with method ID as keys and method names as value
    :return: list of method names
    """
    return [id2names[method] for method in methods]


def remove_residue_column(data):
    """Remove legacy residue column (i.e. the first) from correlation table data

    :param data: iterable of lists (rows) with data (a table)
    :return: list of lists with data without the first column
    """
    return [entry[1:] for entry in data]


def remove_model_column(data):
    """Remove legacy model column, wrapper of remove_residue_column()

       :param data: iterable of lists (rows) with data (a table)
       :return: list of lists with data without the first column
    """
    return remove_residue_column(data)


