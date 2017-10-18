from os import listdir, walk
from os.path import isfile, join
from re import compile
from subprocess import run


def find_all_files(directory):
    """Returns all filenames found in a directory structure

    :param directory: Top directory to scan
    :return: list of full paths of all files found
    """
    files = []
    for (dirpath, dirnames, filenames) in walk(directory):
        for filename in filenames:
            files.append(join(dirpath, filename))
    return files


def find_targets_downloaded(directory, verbose=False):
    """Scan a directory of files

    :param directory: string of directory path to list
    :param verbose: bool; true print all files found
    :return: dictionary with string filenames as keys and text filepath as
             values
    """
    targets_downloaded = {}
    # Check all files in directory
    for target in listdir(directory):
        # Only consider files
        target_path = join(directory, target)
        if isfile(join(directory, target)):
            if verbose:
                print("Found target " + target + " with path " + target_path)
            targets_downloaded[target] = target_path
    return targets_downloaded


def identify_tarballs(targets, tar_regexes=["^.*\.tgz", "^.*\.tar\.gz"]):
    """Use regexes to identify tarballs from target file listings

    :param targets: Nested dictionary with targets as keys and dictionary as
                    values. Value dictionary with filenames as keys and path as
                    values.
    :param tar_regexes: list of strings with regexes to recognize tarballs
    :return: list of recognized tarball paths
    """
    tarballs = []
    regexes = [compile(regex) for regex in tar_regexes]
    for target in targets:
        for filename in targets[target]:
            for regex in regexes:
                if regex.match(filename):
                    tarballs.append(targets[target][filename])
                    break
    return tarballs



def unpack_tarballs(files, destination):
    """ Unpacks a number of files using tar xzf

    :param files: iterable with strings of tarball filenames
    :param destination: string path to destination directory, where to unpack
    """
    unpack_cmd = ["tar", "xzf"]
    unpack_suffix = ["-C", destination]
    for ball in files:
        cmd = unpack_cmd + [ball] + unpack_suffix
        run(cmd)
