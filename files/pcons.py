from os import path


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
