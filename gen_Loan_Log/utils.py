import json
import traceback

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
from pm4py.algo.simulation.playout.petri_net import algorithm as simulator

def random_pick(some_list, probabilities):
    '''
    probabilities之和小于1或者大于1时，最后一个 probability 失效 ，即最后一个 probability 为 1 - other ,其中other之和必须小于1
    :param some_list:
    :param probabilities:
    :return:
    '''
    x = random.uniform(0,1)
    cumulative_probability = 0.0
    for item, item_probability in zip(some_list, probabilities):
         cumulative_probability += item_probability
         if x < cumulative_probability:
               break
    return item



def playout(net, initial_marking, final_marking, num_traces=1000, max_trace_length=50, case_id_key=xes_constants.DEFAULT_TRACEID_KEY, activity_key=xes_constants.DEFAULT_NAME_KEY, timestamp_key=xes_constants.DEFAULT_TIMESTAMP_KEY, fr_info=None):
    '''

    :param net:
    :param initial_marking:
    :param final_marking:
    :param num_traces:
    :param max_trace_length:
    :param case_id_key:
    :param activity_key:
    :param timestamp_key:
    :param fr_info: {'p_12':{'name_9':0.1,'name_19':0.9}}
    :return:
    '''
    if fr_info is not None and len(fr_info)!=0:
        if len(fr_info)==0:
            fr_info=None

    tempfr_info = {}

    if fr_info is not None:
        places=net.places
        for k ,v in fr_info.items():
            for p in places:
                if p.name==k:
                    tempfr_info[p]={}
                    for oa in p.out_arcs:
                        if oa.target.name in v.keys():
                            tempfr_info[p][oa.target]=v[oa.target.name]

    curr_timestamp = 10000000
    all_visited_elements = []


    for i in range(num_traces):
        visited_elements = []
        visible_transitions_visited = []

        marking = copy(initial_marking)
        while len(visible_transitions_visited) < max_trace_length:
            visited_elements.append(marking)

            if not semantics.enabled_transitions(net, marking):  # supports nets with possible deadlocks
                break
            all_enabled_trans = semantics.enabled_transitions(net, marking)

            places = set(marking.keys())

            if final_marking is not None and marking == final_marking:
                transList = list(all_enabled_trans).append(None)
            else:
                transList = list(all_enabled_trans)
            meanprob = 1 / len(transList)
            probabilities = [meanprob for i in range(len(transList))]
            if len(places.intersection(set(tempfr_info.keys()))) > 0:#需要再分配
                for place in places:
                    if place in tempfr_info.keys():
                        if place == list(final_marking.keys())[0]:  #是finalmarking
                            thissumprob = (len(tempfr_info[place]) + 1) * meanprob
                        else:
                            thissumprob = (len(tempfr_info[place]) ) * meanprob
                        for t, prob in tempfr_info[place].items():
                            probabilities[transList.index(t)] = thissumprob * prob

            tran = random_pick(transList, probabilities)
            if tran is None:
                break

            visited_elements.append(tran)
            if tran.label is not None:
                visible_transitions_visited.append(tran)

            marking = semantics.execute(tran, net, marking)

        all_visited_elements.append(tuple(visited_elements))


    log = log_instance.EventLog()

    for index, visited_elements in enumerate(all_visited_elements):
        trace = log_instance.Trace()
        trace.attributes[case_id_key] = str(index)
        for element in visited_elements:
            if type(element) is PetriNet.Transition and element.label is not None:
                event = log_instance.Event()
                event[activity_key] = element.label
                event[timestamp_key] = datetime.datetime.fromtimestamp(curr_timestamp)
                trace.append(event)
                # increases by 1 second
                curr_timestamp += 1
        log.append(trace)

    return log


def insert_noise(log,noisepercent):
    errortrace=set()
    sumtrace=len(log)
    # activity = ["Loan__application_received", "Check__application__form_completeness", "Appraise_property",
    #             "Check_credit_history", "Assess_loan_risk",
    #             "Assess_eligibility", "Prepare_acceptance_pack", "Check_if_home_insurance_quote_is_requested",
    #             "Send_home_insurance_quote",
    #             "Verify_repayment_agreement", "Approve_application", "Loan__application_approved",
    #             "Return_application_back_to_applicant", "Receive_updated_application",
    #             "Reject_application", "Loan_application_rejected", 'Cancel_application', 'Loan__application_canceled',
    #             'Send_acceptance_pack']
    activity=set()  #所有出现的活动名称
    for i in range(len(log)):
        for j in range(len(log[i])):
            event_name = log[i][j][xes_constants.DEFAULT_NAME_KEY]
            activity.add(event_name)
    activity=list(activity)
    while len(errortrace) < sumtrace*noisepercent:
        changetracepos=random.randint(0,sumtrace-1)
        if changetracepos not in errortrace:
            errortrace.add(changetracepos)
            trace=log[changetracepos]
            changeeventNum=random.randint(1,min(len(trace)-1,5))
            for i in range(changeeventNum):
                type=random.choice([1,2])
                changeeventpos = random.randint(0, len(trace) - 1)
                if type==1:  #修改event的活动名称
                    trace[changeeventpos][xes_constants.DEFAULT_NAME_KEY] =random.choice(activity)
                else:   #随机增加event
                    event = Event()
                    event[xes_constants.DEFAULT_NAME_KEY] = random.choice(activity)
                    event[xes_constants.DEFAULT_TIMESTAMP_KEY] = datetime.datetime.fromtimestamp(100000000)
                    trace.insert(changeeventpos, event)


def gradual_function(x,number):
    return (number-x)/number



def gen_sudden(baseNet,baseim,basefm,basefr_info,driftNet,driftim,driftfm,driftfr_info,segmentSize,noisepercent=0,save_path=None):
    '''
    首先出现的为baseNet生成的log 然后driftNet生成的log  ,其实是recurring的特例
    size = segmentSize*sumseg
    :param baseNet:
    :param baseim:
    :param basefm:
    :param driftNet:
    :param driftim:
    :param driftfm:
    :param segmentSize:
    :param sumseg: 发生drift次数为sumseg-1 ，
    :param noisepercent: 异常trace所占百分比   ，  randomly insert、change events in the traces
    :return:
    '''
    return gen_recurring_sudden(baseNet, baseim, basefm, basefr_info, driftNet, driftim, driftfm, driftfr_info, segmentSize, noisepercent, 2,save_path)



def gen_recurring_sudden(baseNet, baseim, basefm, basefr_info, driftNet, driftim, driftfm, driftfr_info, segmentSize, noisepercent=0, sumseg=10,save_path=None):
    '''
    首先出现的为baseNet生成的log 然后driftNet生成的log 然后baseNet生成的log ...   如此循环sumseg次
    size = segmentSize*sumseg
    :param baseNet:
    :param baseim:
    :param basefm:
    :param driftNet:
    :param driftim:
    :param driftfm:
    :param segmentSize:
    :param sumseg: 发生drift次数为sumseg-1 ，
    :param noisepercent: 异常trace所占百分比   ， inserting random events into the traces
    :return:
    '''
    log = EventLog()
    index = 0
    for i in range(sumseg):
        if i%2==0:
            simulated_log = playout(baseNet, baseim, basefm, num_traces=segmentSize, fr_info=basefr_info)
        else:
            simulated_log = playout(driftNet, driftim, driftfm, num_traces=segmentSize, fr_info=driftfr_info)
        for trace in simulated_log:
            trace.attributes[xes_constants.DEFAULT_TRACEID_KEY] = str(index)
            log.append(trace)
            index += 1
    insert_noise(log, noisepercent)
    if save_path is None:
        return log
    else:
        print("save to path :" +  save_path )
        pm4py.write_xes(log, save_path)

def gen_recurring_gradual(baseNet, baseim, basefm, basefr_info, driftNet, driftim, driftfm, driftfr_info, segmentSize , gradualdriftsize , noisepercent=0, sumseg=10,save_path=None):
    '''

    |          segmentSize        |          segmentSize         |          segmentSize        |          segmentSize         |
                                  |center                                                     |center
    --------------------------------------------------------------------------------------------------------------------------
                        ^                   ^                                       ^                   ^
                gradualdriftBegin       gradualdriftEND                     gradualdriftBegin       gradualdriftEND
                        | gradualdriftsize |                                        | gradualdriftsize |
    :param baseNet:
    :param baseim:
    :param basefm:
    :param basefr_info:
    :param driftNet:
    :param driftim:
    :param driftfm:
    :param driftfr_info:
    :param segmentSize:
    :param gradualdriftsize:
    :param noisepercent:
    :param sumseg:
    :return:
    '''
    log = EventLog()
    index = 0
    flag=False
    for i in range(sumseg):
        if not flag:#第一个
            simulated_log = playout(baseNet, baseim, basefm, num_traces=int(segmentSize-gradualdriftsize/2), fr_info=basefr_info)
            for trace in simulated_log:
                trace.attributes[xes_constants.DEFAULT_TRACEID_KEY] = str(index)
                log.append(trace)
                index += 1
            flag=True
        else:
            if i%2==0:
                simulated_log1 = playout(driftNet, driftim, driftfm, num_traces=gradualdriftsize, fr_info=driftfr_info)
                simulated_log2 = playout(baseNet, baseim, basefm, num_traces=gradualdriftsize, fr_info=basefr_info)
            else:
                simulated_log1 = playout(baseNet, baseim, basefm, num_traces=gradualdriftsize, fr_info=basefr_info)
                simulated_log2 = playout(driftNet, driftim, driftfm, num_traces=gradualdriftsize, fr_info=driftfr_info)

            for k in range(gradualdriftsize):
                if gradual_function(k, gradualdriftsize) > random.random():
                    simulated_log1[k].attributes[xes_constants.DEFAULT_TRACEID_KEY] = str(index)
                    log.append(simulated_log1[k])
                    index += 1
                else:
                    simulated_log2[k].attributes[xes_constants.DEFAULT_TRACEID_KEY] = str(index)
                    log.append(simulated_log2[k])
                    index += 1

            if i % 2 == 0:
                simulated_log = playout(baseNet, baseim, basefm, num_traces=int(segmentSize-gradualdriftsize), fr_info=basefr_info)
            else:
                simulated_log = playout(driftNet, driftim, driftfm, num_traces=int(segmentSize-gradualdriftsize), fr_info=driftfr_info)

            for trace in simulated_log:
                trace.attributes[xes_constants.DEFAULT_TRACEID_KEY] = str(index)
                log.append(trace)
                index += 1
    if i % 2 == 0:
        simulated_log = playout(baseNet, baseim, basefm, num_traces= int(gradualdriftsize/2), fr_info=basefr_info)
    else:
        simulated_log = playout(driftNet, driftim, driftfm, num_traces=int(gradualdriftsize/2),
                                fr_info=driftfr_info)
    for trace in simulated_log:
        trace.attributes[xes_constants.DEFAULT_TRACEID_KEY] = str(index)
        log.append(trace)
        index += 1

    insert_noise(log, noisepercent)
    if save_path is None:
        return log
    else:
        print("save to path :" + save_path)

        pm4py.write_xes(log, save_path)



if __name__ == '__main__':
    ROOT_DIR = Path(__file__).parent.parent
    segmentSize=1000
    noisepercent=0.09
    gradualdriftsize=500
    basenetPath = os.path.join(ROOT_DIR,'data', 'Loanlogs', 'Loan_baseline_petriNet.pnml')
    baseNet, baseim, basefm= pnml_importer.apply(basenetPath)
    with open(os.path.join(ROOT_DIR,'data', 'Loanlogs', 'frequent_info.json'), 'r', encoding='utf8') as fp:
        basefrInof = json.load(fp)
    dir ='pm'
    driftnetPath = os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir,'Loan_'+dir+'_petriNet.pnml')
    driftNet, driftim, driftfm= pnml_importer.apply(driftnetPath)
    with open(os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir,'frequent_info.json'), 'r', encoding='utf8') as fp:
        driftfrInof = json.load(fp)


    # log =  gen_recurring_sudden(baseNet, baseim, basefm, basefrInof, driftNet, driftim, driftfm, driftfrInof, segmentSize, noisepercent, 2)
    # pm4py.write_xes(log, os.path.join(ROOT_DIR, 'data', 'Loanlogs', 'cb','sudden_noise'+str(noisepercent)+'_'+str(segmentSize*2)+'_'+'cb'+'.xes'))
    # log =  gen_recurring_gradual(baseNet, baseim, basefm, basefrInof,driftNet, driftim, driftfm, driftfrInof, segmentSize,gradualdriftsize ,noisepercent=noisepercent,sumseg=4)
    # pm4py.write_xes(log, os.path.join(ROOT_DIR, 'data', 'Loanlogs', 'cb','recurring_gradual_noise'+str(noisepercent)+'_'+str(segmentSize*4)+'_'+str(gradualdriftsize)+'cb'+'.xes'))
    logPath = os.path.join(ROOT_DIR, 'data', 'Loanlogs', dir, 'sudden_noise'+str(noisepercent)+'_1000-2_'+dir+'.xes')
    gen_sudden( baseNet, baseim, basefm, basefrInof, driftNet, driftim, driftfm,driftfrInof, segmentSize, noisepercent, logPath)
