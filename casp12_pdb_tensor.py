#!/usr/bin/env python3
from pdbparse.pdb_distances import getAtomPositions, getDistance


# Library functions
def printDistanceMatrix(chains, chainorder, chainlength, delimiter=';'):
    """Prints a MATLAB dlmread-readable matrix

    :param chains: a dict with chain identifiers pointing to lists of tuples
                   with coordinates
    :param chainorder: a list of the sorted keys of the dict chains
    :param chainlength: a dict with the length of each chain
    """
    # for every residue in every chain
    for ca in chainorder:
        for a in range(chainlength[ca]):
            # do, for every residue in every chain,
            distances = []
            for cb in chainorder:
                for b in range(chainlength[cb]):
                    # save the minimum distance between the residues
                    distances.append(getDistance(chains, a, b, ca, cb))
            # Print the distances to the current residue
            print(delimiter.join([str(i) for i in distances]))

# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Print a MATLAB distance tensor from a set of PDB-interface." +
    " This version is not aware of residue numbering")
    parser.add_argument(
        "-delim", nargs=1, default=[";"], metavar="str",
        help="Set delimiter, default=;")
    parser.add_argument(
        "interface", nargs="*", metavar="FILE", help="PDB-interface for input")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files

    # Set variables here
    delimiter = arguments.delim[0]
    chainlength = {}

    # Parse interface, checking for lengths
    # this is currently unnecessary since we are not residue aware here
    for f in files:
        with open(f, 'r') as infile:
            chains = getAtomPositions(infile)
            for chain in chains:
                if chain not in chainlength:
                    chainlength[chain] = len(chains[chain])
                elif chainlength[chain] != len(chains[chain]):
                    # This is a safety check until we implement a mapper method
                    # to handle models of varying length
                    raise IndexError("Chains with identical ID is not of" +
                                     " same length! (deviant (file, chain," +
                                     " len); ({}," +
                                     " {}, {}))".format(f, chain,
                                                        len(chains[chain])))

    # This is the residual length of the model
    total_len = sum([chainlength[i] for i in chainlength])
    chainorder = list(chainlength.keys())
    chainorder.sort()

    # Reread and print the tensor
    for f in files:
        with open(f, 'r') as infile:
            chains = getAtomPositions(infile)
            printDistanceMatrix(chains, chainorder, chainlength,
                                delimiter=delimiter)


if __name__ == '__main__':
    main()
