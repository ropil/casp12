from lxml.etree import HTML
from csv import unix_dialect, DictReader, register_dialect
from collections import OrderedDict
from ..database import get_or_add_method, store_qa, store_model_caspmethod
from re import compile


class casp_dialect(unix_dialect):
    """Change delimiter to ;"""
    delimiter = ';'
register_dialect("casp", casp_dialect)


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


def parse_lga_sda_summary(infile, summaryregex="^([^\.])\.lga:SUMMARY(GDT)\s+(.*)\Z"):
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



def parse_lga_sda(infile, lgaregex="^LGA", modelregex = "^# Molecule1:.* selected  (\d+) .* name (\S+)$", evidenceregex = "^# Molecule2:.* selected  (\d+) .* name (\S+)$"):
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
             4) tuple with integer length of selection evaluated, first element
                is model, second is gold standard
    """
    lgaentry = compile(lgaregex)
    evidence_entry = compile(evidenceregex)
    model_entry = compile(modelregex)

    distances = OrderedDict()
    model = None
    evidence = None
    selection = (None, None)

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
                    selection[0] = int(m.group[0])


    return distances, model, evidence, selection


def parse_lga_lddt(infile, lddtregex="^.\s+(\S+)\s+(\d+)\s+(\S+)\s(\S+)\s*\Z", modelregex = "^File: (\S+)", globalregex="^Global LDDT score: (\d+\.\d+)"):
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
        if lddtentry:
            residue = int(m.group(3))
            try:
                score = float(m.group(6))
                scores[residue] = score
            except:
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


def store_casp_qa(target, caspserver, model, global_score, scores, qa_method, database, component=None):
    """ Save local scores from CASP-server, converting casp-server to method ID
    and padding score/distance list

    :param target: text CASP target
    :param caspserver: integer CASP server ID
    :param model: integer server model serial
    :param global_score: float global score
    :param scores: OrderedDict with integer residue serials as keys and float
                   scores as values
    :param qa_method: integer qa method ID
    :param database: database connection
    :param component: integer domain ID (None is default)
    :return: integer ID of stored QA
    """
    # Create a enumerate list from 1, with Nones for missing data, so that it is
    # compatible with database.store_local_score
    local_score = pad_scores(scores)

    # Get the model ID using the conversion getting method, model should be modelname containing
    # Target, server and model identifiers that are parseable.
    model_id = store_model_caspmethod(target, caspserver, model, database)

    qa_id = store_qa(model_id, global_score, local_score, qa_method, database,
             component=component)

    return qa_id



