#!/usr/bin/env python3
from urllib.request import urlopen
from sqlite3 import connect
from casp12.interface.casp import parse_target_information
from casp12.database import store_target_information

'''
 Read online CASP target information and store it in database
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
        "casp12_target_information  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
        ])


# Library functions
def get_target_information(url):
    """Opens url with urllib and passes it to target parser function

    :param url: Text CASP target csv url to open
    :return: csv DictionaryReader class with target information
    """

    # Get and read the text from the webpage
    response = urlopen(url)
    target_information = response.read()

    targets = parse_target_information(target_information.decode().split('\n'))

    return targets


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Utility to read CASP target information from online web.")
    parser.add_argument(
        "-casp", nargs=1, default=["12"], metavar="int",
        help="CASP experiment, default=12")
    parser.add_argument(
        "-force", action="store_true", default=False,
        help="Force storing new targets, default=Only update present targets")
    parser.add_argument(
        "-url", nargs=1, default=["http://predictioncenter.org/casp12/targetlist.cgi?type=csv"],
        metavar="URL", help="CASP target listing, " +
                            "default=http://predictioncenter.org/casp12/targetlist.cgi?type=csv")
    parser.add_argument('-v', '--version', action='version', version=get_version_str())
    parser.add_argument(
        "database", nargs=1, metavar="file", help="Database within which to store results")
    arguments = parser.parse_args(argv[1:])
    database_file = arguments.database[0]

    # Set variables here
    casp = int(arguments.casp[0])
    force = arguments.force
    url = arguments.url[0]

    # Get all new target urls
    dictreader = get_target_information(url)

    # Store servers and save database
    database = connect(database_file)
    (targets, stored) = store_target_information(dictreader, casp, database, force=force)
    database.commit()
    database.close()

    # Print found targets, indicating which was stored in database
    for target in targets:
        print("".join(["{}\t: {}".format(target, targets[target]), " (stored)" if target in stored else ""]))




if __name__ == '__main__':
    main()