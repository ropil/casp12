from lxml.etree import HTML
from csv import unix_dialect, DictReader, register_dialect
from collections import OrderedDict
from ..database import get_or_add_method, store_qa
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

#X        MET     3       No      No      -       -
def parse_lga_lddt(infile, lddtregex="^.\s+(\S+)\s+(\d+)\s+(\S+)\s(\S+)\s*\Z", modelregex = "^File: (\S+)"):
    """Parse a LDDT file

    :param infile: interable with strings of LDDT file to parse
    :param lddtregex: string with regex finding LDDT score lines
    :param modelregex: string with regex identifying model file
    :return: tuple with
             1) OrderedDict containing integer of residue number as keys and
                float of transformed distance (score) as value
             2) string with Model file name
    """
    lddtentry = compile(lddtregex)
    modelentry = compile(modelregex)

    scores = OrderedDict()
    model = None
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

    return scores, model


def store_lga_sda(model, global_score, distances, qa_method, database, component=None):
    length = max(distances.keys())

    # Create a enumerate list from 1, with Nones for missing data, so that it is
    # compatible with database.store_local_score
    local_score = []
    for i in range(1, length + 1):
        if i in distances:
            local_score.append(distances[i])
        else:
            local_score.append(None)

    method_id = get_or_add_method(qa_method, "CASP lga_sda,\nadded by store_lga_sda", "qa", database)

    # Get the model ID using the conversion getting method, model should be modelname containing
    # Target, server and model identifiers that are parseable.

    qa_id = store_qa(model, global_score, local_score, method_id, database,
             component=component)



