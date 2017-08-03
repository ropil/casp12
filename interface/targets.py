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


