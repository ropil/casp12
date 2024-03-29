#!/usr/bin/env python3
from pdb_reader import Pdb

#library functions go here

def readDomOutput(infile):
    defs = []
    for line in infile:
        [i, dom] = line.split()
        defs.append(int(dom))
    return defs

def printDomains(domainresidues):
    for domain in domainresidues:
        previous = int(domain[0])
        print(str(previous), end="")
        for residue in domain:
            if previous < int(residue) - 1:
                print(" {} {}".format(previous, int(residue)), end="")
            if residue == domain[-1]:
                print(" {}".format(int(residue)))
            previous = int(residue)

def printDomainsDat(defs, pdb):
    num = 0
    for i in range(len(defs)):
        for chain in pdb:
            # Print out the first residue found in the PDB
            try:
                print("{} {}".format(i+1, defs[i]))
                break
            except:
                pass


#main definition for callable scripts
def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Reformat partition.dat to domains.def format.")
    parser.add_argument(
        "-p", action="store_true", default=False,
        help="Just renumber, keeping partition.dat format")
    parser.add_argument("dom", nargs=1, metavar="DOMinfile",
                        help="geteigen output file")
    parser.add_argument("pdb", nargs=1, metavar="PDBinfile",
                        help="PDB file")
    arguments = parser.parse_args(sys.argv[1:])

        #Read domain definitions
    with open(arguments.dom[0], 'r') as infile:
        defs = readDomOutput(infile)

    printDat=arguments.p

        #read PDB-file
    pdb = Pdb()
    with open(arguments.pdb[0], 'r') as infile:
        pdb.read(infile)


        #sort the domains pertaining to first occuring residue
    domains = {}
    for residue in range(len(defs)):
        if not defs[residue] in domains:
            domains[defs[residue]] = residue
    domainorder = [[domains[domain], domain] for domain in list(domains.keys())]
    domainorder.sort()

    if printDat:
        printDomainsDat(defs, pdb)
    else:
        #split the pdb's
        domainresidues = []
        for d in domainorder:
            domain = d[1];
            domainresidues.append([])
            num = 0
            for chain in pdb:
                for residue in chain:
                    if defs[num] == domain:
                        domainresidues[-1].append(residue.aanumber)
                    num += 1

        printDomains(domainresidues)


    #if called from command line
if __name__ == '__main__':
    main()
