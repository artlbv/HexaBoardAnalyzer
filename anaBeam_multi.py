#!/usr/bin/env python2

import glob, sys, os, array, math
import numpy as np
import ROOT as rt

#rt.TGaxis.SetMaxDigits(3)
brd_number = 0

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
def getChansData(tree, chip = 0, chans = [0], timesamp = 3, variabs = []):

    global brd_number
    chip_offset = brd_number*4

    #data = { chan: {var:[] for var in variabs }} for chan in chans}
    data = { chan: { var:[] for var in variabs } for chan in chans}

    for ientry, entry in enumerate(tree):
        # skip first event
        if tree.event < 1: continue

        #if tree.event > 10: break
        #if tree.event > 8000: break
        #if ientry > 1000: break

        #if tree.event % 100 == 0: print("Event: %i" % tree.event)
        if ientry % 100 == 0: print("Event: %i" % ientry)

        #if entry.sum_lg[0] > 400000: continue
        # check chip
        #if chip != "all":
        #    if tree.chip != chip: continue

        # determine SCA
        for sca in range(13):
            if tree.timesamp[4*brd_number*13 + sca] == timesamp: break

        #print "HEHEHE", tree.event

        #if ientry % 1000 == 0: print(ientry)
        for var in variabs:

            # TOT/TOA have no sca!
            if ("tot" in var) or ("toa" in var): isca = 0
            else: isca = sca

            if chip == "all":
                for chan in chans:#[:len(chans)/4]:#range(64):
                    chip_nb = chan/64 + chip_offset
                    if ("tot" in var) or ("toa" in var):
                        val = getattr(tree,var)[chip_nb*64 + (chan)%64 ]
                    else:
                        val = getattr(tree,var)[chip_nb*64*13 + isca*64 + (chan)%64 ]

                    #if val == 0: val = 4096
                    #elif val == 4: val = 0

                    #if val > 0:
                    data[chan][var].append(val)
            else:
                for chan in chans:
                    val = getattr(tree,var)[chip *64*13 + isca*64 + (chan) ]
                    #if val == 0: val = 4096
                    #elif val == 4: val = 0

                    data[chan][var].append(val)

    # Convert lists to numpy arrays
    #for key,arr in data.items(): data[key] = np.array(data[key])
    for chan in data:
        for var in variabs:
            data[chan][var] = np.array(data[chan][var])

    return data

def readTree(fname, chip = 0, timesamp = 3, nchans = 64, chan_select = "all"):
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
    variabs = ["lg","hg","toa_rise","tot_fast"]
    #variabs = ["lg"]

    if chip == "all": nchans *= 4
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
    chans_data = getChansData(tree,chip,chans,timesamp,variabs)
    print("...done")
    tfile.Close()

    return chans_data

def subtractPedestal(chans_data):

    chans = chans_data.keys()
    variabs = chans_data[chans[0]].keys()
    #print chans_data[0]
    #print chans_data[2]

    all_chan_data = { chan:{var:[] for var in variabs} for chan in chans}

    print("Subtracting pedestals...")

    #for chan in chans:
    #    chan_data = chans_data[chan]
        # Pedestal subtraction
        #for var,values in chan_data.items():

    # calc global pedestal
    for var in variabs:
        all_val = np.array([chans_data[chan][var] for chan in chans]).T

        # per event pedestals
        #glob_peds = [np.mean(event) for event in all_val]
        glob_peds = [np.median(event) for event in all_val]
        #print glob_peds

        for chan in chans:
            values = chans_data[chan][var]
            #chan_ped = values.mean()
            chan_ped = np.median(values)
            #chan_ped = np.mean(values)
            chan_ped_std = values.std()

            #if "hg" in var: print chan, chan_ped, chan_ped_std

            if chan_ped_std < -3.0:
                print(80*"!")
                print chan, chan_ped, chan_ped_std
                # put channel to zero
                all_chan_data[chan][var] = np.subtract(values,10000)
            else:
                # subtract pedestal from values
                #all_chan_data[chan][var] = np.subtract(values,glob_peds)
                #all_chan_data[chan][var] = np.subtract(values,chan_ped)
                #all_chan_data[chan][var] = np.subtract(values,200)
                all_chan_data[chan][var] = values
                #print values
                ##if chan < 2:
                #    print all_chan_data[chan][var]

    print("...done")

    return all_chan_data

def plot_rms(all_chan_data, outdir = "./", suffix = ""):#foutname = "rms_avg.txt"):
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
        #print(var)

        for chan in chans:

            chan_data = all_chan_data[chan][var]
            #print chan_data

            #chan_ped = chan_data.mean()
            #chan_ped = np.median(chan_data)
            #datas = [data for data in chan_data if data > 0]
            datas = chan_data
            if len(datas) > 0:
                chan_ped = np.mean(datas)
            else:
                chan_ped = 0#2222
                #chan_ped = np.mean([0]+[data for data in chan_data if data > 0])
            #chan_ped = sum(chan_data > np.mean(chan_data)+100)
            chan_rms = chan_data.std()
            #chan_rms = np.std(data)

            chip = chan/64
            real_chan = chan/4

            rms_data[chan] = (chan_ped,chan_rms)


        fout.write(var + "\n")
        for sens_chan in sens_map:
            (chip,chip_chan) = sens_map[sens_chan]

            glob_chan = chip * 64 + chip_chan
            fout.write("%.2f %.2f\n" %(rms_data[glob_chan][0], rms_data[glob_chan][1]))

        canv = rt.TCanvas("hexa_"+var,"hex",700,600)
        #canv = rt.TCanvas("hexa_"+var,"hex",1200,600)
        #canv.Divide(2,1)
        rt.gStyle.SetOptStat(0)

        # Plot values in Hexagon
        hHex_ped = rt.SingleLayerPlot()
        #hHex_ped.SetName("ped_"+var); hHex_ped.SetTitle("Mean (ADC) for " + var + suffix.replace('_',' '))
        hHex_ped.SetName("ped_"+var); hHex_ped.SetTitle("ADC " + var + suffix.replace('_',' '))
        hHex_rms = rt.SingleLayerPlot()
        hHex_rms.SetName("rms_"+var); hHex_rms.SetTitle("Ped RMS (ADC) for " + var + suffix.replace('_',' '))

        for hex_cell in range(133):
            sens_chan = hexmap[hex_cell]
            (chip,chip_chan) = sens_map[sens_chan]
            glob_chan = chip * 64 + chip_chan
            #print hex_cell, sens_chan, glob_chan
            hHex_ped.SetBinContent(hex_cell+1, int(rms_data[glob_chan][0]))
            hHex_rms.SetBinContent(hex_cell+1, round(rms_data[glob_chan][1],2))

        #canv.cd(1)
        hHex_ped.Draw("colz text")
        #canv.cd(2)
        #hHex_rms.Draw("colz text")
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
    run_dir = run_name + '_plots_brd%i/' %brd_number
    if not os.path.exists(run_dir): os.makedirs(run_dir)
    print("Output dir: " + run_dir)

    #chip = 0
    #sca = 6
    timesamp = 3
    nchans = 64
    #chan_select = "all"
    chan_select = "even"

    outfile = rt.TFile(run_dir + "plots.root","recreate")

    #chips = [0,1,2,3]#,"all"]
    chips = ["all"]
    #chips = [0,1,2,3,"all"]

    #for sca in range(1):
    for timesamp in range(0,8):
    #for timesamp in range(8):
        for chip in chips:
            print(80*"#")
            print("Analyzing: chip %s, TS %i" %(str(chip),timesamp))

            raw_all_data = readTree(fname, chip, timesamp, nchans, chan_select)
            all_data = subtractPedestal(raw_all_data)

            #print raw_all_data
            #print all_data
            #exit(0)

            #print all_data
            if chip == "all":
                #foutname = run_dir + "avg_rms_summary.txt"
                suffix = "_timesamp_%s" %timesamp
                #plot_rms(raw_all_data, run_dir, suffix)
                plot_rms(all_data, run_dir, suffix)

    outfile.Close()
