import os
from concurrent.futures import  ProcessPoolExecutor
import json

from pm4py.objects.log import obj as log_instance
from pm4py.objects.petri_net import semantics
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.util import xes_constants
import datetime
from copy import copy
from pm4py.objects.log.obj import EventLog, Trace, Event
import os
from pathlib import Path
import random
from pm4py.objects.petri_net.importer import importer as pnml_importer
import pm4py
from gen_Loan_Log.utils import gen_sudden,gen_recurring_sudden,gen_recurring_gradual

processPool = ProcessPoolExecutor(20)


if __name__ == '__main__':
    recurring_sudden_sumseg=10     #recurring的数量
    recurring_gradual_sumseg = 10
    gradualdriftsize=500
    ROOT_DIR = Path(__file__).parent.parent

    basenetPath = os.path.join(ROOT_DIR, 'data', 'Loanlogs', 'Loan_baseline_petriNet.pnml')
    baseNet, baseim, basefm = pnml_importer.apply(basenetPath)
    with open(os.path.join(ROOT_DIR, 'data', 'Loanlogs', 'frequent_info.json'), 'r', encoding='utf8') as fp:
        basefrInof = json.load(fp)

    logsrootpath = os.path.join(ROOT_DIR, 'data','Loanlogs')
    logsdir = os.listdir(logsrootpath)
    for dir in logsdir:
        dirpath = os.path.join(logsrootpath, dir)
        if os.path.isdir(dirpath):
            driftnetPath = os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir, 'Loan_' + dir + '_petriNet.pnml')
            driftNet, driftim, driftfm = pnml_importer.apply(driftnetPath)
            with open(os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir, 'frequent_info.json'), 'r',
                      encoding='utf8') as fp:
                driftfrInof = json.load(fp)
            for segmentSize in range(250,1001,250):  #生成recurring_sudden
                for tempnoisepercent in range(0,101,15):
                    noisepercent=tempnoisepercent/1000
                    savepath=os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir,'recurring_sudden_noise'+str(noisepercent)+'_'+str(segmentSize)+'-'+str(recurring_sudden_sumseg)+'_'+dir+'.xes')
                    # print(savepath)
                    processPool.submit(gen_recurring_sudden,baseNet, baseim, basefm, basefrInof, driftNet, driftim, driftfm, driftfrInof, segmentSize, noisepercent, recurring_sudden_sumseg,savepath)
            segmentSize=1000
            for tempnoisepercent in range(0,101,15):#生成sudden
                noisepercent = tempnoisepercent / 1000

                savepath = os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir,
                                        'sudden_noise' + str(noisepercent) + '_' + str(
                                            segmentSize)+'-2' + '_' + dir + '.xes')
                # print(savepath)
                processPool.submit(gen_sudden, baseNet, baseim, basefm, basefrInof, driftNet, driftim, driftfm,
                                   driftfrInof, segmentSize, noisepercent, savepath)

                 # 生成recurring_gradual
            for tempnoisepercent in range(0,101,15):
                noisepercent = tempnoisepercent / 1000
                savepath =os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir,'recurring_gradual_noise'+str(noisepercent)+'_'+str(segmentSize)+'-'+str(recurring_gradual_sumseg)+'_'+str(gradualdriftsize)+'_'+dir+'.xes')
                # print(savepath)
                processPool.submit( gen_recurring_gradual,baseNet, baseim, basefm, basefrInof,driftNet, driftim, driftfm, driftfrInof, segmentSize,gradualdriftsize ,noisepercent,recurring_gradual_sumseg, savepath)