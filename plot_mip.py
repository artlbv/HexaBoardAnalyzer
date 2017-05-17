#!/usr/bin/env python2
import ROOT
import numpy as np

def getHist(tree,maxTS):

    hname = "hMaxTS"+str(maxTS)
    hist = ROOT.TH1F(hname,hname,250,-100,150)
    #hist = ROOT.TH1F(hname,hname,3000,0,3000)

    chan_i = 34
    chip_i = 0

    for entry in tree:

    #if tree.event > 10: break

        did_toa_fire = False
        for chip in [chip_i]:#range(4):
            for chan in range(0,64,2):
                if tree.toa_rise[chip * 64 + chan] > 0 or tree.tot_fast[chip * 64 + chan] > 0:
                    did_toa_fire = True;
                    break
            if did_toa_fire: break
        if did_toa_fire: continue

        maxSCA = -1
        #roll = tree.roll
        for ts in range(13):
            if tree.timesamp[ts] == maxTS:
                maxSCA = ts
                break

        if maxSCA == -1:
            print "ha"
            exit()
        #elif maxSCA != 0: continue

        charges = []
        for chip in [chip_i]:#range(4):
            for chan in range(0,64,2):
                if abs(chan - chan_i) < 4 and chip == chip_i: continue
                charge = tree.hg[chip * 13 * 64 + maxSCA * 64 + chan]
                #if charge < 2000 and charge > 0:
                charges.append(charge)

        #if len(charges) < 32: continue
        mean = int(np.median(charges))
        #mean = np.mean(charges)
        if mean < 4: continue
        signal = tree.hg[chip_i * 13 * 64 + maxSCA * 64 + chan_i]
        if signal < 4: continue
        #if signal == mean : continue

        #if abs(signal-mean) < 4: print signal, mean
        #if abs(signal-mean) < 2: continue
        shift = 10
        hist.Fill(int(signal - mean - shift))
        '''
        if maxTS == 0:
            hist.Fill(np.median(charges))
        elif maxTS == 3:
            hist.Fill(np.mean(charges))
        #print mean
        '''

    print hist
    return hist

if __name__ == "__main__":

    #fname = "/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/ele200/merge.root"
    #fname = "/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/all_data/disk2_2TB/data/PED_RUN_0042_100517_1954.rootall.root"
    #fname = "/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/all_data/disk2_2TB/data/merge_ele200plus.root"
    #fname = "/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/all_data/disk2_2TB/data/merge_ele250.root"

    tfile = ROOT.TFile(fname)

    tree = tfile.Get("sk2cms")

    #hist = ROOT.TH1F("hist","hist",200,-50,150)
    #hist = ROOT.TH1F("hist","hist",3000,-250.5,2500.5)


    hist_ts3 = getHist(tree,3);
    hist_ts0 = getHist(tree,0)

    h_diff = hist_ts3.Clone("diff")

    hist_ts3.SetLineColor(ROOT.kRed)
    h_diff.SetLineColor(ROOT.kBlack)

    ts0_max = hist_ts0.GetMaximum()
    ts3_max = hist_ts3.GetMaximum()

    hist_ts0.Scale(ts3_max/ts0_max)
    #hist_ts3.Add(hist_ts0,-ts3_max/ts0_max)
    h_diff.Add(hist_ts0,-1)#-ts3_max/ts0_max)

    h_diff.Fit("landau","R","",20,120)

    hist_ts0.Draw("hist")
    hist_ts3.Draw("hist same")
    h_diff.Draw("hist same")
    q = raw_input("")
