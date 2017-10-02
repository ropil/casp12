from lxml.etree import HTML


def parse_server_definitions(page):
    xml = HTML(page)

    path_groupname = "//table[@id='table_results']//td[@title='Group Name']/b"
    group_names = [element.text for element in xml.xpath(path_groupname)]
    print(group_names)

    path_groupcode = "//table[@id='table_results']//td[@title='Group Code']"
    group_codes = [element.text for element in xml.xpath(path_groupcode)]
    print(group_codes)

    path_grouptype = "//table[@id='table_results']//td[@title='Group Type']"
    group_types = [element.text for element in xml.xpath(path_grouptype)]
    print(group_types)

    servers = {}
    for (code, name, stype) in zip(group_codes, group_names, group_types):
        servers[code] = (name, stype)

    return servers