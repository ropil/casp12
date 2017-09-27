from os import listdir, path
from re import compile
from sqlite3 import connect
from ..definitions import method_type


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


def identify_models_and_servers(modeldict, regex="(\S+)_TS(\d+)"):
    """Parses filenames into server and model dictionaries

    :param modeldict: dictionary of models filename as keys with pathnames as
                      values
    :param regex: string of regex to use for parsing filenames
    :return: tuple with dictionary of, in order,
             1) server names as keys and lists with model numbers as integers
             2) pcons model name as keys and tuple of server name and model
                number as values
             3) tuple of server names and model integers as keys and model file
                pathnames as values
    """
    nameregex = compile(regex)
    servers = {}
    modeltuples = {}
    filenames = {}
    for entry in modeldict:
        # parse filename
        (server, model) = nameregex.search(entry).group(1, 2)
        model = int(model)
        # Add a list for any new servers
        if server not in servers:
            servers[server] = []
        # Set server and model dictionaries to point to each other
        servers[server].append(model)
        modeltuples[entry] = (server, model)
        # Save filename in a tuple accessed dictionary
        filenames[(server, model)] = modeldict[entry]

    return servers, modeltuples, filenames


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


def get_domains(targets, method, database):
    """Get domain identifiers for each CASP target

    :param targets: list of target indentifiers, each as a string
    :param method: integer id of domain partitioning method
    :param database: sqlite3 connector object to domain definition database
    :return: dictionary with target ID's as keys and a tuple of lists of domain
             ID's and values
    """
    domains = {}

    for target in targets:
        domains[target] = get_domain(target, method, database)

    return domains


def get_domain(target, method, database):
    """Get domain identifiers for each CASP target

    :param method: integer domain partitioner method identifier
    :param targets: target identifier, string
    :param database: sqlite3 connector object to domain definition database
    :return: tuple of List of component numberings and domain identifiers,
             as integers
    """

    # For every domain
    query = "SELECT component.num, component.domain FROM component INNER JOIN domain ON component.domain = domain.id WHERE component.target='{}' AND domain.method = {} ORDER BY component.num;".format(target, method)
    components, domains = zip(*database.execute(query))
    return (list(components), list(domains))


def get_domain_number(target, domain, database):
    """Get domain numberings for a domain if it is present in target

    :param target: integer id of target to check
    :param domain: integer id of domain to find
    :param database: database connection to use
    :return: list of integer numberings for domain found
    """
    query = "SELECT num FROM component WHERE target='{}' AND domain = {} ORDER BY num".format(target, domain)
    return [num for (num,) in database.execute(query)]



def get_length(target, database, method=None):
    """Get number of residues in target from database

    :param target: target ID, string
    :param method: domain partitioning method, integer
    :param database: database handle, sqlite3 connector
    :return: target length, integer
    """
    query = 'SELECT len FROM target WHERE id="{}";'.format(target)
    target_length = database.execute(query).fetchone()[0]
    ignore_residues = {}

    # Get first listed partitioner method stored in database, if not specified
    # by user
    if method is None:
        query = 'SELECT id FROM method WHERE type = {} LIMIT 1'.format(method_type["partitioner"])
        method = database.execute(query).fetchone()[0]

    # Sum domain lengths if target length not specified
    if target_length is None:
        query = "SELECT SUM(dlen) FROM domain_size WHERE target='{}' AND method={} GROUP BY target;".format(
            target, method)
        target_length = database.execute(query).fetchone()[0]

    return target_length
