import os
import uuid
from math import inf
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.objects.petri_net.obj import PetriNet, Marking
from Objects.conversion.wf_net import converter as wf_net_converter
from Objects.process_tree.obj import Operator
from stack import Stack
from pm4py.util import xes_constants

def log2X(log):
    sumlen = 0
    activityset = set()  # 所有出现的活动名称
    for i in range(len(log)):
        sumlen += len(log[i])
        for j in range(len(log[i])):
            event_name = log[i][j][xes_constants.DEFAULT_NAME_KEY]
            activityset.add(event_name)
    activity2num = {}
    num = 1
    for activity in activityset:
        activity2num[activity] = num
        num += 1
    # X = [[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[1,0] ]
    xlen=int(sumlen/len(log))+1
    X = []
    for i in range(len(log)):
        temp = []
        for j in range(min(len(log[i]),xlen)):
            event_name = log[i][j][xes_constants.DEFAULT_NAME_KEY]
            temp.append(activity2num[event_name])
        for k in range(xlen - len(log[i])):
            temp.append(0)
        X.append(temp)
    return X

    # sumlen = 0
    # activitydict ={}  # 所有出现的活动名称
    # for i in range(len(log)):
    #     sumlen += len(log[i])
    #     for j in range(len(log[i])):
    #         event_name = log[i][j][xes_constants.DEFAULT_NAME_KEY]
    #         if event_name not in activitydict:
    #             activitydict[event_name]=1
    #         else:
    #             activitydict[event_name] +=1
    # # X = [[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[1,0] ]
    # xlen = int(sumlen / len(log)) + 1
    # X = []
    # for i in range(len(log)):
    #     temp = []
    #     for j in range(min(len(log[i]), xlen)):
    #         event_name = log[i][j][xes_constants.DEFAULT_NAME_KEY]
    #         temp.append(activitydict[event_name])
    #     for k in range(xlen - len(log[i])):
    #         temp.append(0)
    #     X.append(temp)
    # return X

def reverse_net(net,initial_marking, final_marking):
    '''
    反转net结构
    :param net:
    :param initial_marking:
    :param final_marking:
    :return: rvnet2netRelation：反转后的petri net 中的transition 作为key  ；value为 key 对应的 原来petri net 中的transition
    '''
    rvnet2netRelation={}
    net2rvnetRelation = {}
    reversed_net = PetriNet("reversed_petri_net")
    for place in net.places:
        p = PetriNet.Place(place.name)
        reversed_net.places.add(p)
        rvnet2netRelation[p]=place
        net2rvnetRelation[place]=p
    for transition in net.transitions:
        t = PetriNet.Transition("rv_"+transition.name, transition.label)
        reversed_net.transitions.add(t)
        rvnet2netRelation[t]=transition
        net2rvnetRelation[transition]=t
    for arc in net.arcs:
        petri_utils.add_arc_from_to(net2rvnetRelation[arc.target], net2rvnetRelation[arc.source], reversed_net)
        # petri_utils.remove_arc(net, arc)
    reversed_net_initial_marking = Marking()
    sourcePlace = list(final_marking.keys())[0]
    reversed_net_initial_marking[net2rvnetRelation[sourcePlace]] = 1
    reversed_net_final_marking= Marking()
    sinkPlace = list(initial_marking.keys())[0]
    reversed_net_final_marking[net2rvnetRelation[sinkPlace]] = 1
    return (rvnet2netRelation,reversed_net,reversed_net_initial_marking,reversed_net_final_marking)




def get_path_to_leaf(leaf):
    '''
    获得process tree中 叶子节点到根节点的路径
    :param leaf:
    :return:
    '''
    stack=Stack()
    node=leaf
    path=[]
    while node is not None:
        stack.push(node)
        node=node.parent
    while not stack.isEmpty():
        path.append(stack.pop())
    return path




def getcommon_ancestor(nodes):
    if len(nodes)==1:
        return list(nodes)[0]
    paths = []
    common_ancestor = None
    for leaf in nodes:
        paths.append(get_path_to_leaf(leaf))

    minlen = inf
    for path in paths:
        minlen = min(minlen, len(path))

    for i in range(minlen - 1):  ##寻找公共祖先 ，看前缀最多到哪，那就是公共祖先
        temp = paths[0][i]
        flag = True
        for path in paths:
            if temp != path[i]:
                flag = False
        if flag:
            common_ancestor = temp
    return  common_ancestor

def refinePair(pair,transitions2leaf):
    '''
    删除 forwardtransitionsSet和backwardtransitionsSet里公共祖先全为Xor的transition
    :param pair:
    :return:
    '''
    forwardtransitionsSettemp=set(pair[0])
    backwardtransitionsSettemp=set(pair[1])
    forwardtransitionsSet = pair[0]
    backwardtransitionsSet = pair[1]
    if len(forwardtransitionsSet)==0 or len(backwardtransitionsSet)==0:
        return
    matrix={}
    for transition1 in forwardtransitionsSet:
        matrix[transition1]={}
        for transition2 in backwardtransitionsSet:
            nodesSet=set()
            if transition1 in transitions2leaf.keys():
                nodesSet.add(transitions2leaf[transition1])
            if transition2 in transitions2leaf.keys():
                nodesSet.add(transitions2leaf[transition2])
            common_ancestor = getcommon_ancestor(nodesSet)
            if common_ancestor.operator==Operator.XOR:##公共祖先是XOR
                matrix[transition1][transition2] = True
            else:
                matrix[transition1][transition2] = False
    for transition1 in list(forwardtransitionsSet):
        flag=True
        for transition2 in backwardtransitionsSet:
            flag=flag and matrix[transition1][transition2]
        if flag:
            forwardtransitionsSet.remove(transition1)
    for transition2 in list(backwardtransitionsSet):
        flag=True
        for transition1 in forwardtransitionsSet:
            flag = flag and matrix[transition1][transition2]
        if flag:
            backwardtransitionsSet.remove(transition2)
    if len(forwardtransitionsSet)==0 and len(backwardtransitionsSet)==0:
        for tran in forwardtransitionsSettemp:
            forwardtransitionsSet.add(tran)
        for tran in backwardtransitionsSettemp:
            backwardtransitionsSet.add(tran)


def find_leaves(labels,tree):
    '''
    查找enabled_activityNames的所有对应于树的节点   ：深度优先遍历
    :param enabled_activityName:
    :param tree:
    :return:
    '''
    stack=Stack()
    leaves=set()

    enabled_activityNamescopy=labels.copy()
    stack.push(tree)
    while not stack.isEmpty() and len(enabled_activityNamescopy) !=0 :
        node = stack.pop()
        if node.label is None and node.operator is None:   #跳过空节点
            continue
        if node.label is None:
            for n in node.children:
                stack.push(n)
        else:
            if node.label in enabled_activityNamescopy:
                enabled_activityNamescopy.remove(node.label)
                leaves.add(node)
    return leaves



def get_leaves(tree):
    '''
    获得以tree为根节点的树中的所有leaves  ：深度优先遍历
    :param tree:
    :return:
    '''
    stack = Stack()
    leaves = set()
    stack.push(tree)
    while not stack.isEmpty() :
        node = stack.pop()
        if node.label is None and node.operator is None:#跳过空节点
            continue
        if node.label is None:
            for n in node.children:
                stack.push(n)
        else:
            leaves.add(node)
    return leaves


def getTreeAndcorrespondingLeaves(net, initial_marking, final_marking):
    '''
    传入net
    :return:transitions2leaf net中的transition对应的tree中的leaf   ；leaf2transitions   tree中的leaf对应的 net中的transition
    '''
    index2labelOFtransitions={}
    index2transitions={}
    transitions2leaf={}
    leaf2transitions={}
    index=0
    for t in net.transitions:
        if t.label is None:
            continue
        else:
            index2transitions[str(index)]=t
            index2labelOFtransitions[str(index)] = t.label
            t.label = str(index)
            index += 1
    tree = wf_net_converter.apply(net, initial_marking, final_marking)

    leaves = find_leaves(list(index2transitions.keys()), tree)

    for leaf in leaves:
        temp = leaf.label
        leaf.label = index2labelOFtransitions[leaf.label]
        transitions2leaf[index2transitions[temp]]=leaf
        leaf2transitions[leaf]=index2transitions[temp]
        # transitions2leaf[index2transitions[leaf.label]] = leaf
        # leaf2transitions[leaf] = index2transitions[leaf.label]
        # leaf.label = index2labelOFtransitions[leaf.label]
    for t in net.transitions:
        if t.label is None:
            continue
        else:
            t.label = index2labelOFtransitions[t.label]
    return (tree,transitions2leaf,leaf2transitions)

def get_Parallel_XorLoop_Node(tree):
    '''
    获得所有operator为 Parallel和XorLoop(且第一个孩子为None)的节点  ：深度优先遍历
    :param enabled_activityName:
    :param tree:
    :return:
    '''
    stack=Stack()

    Parallel=[]
    XorLoop=[]

    stack.push(tree)
    while not stack.isEmpty() :
        node = stack.pop()
        if node.label is None and node.operator is None:
            continue
        if node.label is None:
            if node.operator== Operator.PARALLEL:
                Parallel.append(node)
            # elif node.operator== Operator.LOOP and node.children[0].label==None and node.children[0].operator==None :
            elif node.operator == Operator.LOOP:
                XorLoop.append(node)
            for n in node.children:
                stack.push(n)
    return (Parallel,XorLoop)

def initcheckgraphNodeSetList(tree,leaf2transitions):
    '''
    获得所有 and 和xorloop下的所有transition
    :param tree:
    :param leaf2transitions:
    :return:
    rootNodes：and 和 xorloop 节点 ，rootnode对应节点下所有的叶节点对应的transition
    '''
    checkgraphNodeSetList = []
    Parallel,XorLoop = get_Parallel_XorLoop_Node(tree)
    rootNodes=Parallel+XorLoop
    for node in rootNodes:
        leaves=get_leaves(node)
        checkgraphNodeset=set()
        for leaf in leaves:
            checkgraphNodeset.add(leaf2transitions[leaf])
        checkgraphNodeSetList.append(checkgraphNodeset)

    return (rootNodes,checkgraphNodeSetList)

def genedges(itemset,sourceList):
    temp=[]
    for item in sourceList:
        if item in itemset:
            temp.append(item)
    edges =  [(temp[i],temp[i+1]) for i in range(len(temp) - 2 + 1)]
    edges=set(edges)
    return edges

def removeRedundantTransitions(net, initial_marking, final_marking,frequency):
    '''
    根据字典  frequency key：trnsition ； value：访问次数  对net进行删除访问频率为0的transition
    :param net:
    :param initial_marking:
    :param final_marking:
    :param frequency:
    :return:
    '''
    redundantTransitions=[]
    for transition,times in frequency.items():
        if times == 0 :
            redundantTransitions.append(transition)
    for transition in redundantTransitions:
        net.transitions.remove(transition)
        inarcs=transition.in_arcs
        outarcs=transition.out_arcs


        for arc in inarcs:
            p = arc.source
            p.out_arcs.remove(arc)
            net.arcs.remove(arc)
        for arc in outarcs:
            p = arc.target
            p.in_arcs.remove(arc)
            net.arcs.remove(arc)


    for p in list(net.places):
        if (p  in initial_marking) or  (p in final_marking):
            continue
        if len(p.in_arcs)==0 or len(p.out_arcs)==0:
            net.places.remove(p)

    return redundantTransitions  ##

def random_filename(filename):
    '''
    不带路径的文件名转换为不会重复的字符串
    :param filename:
    :return:
    '''
    ext = os.path.splitext(filename)[1]#后缀
    new_filename = uuid.uuid1().hex + ext
    return new_filename