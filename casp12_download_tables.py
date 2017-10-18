#!/usr/bin/env python3
from casp12.interface.http import download_new_targets
from casp12.interface.filesystem import identify_tarballs, unpack_tarballs

'''
 Download and unpack tables from predictioncenter.org or other
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
        "casp12_download_tables  Copyright (C) 2017  Robert Pilstål;",
        "This program comes with ABSOLUTELY NO WARRANTY.",
        "This is free software, and you are welcome to redistribute it",
        "under certain conditions; see supplied General Public License."
    ])


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Download table data from predictioncenter.org or other")
    parser.add_argument(
        "-regex", nargs=1, default=["^(T.\d+)[-.]"], metavar="str",
        help="Target regex to use, default='^(T.\d+)[-.]'")
    parser.add_argument('-v', '--version', action='version',
                        version=get_version_str())
    parser.add_argument(
        "url", nargs=1, metavar="URL", help="Download URL")
    parser.add_argument(
        "destination", nargs=1, metavar="DIR", help="Destination directory")
    arguments = parser.parse_args(argv[1:])

    # Set variables here
    destination = arguments.destination[0]
    regex = arguments.regex[0]
    url = arguments.url[0]

    # Download and unpack
    targets = download_new_targets(url, destination, targetregex=regex)
    tarballs = identify_tarballs(targets)
    unpack_tarballs(tarballs, destination)


if __name__ == '__main__':
    main()
