from re import search
from os import path
from statistics import mean
from subprocess import check_output


def pcons_domain_specifications(casp, target, database):
    """Get domain ignore specifications for PCONS

    :param casp: integer CASP experiment serial identifier
    :param target: string target identifier
    :param database: sqlite3 connector object to domain definition database
    :return: dictionary with domain ID's as keys containing a full text PCONS
             ignore-file definition
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

    # For every domain
    query = "SELECT num FROM domain WHERE casp={} AND target='{}';".format(casp,
                                                                           target)
    for (domain,) in database.execute(query):
        # Make an ignore-all template
        ignore_residues[domain] = set([i for i in range(1, target_length + 1)])
        # Collect all domain residues from all segments
        domain_residues = set()
        query = "SELECT start, stop FROM segment WHERE casp={} AND target='{}' AND domain={};".format(
            casp, target, domain)
        for (start, stop) in database.execute(query):
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
        with open(path.join(directory,
                            "pcons_domain_{}{}.ign".format(domain, method_ext)),
                  'w') as ignore_file:
            ignore_file.write(ignore_residues[domain])


def global_score(local_score):
    """Calculates PCONS global score, i.e an average

    :param local_score: vector of local scores, list of floats
    :return: Arithmetic mean of score vector, float
    """
    return mean([x for x in local_score if x is not None])


def join_models(pcons_domains, total_len):
    """Join separate PCONS assessments on domain partitions

    :param pcons_domains: Dictionary with domain identifiers as keys (integers)
                          and dictionaries as values, which has targets as keys
                          and PCONS score vectors as values, as values.
    :param total_len: number of residues in the target sequence
    :return: tuple pair with two dictionaries using model identifiers as keys,
             the first dict containing global scores as values, the second local
             score vectors.
    """
    joined_domain_local = {}
    joined_domain_global = {}
    # Joining of models
    for domain in pcons_domains:
        for model in pcons_domains[domain]:
            if not model in joined_domain_local:
                joined_domain_local[model] = [None] * total_len
            for i in range(total_len):
                if pcons_domains[domain][model][i] is not None:
                    joined_domain_local[model][i] = \
                    pcons_domains[domain][model][i]

    # Collapsing of models
    for model in joined_domain_local:
        joined_domain_global[model] = global_score(joined_domain_local[model])

    return (joined_domain_global, joined_domain_local)


def read_pcons(output, transform_distance=False, d0=3):
    score_global = {}
    score_global2 = {}
    score_local = {}
    for line in output:
        if search(r"TS\d\s", line):
            temp = line.rstrip().split()
            key = temp[0]
            score_global2[key] = float(temp[1])
            scores = [None if x == "X" else float(x) for x in temp[2:]]
            if transform_distance:
                score_local[key] = d2S(scores, d0)
            else:
                score_local[key] = scores
            score_global[key] = global_score(score_local[key])
    return (score_global, score_local)


def run_pcons(model_listing_file, total_len, d0=3, ignore_file=None,
              pcons_binary="pcons"):
    """Run PCONS using subprocess on target model files w/wo partition

    :param model_listing_file: file with paths to model files, str
    :param total_len: expected total length of model, int
    :param d0: TM-score parameter, float
    :param ignore_file: PCONS ignore file for domain partitions, str
    :param pcons_binary: PCONS binary path, str
    :return: PCONs output as a list of strings (one string per line)
    """
    cmd = [pcons_binary, "-i", model_listing_file, "-L", str(total_len), "-d0",
           str(d0)]
    if ignore_file is not None:
        cmd += ["-ignore_res", ignore_file]
    output = check_output(cmd)
    return str(output).split('\n')


def d2S(d_in, d0=3):
    """Convert PCONS CASP distance quality measure to score quality

    :param d_in: distance vector, vector of float in Ångström
    :param d0: TM-score parameter
    :return: score vector of floats
    """
    return [None if x is None else 1 / (1 + float(x) * float(x) / (d0 * d0)) for
            x in d_in]


def S2d(S, d0=3):
    """Convert PCONS score quality measure to CASP distance quality

    :param S: PCONS score, single float
    :param d0: TM-score parameter
    :return: CASP distance quality, single float
    """
    rmsd = 0
    rmsd = 15
    if S > 0.03846:
        if S >= 1:
            rmsd = 0
        else:
            rmsd = math.sqrt(1 / S - 1) * d0
    return rmsd
