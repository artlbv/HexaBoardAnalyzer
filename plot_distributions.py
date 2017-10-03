#!/usr/bin/env python2
import os
import ROOT as rt
rt.gStyle.SetOptStat(0)
rt.gStyle.SetOptTitle(0)

'''
fnames = {}
fnames["wed"] = "/Users/artur/Dropbox/Hebaboard/Acquisitions_2017_09_27/Module_53.root"
fnames["fri1"] = "/Users/artur/Downloads/Acquisitions_2017_09_29/RUN_290917_1601.root"
fnames["fri2"] = "/Users/artur/Downloads/Acquisitions_2017_09_29/RUN_290917_1638.root"

labels = {}
labels["wed"] = "Wednesday (Table)"
labels["fri1"] = "Friday 16:01 (EE stack)"
labels["fri2"] = "Friday 16:38 (EE stack)"
'''
fnames = ["/Users/artur/Dropbox/Hebaboard/Acquisitions_2017_09_27/Module_53.root",
          "/Users/artur/Downloads/Acquisitions_2017_09_29/RUN_290917_1601.root",
          "/Users/artur/Downloads/Acquisitions_2017_09_29/RUN_290917_1638.root"
          ]

keys = ["wed","fri1","fri2"]

'''
labels = ["Wednesday (Table)",
          "Friday 16:01 (EE stack)",
          "Friday 16:38 (EE stack)"
          ]
'''
labels = ["Before mounting, Keithley (Wed.)",
          "EE stack, CAEN (Fri.)",
          "EE stack, Keithley (Fri.)",
          ]

colors = [rt.kBlack,rt.kRed,rt.kBlue]

var_names = ["hg","lg"]
#var_names = ["hg"]

chip = 0
chan = 22

chans = [(0,12),(1,12),(2,12),(3,12),(0,22),(0,28),(2,4)]
chans += [(0,11),(1,11),(2,11),(3,11)]

for chip,chan in chans:

    outdir = "plots/chip%i_chan%i/" %(chip,chan)
    if not os.path.exists(outdir): os.makedirs(outdir)

    for var in var_names:

        histos = []

        for i,fname in enumerate(fnames):

            tfile = rt.TFile(fname)
            tree = tfile.Get("sk2cms")

            #var_name = var + "["+chip+"][]["+chan+"]"
            var_name = var + "[ %i ][][ %i ]" %(chip, chan)

            cut = "timesamp[] < 9 && event > 0"
            hname = "h_" + var + "_" + keys[i]

            if "hg" in var and chan%2 == 0: xmax = 2500
            else: xmax = 500

            hist = rt.TH1F(hname,labels[i],250,0,xmax)

            tree.Draw(var_name+">>"+hname,cut,"")

            hist.SetDirectory(0)

            hist.SetName(labels[i])
            hist.SetLineColor(colors[i])

            hist.GetXaxis().SetTitle(var.upper() + " [ADC]")

            histos.append(hist)

            tfile.Close()

        cname = var +"_chip%i_chan%i" %(chip,chan)
        canv = rt.TCanvas(cname,cname,800,600)
        #if "hg" in var: canv.SetLogy()
        canv.SetLogy()

        for i,hist in enumerate(histos):
            if i == 0:
                hist.Draw()
            else:
                hist.Draw("same")

        title = "Module 53: chip %i chan %i" %(chip,chan)
        leg = canv.BuildLegend()
        leg.SetHeader(title)

        #histos[0].SetTitle(title)
        canv.Draw()
        canv.Update()
        canv.SaveAs(outdir + cname + ".png")
        canv.SaveAs(outdir + cname + ".pdf")
        #q = raw_input("quit")
