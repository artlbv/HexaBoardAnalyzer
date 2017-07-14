#!/usr/bin/env python2

import glob, sys, os, array, math
import numpy as np
import ROOT as rt

#rt.TGaxis.SetMaxDigits(3)
n_hexa = 1

def getSensorMap():

    sens_map = {}
    fmap = open("//Users/artur/Dropbox/Work/LLR/HGCAL/SK2cms/hexaboard/fromDocDB/Skiroc2CMS_sensor_map_simplified.csv","r")

    for line in fmap.readlines():
        #print len(line.split(','))
        if 'Chan' in line: continue
        if len(line.split(',')) != 3: continue

        (sens_chan,chip,chip_chan) = line.split(',')

        #sens_map[(int(chip),int(chip_chan))] = int(sens_chan)
        sens_map[int(sens_chan)] = (int(chip),int(chip_chan))

    return sens_map

def getHexMap():
    return [104,104,81,92,103,113,121,
            58,69,80,91,102,112,120,126,
            25,46,57,68,79,90,101,111,119,125,127,
            25,35,45,56,67,78,89,100,110,118,124,127,
            24,34,44,55,66,77,88,99,109,117,123,
            14,23,33,43,54,65,76,87,98,108,116,122,13,22,32,
            42,53,64,75,86,97,107,115,6,12,21,31,41,52,63,74,
            85,96,106,114,5,11,20,30,40,51,62,73,84,95,105,1,
            4,10,19,29,39,50,61,72,83,94,93,1,3,9,18,28,38,49,
            60,71,82,93,2,8,17,27,37,48,59,70,7,16,26,36,47,15,15]

########################
def getChansData(tree, chip = 0, chans = [0], sca = 0, variabs = []):

    #data = { chan: {var:[] for var in variabs }} for chan in chans}
    #data = { brd: {chan: { var:[] for var in variabs } for chan in chans} for brd in range(5)}
    #data = np.zeros((5,4,13,64))
    data = { var:[] for var in variabs}

    ev_cnts = 0
    dat = []#np.zeros(256)

    for ientry, entry in enumerate(tree):
        # skip first event
        if tree.event < 1: continue
        #if tree.event > 1: continue
        #if ev_cnts > 100: break

        #if tree.event % 1000 == 0 and tree.chip == 0: print("Event: %i" % tree.event)
        #if tree.event % 100 == 0: print("Event: %i" % tree.event)
        if ientry % 100 == 0: print("Event: %i" % ientry)

        # check sca is not in roll mode!
        #if tree.roll[sca] == 1: continue
        #if tree.timesamp[sca] > 9: continue
        #if tree.timesamp[sca] > 8: continue
        if tree.timesamp[sca] > 8: continue
        #if tree.timesamp[sca] < 8: continue
        #if tree.timesamp[sca] > 10: continue

        ## filter TOA mishits
        #n_toa = sum([1 for toa in tree.toa_rise if toa > 0])
        #if n_toa > 10: continue

        #if ientry % 1000 == 0: print(ientry)
        for var in variabs[1:]:

            # TOT/TOA have no sca!
            if ("tot" in var) or ("toa" in var): isca = 0
            else: isca = sca

            values_arr = getattr(tree,var)
            #values_matr = np.array(values_arr).reshape(5,4,13,64)
            values_matr = np.array(values_arr).reshape(4*n_hexa,13,64)
            # all data in HEXBRD / CHIP / SCA / CHAN format

            #data[chan][var].append(val)
            #t =  values_matr[:,:,sca,:]
            t = values_matr[:,sca,:]
            t = t.flatten()

            if len(dat) == 0:
                dat = t
            else:
                #print t.shape
                #t = np.append(t,t,axis=0)
                dat = np.vstack((dat,t))
                #dat = np.append(dat,t)
            #print len(dat), dat.shape

            #print t.shape
            #a = np.concatenate(t,t)
            #print a

            #data[brd][chip][chan].append()
            #data[var]

            #exit(0)
        ev_cnts += 1

    #print dat
    #print dat.T

    dat = dat.T.reshape(4*n_hexa,64,len(dat))
    print dat.shape

    for chip in range(4*n_hexa):
        print 80*"#"
        for chan in range(64):
            print "%0.2f" %np.std(dat[chip][chan]),
        print
    exit(0)

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

    if chip == "all": nchans *= 4# * 5
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

    # read in all channels' data
    print("Reading chan data")
    chans_data = getChansData(tree,chip,chans,sca,variabs)
    print("...done")
    tfile.Close()

    return chans_data

def subtractPedestal(chans_data):

    chans = chans_data.keys()
    variabs = chans_data[chans[0]].keys()

    all_chan_data = { chan:{var:[] for var in variabs} for chan in chans}

    print("Subtracting pedestals...")
    for chan in chans:
        chan_data = chans_data[chan]

        # Pedestal subtraction
        for var,values in chan_data.items():
            #chan_ped = values.mean()
            chan_ped = np.median(values)
            chan_ped_std = values.std()

            #if "hg" in var: print chan, chan_ped, chan_ped_std

            if chan_ped_std < -3.0:
                print(80*"!")
                print chan, chan_ped, chan_ped_std
                # put channel to zero
                all_chan_data[chan][var] = np.subtract(values,10000)
            else:
                # subtract pedestal from values
                all_chan_data[chan][var] = np.subtract(values,chan_ped)
                #all_chan_data[chan][var] = np.subtract(values,200)
                #all_chan_data[chan][var] = values
                #if chan < 2:
                #    print all_chan_data[chan][var]

    print("...done")

    return all_chan_data

def makePedPlot(all_chan_data, cname = "ped_plot.pdf"):
    rt.gStyle.SetOptStat(0)

    chans = all_chan_data.keys()
    variabs = all_chan_data[chans[0]].keys()
    nchans = chans[-1]

    hists = []

    if "ped" in cname: name = "pedestal"
    elif "rms" in cname: name = "rms"
    else: name = ""

    for var in variabs:
        hist = rt.TH1F("h_ped_"+var,name +" for "+var,nchans,0,nchans)

        for chan in chans:

            chan_data = all_chan_data[chan][var]

            #chan_ped = chan_data.mean()
            chan_ped = np.median(chan_data)
            chan_rms = chan_data.std()

            #print var,chan,chan_ped,chan_rms
            if chan_ped < 10: # means we are analyzing ped subtracted data
                hist.SetBinContent(chan+1,min(5,chan_rms))
            else:
                hist.SetBinContent(chan+1,chan_ped)
                hist.SetBinError(chan+1,chan_rms)

            #if chan_ped < 1 and chan_rms > 3:
            #    print "## High RMS", var,chan,chan_rms

        hists.append(hist)

    canv = rt.TCanvas("canv_ped","canv",1000,500)
    canv.Divide(len(hists),1,0.01,0.01)

    for i,hist in enumerate(hists):
        canv.cd(i+1)
        hist.Draw("colz")

    canv.Update()
    canv.Draw()
    rt.gStyle.SetOptStat(1)

    #q = raw_input("continue?")

    canv.SaveAs(cname+".pdf")
    return canv

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

            '''
            if abs(sumAS) > 1500:
                print("Suspiciously large AS: %i in event %i" %(sumAS,event))
                continue
            if abs(sumDS) > 1500:
                print("Suspiciously large DS: %i in event %i" %(sumDS,event))
                continue
            '''
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
        hist.Draw("")

    #canv.Draw()
    canv.Update()

    #q = raw_input("Continue?")
    canv.SaveAs(cname+".pdf")

    return canv

def calcCorr(all_chan_data, cname = "corr_plot.pdf"):
    rt.gStyle.SetOptStat(0)
    rt.gStyle.SetPadRightMargin(0.15)

    chans = all_chan_data.keys()#[:3]
    variabs = all_chan_data[chans[0]].keys()
    nchans = chans[-1]

    hists = {}
    for var in variabs:
        #hist = rt.TH2F("h_corr_"+var,"correlation for "+var,64,0,64,64,0,64)
        hist = rt.TH2F("h_corr_"+var,"correlation for "+var,nchans,0,nchans,nchans,0,nchans)
        rt.SetOwnership(hist,0)
        hists["h_corr_"+var] = hist

    # compute correlations and fill histos
    for var in variabs:
        data_matrix = np.array([all_chan_data[chan][var] for chan in chans])
        corr_matr = np.corrcoef(data_matrix)

        for i1,chan1 in enumerate(chans):
            for i2,chan2 in enumerate(chans):
                corr = abs(corr_matr[i1][i2])
                if chan1 != chan2:
                    hists["h_corr_"+var].SetBinContent(chan1+1,chan2+1,corr)

                    #if corr > 3*corr_matr.mean() : print chan1, chan2, corr
                    #if corr > corr_matr.mean() + 3*corr_matr.std(): print "## Corr", var, chan1, chan2, corr
                    if chan1 < 256 and chan2 > 256:
                        if corr > 0.9: print "## Corr", var, chan1, chan2, corr

    canv = rt.TCanvas("canv_noise","canv",1000,500)
    canv.Divide(len(hists),1,0.01,0.01)

    for i,hname in enumerate(hists):
        hist = hists[hname]
        canv.cd(i+1)
        hist.Draw("colz")

    canv.Update()
    #canv.Draw()
    rt.gStyle.SetOptStat(1)

    #q = raw_input("continue?")

    canv.SaveAs(cname+".pdf")
    return canv

def print_rms(all_chan_data, outdir = "./", suffix = ""):#foutname = "rms_avg.txt"):
    chans = all_chan_data.keys()#[:3]
    variabs = all_chan_data[chans[0]].keys()
    nchans = chans[-1]

    #rms_data = { chip:{chan:() for chan in chans} for chip in range(4)}
    #rms_data = { chip:{} for chip in range(4)}
    rms_data = {}

    #print chans
    foutname = outdir + "avg_rms_summary" + suffix + ".txt"
    fout = open(foutname,"w")

    #for var in ['hg']:#variabs:
    sens_map = getSensorMap()
    hexmap = getHexMap()
    rt.gROOT.LoadMacro("SingleLayer.C")

    for var in variabs:
        print(var)

        for chan in chans:

            chan_data = all_chan_data[chan][var]

            chan_ped = chan_data.mean()
            chan_rms = chan_data.std()
            #print chan_data

            chip = chan/64
            real_chan = chan/4

            #print chan, chip, real_chan

            '''
            if (chip,real_chan) in rms_data:
                print "already in", chip, real_chan
            else:
                rms_data[(chip,real_chan)] = (chan_ped,chan_rms)
            '''
            rms_data[chan] = (chan_ped,chan_rms)

        #print rms_data
        #print len(chans), len(rms_data)

        fout.write(var + "\n")
        for sens_chan in sens_map:
            (chip,chip_chan) = sens_map[sens_chan]

            #print chip, chan
            #print sens_chan, rms_data[chip][chan]
            #if chip in rms_data:
            #    if chan in rms_data:
            #        print sens_chan, chip, chan
            #if (chip,chip_chan) in rms_data:
            #    print chip, chip_chan, rms_data[(chip,chip_chan)]
            glob_chan = chip * 64 + chip_chan
            #print chip, chip_chan, rms_data[glob_chan]
            #print("%.2f %.2f" %(rms_data[glob_chan][0], rms_data[glob_chan][1]))
            fout.write("%.2f %.2f\n" %(rms_data[glob_chan][0], rms_data[glob_chan][1]))

        canv = rt.TCanvas("hexa_"+var,"hex",1300,600)
        canv.Divide(2,1)
        rt.gStyle.SetOptStat(0)

        # Plot values in Hexagon
        hHex_ped = rt.SingleLayerPlot()
        hHex_ped.SetName("ped_"+var); hHex_ped.SetTitle("Mean (ADC) for " + var + suffix.replace('_',' '))
        hHex_rms = rt.SingleLayerPlot()
        hHex_rms.SetName("rms_"+var); hHex_rms.SetTitle("Ped RMS (ADC) for " + var + suffix.replace('_',' '))

        for hex_cell in range(133):
            sens_chan = hexmap[hex_cell]
            (chip,chip_chan) = sens_map[sens_chan]
            glob_chan = chip * 64 + chip_chan
            #print hex_cell, sens_chan, glob_chan
            hHex_ped.SetBinContent(hex_cell+1, int(rms_data[glob_chan][0]))
            hHex_rms.SetBinContent(hex_cell+1, round(rms_data[glob_chan][1],2))

        if 'hg' in var:
            for chan in sorted(rms_data.keys(), key = lambda x:rms_data[x][1], reverse=True):
                #print chan,
                print("%i %i\t%0.2f" %(chan/64,chan%64,rms_data[chan][1]))

        canv.cd(1)
        hHex_ped.Draw("colz text")
        canv.cd(2)
        hHex_rms.Draw("colz text")
        #rt.gPad.SetLogz()
        canv.Update()

        canv.SaveAs(outdir+ canv.GetName()+suffix+".pdf")
        #q = raw_input("wait")

    fout.close()

    rt.gStyle.SetOptStat(0)

    return 1

if __name__ == "__main__":


    '''
    if '-b' in sys.argv:
        sys.argv.remove('-b')
        _batchMode = True
    '''

    if len(sys.argv) > 1:
        fname = sys.argv[1]
        print '# Input files are', fname
    else:
        print "No input files given!"
        #exit(0)

        fname = "sk2cms_tree.root"

        print("Using " + fname)


    fname = fname.replace(".txt",".root")
    #fnames = glob.glob(fname)
    run_name = fname.replace('.root','')
    #run_dir = run_name + '_plots_nopedsub/'
    run_dir = run_name + '_plots_Multi/'
    if not os.path.exists(run_dir): os.makedirs(run_dir)
    print("Output dir: " + run_dir)

    #chip = 0
    sca = 6
    nchans = 64
    chan_select = "all"

    outfile = rt.TFile(run_dir + "plots.root","recreate")

    #chips = [0,1,2,3]#,"all"]
    chips = ["all"]
    #chips = [0,1,2,3,"all"]

    #for sca in [0]:#range(13):
    #for sca in range(13):
    scas = range(13)#[0]
    scas = [0]
    chip = chips[0]

    for sca in scas:
        print(80*"#")

        raw_all_data = readTree(fname, chip, sca, nchans, chan_select)
        all_data = subtractPedestal(raw_all_data)

        cname = run_dir + "ped_chip_%s_sca_%i_chans_%s" %(str(chip),sca,chan_select)
        makePedPlot(raw_all_data,cname)
        cname = run_dir + "rms_zoom_chip_%s_sca_%i_chans_%s" %(str(chip),sca,chan_select)
        makePedPlot(all_data,cname)

        #continue

        cname = run_dir + "corr_chip_%s_sca_%i_chans_%s" %(str(chip),sca,chan_select)
        canv = calcCorr(raw_all_data, cname)
        outfile.cd()
        canv.Write()

        cname = run_dir + "noise_chip_%s_sca_%i_chans_%s" %(str(chip),sca,chan_select)
        noise_data = calcNoise(all_data)
        canv = plotNoise(noise_data, cname)
        outfile.cd()
        canv.Write()

        if chip == "all":
            #foutname = run_dir + "avg_rms_summary.txt"
            suffix = "_sca_%s" %sca
            #print_rms(raw_all_data, run_dir, suffix)
            print_rms(raw_all_data, run_dir, suffix)

    outfile.Close()
