from pm4py.objects.petri_net import semantics

visited=set()

def replayHelper2(net, trace2transition, temp_trace2transitionList):
    '''
     以trace2transition中的marking，通过None的transition能够生成的所有路径加入到temp_trace2transitionList中
    :param net:
    :param trace2transition:
    :param temp_trace2transitionList:
    :return:
    '''
    global visited
    marking=trace2transition[-1]
    for transition in semantics.enabled_transitions(net, marking):
        if transition.label is None :
        # if transition.label is None:
            newmarking = semantics.execute(transition, net, marking)
            if newmarking not in visited:
                visited.add(newmarking)
                temp = trace2transition.copy()
                temp[-1] = transition
                temp.append(newmarking)
                temp_trace2transitionList.append(temp)
                replayHelper2(net, temp, temp_trace2transitionList)


def replayHelper(net, trace2transitionList):#trace2transitionList就是一个list里有个item为transition的listz
    '''
    基于token的replay，对trace2transitionList进行扩展，生成通过None节点能到达的所有新状态
    :param net:
    :param trace2transitionList:
    :return:
    '''
    global  visited
    visited=set()
    temp_trace2transitionList=[]
    for trace2transition in trace2transitionList:
        visited.add(trace2transition[-1])
        temp_trace2transitionList.append(trace2transition.copy())
        replayHelper2(net, trace2transition, temp_trace2transitionList)
    return temp_trace2transitionList



def checkConformance(trace,net, initial_marking, final_marking,rvnet2netRelation=None,reversed_net=None,reversed_net_initial_marking=None):
    '''
    rvnet2netRelation=None,reversed_net=None,reversed_net_initial_marking=None时，获取trace是否fit net 。如果fit返回(True, besttrace2transition,None,None)否则(False, None, None,None)
    rvnet2netRelation,reversed_net,reversed_net_initial_marking 不为None时，目的是获取unfit时激活的pair对
    :param trace:
    :param net:
    :param initial_marking:
    :param final_marking:
    :param rvnet2netRelation:
    :param reversed_net:
    :param reversed_net_initial_marking:
    :return:
    '''

    trace2transitionList = []  # fit时候保存trace对应的transition

    markings = [initial_marking]  # 允许同时有多个可能的marking   即petrinet中存在相同label名字的transition时会出现这种情况
    forwardenabled_transitions = set()
    backwardenabled_transitions = set()


    trace2transitionList.append(markings)  # 利用marking做跳板
    trace2transitionList = replayHelper(net, trace2transitionList)
    flag=True
    for j in range(len(trace)):
        flag = False
        event_name = trace[j]['concept:name']
        temptrace2transitionList = []
        for trace2transition in trace2transitionList:
            marking = trace2transition[-1]
            for transition in semantics.enabled_transitions(net, marking):
                if transition.label is not None:
                    if transition.label == event_name:
                        flag = True
                        newmarking = semantics.execute(transition, net, marking)
                        temp = trace2transition.copy()
                        temp[-1] = transition
                        temp.append(newmarking)
                        temptrace2transitionList.append(temp)
        if not flag:  # 出错了，没有任何一个激活的transition的label和trace中的活动相同
            for trace2transition in trace2transitionList:
                marking = trace2transition[-1]
                for transition in semantics.enabled_transitions(net, marking):
                    if transition.label is not None:
                        forwardenabled_transitions.add(transition)
            break
        else:
            trace2transitionList = temptrace2transitionList
            trace2transitionList = replayHelper(net, trace2transitionList)
            # print(trace2transitionList)
        # print(trace2transitionList)

    if flag :  # 走到了trace最后   ,trace  fit net .  如果有多条路径满足结果，那么取最短路径。
        besttrace2transition=None
        for trace2transition in trace2transitionList:
            if trace2transition[-1] == final_marking:
                if besttrace2transition is None:
                    besttrace2transition=trace2transition[:-1]
                elif len(trace2transition[:-1])<len(besttrace2transition):
                    besttrace2transition = trace2transition[:-1]
        if besttrace2transition is not None: #  trace 走没了，并且到sink节点
            return (True, besttrace2transition,None,None)
        else:  #  trace 走没了，没到sink节点
            for trace2transition in trace2transitionList:
                marking = trace2transition[-1]
                for transition in semantics.enabled_transitions(net, marking):
                    if transition.label is not None:
                        forwardenabled_transitions.add(transition)
    if rvnet2netRelation is None and reversed_net is None and reversed_net_initial_marking is None:  #不需要获取激活pair对，也就不需要反向跑
        return (False, None, None,None)
    #############################没返回，说明trace not fit petrinet
    ######################################unfit 时 反向跑一遍获取激活的transition##################
    markings = [reversed_net_initial_marking]

    trace2transitionList = []  # fit时候保存trace对应的transition
    trace2transitionList.append(markings)  # 利用marking做跳板
    trace2transitionList = replayHelper(reversed_net, trace2transitionList)
    flag = True
    for j in range(len(trace) - 1, -1, -1):
        flag = False
        event_name = trace[j]['concept:name']
        # temptrace2transition = []
        # print(markings)
        temptrace2transitionList = []
        for trace2transition in trace2transitionList:
            marking = trace2transition[-1]
            for transition in semantics.enabled_transitions(reversed_net, marking):
                if transition.label is not None:
                    if transition.label == event_name:
                        flag = True
                        newmarking = semantics.execute(transition, reversed_net, marking)
                        temp = trace2transition.copy()
                        temp[-1] = transition
                        temp.append(newmarking)
                        temptrace2transitionList.append(temp)
        if not flag:  # 出错了，没有任何一个激活的transition的label和trace中的活动相同
            for trace2transition in trace2transitionList:
                marking = trace2transition[-1]
                for transition in semantics.enabled_transitions(reversed_net, marking):
                    if transition.label is not None:
                        backwardenabled_transitions.add(rvnet2netRelation[transition])
            break
        else:
            trace2transitionList = temptrace2transitionList
            trace2transitionList = replayHelper(reversed_net, trace2transitionList)

    if flag:  # 走到了trace最后 ， 因为unfit 所以一定没到sink节点
        for trace2transition in trace2transitionList:
            marking = trace2transition[-1]
            for transition in semantics.enabled_transitions(net, marking):
                if transition.label is not None:
                    backwardenabled_transitions.add(transition)
    return (False, None,forwardenabled_transitions,backwardenabled_transitions)