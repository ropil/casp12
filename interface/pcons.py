from math import sqrt
from re import compile, search
from operator import itemgetter
from os import path
from statistics import mean, StatisticsError
from subprocess import check_output
from casp12.interface.targets import get_length
import resource


def pcons_domain_specifications(casp, target, database):
    """Get domain ignore specifications for PCONS

    :param casp: integer CASP experiment serial identifier
    :param target: string target identifier
    :param database: sqlite3 connector object to domain definition database
    :return: dictionary with domain ID's as keys containing a full text PCONS
             ignore-file definition
    """

    # Get the length of the target
    target_length = get_length(casp, target, database)
    ignore_residues = {}

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


def pcons_get_domain_file_name(directory, domain, method=None):
    """Standard naming convention for PCONS domain ignore files

    :param directory: target directory, string
    :param domain: domain identifier, integer
    :param method: partitioning method identifier, string
    :return: filename and path, string
    """
    method_ext = ""
    if method is not None:
        method_ext = "_" + method
    return path.join(directory,
                     "pcons_domain_{}{}.ign".format(domain, method_ext))


def pcons_get_model_file_name(directory):
    """Standard naming convention for PCONS model file lists

    :param directory: target directory, string
    :return: filename and path, string
    """

    return path.join(directory, "pcons_models.lst")


def pcons_write_domain_files(directory, ignore_residues, method=None):
    """Write a pcons domain ignore file

    :param directory: target model directory
    :param ignore_residues: dictionary with domains as keys and ignore residue
                            string lists as values
    :param method: partition method type to append to filename,
                   default=no extension
    """

    for domain in ignore_residues:
        with open(pcons_get_domain_file_name(directory, domain, method),
                  'w') as ignore_file:
            ignore_file.write(ignore_residues[domain])
            ignore_file.close()


def pcons_write_model_file(directory, models):
    """Write a PCONS model list file

    :param directory: target model directory
    :param models: dictionary with model ID's as keys and model pathways as keys
    """

    with open(pcons_get_model_file_name(directory), 'w') as model_list:
        for model in models:
            model_list.write(models[model] + "\n")


def global_score(local_score):
    """Calculates PCONS global score, i.e an average

    :param local_score: vector of local scores, list of floats
    :return: Arithmetic mean of score vector, float
    """
    try:
        return mean([x for x in local_score if x is not None])
    except StatisticsError:
        return None


def join_models(pcons_domains, total_len):
    """Join separate PCONS assessments on domain partitions

    :param pcons_domains: Dictionary with domain identifiers as keys (integers)
                          and dictionaries as values, which has targets as keys
                          and PCONS score vectors as values.
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


def read_pcons(output, transform_distance=True, d0=3, regex="^\S+_TS\d+"):
    """Reads PCONS output

    :param output: File handle or iterable of strings (one string per row)
    :param transform_distance: Indicate if distances should be converted into
                               TM-score/PCONS QA
    :param d0: TM-/PCONS score cutoff parameter
    :return: tuple of dictionaries, first with keys pertaining to model ID and
             global scores as values, second with dito keys but vectors of local
             scores as values.
    """
    score_global = {}
    score_local = {}
    # print(output)
    target = compile(regex)
    for line in output:
        if target.match(line):
            temp = line.rstrip().split()
            key = temp[0]
            score_global[key] = float(temp[1]) if temp[1] != 'X' else None
            scores = [None if x == "X" else float(x) for x in temp[2:]]
            if transform_distance:
                score_local[key] = d2S(scores, d0)
            else:
                score_local[key] = scores
            # score_global[key] = global_score(score_local[key])
    # print((score_global, score_local))
    return (score_global, score_local)


def run_pcons(model_listing_file, total_len, d0=3, ignore_file=None,
              pcons_binary="pcons"):
    """Run PCONS using subprocess on target model interface w/wo partition

    :param model_listing_file: file with paths to model interface, str
    :param total_len: expected total length of model, int
    :param d0: TM-score parameter, float
    :param ignore_file: PCONS ignore file for domain partitions, str
    :param pcons_binary: PCONS binary path, str
    :return: PCONs output as a list of strings (one string per line)
    """

    # Set stacksize to unlimited
    resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    # Form command
    cmd = [pcons_binary, "-i", model_listing_file, "-L", str(total_len), "-d0",
           str(d0)]
    if ignore_file is not None:
        cmd += ["-ignore_res", ignore_file]
    print("Running: " + " ".join(cmd))
    output = check_output(cmd)
    return str(output).split('\\n')


def d2S(d_in, d0=3):
    """Convert PCONS CASP distance quality measure to score quality

    :param d_in: distance vector, vector of float in Ångström
    :param d0: TM-score parameter
    :return: score vector of floats
    """
    return [None if x is None else 1 / (1 + float(x) * float(x) / (d0 * d0)) for
            x in d_in]


def S2d(S, d0=3, interval=(0.03846, 1.0), max_rmsd=15.0, min_rmsd=1.0):
    """Convert PCONS score quality measure to CASP distance quality

    :param S: PCONS score, vector of floats float
    :param d0: TM-score parameter
    :param interval: (min, max) score values, tuple of floats
    :param max_rmsd: maximum rmsd to return, if outside interval, float
    :param min_rmsd: minimum rmsd to return, if outside interval, float
    :return: CASP distance quality, vector of float
    """
    rmsd = []
    for x in S:
        # If there is a QA for residue
        if x is not None:
            # and if score is too low
            if x < interval[0]:
                # set to max distance limit limit
                rmsd.append(max_rmsd)
            # and if within inteval
            elif x < interval[1]:
                # Convert using inverse TM-score
                rmsd.append(sqrt(1 / x - 1) * d0)
            else:
                # Otherwise set to minimum distance
                rmsd.append(min_rmsd)
        else:
            # If no QA, append None
            rmsd.append(x)
    return rmsd


def get_scorefile_name(directory, method=None, partitioned=False):
    """Get PCONS output naming convention

    :param directory: target directory, string
    :param method: indicate method identifier, string
    :param partitioned: Indicate if domain method, boolean
    :return: pathway to output file, string
    """
    method_ext = ""
    domain_ext = ""
    if partitioned:
        domain_ext = "_domain"
    if method is not None:
        method_ext = "_" + method
    return path.join(directory, "pcons{}{}.pcn".format(domain_ext, method_ext))


def write_scorefile(outfile, global_score, local_score, d0=3):
    """Print a PCONS score file given local and global score dictionaries

    :param outfile: Writeable filehandle to write output into
    :param global_score: Dictionary with model ID as keys and global score as
                         values (float)
    :param local_score: Dictionary with model ID as keys and local score vectors
                        as values (vectors of floats, with None elements where
                        QA is missing)
    :param d0: TM-/PCONS score parameter (float)
    """

    #print(global_score)
    # Fastest sorting algorithm as indicated in benchmark;
    # https://writeonly.wordpress.com/2008/08/30/sorting-dictionaries-by-value-in-python-improved/
    global_score_sorted = sorted(global_score.items(), key=itemgetter(1),
                                 reverse=True)

    #print(global_score_sorted)

    # Header
    outfile.write("PFRMAT QA\n")
    outfile.write("TARGET T0XXX\n")
    outfile.write("AUTHOR XXXXXXXXXX\n")
    outfile.write("MODEL 1\n")
    outfile.write("QMODE 2\n")

    # Score section
    for (model, score) in (global_score_sorted):
        # Global score
        outfile.write("%s %.3f" % (model, score))
        # Local scores
        for value in S2d(local_score[model], d0=d0):
            if value is None:
                outfile.write(" X")
            else:
                outfile.write(" %.3f" % value)
        outfile.write("\n")


def which(program):
    """Find absolute path of program executable

    Found and copied from stack overflow at:
      https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python#377028

    :param program: Program to search for, str
    :return: return path to executable, or None if no executable found
    """
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None