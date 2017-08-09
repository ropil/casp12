#!/usr/bin/env python3
from numpy import array, zeros


# Library functions
def readArrayFromFile(infile):
    entries = []
    for line in infile:
        entries.append(float(line))
    return array(entries)

def average(vectors):
    vector = zeros(vectors[0].shape)
    for v in vectors:
        vector = vector + v
    vector /= float(len(vectors))
    return vector

def divideBySum(vector):
    return vector / sum(vector)

def printVector(vector):
    for element in vector:
        print(str(element))


# Main; for callable scripts
def main():
    from argparse import ArgumentParser
    from sys import argv, stdin
    parser = ArgumentParser(
        description="Operate on quality assesment vectors.")
    parser.add_argument(
        "-sum", action="store_true", default=False,
        help="Divide scores with the sum of all scores (default)")
    parser.add_argument(
        "-t", nargs=1, default=["nothing"], metavar="TEXT",
        help="What to print")
    parser.add_argument(
        "files", nargs="*", metavar="FILE", help="Files for input")
    arguments = parser.parse_args(argv[1:])
    files = arguments.files
    # Use stdin if no supplied interface
    if len(arguments.files) == 0:
        files = [stdin]

    # Set variables here
    vectors = []

    # Parse STDIN or interface
    for f in files:
        infile = f
        # Open for reading if file path specified
        if isinstance(f, str):
            infile = open(f, 'r')
        vectors.append(readArrayFromFile(infile))
        infile.close()

    vector = average(vectors)

    if arguments.sum:
        vector = divideBySum(vector)
    else:
        vector = divideBySum(vector)

    printVector(vector)

if __name__ == '__main__':
    main()