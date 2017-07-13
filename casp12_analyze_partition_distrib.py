#!/usr/bin/env python3
from re import compile
from sqlite3 import connect

'''
 Analyze domain partition distribution in target set, storing result in database
 Copyright (C) 2017  Robert Pilstål

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.
'''


# Version and license information
def get_version_str():
    return "\n".join([
        "casp12_analyze_partition_distrib  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
    ])


# Library functions
def create_database():
    # Create in-memory
    """Creates the database, in memory, to use for analyzing domain partitions

    :return: the database connection handle
    """

    '''Copy the following to sqlite3 prompt to try it in console
    CREATE TABLE casp(id int PRIMARY KEY);
    CREATE TABLE target(id text, len int, casp int REFERENCES casp(id), PRIMARY KEY (id, casp));
    CREATE TABLE domain(num int, target text REFERENCES target(id), casp int REFERENCES target(casp), PRIMARY KEY (num, target, casp));
    CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(num), target text REFERENCES domain(target), casp int REFERENCES domain(casp), PRIMARY KEY (start, domain, target, casp));
    CREATE TRIGGER segment_length_insert BEFORE INSERT ON segment FOR EACH ROW BEGIN UPDATE NEW SET len = stop - start + 1; END;
    CREATE TRIGGER segment_length_update BEFORE UPDATE ON segment FOR EACH ROW BEGIN UPDATE NEW SET len = stop - start + 1; END;
    CREATE VIEW domain_size (casp, target, domain, dlen, nseg) AS SELECT domain.casp, domain.target, domain.num, SUM(segment.len), COUNT(*) FROM domain INNER JOIN segment ON (domain.casp = segment.casp, domain.target = segment.target, domain.num = segment.domain) GROUP BY domain.casp, domain.target, domain.num ORDER BY dlen;
    '''

    database = connect(":memory:")
    # CASP table
    database.execute("CREATE TABLE casp(id int PRIMARY KEY);")
    # CASP targets table
    #
    database.execute("CREATE TABLE target(id text, " +
                     "len int, " +
                     "casp int REFERENCES casp(id), " +
                     "PRIMARY KEY (id, casp));")
    # Corresponding domains table
    # "CREATE TABLE domain(num int, target text REFERENCES target(id), casp int REFERENCES target(casp), PRIMARY KEY (num, target, casp));
    database.execute("CREATE TABLE domain(num int, " +
                     "target text REFERENCES target(id), " +
                     "casp int REFERENCES target(casp), " +
                     "PRIMARY KEY (num, target, casp));")
    # Segment definitions table
    database.execute("CREATE TABLE segment(start int, stop int, len int, domain int REFERENCES domain(num), target text REFERENCES domain(target), casp int REFERENCES domain(casp), PRIMARY KEY (start, domain, target, casp));")
    # Synthetic variables
    # Triggers for segment length calculation
    database.execute("CREATE TRIGGER segment_length_insert BEFORE INSERT ON segment FOR EACH ROW BEGIN UPDATE NEW SET len = stop - start + 1; END;")
    database.execute("CREATE TRIGGER segment_length_update BEFORE UPDATE ON segment FOR EACH ROW BEGIN UPDATE NEW SET len = stop - start + 1; END;")
    # Domain size view, sorted by largest domain
    database.execute("CREATE VIEW domain_size (casp, target, domain, dlen, nseg) AS SELECT domain.casp, domain.target, domain.num, SUM(segment.len), COUNT(*) FROM domain INNER JOIN segment ON (domain.casp = segment.casp, domain.target = segment.target, domain.num = segment.domain) GROUP BY domain.casp, domain.target, domain.num ORDER BY dlen;")
    return database


def read_domain(infile):
    """Parse the domain definitions and the corresponding segments in a given
    domain file.

    :param infile: iterator object with an entry/line per domain defined;
                   segments are defined by pairs of index integers separated by
                   whitespace.
    :return: list of domains constituted of lists of segment definition tuples
    """
    domains = []
    for line in infile:
        segdef = [int(x) for x in line.split()]
        domains.append([segdef[i:i + 2] for i in range(0, len(segdef), 2)])
    return domains


def print_domains(domains):
    """Regurgitates what is already read, in text format: <target> <seg> <seg> .

    :param domains: domain definitions, a dictionary with target names as keys
                    to lists of domains pertaining to that target.
    """
    namelen = max([len(name) for name in domains])
    output = "{: <" + str(namelen) + "} {}"
    for target in domains:
        for domain in domains[target]:
            print(output.format(target, " ".join(
                [str(seg[0]) + " " + str(seg[1]) for seg in domain])))


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Analyze domain partition distribution in a target set" +
                    " and store results in sqlite3.")
    parser.add_argument(
        "-a", action="store_true", default=False, help="Prints nothing")
    parser.add_argument(
        "-nameregex", nargs=1, default=["^.*/(T\d{4})/.*$"], metavar="TEXT",
        help="Regex to use for extracting targetnames from file pathnames" +
             ", default=^.*/(T\d{4})/.*$")
    parser.add_argument(
        "-target", nargs=1, default=[None], metavar="TEXT",
        help="Target name (if reading STDIN), default=None")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "files", nargs="*", metavar="FILE", help="Files for input")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files
    # Use stdin if no supplied files
    if len(arguments.files) == 0:
        files = [stdin]

    # Set variables here
    target = arguments.target[0]
    if target is None:
        target = 'UNK'
    nameregex = compile(arguments.nameregex[0])
    domains = {}

    # Parse STDIN or files
    for f in files:
        infile = f
        thistarget = target
        # Open for reading if file path specified
        if isinstance(f, str):
            infile = open(f, 'r')
            thistarget = nameregex.search(f).group(1)
        domains[thistarget] = read_domain(infile)

    # Dump read domains
    print_domains(domains)


if __name__ == '__main__':
    main()
