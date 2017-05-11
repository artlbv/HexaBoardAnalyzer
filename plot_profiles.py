#!/usr/bin/env python2
import os
import ROOT as rt
rt.gStyle.SetOptStat(0)

fname = "/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/RUN_0705_100517_0316.root"
tfile = rt.TFile(fname)

tree = tfile.Get("sk2cms")

chip = str(0)
chan = str(1)

variabs = ["lg["+chip+"][]["+chan+"]","hg["+chip+"][]["+chan+"]"]
var_suf = ":timesamp[Iteration$]"
var_name = ["lg","hg"]

cuts = ["","toa_rise["+chip+"]["+chan+"] > 100","tot_fast[1][24] > 100"]
cut_name = ["all","wTOA","wTOT"]

outdir = "plots/chip"+chip+"_chan"+chan+"/"
if not os.path.exists(outdir): os.makedirs(outdir)

for i,var in enumerate(variabs):
    for j,cut in enumerate(cuts):

        cname = var_name[i] + "_" + cut_name[j]
        print cname
        hname = "h" + cname

        canv = rt.TCanvas("canv","canv",800,600)
        canv.SetLogz()
        print var+var_suf+hname, cut
        tree.Draw(var+var_suf+">>"+hname,cut,"colz")
        hist = rt.gDirectory.Get(hname)
        hist.GetXaxis().SetTitle("Time Sample")
        hist.GetYaxis().SetTitle("ADC")
        hist.GetYaxis().SetTitleOffset(1.2)
        #hist.GetXaxis().SetRangeUser(0,10)

        canv.SaveAs(outdir + cname + "_scat.png")

        proj = hist.ProfileX()
        proj.SetMarkerStyle(20)
        proj.GetYaxis().SetTitle("ADC")
        proj.GetYaxis().SetTitleOffset(1.2)

        proj.GetYaxis().UnZoom()
        #proj.GetXaxis().SetRangeUser(0,10)

        canv2 = rt.TCanvas("canv2","canv2",800,600)

        proj.Draw("p")
        canv2.Update()

        canv2.SaveAs(outdir + cname + "_prof.png")

        print hist
        canv.Update()
        #q = raw_input()
