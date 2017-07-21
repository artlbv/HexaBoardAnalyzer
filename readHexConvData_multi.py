#!/usr/bin/env python2

import sys,csv
import numpy as np
from array import array

print("Loading ROOT")
import ROOT as rt

# global variables
nchips = 4*4
nchans = 64
nsca = 13

def getTimePos(roll):

    roll_np = np.array(roll)
    timepos = np.array(range(13))

    # roll/shift positions
    if (roll_np[0] == 1 and roll_np[12] == 1):
        # 100000000001
        timepos[0] = 12
        for i in range(1,13): timepos[i] = i-1
    else:
        # 000011000000
        # 1. find first sca in track
        pos_trk1 = -1
        for i in range(13):
            if roll[i] == 1:
                pos_trk1 = i
                break
        # 2. shift all positions
        for i in range(13):
            if i <= pos_trk1 + 1: timepos[i] = i + 12 - (pos_trk1 + 1)
            else: timepos[i] = i - 1 - (pos_trk1 + 1)

    #print roll_np, timepos

    return timepos

def createTree(fname):

    #foutname = fname.replace('.txt','_new.root')
    foutname = fname.replace('.txt','_multi.root')
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
    roll_b = array('i', nchips * nsca * [ 0 ])
    ts_b = array('i', nchips * nsca * [ 0 ])

    # charges
    hgain_b = array('i', nchips * nsca * nchans * [ -99 ])
    lgain_b = array('i', nchips * nsca * nchans * [ -99 ])
    # tot
    tot_fast_b = array('i', nchips * nchans * [ -99 ])
    tot_slow_b = array('i', nchips * nchans * [ -99 ])
    # toa
    toa_rise_b = array('i', nchips * nchans * [ -99 ])
    toa_fall_b = array('i', nchips * nchans * [ -99 ])
    ## sums
    sum_lg_b = array('i', nchips * [0])
    sum_hg_b = array('i', nchips * [0])
    nhits_toa_b = array('i', nchips * [0])
    nhits_tot_b = array('i', nchips * [0])
    nhits_toa_all_b = array('i', [0])
    nhits_tot_all_b = array('i', [0])

    # tree branches
    ## sk2cms data
    tree.Branch( 'event', event_b, 'event/I' )
    tree.Branch( 'chip', chip_b, 'chip/I' )
    tree.Branch( 'roll', roll_b, 'roll[' + str(nchips) + '][13]/I' )
    tree.Branch( 'timesamp', ts_b, 'timesamp[' + str(nchips) + '][13]/I' )
    tree.Branch( 'hg', hgain_b, 'hg[' + str(nchips) + '][13][64]/I' )
    tree.Branch( 'lg', lgain_b, 'lg[' + str(nchips) + '][13][64]/I' )
    tree.Branch( 'tot_fast', tot_fast_b, 'tot_fast[' + str(nchips) + '][64]/I' )
    tree.Branch( 'tot_slow', tot_slow_b, 'tot_slow[' + str(nchips) + '][64]/I' )
    tree.Branch( 'toa_rise', toa_rise_b, 'toa_rise[' + str(nchips) + '][64]/I' )
    tree.Branch( 'toa_fall', toa_fall_b, 'toa_fall[' + str(nchips) + '][64]/I' )

    ## sums
    tree.Branch( 'sum_lg', sum_lg_b, 'sum_lg[' + str(nchips) + ']/I' )
    tree.Branch( 'sum_hg', sum_hg_b, 'sum_hg[' + str(nchips) + ']/I' )
    tree.Branch( 'nhits_toa', nhits_toa_b, 'nhits_toa[' + str(nchips) + ']/I' )
    tree.Branch( 'nhits_tot', nhits_tot_b, 'nhits_tot[' + str(nchips) + ']/I' )
    tree.Branch( 'nhits_toa_all', nhits_toa_all_b, 'nhits_toa_all/I' )
    tree.Branch( 'nhits_tot_all', nhits_tot_all_b, 'nhits_tot_all/I' )

    event = -99
    gain_type = "lg"
    chan = 0
    chip = -99

    #skip_file = False

    fin = open(fname,"read")
    print("Reading file %s"%fname)
    for line in fin.readlines():#[:1000]:

        if "Event" in line:
            # check counter
            if chan != 0:
                print("Channel number incorrect!!!!!")
                chan = 0

                event = -99
                gain_type = "lg"
                chan = 0
                chip = -99

                break
                #exit(0)

            # fill previous event/chip  ## Reset counters
            if event > 0 and chip == nchips-1:
                #calc toa/tot tot hits
                nhits_toa_all_b[0] = int(sum(nhits_toa_b))
                nhits_tot_all_b[0] = int(sum(nhits_tot_b))
                #print nhits_toa_b, nhits_tot_b
                #print nhits_toa_all_b, nhits_tot_all_b

                tree.Fill()

                #nhits_toa_all_b = 0
                #nhits_tot_all_b = 0
                #print nhits_toa_b, nhits_tot_b

            #if event > 100: break

            header_items = line.split()
            event = int(header_items[1])
            chip = int(header_items[3])

            # read and convert roll position
            roll_bin = format(int(header_items[5],16), '#015b')
            roll = array('i', [ int(roll_bin[i+2]) for i in range(nsca) ] )

            # check rollmask has only two 1
            if sum(roll) != 2 and chip == 0:
                print("Warning! In event %i the rollmask sum is %i" %(event, sum(roll)))
                print("Stopping!")
                break

            '''
            if chip > 0:
                if roll_b != roll:
                    print "Rollmask mistmach between chips!:", event, roll_b, roll
            '''

            # fill branches
            event_b[0] = event
            chip_b[0] = chip
            for i in range(nsca): roll_b[chip*nsca + i] = roll[i]
            #print roll, roll_b

            # time pos
            timepos = getTimePos(roll)
            sca_in_ts30 = -1
            sca_in_ts3 = -1
            #print timepos
            for i in range(nsca):
                ts_b[chip*nsca + i] = timepos[i]
                if timepos[i] == 3: sca_in_ts3 = i
                if timepos[i] == 0: sca_in_ts0 = i

            #if (chip == 0) and (event % 100 == 0): print("Event %i, chip %i" % (event, chip))
            if (chip == 0) and (event % 100 == 0): print("Event %i" % (event))

            #print sum_lg_b
            #print nhits_toa_b, nhits_tot_b
            # reset arrays
            for k in [chip]:
                sum_lg_b[k] = 0
                sum_hg_b[k] = 0
                nhits_toa_b[k] = 0
                nhits_tot_b[k] = 0

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
            if (len(items) != 15):
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

                #sum_hg_b[chip] += sum(items)
                if chan %2 == 1:
                    #sum_hg_b[chip] += items[nsca-1-sca_in_ts3] - items[nsca-1-sca_in_ts0]
                    sum_hg_b[chip] += max(items)

            elif gain_type == "lg":
                # fill charge
                for i in range(nsca): lgain_b[chip * nchans*nsca + i*nchans + nchans-1-chan] = int(items[nsca-1-i])
                # fill tot/toa
                if (len(items) == 15):
                    toa_rise_b[chip * nchans + nchans-1-chan] = items[13]
                    tot_fast_b[chip * nchans + nchans-1-chan] = items[14]

                #sum_lg_b[chip] += sum(items)
                if chan %2 == 1:
                    #sum_lg_b[chip] += items[nsca-1-sca_in_ts3] - items[nsca-1-sca_in_ts0]
                    sum_lg_b[chip] += max(items)
                    if items[13] > 5: nhits_toa_b[chip] += 1
                    if items[14] > 5: nhits_tot_b[chip] += 1
                    #nhits_toa_b[chip] += 1

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


if __name__ == "__main__":


    if len(sys.argv) == 2:
        fnames = sys.argv[1:]
        #fname = fnames[0]
        print '# Input file is', fnames[0]
    elif len(sys.argv) > 2:
        fnames = sys.argv[1:]
        #fname = fnames[0] + "all.txt"
        print("#input file %i"%len(fnames))
    else:
        print("No input files given!")
        #exit(0)

        #fname = "/Users/artur/Dropbox/Work/LLR/HGCAL/SK2cms/hexaboard/fromDocDB/RUN_170317_0912.txt"
        fnames = ["/Users/artur/Downloads/Hexaboard_data/RUN_290317_1109.txt"]

        print("Using " + fname[0])

    for fname in fnames:
        if "raw.txt" in fname: continue
        print fname
        createTree(fname)
