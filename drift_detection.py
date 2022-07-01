import os.path
from collections import deque

from pypinyin import lazy_pinyin
from werkzeug.utils import secure_filename

from check_conformance import checkConformance
from gen_new_net import gen_new_net
from utils import *


count=0


def initbasegraph(graphs, nowedges, appearSP):
    global count
    flag=True
    for i in range(len(graphs)):
        if not nowedges[i] <= graphs[i]:
            flag=False
            graphs[i]=graphs[i].union(nowedges[i])
    if flag:
        count+=1
    else:
        count=0
    if count>=appearSP:
        return True
    else:
        return False


def mydeepcopy(dict):
    if len(dict)==0:
        return {}
    copyres={}
    for p in dict.keys():
        dict2=dict[p]
        copyres[p] = {}
        if len(dict2) == 0:
            continue
        else:
            for t in dict2.keys():
                copyres[p][t]=dict2[t]
    return copyres


def drift_detection_helper(net, initial_marking, final_marking, log, startpos, windowSize, appearSP, disappearSP, alpha, beta, gamma, filterrate):

    global count
    count = 0
    tree, transitions2leaf, leaf2transitions = getTreeAndcorrespondingLeaves(net, initial_marking, final_marking)

    rvnet2netRelation, reversed_net, reversed_net_initial_marking, reversed_net_final_marking = reverse_net(net,
                                                                                                            initial_marking,
                                                                                                            final_marking)
    rootNodes, checkgraphNodeSetList = initcheckgraphNodeSetList(tree, leaf2transitions)  #And-structure ;loop-structure
    stablegraphs = []
    queuegraphs = []
    pair2FreqDict = {}
    transition2FreqDict = {}
    unfitnumber = 0
    queue = deque()
    candidateCP=None
    stable = False
    for transition in net.transitions:
        transition2FreqDict[transition] = 0

    DD=[]
    for i in range(len(checkgraphNodeSetList)):
        stablegraphs.append(set())
        queuegraphs.append({})
        DD.append(0)


    for k in range(startpos,len(log)):  # 第K个trace
        flag = -1  # flag为1表示transition2FreqDict中有一个变为0了，也就是说有transition在窗口内从来没被访问，flag为2表示direct follow 中有一条边被删除了，
        trace = log[k]
        fitness, enabled_transitionstrace, forwardenabled_transitions, backwardenabled_transitions = checkConformance(
            trace, net, initial_marking, final_marking, rvnet2netRelation, reversed_net, reversed_net_initial_marking)
        # end=time.time()
        # print(end-begin)
        #########################################################增量维护queue
        if fitness:
            for transition in enabled_transitionstrace:  # 维护transitonfrequency
                transition2FreqDict[transition] += 1
            nowedgesList = []
            for i in range(len(checkgraphNodeSetList)):
                edges = genedges(checkgraphNodeSetList[i], enabled_transitionstrace)
                nowedgesList.append(edges)
            if not stable:
                stable = initbasegraph(stablegraphs, nowedgesList, appearSP)
                queue.append((trace, None, enabled_transitionstrace, None))
            else:
                for i in range(len(checkgraphNodeSetList)):
                    for edge in nowedgesList[i]:
                        if edge in queuegraphs[i].keys():
                            queuegraphs[i][edge] += 1
                        else:
                            queuegraphs[i][edge] = 1
                queue.append((trace, nowedgesList, enabled_transitionstrace, None))
        else:
            pair = (tuple(forwardenabled_transitions), tuple(backwardenabled_transitions))
            # print(str(k) + " :  " + str(pair))
            if pair in pair2FreqDict.keys():
                pair2FreqDict[pair] += 1
            else:
                pair2FreqDict[pair] = 1
            unfitnumber += 1
            queue.append((trace, None, None, pair))

        if not len(queue) <= windowSize:  # queue满了
            abandoned_trace, abandoned_edgesList, abandoned_enabled_transitionstrace, abandoned_pair = queue.popleft()
            if abandoned_edgesList is not None:
                for i in range(len(checkgraphNodeSetList)):
                    for edge in abandoned_edgesList[i]:
                        queuegraphs[i][edge] -= 1
                        if queuegraphs[i][edge] == 0:
                            flag = 2
                            del queuegraphs[i][edge]
            if abandoned_enabled_transitionstrace is not None:
                for transition in abandoned_enabled_transitionstrace:
                    transition2FreqDict[transition] -= 1
                    if transition2FreqDict[transition] == 0:
                        flag = 1
            if abandoned_pair is not None:
                if abandoned_pair in pair2FreqDict.keys():
                    pair2FreqDict[abandoned_pair] -= 1
                    if pair2FreqDict[abandoned_pair] == 0:
                        del pair2FreqDict[abandoned_pair]
                unfitnumber -= 1
        # print(transition2FreqDict)
        ##############################################################
        if len(queue) == windowSize:
            if unfitnumber > windowSize * alpha:
                explanation='a decrease in fitness'
                meaningfulpairList = []
                for pair, times in pair2FreqDict.items():
                    if times > gamma:
                        meaningfulpairList.append(pair)
                if len(meaningfulpairList)==0:
                    mostfreqency=-1
                    for pair, times in pair2FreqDict.items():
                        if times>mostfreqency:
                            meaningfulpairList=[pair]
                            mostfreqency=times
                        elif times==mostfreqency:
                            meaningfulpairList.append(pair)



                logInqueue = EventLog()
                startTime = None
                for i in range(len(queue)):
                    queueTrace = queue[i][0]
                    queuepair = queue[i][3]
                    if startTime is None:
                        if queuepair is not None:
                            if queuepair in meaningfulpairList:
                                startTime = k - windowSize + 1 + i
                                logInqueue.append(queueTrace)
                    else:
                        if queuepair is None or queuepair in meaningfulpairList:
                            logInqueue.append(queueTrace)
                while len(logInqueue) < windowSize and k < len(log):

                    fitness, enabled_transitionstrace, forwardenabled_transitions, backwardenabled_transitions = checkConformance(
                        log[k], net, initial_marking, final_marking, rvnet2netRelation, reversed_net,
                        reversed_net_initial_marking)


                    if fitness:
                        logInqueue.append(log[k])
                    else:
                        pair = (tuple(forwardenabled_transitions), tuple(backwardenabled_transitions))
                        if pair in meaningfulpairList:
                            logInqueue.append(log[k])
                    k += 1
                # print(meaningfulpairList)
                # print(k)
                # print("drift time : " + str(startTime))
                # print(len(logInqueue))
                tempmeaningfulpairList=list(meaningfulpairList)
                meaningfulpairList=[]
                for pair in tempmeaningfulpairList:#list pair convert to set pair
                    forwardtransitionsSet = set(pair[0])
                    backwardtransitionsSet = set(pair[1])
                    pair = (forwardtransitionsSet, backwardtransitionsSet)
                    meaningfulpairList.append(pair)

                for meaningfulpair in list(meaningfulpairList):
                    # print(meaningfulpair)
                    # print(type(meaningfulpair))
                    refinePair(meaningfulpair, transitions2leaf)
                    # if len(meaningfulpair[0]) == 0 and len(meaningfulpair[1]) == 0:
                    #     meaningfulpairList.remove(meaningfulpair)



                enabled_transitions = set()
                for meaningfulpairs in meaningfulpairList:
                    enabled_transitions = enabled_transitions.union(meaningfulpairs[0])
                    enabled_transitions = enabled_transitions.union(meaningfulpairs[1])



                leaves = set()
                for t in enabled_transitions:
                    if t in transitions2leaf:
                        leaves.add(transitions2leaf[t])


                net, initial_marking, final_marking, localfilename= gen_new_net(net, initial_marking, final_marking, tree, logInqueue,
                                                                  leaves, leaf2transitions,filterrate,startTime)

                gviz = visualize.apply(net, initial_marking, final_marking, parameters={"format": "svg"})
                actualfilename = 'WN_{}.svg'.format(str(startTime))
                pn_visualizer.save(gviz, os.path.join('result',actualfilename))

                return ( net, initial_marking, final_marking ,k,startTime,actualfilename,localfilename,explanation)
            elif flag == 1 :
                explanation='a decrease in precision of choice structure'

                startTime= k - windowSize + 1


                redundantTransitions = []
                for transition, times in transition2FreqDict.items():
                    if times == 0:
                        redundantTransitions.append(transition)
                decorations = {}
                color = '#FF0000'
                for transition in redundantTransitions:
                    if transition.label is not None:
                        decorations[transition] = {"label": transition.label, "color": color}
                    else:
                        decorations[transition] = {"label": 'hidden', "color": color}
                gviz = visualize.apply(net, initial_marking, final_marking, parameters={"format": "svg"},
                                       decorations=decorations)
                localfilename = 'Localization_{}.svg'.format(str(startTime))
                pn_visualizer.save(gviz, os.path.join('result',localfilename))

                removeRedundantTransitions(net, initial_marking, final_marking, transition2FreqDict)

                gviz = visualize.apply(net, initial_marking, final_marking, parameters={"format": "svg"})
                actualfilename = 'WN_{}.svg'.format(str(startTime))
                pn_visualizer.save(gviz, os.path.join('result',actualfilename))

                return ( net, initial_marking, final_marking ,k+1,startTime,actualfilename,localfilename,explanation)
            elif flag == 2:
                for i in range(len(stablegraphs)):
                    stablegraphEdgeSet = stablegraphs[i]
                    if len(stablegraphEdgeSet)!=0:
                        queuegraphEdgeSet = set(queuegraphs[i].keys())
                        # print(len(stablegraphEdgeSet))
                        # print(len(queuegraphEdgeSet))
                        # print(stablegraphEdgeSet)
                        # print(queuegraphEdgeSet)
                        lossedge = stablegraphEdgeSet - queuegraphEdgeSet
                        # print(lossedge)
                        lossPercent = len(lossedge) / len(stablegraphEdgeSet)
                        DD[i] = lossPercent
                candidateCP = k
            if candidateCP is not None:
                disappearCount=k-candidateCP
                # print(disappearCount)
                if disappearCount>disappearSP :
                    if max(DD)>=beta: # 说明发生了 drift。
                        startTime= candidateCP - windowSize + 1
                        # print("drift time : " + str(startTime))
                        # print("start ："+str(k-queuesize+1),"end ："+str(k) ) #全闭区间
                        # print(rootNodes[driftstructurepos])
                        logInqueue = EventLog()
                        for i in range(len(queue)):
                            queueTrace = queue[i][0]
                            queuepair = queue[i][3]
                            if queuepair is None:
                                logInqueue.append(queueTrace)
                        if rootNodes[DD.index(max(DD))].operator=='+':
                            explanation = 'a decrease in precision of concurrency structure'
                        else:
                            explanation = 'a decrease in precision of loop structure'
                        net, initial_marking, final_marking,localfilename = gen_new_net(net, initial_marking, final_marking, tree, logInqueue, [rootNodes[DD.index(max(DD))]],
                                leaf2transitions,filterrate,startTime)
                        gviz = visualize.apply(net, initial_marking, final_marking, parameters={"format": "svg"})
                        actualfilename = 'WN_{}.svg'.format(str(startTime))
                        pn_visualizer.save(gviz, os.path.join('result',actualfilename))
                        return ( net, initial_marking, final_marking ,k+1,startTime,actualfilename,localfilename,explanation)
                    else:
                        candidateCP=None

    return ( net, initial_marking, final_marking , None , None ,None,None,None)


def drift_detectionHelper2(net, initial_marking, final_marking, log, windowSize =200,appearSP=40,disappearSP=10,alpha =0.2, beta =0.2, abnormalpairthreshold = 5, filterrate=0.05):
    drift_timeLIST=[]
    explanationList=[]
    localfilenameList=[]
    actualfilenameList=[]

    startpos=0
    while startpos is not None:
        # gviz = pn_visualizer.apply(net, initial_marking, final_marking)
        # pn_visualizer.view(gviz)

        net, initial_marking, final_marking , startpos ,driftTime,actualfilename,localfilename,explanation= drift_detection_helper(net, initial_marking, final_marking, log, startpos, windowSize, appearSP, disappearSP, alpha, beta, abnormalpairthreshold, filterrate)


        if driftTime is not None:
            drift_timeLIST.append(driftTime)
            explanationList.append(explanation)
            localfilenameList.append(localfilename)
            actualfilenameList.append(actualfilename)

    return (drift_timeLIST,localfilenameList,actualfilenameList,explanationList)
