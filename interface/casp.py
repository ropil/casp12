from lxml.etree import HTML
from csv import unix_dialect, DictReader, register_dialect


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