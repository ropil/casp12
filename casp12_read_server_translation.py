#!/usr/bin/env python3
from re import compile
from urllib.request import urlopen
from sqlite3 import connect
from casp12.database import store_caspservers
from casp12.interface.casp import parse_server_definitions

'''
 Read online CASP server definitions and store translation in database
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
        "casp12_read_server_translation  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
        ])


# Library functions
def find_servers(url):
    """Opens url with urllib and passes it to server parser function

    :param url: Text CASP server url to open
    :return: Dictionary with CASP server id integers as keys and tuples of
             server textual name and server textual type as values
    """
    servers = {}

    # Get and read the text from the webpage
    with urlopen(url) as webpage:
        server_listing = webpage.read()

    servers = parse_server_definitions(server_listing)

    return servers


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Utility to identify CASP servers from online web.")
    parser.add_argument(
        "-all", action="store_true", default=False,
        help="Store all servers, default=only those that translate to method"
    )
    parser.add_argument(
        "-casp", nargs=1, default=["12"], metavar="int",
        help="CASP experiment, default=12")
    parser.add_argument(
        "-url", nargs=1, default=["http://predictioncenter.org/casp12/docs.cgi?view=groupsbyname"],
        metavar="URL", help="CASP server listing, " +
                            "default=http://predictioncenter.org/casp12/docs.cgi?view=groupsbyname")
    parser.add_argument('-v', '--version', action='version', version=get_version_str())
    parser.add_argument(
        "database", nargs=1, metavar="file", help="Database within which to store results")
    arguments = parser.parse_args(argv[1:])
    database_file = arguments.database[0]

    # Set variables here
    all = arguments.all
    casp = int(arguments.casp[0])
    url = arguments.url[0]

    # Get all new target urls
    servers = find_servers(url)

    # Store servers and save database
    database = connect(database_file)
    stored = store_caspservers(servers, casp, database, all=all)
    database.commit()
    database.close()

    for server in servers:
        print("".join(["{:03d}\t: {}".format(int(server), servers[server][0]), " (stored)" if server in stored else ""]))


if __name__ == '__main__':
    main()