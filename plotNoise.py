#!/usr/bin/env python2

import glob, sys, os, array, math
import numpy as np
import ROOT as rt

#rt.TGaxis.SetMaxDigits(3)

########################
def getChanData(tree, chip = 0, chan = 0, sca = 0, variabs = []):

    data = { var:[] for var in variabs }

    for ientry, entry in enumerate(tree):
        # skip first event
        if tree.event == 1: continue

        # check chip
        if tree.chip != chip: continue

        # check sca is not in roll mode!
        if tree.roll[sca] == 1: continue

        #if ientry % 1000 == 0: print(ientry)
        for var in variabs:

            # TOT/TOA have no sca!
            if ("tot" in var) or ("toa" in var): isca = 0
            else: isca = sca

            val = getattr(tree,var)[isca*64 + chan]
            if val == 0: val = 4096
            elif val == 4: val = 0

            data[var].append(val)

    # Convert lists to numpy arrays
    for key,arr in data.items(): data[key] = np.array(data[key])

    return data


if __name__ == "__main__":

    fnames = glob.glob("sk2cms_tree.root")

    # read data
    #tfile = rt.TFile(fname)
    #tree = tfile.Get("sk2cms")
    tree = rt.TChain("sk2cms")
    for fname in fnames: tree.Add(fname)

    if not tree:
        print("No tree found!")
        exit(0)
    else:
        print("Found tree with %i events" %tree.GetEntries())

    #variabs = ["charge_lowGain","charge_hiGain"]
    variabs = ["lg","hg"]

    sca = 2
    chip = 1
    nchans = 64

    print("Starting event loop")
    # read in all channels' data
    all_chan_data = { chan:{var:[] for var in variabs} for chan in range(nchans)}
    for chan in range(nchans):
        print("Reading chan %i" %chan)
        chan_data = getChanData(tree,chip,chan,sca,variabs)

        for var,values in chan_data.items():
            chan_ped = values.mean()
            print chan, chan_ped

            # subtract pedestal from values
            all_chan_data[chan][var] = np.subtract(values,chan_ped)

    data = {}
    for var in variabs:
        data[var + "_IN"] = []
        data[var + "_CN"] = []
        data[var + "_DS"] = []
        data[var + "_AS"] = []

    for var in variabs:
        for event in range(len(all_chan_data[0][var])):

            sumAS = 0
            sumDS = 0

            for chan in range(nchans):

                val = all_chan_data[chan][var][event]
                # direct sum
                sumDS += val
                # alternate sum
                if chan%2 == 0: sumAS += val
                else: sumAS -= val

            # calc noise
            inc_noise = sumAS / math.sqrt(nchans)
            coh_noise = math.sqrt(abs(sumDS * sumDS - sumAS * sumAS)) / nchans

            data[var + "_AS" ].append(sumAS)
            data[var + "_DS" ].append(sumDS)
            data[var + "_IN" ].append(inc_noise)
            data[var + "_CN" ].append(coh_noise)

    print("Finished event loop")
    # Convert lists to numpy arrays
    for key,arr in data.items(): data[key] = np.array(data[key])

    #print(data)
    # make histograms
    hists = []
    #for key,values in data.items():
    for key in sorted(data):
        values = data[key]
        print key, values.mean(),values.std()

        nbins = len(values)/10
        xmin = values.min()
        xmax = values.max()

        hist = rt.TH1F("h_" + key, key , nbins, xmin, xmax)
        for val in values: hist.Fill(val)
        #hist.Draw()
        hists.append(hist)

    canv = rt.TCanvas("canv_noise","canv",1000,800)
    #canv.DivideSquare(len(hists),0.01,0.01)
    canv.Divide(4,len(hists)/4)
    for i, hist in enumerate(hists):
        canv.cd(i+1)
        hist.Draw()

    canv.Draw()

    q = raw_input("Continue?")

    #tfile.Close()

    '''
    histIN = rt.TH1F("h_IN_"+ var, "Incoherent noise of " + var, 100, -400,400)
    histCN = rt.TH1F("h_CN_"+ var, "Coherent noise of " + var, 100, -400,400)
    hists.append(histCN)
    hists.append(histIN)
    dhists["h_IN_"+ var] = histIN
    dhists["h_CN_"+ var] = histCN
    '''
