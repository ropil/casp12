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


def guess_casp_experiment(directory, regex="CASP(\d+)"):
    """Guesses CASP experiment integer ID

    :param directory: full path to CASP files directory
    :param regex: expected nomenclature of CASP directory name
    :return: None if no regex match, integer CASP experiment ID otherwise
    """
    casp_guess = compile(regex)
    caspdir = path.split(directory)[-1]
    casphit = casp_guess.search(caspdir)
    if casphit:
        return int(casphit[1])
    return None


def pcons_domain_specifications(casp, target, database):
    target_length = database.execute(
        'SELECT len FROM target WHERE casp="{}" AND id="{};"'.format(casp,
                                                                     target))[
        0][
        0]
    ignore_residues = {}

    # Sum domain lengths if target length not specified
    if target_length is None:
        target_length = database.execute(
            "SELECT SUM(dlen) FROM domain_size WHERE casp={} AND target='{}' GROUP BY casp, target;".format(
                casp, target))[0][0]

    # For every domain
    for (domain) in database.execute(
            "SELECT num FROM domain WHERE casp={} AND target='{}';".format(casp,
                                                                           target)):
        # Make an ignore-all template
        ignore_residues[domain] = set([i for i in range(1, target_length + 1)])
        # Collect all domain residues from all segments
        domain_residues = set()
        for (start, stop) in database.exectue(
                "SELECT start, stop FROM segment WHERE casp={} AND target='{}' AND domain={};".format(
                    casp, target, domain)):
            domain_residues = domain_residues.union(range(start, stop + 1))
        # Only ignore non-domain residues
        ignore_residues[domain] = ignore_residues[domain] - domain_residues
        # Convert to a writable string
        ignore_residues[domain] = list(ignore_residues[domain])
        ignore_residues[domain].sort()
        ignore_residues[domain] = "\n".join(
            [str(i) for i in ignore_residues[domain]])

    return ignore_residues


def pcons_write_domain_file(directory, ignore_residues, method=None):
    """Write a pcons domain ignore file

    :param directory: target model directory
    :param ignore_residues: dictionary with domains as keys and ignore residue
                            string lists as values
    :param method: partition method type to append to filename,
                   default=no extension
    """
    method_ext = ""
    if method is not None:
        method_ext = "_" + method
    for domain in ignore_residues:
        with open(path.join(directory, "pcons_domain_{}{}.ign".format(domain, method_ext)), 'w') as ignore_file:
            ignore_file.write(ignore_residues[domain])