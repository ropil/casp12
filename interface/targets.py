from os import listdir, path
from re import compile
from sqlite3 import connect


def find_targets(directory, regex="T\d{4}"):
    target_regex = compile(regex)
    targets = {}
    for filename in listdir(directory):
        if path.isdir(path.join(directory, filename)):
            if target_regex.match(filename):
                targets[filename] = path.join(directory, filename)
    return targets


def find_models(directory, regex="\S+_TS\d+\.pdb\Z"):
    model_regex = compile(regex)
    models = {}
    for filename in listdir(directory):
        if path.isfile(path.join(directory, filename)):
            if model_regex.match(filename):
                models[filename] = path.join(directory, filename)
    return models


def guess_casp_experiment(directory, regex="[Cc][Aa][Ss][Pp](\d+)"):
    """Guesses CASP experiment integer ID

    :param directory: full path to CASP interface directory
    :param regex: expected nomenclature of CASP directory name
    :return: None if no regex match, integer CASP experiment ID otherwise
    """
    casp_guess = compile(regex)
    caspdir = path.split(directory)[-1]
    casphit = casp_guess.search(caspdir)
    if casphit:
        return int(casphit[1])
    return None


def get_domains(casp, targets, database):
    """Get domain identifiers for each CASP target

    :param casp: integer CASP experiment serial identifier
    :param targets: list of target indentifiers, each as a string
    :param database: sqlite3 connector object to domain definition database
    :return: dictionary with target ID's as keys and lists of domain ID's as
             values
    """
    domains = {}

    for target in targets:
        domains[target] = get_domain(casp, target, database)

    return domains


def get_domain(casp, target, database):
    """Get domain identifiers for each CASP target

    :param casp: integer CASP experiment serial identifier
    :param targets: target identifier, string
    :param database: sqlite3 connector object to domain definition database
    :return: List of domain identifiers, integers
    """

    # For every domain
    query = "SELECT num FROM domain WHERE casp={} AND target='{}';".format(casp, target)
    return [domain for (domain,) in database.execute(query)]


