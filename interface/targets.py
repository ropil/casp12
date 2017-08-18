from os import listdir, path
from re import compile
from sqlite3 import connect


def find_targets(directory, regex="T\d{4}"):
    """Search for CASP targets in specified directory

    :param directory: directory path, string
    :param regex: target regex, string
    :return: dictionary with target ID's as keys and paths to their data dirs as
             values
    """
    target_regex = compile(regex)
    targets = {}
    for filename in listdir(directory):
        if path.isdir(path.join(directory, filename)):
            if target_regex.match(filename):
                targets[filename] = path.join(directory, filename)
    return targets


def find_models(directory, regexes=["\S+_TS\d+\.pdb\Z", "\S+_TS\d+\Z"]):
    """ Find models in target directory using a list of regexes

    :param directory: Directory to search, string
    :param regexes: Regexes to use
    :return: a dictionary with model id's as keys and their pathnames as values
    """

    models = {}
    regex = 0
    while len(models) == 0 and len(regexes) > regex:
        model_regex = compile(regexes[regex])
        regex += 1
        for filename in listdir(directory):
            if path.isfile(path.join(directory, filename)):
                if model_regex.match(filename):
                    models[filename] = path.join(directory, filename)
    if len(models) == 0:
        raise FileNotFoundError('Could not find any models files in "{}"'.format(directory))
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


def get_length(casp, target, database):
    """Get number of residues in target from database

    :param casp: CASP experiment ID, integer
    :param target: target ID, string
    :param database: database handle, sqlite3 connector
    :return: target length, integer
    """
    query = 'SELECT len FROM target WHERE casp="{}" AND id="{}";'.format(casp,
                                                                         target)
    target_length = database.execute(query).fetchone()[0]
    ignore_residues = {}

    # Sum domain lengths if target length not specified
    if target_length is None:
        query = "SELECT SUM(dlen) FROM domain_size WHERE casp={} AND target='{}' GROUP BY casp, target;".format(
            casp, target)
        target_length = database.execute(query).fetchone()[0]

    return target_length
