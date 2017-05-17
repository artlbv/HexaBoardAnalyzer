#!/usr/bin/env python2
import os
import ROOT# as rt
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

ofile = ROOT.TFile("hv_scan.root","recreate")
file_map = []
#file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0712_100517_1417.root","unplugged"))

file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0714_100517_1427.root","0V",25))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0715_100517_1432.root","5V",30))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0716_100517_1435.root","10V",32))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0717_100517_1440.root","20V",34))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0718_100517_1444.root","50V",38))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0719_100517_1448.root","100V",42))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0720_100517_1452.root","150V",45))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0721_100517_1456.root","200V",47))
file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0722_100517_1500.root","250V",50))
#file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0711_100517_1404.root","250V orig",2))
#file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0126_120517_1529.root","New",1))
#file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0127_120517_1544.root","New",1))
#file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0047_100517_2054.root","cover"))
#file_map.append(("/Users/artur/Work/LLR/HGCAL/Testbeam/data/may17/PED_RUN_0046_100517_2022.root","cover + GND"))

canv = ROOT.TCanvas("canv","canv",1000,600)
ROOT.SetOwnership(canv,0)

#sk2cms.Draw("hg[0][][10]","roll[Iteration$] == 0 && event < 900","colz"); c.Draw()
pOpt = "hist"

hists = []

chip = 3
chan = 9

for fname,label,col in file_map:
    hname = "h" + label

    tfile = ROOT.TFile(fname)
    tree = tfile.Get("sk2cms")
    if not tree: continue

    hist = ROOT.TH1F(hname,label,100,0,500)
    #tree.Draw("hg[ %i" + str(chip) + "][][ %i" + str(chan) + "] >>" + hname + "(100,0,1000)","roll[Iteration$] == 0",pOpt);

    tree.Draw("hg[ %i" %chip + "][][ %i"  %chan + "] >>" + hname,"roll[Iteration$] == 0",pOpt);
    #tree.Draw("hg[ %i" + %chip + "][][9] >>" + hname,"roll[Iteration$] == 0",pOpt);
    #tree.Draw("hg[ %i" + %chip + "][][ %i" %chan + "]" >>" + hname,"roll[Iteration$] == 0",pOpt);
    #tree.Draw("hg[2][][16] >>" + hname,"timesamp[Iteration$] < 8",pOpt);
    #tree.Draw("lg[ %i" + %chip + "][][9] >>" + hname,"roll[Iteration$] == 0",pOpt);
    #tree.Draw("hg[ %i" + %chip + "][][9] >>" + hname,"roll[Iteration$] == 0",pOpt);
    hist.SetDirectory(ofile)

    hist.SetLineColor(col)
    hist.SetLineWidth(3)
    hist.GetXaxis().SetTitle("ADC")

    '''
    hist = ROOT.gDirectory.Get(hname)#.Clone(hname)
    if not hist:
        print "fail", hname
        continue
    else:
        hist = hist.Clone(hname)
        #ROOT.SetOwnership(hist,0)
        hist.SetDirectory(ofile)
    '''
    print hist
    hists.append(hist)
    #print fname,label

    #break
    #if "same" not in pOpt:
    pOpt = pOpt + " same"

print hists
canv.Update()

leg_head = "Chip %i/%i" %(chip,chan)

leg = canv.BuildLegend()
leg.SetHeader(leg_head)
#canv.SetLogy()
canv.Draw()
canv.Update()
q = raw_input()

canv.SaveAs("hv_scan_hg_%i" %chip + "_%i"  %chan + ".pdf")
ofile.Close()
