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
        #if tree.event < 50: continue
        #if tree.event > 100: continue
        if tree.event > 8000: break

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

########################
def getChansData(tree, chip = 0, chans = [0], sca = 0, variabs = []):

    #data = { chan: {var:[] for var in variabs }} for chan in chans}
    data = { chan: { var:[] for var in variabs } for chan in chans}

    for ientry, entry in enumerate(tree):
        # skip first event
        if tree.event == 0: continue
        #if tree.event < 50: continue
        #if tree.event > 100: continue
        if tree.event > 8000: break

        # check chip
        if tree.chip != chip: continue

        # check sca is not in roll mode!
        if tree.roll[sca] == 1: continue

        #if ientry % 1000 == 0: print(ientry)
        for var in variabs:

            # TOT/TOA have no sca!
            if ("tot" in var) or ("toa" in var): isca = 0
            else: isca = sca

            for chan in chans:
                val = getattr(tree,var)[isca*64 + chan]
                if val == 0: val = 4096
                elif val == 4: val = 0

                data[chan][var].append(val)

    # Convert lists to numpy arrays
    #for key,arr in data.items(): data[key] = np.array(data[key])
    for chan in data:
        for var in variabs:
            data[chan][var] = np.array(data[chan][var])

    return data

def readTree(fname, chip = 0, sca = 0, nchans = 64, chan_select = "all"):
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

    # create channel list
    if chan_select == "all":
        chans = range(nchans)
    elif chan_select == "even":
        chans = range(0,nchans,2)
    elif chan_select == "odd":
        chans = range(1,nchans,2)
    else:
        chans = range(nchans)
    print("Going to analyze these channels:")
    print(chans)

    print("Starting event loop")
    # read in all channels' data
    all_chan_data = { chan:{var:[] for var in variabs} for chan in chans}

    print("Reading chan data")
    chans_data = getChansData(tree,chip,chans,sca,variabs)

    #oexit(0)
    print("Analyzing chan data")
    for chan in chans:
        #print("Reading chan %i" %chan)
        #chan_data = getChanData(tree,chip,chan,sca,variabs)
        chan_data = chans_data[chan]

        # Pedestal subtraction
        for var,values in chan_data.items():
            chan_ped = values.mean()
            chan_ped_std = values.std()
            if chan_ped_std > 3.0:
                print(80*"!")
                print chan, chan_ped, chan_ped_std
                # put channel to zero
                all_chan_data[chan][var] = np.subtract(values,10000)
            else:
                # subtract pedestal from values
                all_chan_data[chan][var] = np.subtract(values,chan_ped)
                #if chan < 2:
                #    print all_chan_data[chan][var]

    print("Finished event loop")

    tfile.Close()

    return all_chan_data

def calcNoise(all_chan_data):

    noise_data = {}
    chans = all_chan_data.keys()
    variabs = all_chan_data[chans[0]].keys()

    for var in variabs:
        noise_data[var + "_IN"] = []
        noise_data[var + "_CN"] = []
        noise_data[var + "_DS"] = []
        noise_data[var + "_AS"] = []
        noise_data[var + "_large_sumDS"] = []

    for var in variabs:
        # Loop over events (based on 0 channel)
        for event in range(len(all_chan_data[chans[0]][var])):

            sumAS = 0
            sumDS = 0
            n_valid_chans = 0

            for i,chan in enumerate(chans):

                val = all_chan_data[chan][var][event]

                if val > -999: n_valid_chans += 1
                else: continue

                # direct sum
                sumDS += val
                # alternate sum
                if i % 2 == 0: sumAS += val
                else: sumAS -= val

            # calc noise
            #if n_valid_chans < 63: print(n_valid_chans)
            inc_noise = sumAS / math.sqrt(n_valid_chans)
            coh_noise = math.sqrt(abs(sumDS * sumDS - sumAS * sumAS)) / n_valid_chans

            if abs(sumAS) > 500:
                print("Suspiciously large AS: %i in event %i" %(sumAS,event))
                continue
            if abs(sumDS) > 500:
                print("Suspiciously large DS: %i in event %i" %(sumDS,event))
                continue

            if sumDS > 150:
                #print("SumDS: %f, event %i" % (sumDS, event))
                noise_data[var + "_large_sumDS"].append(event)

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

    #h_order = ["_DS","_AS"]#,"_IN","_CN"]#,"_CNF"]
    h_order = ["_DS","_AS"]#,"_large_sumDS"]
    variabs = ["lg","hg"]

    #for key in sorted(data):
    #for key in sorted(noise_data):
    for var in variabs:
        for htype in h_order:
            key = var + htype

            values = noise_data[key]
            if len(values) == 0: values = np.array([0])
            print key, values.mean(),values.std()

            xmin = math.floor(values.min())-0.5
            xmax = math.ceil(values.max())+0.5
            nbins = int((xmax-xmin))/2
            #nbins = min(100,len(values)/50)

            hist = rt.TH1F("h_" + key, key , nbins, xmin, xmax)
            for val in values: hist.Fill(val)
            #hist.Draw()
            hists.append(hist)

    canv = rt.TCanvas("canv_noise","canv",1000,800)
    #canv.Divide(4,len(hists)/4,0.01,0.01)
    canv.Divide(len(h_order),len(hists)/len(h_order),0.01,0.01)
    for i, hist in enumerate(hists):
        canv.cd(i+1)
        hist.Draw()

    #canv.Draw()
    canv.Update()

    #q = raw_input("Continue?")
    canv.SaveAs(cname+".pdf")

def calcCorr(all_chan_data, cname = "corr_plot.pdf"):
    rt.gStyle.SetOptStat(0)
    rt.gStyle.SetPadRightMargin(0.15)

    chans = all_chan_data.keys()#[:3]
    variabs = all_chan_data[chans[0]].keys()

    hists = {}
    for var in variabs:
        hist = rt.TH2F("h_corr_"+var,"correlation for "+var,64,0,64,64,0,64)
        hists["h_corr_"+var] = hist

    for chan1 in chans:
        for chan2 in chans:

            for var in variabs:
                if chan1 == chan2:
                    corr = 0
                else:
                    corr_matr = np.corrcoef(all_chan_data[chan1][var],all_chan_data[chan2][var])
                    corr = abs(corr_matr[0][1])
                    #print corr[0][1]
                hists["h_corr_"+var].SetBinContent(chan1+1,chan2+1,corr)

    canv = rt.TCanvas("canv_noise","canv",1000,500)
    canv.Divide(len(hists),1,0.01,0.01)

    for i,hname in enumerate(hists):
        hist = hists[hname]
        canv.cd(i+1)
        hist.Draw("colz")

    canv.Update()
    canv.Draw()
    rt.gStyle.SetOptStat(1)

    #q = raw_input("continue?")

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
    sca = 4
    nchans = 64
    chan_select = "all"

    for chip in range(4):
        print(80*"#")
        print("Analyzing: chip %i, sca %i" %(chip,sca))

        all_data = readTree(fname, chip, sca, nchans, chan_select)

        cname = run_dir + "corr_chip_%i_sca_%i_chans_%s" %(chip,sca,chan_select)
        calcCorr(all_data, cname)

        cname = run_dir + "noise_chip_%i_sca_%i_chans_%s" %(chip,sca,chan_select)
        noise_data = calcNoise(all_data)
        plotNoise(noise_data, cname)

