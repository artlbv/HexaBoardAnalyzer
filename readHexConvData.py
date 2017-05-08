#!/usr/bin/env python2

import sys,csv
import numpy as np
from array import array

print("Loading ROOT")
import ROOT as rt

# global variables
nchips = 4
nchans = 64
nsca = 13

if __name__ == "__main__":


    if len(sys.argv) > 1:
        fname = sys.argv[1]
        print '# Input files are', fname
    else:
        print "No input files given!"
        #exit(0)

        #fname = "/Users/artur/Dropbox/Work/LLR/HGCAL/SK2cms/hexaboard/fromDocDB/RUN_170317_0912.txt"
        fname = "/Users/artur/Downloads/Hexaboard_data/RUN_290317_1109.txt"

        print("Using " + fname)

    fin = open(fname,"read")
    #foutname = fname.replace('.txt','_new.root')
    foutname = fname.replace('.txt','.root')
    print("Storing data in " + foutname)

    fout = rt.TFile( foutname, 'recreate' )
    tree = rt.TTree( 'sk2cms', 'sk2cms tree' )

    # variables for tree
    event_b = np.array(  [ 0 ] , dtype=int)
    chip_b = np.array(  [ 0 ] , dtype=int)

    #nsca_b = np.array(  [ nsca ] , dtype=int)
    #nchans_b = np.array(  [ nchans ] , dtype=int)

    # roll position: roll[13] of 1 or 0
    #roll_b = np.array(nsca * [ 0 ], dtype=int)
    roll_b = array('i', nsca * [ 0 ])

    # charges
    hgain_b = array('i', nchips * nsca * nchans * [ -99 ])
    lgain_b = array('i', nchips * nsca * nchans * [ -99 ])
    # tot
    tot_fast_b = array('i', nchips * nchans * [ -99 ])
    tot_slow_b = array('i', nchips * nchans * [ -99 ])
    # toa
    toa_rise_b = array('i', nchips * nchans * [ -99 ])
    toa_fall_b = array('i', nchips * nchans * [ -99 ])

    # tree branches
    ## sk2cms data
    tree.Branch( 'event', event_b, 'event/I' )
    tree.Branch( 'chip', chip_b, 'chip/I' )
    tree.Branch( 'roll', roll_b, 'roll[13]/I' )
    tree.Branch( 'hg', hgain_b, 'hg[4][13][64]/I' )
    tree.Branch( 'lg', lgain_b, 'lg[4][13][64]/I' )
    tree.Branch( 'tot_fast', tot_fast_b, 'tot_fast[4][64]/I' )
    tree.Branch( 'tot_slow', tot_slow_b, 'tot_slow[4][64]/I' )
    tree.Branch( 'toa_rise', toa_rise_b, 'toa_rise[4][64]/I' )
    tree.Branch( 'toa_fall', toa_fall_b, 'toa_fall[4][64]/I' )

    event = -99
    gain_type = "lg"
    chan = 0
    chip = -99

    print("Reading file")
    for line in fin.readlines():#[:1000]:

        if "Event" in line:
            # check counter
            if chan != 0: print("Channel number incorrect!!!!!")

            # fill previous event/chip
            if event >= 0 and chip == 3: tree.Fill()
            #if event > 10: break

            header_items = line.split()
            event = int(header_items[1])
            chip = int(header_items[3])

            # read and convert roll position
            roll_bin = format(int(header_items[5],16), '#015b')
            roll = array('i', [ int(roll_bin[i+2]) for i in range(nsca) ] )

            #if chip != 0: break

            # fill branches
            event_b[0] = event
            chip_b[0] = chip
            for i in range(nsca): roll_b[i] = roll[i]

            if (chip == 0) and (event % 500 == 0): print("Event %i, chip %i" % (event, chip))

            # reset arrays
            for k in [chip]:
                for j in range(nchans):

                    tot_fast_b[k*nchans + j] = -99
                    tot_slow_b[k*nchans + j] = -99
                    toa_rise_b[k*nchans + j] = -99
                    toa_fall_b[k*nchans + j] = -99

                    for i in range(nsca):

                        hgain_b[k*nchans*nsca + i*nchans + j] = -99
                        lgain_b[k*nchans*nsca + i*nchans + j] = -99

        else:
            # check line contains data (x nsca)
            items = line.split()

            #if (len(items) != nsca) or (len(items) != (nsca + 2)): continue
            if (len(items) != 13): continue
            # check there was an event header before
            if event == -99:
                print("No event header before data line!");
                continue

            # read data
            #print("Reading chan %i in %s" %(chan,gain_type) )
            items = [int(item) for item in line.split()]

            # convert over/undershoot
            for i,item in enumerate(items):
                if item == 0: items[i] = 4096
                elif item == 4: items[i] = 0

            # have to invert channel and sca number
            if gain_type == "hg":
                # fill charge
                for i in range(nsca): hgain_b[chip * nchans*nsca + i*nchans + nchans-1-chan] = int(items[nsca-1-i])
                # fill toa/tot
                if (len(items) == 15):
                    toa_fall_b[chip * nchans + nchans-1-chan] = items[13]
                    tot_slow_b[chip * nchans + nchans-1-chan] = items[14]
            elif gain_type == "lg":
                # fill charge
                for i in range(nsca): lgain_b[chip * nchans*nsca + i*nchans + nchans-1-chan] = int(items[nsca-1-i])
                # fill tot/toa
                if (len(items) == 15):
                    toa_rise_b[chip * nchans + nchans-1-chan] = items[13]
                    tot_fast_b[chip * nchans + nchans-1-chan] = items[14]


            # switch counters
            if chan == 63:
                chan = 0
                if gain_type == "lg": gain_type = "hg"
                elif gain_type == "hg": gain_type = "lg"
            else:
                chan += 1

    # fill last event
    tree.Fill()
    print("Tree filled")

    tree.Write()
    tree.Print()

    fout.Close()
