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
        if tree.event == 0: continue

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

def readTree(fname, chip = 0, sca = 0, nchans = 64, skip_chan = 0):
    # read data
    tfile = rt.TFile(fname)
    tree = tfile.Get("sk2cms")
    #tree = rt.TChain("sk2cms")
    #for fname in fnames: tree.Add(fname)

    if not tree:
        print("No tree found!")
        exit(0)
    else:
        print("Found tree with %i events" %tree.GetEntries())

    #variabs = ["charge_lowGain","charge_hiGain"]
    variabs = ["lg","hg"]

    print("Starting event loop")
    # read in all channels' data
    all_chan_data = { chan:{var:[] for var in variabs} for chan in range(nchans)}
    for chan in range(nchans):
        print("Reading chan %i" %chan)
        chan_data = getChanData(tree,chip,chan,sca,variabs)

        # Pedestal subtraction
        for var,values in chan_data.items():
            chan_ped = values.mean()
            #print chan, chan_ped

            # subtract pedestal from values
            all_chan_data[chan][var] = np.subtract(values,chan_ped)

    print("Finished event loop")
    tfile.Close()

    return all_chan_data

def calcNoise(all_chan_data):

    noise_data = {}
    variabs = all_chan_data[0].keys()

    for var in variabs:
        noise_data[var + "_IN"] = []
        noise_data[var + "_CN"] = []
        noise_data[var + "_DS"] = []
        noise_data[var + "_AS"] = []

    for var in variabs:
        # Loop over events (based on 0 channel)
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

            if abs(sumAS) > 500:
                print("Suspiciously large AS: %i in event %i" %(sumAS,event))
                continue
            if abs(sumDS) > 500:
                print("Suspiciously large DS: %i in event %i" %(sumDS,event))
                continue

            noise_data[var + "_AS" ].append(sumAS)
            noise_data[var + "_DS" ].append(sumDS)
            noise_data[var + "_IN" ].append(inc_noise)
            noise_data[var + "_CN" ].append(coh_noise)

    # Convert lists to numpy arrays
    for key,arr in noise_data.items(): noise_data[key] = np.array(noise_data[key])

    return noise_data

def plotNoise(noise_data, cname):

    # make histograms
    hists = []
    #for key,values in noise_data.items():
    for key in sorted(noise_data):
        values = noise_data[key]
        print key, values.mean(),values.std()

        xmin = math.floor(values.min())-0.5
        xmax = math.ceil(values.max())+0.5
        nbins = int((xmax-xmin))

        hist = rt.TH1F("h_" + key, key , nbins, xmin, xmax)
        for val in values: hist.Fill(val)
        #hist.Draw()
        hists.append(hist)

    canv = rt.TCanvas("canv_noise","canv",1400,800)
    #canv.DivideSquare(len(hists),0.01,0.01)
    canv.Divide(4,len(hists)/4,0.01,0.01)
    for i, hist in enumerate(hists):
        canv.cd(i+1)
        hist.Draw()

    canv.Draw()
    canv.Update()

    #q = raw_input("Continue?")
    canv.SaveAs(cname+".pdf")

if __name__ == "__main__":

    if len(sys.argv) > 1:
        fname = sys.argv[1]
        print '# Input files are', fname
    else:
        print "No input files given!"
        #exit(0)

        fname = "sk2cms_tree.root"

        print("Using " + fname)

    #fnames = glob.glob(fname)
    run_name = fname.replace('.root','')
    run_dir = run_name + '_plots/'
    if not os.path.exists(run_dir): os.makedirs(run_dir)
    print("Output dir: " + run_dir)

    #chip = 0
    sca = 0
    nchans = 64

    for chip in range(4):
        print(80*"#")
        print("Analyzing: chip %i, sca %i" %(chip,sca))

        all_data = readTree(fname, chip, sca, nchans)
        cname = run_dir + "noise_chip_%i_sca_%i" %(chip,sca)
        noise_data = calcNoise(all_data)
        plotNoise(noise_data, cname)
