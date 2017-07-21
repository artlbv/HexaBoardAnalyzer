#!/usr/bin/env python2
#import sys
#sys.argv.append('-b')

from plotNoise import *
from readHexConvData import *

rt.gROOT.SetBatch(True)
#sys.argv.remove('-b')

if __name__ == "__main__":

    if len(sys.argv) > 1:
        fname = sys.argv[1]
        print '# Input files are', fname
    else:
        print "No input files given!"
        exit(0)

    treefname = createTree(fname)
    runPlotNoise(treefname)
