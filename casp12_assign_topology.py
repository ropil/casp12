#!/usr/bin/env python3
import pdb_reader

#library functions go here

def readTopology(infile):
    topology = {}
    for line in infile:
        entries = line.split()
        topology[int(entries[0])] = float(entries[1])
    return topology

    #enumerate from 1 to len(domains)
def setBFactor(models, topology):
    for pdb in models:
        #num = 0
        for chain in pdb:
            for residue in chain:
                residue.setTemperature(topology[residue.getNumber()])
                #num += 1
    return models

#main definition for callable scripts
def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Assign topology to tempfactors.")
    parser.add_argument("-top", nargs=1, metavar="FILE",
                        help="Topology file to read")
    parser.add_argument("files", nargs="*", metavar="FILE",
                        help="PDB's to set factors")
    arguments = parser.parse_args(sys.argv[1:])
        
        #Read topology
    topology = []
    with open(arguments.top[0], 'r') as infile:
        topology = readTopology(infile)
        
    files = arguments.files
        #use stdin if no supplied files
    if len(arguments.files) == 0:
        files = [sys.stdin]        
    for f in files:
        infile = f
            #open file for reading if path to file specified
        if isinstance(f, type("")):
            infile = open(f, 'r')
            #read models
        models = pdb_reader.Models()
        models.read(infile)
        infile.close()
            #set bfactor
        models = setBFactor(models, topology)
            #print
        print(models)

    #if called from command line
if __name__ == '__main__':
    main()