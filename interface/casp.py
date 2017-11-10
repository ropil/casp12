from lxml.etree import HTML
from csv import unix_dialect, DictReader, register_dialect
from collections import OrderedDict
from ..database import get_or_add_method, store_qa, store_model_caspmethod
from .pcons import d2S, read_pcons
from re import compile


class LGA_SDAError(Exception):
    pass

class LGA_LDDTError(Exception):
    pass

class QAError(Exception):
    pass


class casp_dialect(unix_dialect):
    """Change delimiter to ;"""
    delimiter = ';'
register_dialect("casp", casp_dialect)


def get_filename_info(filename):
    """ Parses information out of a CASP result filename

    :param filename: string with filename
    :return: tuple of
             1. string of target name
             2. string of method type
             3. integer casp method ID
             4. integer model serial
    """
    filename_regex = compile("(T.\d+)(\D\D)(\d+)_(\d+)")
    info = filename_regex.search(filename)
    target = info.group(1)
    method_type = info.group(2)
    method = int(info.group(3))
    model_name = int(info.group(4))
    return target, method_type, method, model_name


def parse_server_definitions(page):
    """Parses webpage for CASP server definitions using etree from lxml

    :param page: bytes of webpage (from urlopen(url).read())
    :return: dictionary with CASP server ID integer as keys and tuples of server
             textual name and type
    """
    xml = HTML(page)

    path_groupname = "//table[@id='table_results']//td[@title='Group Name']/b"
    group_names = [element.text for element in xml.xpath(path_groupname)]

    path_groupcode = "//table[@id='table_results']//td[@title='Group Code']"
    group_codes = [element.text for element in xml.xpath(path_groupcode)]

    path_grouptype = "//table[@id='table_results']//td[@title='Group Type']"
    group_types = [element.text for element in xml.xpath(path_grouptype)]

    servers = {}
    for (code, name, stype) in zip(group_codes, group_names, group_types):
        servers[code] = (name, stype)

    return servers


def parse_target_information(webpage):
    """Read target information specified in CASP csv file

    :param webpage: iterable of strings, expecting first row to contain column
                    keys
    :return: cvs.DictReader object
    """

    csvfile = []
    for line in webpage:
        if not line == '':
            csvfile.append(line)

    target_info = DictReader(csvfile, dialect='casp')

    return target_info


def parse_lga_sda_summary(infile, summaryregex="^([^\.]+)\.lga:SUMMARY\(GDT\)\s+(.*)"):
    """Parse a CASP SDA summary file

    :param infile: interable holding sommary file lines as strings
    :param summaryregex: string of regex identifying summary lines, with models
                         and summary entries as groups
    :return: dictionary with string of CASP model identifier and float RMSD as
             values
    """
    summaryentry = compile(summaryregex)

    # Parse file
    summary = {}
    for line in infile:
        # For summary lines
        m = summaryentry.match(line)
        if m:
            # Storing model info
            model = m.group(1)
            (N1, N2, DIST, N, RMSD, GDT_TS, LGA_S3, LGA_Q) = m.group(2).split()
            # And RMSD
            summary[model] = float(RMSD)

    return summary



def parse_lga_sda(infile, lgaregex="^LGA\s+", modelregex = "^# Molecule1:.* selected\s+(\d+) .* name\s+(\S+)", evidenceregex = "^# Molecule2:.* selected\s+(\d+) .* name\s+(\S+)", errorregex="^# ERROR!"):
    """ Parse an LGA file in CASP style

    :param infile: iterable with lines of LGA-file
    :param lgaregex: string with regex identifying LGA entry lines
    :param modelregex: string with regex parsing model entry (molecule 1)
    :param evidenceregex: string with regex parsing gold standard entry
                          (molecule 2)
    :return: tuple with
             1) OrderedDict containing integer of residue number as keys and
                float of RMSD (distance) as value
             2) String with name of model file
             3) String with name of gold standard file
             4) list with two integers with length of selection evaluated, first
                element is model, second is gold standard
    """
    lgaentry = compile(lgaregex)
    evidence_entry = compile(evidenceregex)
    model_entry = compile(modelregex)
    error_entry = compile(errorregex)

    distances = OrderedDict()
    model = None
    evidence = None
    selection = [None, None]

    for line in infile:
        # Parse LGA entry if found
        if lgaentry.search(line):
            (aa1, res1, aa2, res2, distance, Mis, MC, All, Dist_max, GDC_mc, GDC_all, Dist_at) = line.split()[1:]
            if aa1 == aa2 and res1 == res2:
                distances[int(res1)] = float(distance)
            else:
                raise IndexError("LGA entry with misalignment: ({}, {}) != ({}, {})".format(aa1, res1, aa2, res2))
        # Otherwise try check for molecule entries
        else:
            # Parse for evidence molecule (gold standard comparison
            m = evidence_entry.match(line)
            if m:
                evidence = m.group(2)
                selection[1] = int(m.group(1))
            else:
                # Otherwise check for decoy/model entry
                m = model_entry.match(line)
                if m:
                    model = m.group(2)
                    selection[0] = int(m.group(1))
                elif error_entry.match(line):
                    raise LGA_SDAError("ERROR: {}".format(infile.name))

    return distances, model, evidence, selection


def parse_lga_lddt(infile, lddtregex="^.\s+(\S+)\s+(\d+)\s+(\S+)\s(\S+)\s+(\S+)\s+(\S+)\s*\Z", modelregex = "^File: (\S+)", globalregex="^Global LDDT score: (\d+\.\d+)"):
    """Parse a LDDT file

    :param infile: interable with strings of LDDT file to parse
    :param lddtregex: string with regex finding LDDT score lines
    :param modelregex: string with regex identifying model file
    :param globalregex: string with regex identifying global score
    :return: tuple with
             1) float of LDDT global score
             2) OrderedDict containing integer of residue number as keys and
                float of transformed distance (score) as value
             3) string with Model file name
    """
    lddtentry = compile(lddtregex)
    modelentry = compile(modelregex)
    globalentry = compile(globalregex)

    scores = OrderedDict()
    model = None
    globalscore = None
    for line in infile:
        m = lddtentry.match(line)
        if m:
            residue = int(m.group(2))
            try:
                score = float(m.group(5))
                scores[residue] = score
            except ValueError:
                pass
        else:
            m  = modelentry.match(line)
            if m:
                model = m.group(1).split('/')[-1]
            else:
                m = globalentry.match(line)
                if m:
                    globalscore = float(m.group(1))

    return globalscore, scores, model


def pad_scores(scores):
    """Create a list of scores, padded from the first residue with Nones where
    residues are missing

    :param scores: OrderedDict with integer residue ID's as keys and float
                   scores as values
    :return: list of floats with scores
    """
    # Check maximal residue number
    length = max(scores.keys())

    # Create a enumerate list from 1, with Nones for missing data, so that it is
    # compatible with database.store_local_score
    padded_list = []
    for i in range(1, length + 1):
        if i in scores:
            padded_list.append(scores[i])
        else:
            padded_list.append(None)

    return padded_list


def process_casp_sda(infile, globalscores, qa_method, database, target=None, caspserver=None, model=None, component=None, modelregex='^(T.\d+)TS(\d+)_(\d+)', d0=None):
    """Process a local LGA_SDA distance file and store as CASP local QA

    :param infile: LGA_SDA score file to parse
    :param globalscores: dictionary with text modelstrings as keys and float
                         global scores as values
    :param qa_method: integer QA method ID
    :param database: sqlite3 database connection
    :param target: text CASP target identifier, if None - parsed from
                   modelstring
    :param caspserver: integer CASP server identifier, if None - parse from
                       modelstring
    :param model: integer CASP server model id, if None - parsed from
                  modelstring
    :param component: integer domain ID
    :param modelregex: text modelstring parser regex
    :param d0: float d0 distance to score conversion constant, if None - do not
               convert; store distances
    :return: integer ID of stored QA
    """
    # Parse local distances
    (distances, modelstring, evidence, selection) = parse_lga_sda(infile)

    # Parse modelstring
    modelre = compile(modelregex)
    m = modelre.match(modelstring)
    # Let specified values have precedence over parsed
    if m:
        if target is None:
            target = m.group(1)
        if caspserver is None:
            caspserver = int(m.group(2))
        if model is None:
            model = int(m.group(3))

    # Create a enumerate list from 1, with Nones for missing data, so that it is
    # compatible with database.store_local_score
    local_dist = pad_scores(distances)
    # convert local scores
    local_score = local_dist
    if d0 is not None:
        local_score = d2S(local_dist, d0=d0)
    # Store local and global scores
    return store_casp_qa(target, caspserver, model, globalscores[target][modelstring], local_score, qa_method, database, component=component)


def process_casp_lddt(infile, qa_method, database, modelregex='^(T.\d+)TS(\d+)_(\d+)', component=None):
    """Process a local CASP LGA LDDT file and store in QA database

    :param infile: iterable with lines of a CASP LGA LDDT file
    :param qa_method: integer ID of QA method used
    :param database: sqlite3 database connection
    :param modelregex: text with regex for parsing CASP model strings
    :param component: integer domain ID, if domain specific QA
    :return: integer ID of resulting QA stored in database
    """
    # Parse file
    (globalscore, scores, model) = parse_lga_lddt(infile)
    # Create a enumerate list from 1, with Nones for missing data, so that it is
    # compatible with database.store_local_score
    if len(scores) == 0:
        raise LGA_LDDTError("ERROR: No LGA entries found in '{}'".format(infile.name))
    local_score = pad_scores(scores)
    # Parse the model string
    m_model = compile(modelregex)
    m = m_model.search(model)
    target = m.group(1)
    caspserver = int(m.group(2))
    model = int(m.group(3))
    # Store QA, return the QA ID
    return store_casp_qa(target, caspserver, model, globalscore, local_score, qa_method, database, component=component)


def process_casp_qa(infile, qa_method, database, modelregex='^(T.\d+)TS(\d+)_(\d+)', component=None):
    """Process a CASP QA file and store in QA database

    :param infile: iterable with lines of a CASP QA file
    :param qa_method: integer ID of QA method used
    :param database: sqlite3 database connection
    :param modelregex: text with regex for parsing CASP model strings
    :param component: integer domain ID, if domain specific QA
    :return: list of integer IDs of resulting QAs stored in database
    """
    # Parse file
    (global_scores, local_scores) = read_pcons(infile, regex=modelregex)
    # Create a enumerate list from 1, with Nones for missing data, so that it is
    # compatible with database.store_local_score
    if len(local_scores) == 0:
        raise QAError("ERROR: No QA score entries found in '{}'".format(infile.name))

    # Parse the model string
    m_model = compile(modelregex)
    new_qa_id = []
    for modelstring in global_scores:
        m = m_model.search(modelstring)
        target = m.group(1)
        caspserver = int(m.group(2))
        model = int(m.group(3))
        local_score = local_scores[modelstring]
        globalscore = global_scores[modelstring]
        # Store QA, return the QA ID
        new_qa_id.append(store_casp_qa(target, caspserver, model, globalscore, local_score, qa_method, database, component=component))
    return new_qa_id


def store_casp_qa(target, caspserver, model, global_score, local_score, qa_method, database, component=None):
    """ Save local scores from CASP-server, converting casp-server to method ID
    and padding score/distance list. Will not store QA if method or target is
    missig in database (return None)

    :param target: text CASP target
    :param caspserver: integer CASP server ID
    :param model: integer server model serial
    :param global_score: float global score
    :param local_score: list of floats of local scores with None where residue
                        scores is missing. Starts from models 1st residue, and
                        ands on the last residue with score not equal to None
    :param qa_method: integer qa method ID
    :param database: database connection
    :param component: integer domain ID (None is default)
    :return: integer ID of stored QA
    """
    # # Create a enumerate list from 1, with Nones for missing data, so that it is
    # # compatible with database.store_local_score
    # local_score = pad_scores(scores)

    # Get the model ID using the conversion getting method, model should be modelname containing
    # Target, server and model identifiers that are parseable.
    model_id = store_model_caspmethod(target, caspserver, model, database)

    # Do not store QA if the method is unknown
    if model_id is None:
        return None

    qa_id = store_qa(model_id, global_score, local_score, qa_method, database,
             component=component)

    return qa_id



