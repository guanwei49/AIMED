import os
from pathlib import Path
from  Objects.process_tree.obj import ProcessTree
from math import inf
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.objects.petri_net import semantics
from Objects.process_tree.obj import Operator
from check_conformance import checkConformance
from Objects.conversion.process_tree import converter as pt_converter
from Discovery.inductive import algorithm as inductive_miner
from pm4py.utils import get_properties
from pm4py.visualization.petri_net.common import visualize
from pm4py.objects.log.obj import EventLog, Trace
from utils import removeRedundantTransitions, get_leaves, reverse_net, get_path_to_leaf, log2X
from sklearn.ensemble import IsolationForest

ROOT_DIR = Path(__file__).parent
visited=set()

def getenabled_transitions(net,markings):
    '''
    获得当前marking下enabled的transition。当有None节点时，也就是空transition时可能出现多组marking，下次fire时选择fire的transition所对应的marking
    :param net:
    :param marking:
    :return:
    '''
    global visited
    visited=set()
    labe2enabled_transitions={}
    enabled_transitions2marking={}
    for marking in markings:
        visited.add(marking)
        getenabled_transitionsHelper(net,marking,labe2enabled_transitions,enabled_transitions2marking)
    return (labe2enabled_transitions,enabled_transitions2marking)


def getenabled_transitionsHelper(net, marking, labe2enabled_transitions, enabled_transitions2marking):
    global visited
    for t in semantics.enabled_transitions(net, marking):
        if t.label is None:
            tempmarking = semantics.execute(t, net, marking)
            if tempmarking not  in visited:
                visited.add(tempmarking)
                getenabled_transitionsHelper(net, tempmarking, labe2enabled_transitions, enabled_transitions2marking)
        else:
            if t.label in labe2enabled_transitions.keys():
                labe2enabled_transitions[t.label].append(t)
            else:
                labe2enabled_transitions[t.label] = [t]
            enabled_transitions2marking[t] = marking



def getXorLoop(node):
    '''
    在process tree的node节点以及所有祖先节点中，寻找离根节点最近的XorLoop节点。如果没有则返回False以及原来节点node，如果有返回True以及离根节点最近的XorLoop节点。
    :param node:process tree的节点
    :return: 如果没有则返回原来节点node，如果有返回离根节点最近的XorLoop节点。
    '''

    xorloop=None
    temp_node=node
    while temp_node is not None:
        if temp_node.operator == Operator.LOOP:
            xorloop=temp_node
        temp_node=temp_node.parent
    if xorloop is None:
        return node
    else:
        return xorloop

def cut_tree_helper(common_ancestor,nodes):
    '''

    :param common_ancestor:
    :param nodes: common_ancestor一层中有问题的节点
    :return: tau或者None 。如果为tau那么接下来需要替换tau这个节点，如果为None 说明整个树都有问题，那么将这个树替换
    '''
    # print(common_ancestor)
    # for n in nodes:
    #     print(n)
    common_ancestor=getXorLoop(common_ancestor)  #有xorloop换成xorloop
    tau = ProcessTree(label=None)
    delnodes=[]
    if common_ancestor.operator == Operator.SEQUENCE:
        if len(common_ancestor.children) == len(nodes):  # 路径以及路径所夹的所有分支等于这个公共祖先的所有分支，那么剪去公共祖先这一分支
            node = common_ancestor
            delnodes.append(node)
            common_ancestor = common_ancestor.parent
            if common_ancestor is None:  ###整个树都有问题
                tau= None
            else:
                pos = common_ancestor.children.index(node)
                common_ancestor.children[pos] = tau
                tau.parent = common_ancestor
        else:    #剪去路径以及路径所夹的所有分支
            postions=set()
            for node in nodes:
                pos = common_ancestor.children.index(node)
                postions.add(pos)
            minpos=min(postions)
            maxpos=max(postions)
            for i in range(maxpos-minpos):
                delnodes.append(common_ancestor.children[minpos])
                common_ancestor.children.remove(common_ancestor.children[minpos])
            delnodes.append(common_ancestor.children[minpos])
            common_ancestor.children[minpos]=tau
            tau.parent = common_ancestor
    else:   #公共祖先为xorloop、XOR、PARALLEL，那么剪去这一分支  ：将公共祖先的位置替换为tau
        node = common_ancestor
        delnodes.append(node)
        common_ancestor = common_ancestor.parent
        if common_ancestor is None:  ###整个树都有问题
            tau = None
        else:
            pos = common_ancestor.children.index(node)
            common_ancestor.children[pos] = tau
            tau.parent = common_ancestor
    return (tau,delnodes)

def get_node_to_Replace(leaves):
    '''
    在process tree 中 剪去leaves的公共祖先所在的分支
    如果公共祖先的祖先有xorloop ，那么将公共祖先换为这个xorloop
    如果公共祖先为xorloop、XOR、PARALLEL，那么剪去这一分支
    如果公共祖先为SEQUENCE：如果路径以及路径所夹的所有分支等于这个公共祖先的所有分支，那么剪去公共祖先这一分支
                         否则剪去路径以及路径所夹的所有分支
    :param tau: tau或者None 。如果为tau那么接下来需要替换tau这个节点，如果为None 说明整个树都有问题，那么将这个树替换
            nodes：所有公共祖先的下级节点
    :return:
    '''
    if len(leaves)==1:##节点只有一个
        if list(leaves)[0].operator is None:
            common_ancestor=(list(leaves)[0]).parent   ##公共祖先为他的父亲
        else:
            common_ancestor=list(leaves)[0]
        tau , delnodes= cut_tree_helper(common_ancestor,leaves)
        return (tau,delnodes)
    paths = []
    common_ancestor = None
    for leaf in leaves:
        paths.append(get_path_to_leaf(leaf))

    minlen = inf
    for path in paths:
        minlen = min(minlen, len(path))
    # print(minlen)
    nodes = set()

    for i in range(minlen-1):               ##寻找公共祖先 ，看前缀最多到哪，那就是公共祖先
        temp = paths[0][i]
        flag=1
        for path in paths:
            if temp!=path[i]:
                flag=0
        if flag:
            common_ancestor=temp
            nodes = set()
            for path in paths:
                nodes.add(path[i+1])
    tau,delnodes = cut_tree_helper(common_ancestor, nodes)
    return (tau,delnodes)



def replaceNode(source ,target):
    '''
    替换tree中节点，将source节点替换为target，与此同时做了一些优化
    :param source:
    :param target:
    :return: None 或者整个新树  ，如果为None 那么就还是原来的节点作为根节点。
    '''
    if target.label is None  and target.operator is None:##需要对树进行优化
        if source.parent.operator == Operator.PARALLEL or source.parent.operator == Operator.SEQUENCE:
            sourceparent = source.parent #删除这个为空的source节点
            pos = sourceparent.children.index(source)
            sourceparent.children.remove(sourceparent.children[pos])
            source.parent=None
            if len(sourceparent.children)==1:  ###将这个孩子连到祖父节点上 ，替换父节点
                child=sourceparent.children[0]
                if sourceparent.parent is None:#如果没有祖父，替换整个树
                    return child
                else:
                    sourcegrandparent=sourceparent.parent
                    child.parent=sourcegrandparent
                    pos = sourcegrandparent.children.index(sourceparent)
                    sourcegrandparent.children[pos]=child
                    sourceparent.children=None
                    sourceparent.parent=None
        else:#只可能是Xor
            sourceparent = source.parent
            Nonenum=0
            for child in sourceparent.children:
                if child.label is None:
                    Nonenum+=1
            if Nonenum>1:  #None节点超过一个，那么删除source节点
                sourceparent = source.parent  # 删除这个为空的source节点
                pos = sourceparent.children.index(source)
                sourceparent.children.remove(sourceparent.children[pos])
                source.parent = None
            if len(sourceparent.children) == 1:  ###将这个孩子连到祖父节点上 ，替换父节点.
                child = sourceparent.children[0]
                if sourceparent.parent is None:  # 如果没有祖父，替换整个树
                    return child
                else:
                    sourcegrandparent = sourceparent.parent
                    child.parent = sourcegrandparent
                    pos = sourcegrandparent.children.index(sourceparent)
                    sourcegrandparent.children[pos] = child
                    sourceparent.children = None
                    sourceparent.parent = None
    else:
        sourceparent=source.parent
        pos = sourceparent.children.index(source)
        sourceparent.children[pos] = target
        target.parent = sourceparent
        source.parent=None
        source.children=None
    return  None

def gen_new_net(net, initial_marking, final_marking,tree,log,leaves,leaf2transitions,filterrate,k):
    '''

    :param net:   仅为了绘制出错位置图片，
    :param initial_marking: 仅为了绘制出错位置图片，
    :param final_marking: 仅为了绘制出错位置图片，
    :param tree:  重点 根据leaves对tree进行剪枝
    :param log:
    :param leaves:
    :param leaf2transitions:  根据leaf找net中对应的transition
    :return:
    '''
    tau, nodes = get_node_to_Replace(leaves)

    #################################################绘图 ， 将错误位置标红。##
    neterrorTrainsitionList = list()  # 找到所有有问题的transition
    leaves = set()
    for node in nodes:
        leaves = leaves.union(get_leaves(node))
    for leaf in leaves:
        neterrorTrainsitionList.append(leaf2transitions[leaf])

    decorations = {}
    color = '#FF0000'
    for transition in neterrorTrainsitionList:
        decorations[transition] = {"label": transition.label, "color": color}
    gviz = visualize.apply(net, initial_marking, final_marking, parameters={"format": "svg"},
                               decorations=decorations)
    localfilename = 'Localization_{}.svg'.format(str(k))
    pn_visualizer.save(gviz, os.path.join(ROOT_DIR,'result',localfilename))
    ###############################################################

    #############################################画出删去有问题部分后的树###############
    if tau is None:
        tree=ProcessTree(label=None)


    #########################################转换成新的net
    cutnet, cutinitial_marking, cutfinal_marking = pt_converter.apply(tree, variant=pt_converter.Variants.TO_PETRI_NET)


    ##########################获得sublog

    rvnet2netRelation, reversed_cutnet, reversed_cutnet_initial_marking, reversed_cutnet_final_marking = reverse_net(
        cutnet, cutinitial_marking, cutfinal_marking)

    sublog = EventLog()

    for i in range(len(log)):  # 第i个trace进行实验
        # for i in range(1):#第i个trace进行实验
        subtrace = Trace()
        markings = [cutinitial_marking]
        trace = log[i]
        forwardpos = -1  ##前向replay时未走过的第一个event位置
        backwardpos = len(trace)  ##反向replay时未走过的第一个event位置
        for j in range(len(trace)):
            event_name = trace[j]['concept:name']

            label2enabled_transitions, enabled_transitions2marking = getenabled_transitions(cutnet,
                                                                                            markings)  # labe2enabled_transitions :根据label找激活的tansition ;
            # enabled_transitions2marking:根据激活的transition找对应的marking
            if event_name in label2enabled_transitions.keys():
                markings = []
                for transition in label2enabled_transitions[event_name]:
                    marking = semantics.execute(transition, cutnet, enabled_transitions2marking[transition])
                    markings.append(marking)
                forwardpos = j
            else:
                break
        #################################### 反向跑一遍  ##################
        markings = [reversed_cutnet_initial_marking]
        for j in range(len(trace) - 1, forwardpos, -1):
            event_name = trace[j]['concept:name']

            label2enabled_transitions, enabled_transitions2marking = getenabled_transitions(reversed_cutnet,
                                                                                            markings)  # labe2enabled_transitions :根据label找激活的tansition ;
            # enabled_transitions2marking:根据激活的transition找对应的marking

            if event_name in label2enabled_transitions.keys():
                markings = []
                for transition in label2enabled_transitions[event_name]:
                    marking = semantics.execute(transition, reversed_cutnet, enabled_transitions2marking[transition])
                    markings.append(marking)
                backwardpos = j
            else:
                break

        # print(forwardpos, backwardpos)
        for j in range(forwardpos + 1, backwardpos):
            # event_name = log[i][j]['concept:name']
            # print(event_name, end=" ; ")
            subtrace.append(log[i][j])
        # print()
        sublog.append(subtrace)
    # print('length of sublog:')
    # print(len(sublog))
    # print('sublog:')
    # print(sublog)

  ########激活的trainsitionpair 相同时 ， 过滤这里面的异常###########################################################################
    X = log2X(sublog)
    clf = IsolationForest(random_state=0, contamination=filterrate).fit(X)
    res = clf.predict(X)

    newlog = EventLog()
    for i in range(len(res)):
        flag = res[i]
        if flag > 0:
            newlog.append(sublog[i])

    sublog=newlog


    parameters = get_properties(sublog)
    parameters[inductive_miner.Variants.IM_CLEAN.value.Parameters.NOISE_THRESHOLD] = 0.2
    subtree = inductive_miner.apply_tree(sublog, variant=inductive_miner.Variants.IM_CLEAN,
                                           parameters=parameters)

    # gviz = pt_visualizer.apply(subtree)
    # pt_visualizer.view(gviz)
    if tau is None:
        tree = subtree
    else:
        flag = replaceNode(tau, subtree)
        if flag is not None:
            tree = flag


    net, initial_marking, final_marking = pt_converter.apply(tree, variant=pt_converter.Variants.TO_PETRI_NET)

    ##############################获得每个transition和place的访问频率
    frequency = {}
    for transition in net.transitions:
        frequency[transition] = 0
    fitnessFlag=False
    for trace in log:
        res=checkConformance(trace, net, initial_marking, final_marking)
        fitness=res[0]
        # for j in range(len(trace)):
        #     event_name = trace[j]['concept:name']
        #     print(event_name, end=" ; ")
        # print()
        # print(fitness)
        if fitness:
            fitnessFlag=True
            for transition in res[1]:
                frequency[transition] += 1
    # print(frequency)
    if fitnessFlag:
        removeRedundantTransitions(net, initial_marking, final_marking, frequency)


    return (net, initial_marking, final_marking,localfilename)