import json
import os
from pathlib import Path
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.visualization.petri_net.common import visualize
from pm4py.objects.petri_net.importer import importer as pnml_importer

ROOT_DIR = Path(__file__).parent.parent

type='RIO'############

path=os.path.join(ROOT_DIR,'data','Loanlogs',type)

if not os.path.exists(path):
    os.makedirs(path)

basenetPath = os.path.join(ROOT_DIR,'data', 'Loanlogs', 'Loan_baseline_petriNet.pnml')
associatedTransitionName=['name_9','name_19']  ######################
frequent_info = {'p_2': {'name_13': 0.15, 'name_20': 0.85}}##########
treepicName = "Loan_"+type+"_tree.png"
treeName = "Loan_"+type+"_tree.ptml"
netpicName = "Loan_"+type+"_petriNet.png"
netName = "Loan_"+type+"_petriNet.pnml"
driftTrainsitionpicName= 'Loan_'+type+'_driftTrainsition.svg'
driftTrainsitionName='Loan_'+type+'_driftTrainsition.json'
frInfoFileName='frequent_info.json'

def genNet():
    net = PetriNet("Loan_petri_net")

    # creating source, p_1 and sink place
    source = PetriNet.Place("source")
    sink = PetriNet.Place("sink")
    p_1 = PetriNet.Place("p_1")
    p_2 = PetriNet.Place("p_2")
    p_3 = PetriNet.Place("p_3")
    p_4 = PetriNet.Place("p_4")
    p_5 = PetriNet.Place("p_5")
    p_6 = PetriNet.Place("p_6")
    p_7 = PetriNet.Place("p_7")
    p_8 = PetriNet.Place("p_8")
    p_9 = PetriNet.Place("p_9")
    p_10 = PetriNet.Place("p_10")
    p_11 = PetriNet.Place("p_11")
    p_12 = PetriNet.Place("p_12")
    p_13 = PetriNet.Place("p_13")
    p_14 = PetriNet.Place("p_14")
    p_15 = PetriNet.Place("p_15")
    p_16 = PetriNet.Place("p_16")
    p_17 = PetriNet.Place("p_17")
    p_18 = PetriNet.Place("p_18")
    # add the places to the Petri Net
    net.places.add(source)
    net.places.add(sink)
    net.places.add(p_1)
    net.places.add(p_2)
    net.places.add(p_3)
    net.places.add(p_4)
    net.places.add(p_5)
    net.places.add(p_6)
    net.places.add(p_7)
    net.places.add(p_8)
    net.places.add(p_9)
    net.places.add(p_10)
    net.places.add(p_11)
    net.places.add(p_12)
    net.places.add(p_13)
    net.places.add(p_14)
    net.places.add(p_15)
    net.places.add(p_16)
    net.places.add(p_17)
    net.places.add(p_18)

    # Create transitions
    Loan__application_received = PetriNet.Transition("name_1", "Loan__application_received")
    Check__application__form_completeness = PetriNet.Transition("name_2", "Check__application__form_completeness")
    Appraise_property = PetriNet.Transition("name_3", "Appraise_property")
    Check_credit_history = PetriNet.Transition("name_4", "Check_credit_history")
    Assess_loan_risk = PetriNet.Transition("name_5", "Assess_loan_risk")
    Assess_eligibility = PetriNet.Transition("name_6", "Assess_eligibility")
    Prepare_acceptance_pack = PetriNet.Transition("name_7", "Prepare_acceptance_pack")
    Check_if_home_insurance_quote_is_requested = PetriNet.Transition("name_8", "Check_if_home_insurance_quote_is_requested")
    Send_home_insurance_quote = PetriNet.Transition("name_9", "Send_home_insurance_quote")
    Verify_repayment_agreement = PetriNet.Transition("name_10", "Verify_repayment_agreement")
    Approve_application = PetriNet.Transition("name_11", "Approve_application")
    Loan__application_approved = PetriNet.Transition("name_12", "Loan__application_approved")
    Return_application_back_to_applicant = PetriNet.Transition("name_13", "Return_application_back_to_applicant")
    Receive_updated_application = PetriNet.Transition("name_14", "Receive_updated_application")
    Reject_application = PetriNet.Transition("name_15", "Reject_application")
    Loan_application_rejected = PetriNet.Transition("name_16", "Loan_application_rejected")
    Cancel_application = PetriNet.Transition("name_17", 'Cancel_application')
    Loan__application_canceled = PetriNet.Transition("name_18", 'Loan__application_canceled')
    Send_acceptance_pack = PetriNet.Transition("name_19", 'Send_acceptance_pack')
    t_N = PetriNet.Transition("name_20", None)
    Prepare_acceptance_pack2 = PetriNet.Transition("name_21", "Prepare_acceptance_pack")
    Check_if_home_insurance_quote_is_requested2 = PetriNet.Transition("name_22",
                                                                     "Check_if_home_insurance_quote_is_requested")

    # Add the transitions to the Petri Net

    net.transitions.add(Loan__application_received)
    net.transitions.add(Check__application__form_completeness)
    net.transitions.add(Appraise_property)
    net.transitions.add(Check_credit_history)
    net.transitions.add(Assess_loan_risk)
    net.transitions.add(Assess_eligibility)
    net.transitions.add(Prepare_acceptance_pack)
    net.transitions.add(Check_if_home_insurance_quote_is_requested)
    net.transitions.add(Send_home_insurance_quote)
    net.transitions.add(Verify_repayment_agreement)
    net.transitions.add(Approve_application)
    net.transitions.add(Loan__application_approved)
    net.transitions.add(Return_application_back_to_applicant)
    net.transitions.add(Receive_updated_application)
    net.transitions.add(Reject_application)
    net.transitions.add(Loan_application_rejected)
    net.transitions.add(Cancel_application)
    net.transitions.add(Loan__application_canceled)
    net.transitions.add(Send_acceptance_pack)
    net.transitions.add(t_N)
    net.transitions.add(Prepare_acceptance_pack2)
    net.transitions.add(Check_if_home_insurance_quote_is_requested2)

    from pm4py.objects.petri_net.utils import petri_utils
    petri_utils.add_arc_from_to(source, Loan__application_received, net)
    petri_utils.add_arc_from_to(Loan__application_received, p_1, net)
    petri_utils.add_arc_from_to(p_1, Check__application__form_completeness, net)
    petri_utils.add_arc_from_to(Check__application__form_completeness, p_2, net)
    petri_utils.add_arc_from_to(p_2, Return_application_back_to_applicant, net)
    petri_utils.add_arc_from_to(Return_application_back_to_applicant, p_3, net)
    petri_utils.add_arc_from_to(p_3, Receive_updated_application, net)
    petri_utils.add_arc_from_to(Receive_updated_application, p_1, net)
    petri_utils.add_arc_from_to(p_2, t_N, net)
    petri_utils.add_arc_from_to(t_N, p_4, net)
    petri_utils.add_arc_from_to(t_N, p_5, net)
    petri_utils.add_arc_from_to(p_4, Check_credit_history, net)
    petri_utils.add_arc_from_to(p_5, Appraise_property, net)
    petri_utils.add_arc_from_to(Check_credit_history, p_7, net)
    petri_utils.add_arc_from_to(Appraise_property, p_6, net)
    petri_utils.add_arc_from_to(p_6, Assess_eligibility, net)
    petri_utils.add_arc_from_to(p_7, Assess_loan_risk, net)
    petri_utils.add_arc_from_to(Assess_loan_risk, p_8, net)
    petri_utils.add_arc_from_to(p_8, Assess_eligibility, net)
    petri_utils.add_arc_from_to(Assess_eligibility, p_9, net)
    petri_utils.add_arc_from_to(p_9, Reject_application, net)
    petri_utils.add_arc_from_to(p_9, Prepare_acceptance_pack, net)
    # petri_utils.add_arc_from_to(p_9, t_N2, net)
    petri_utils.add_arc_from_to(Reject_application, p_11, net)
    petri_utils.add_arc_from_to(p_11, Loan_application_rejected, net)
    petri_utils.add_arc_from_to(Prepare_acceptance_pack, p_10, net)
    petri_utils.add_arc_from_to(p_10, Check_if_home_insurance_quote_is_requested, net)
    petri_utils.add_arc_from_to(Check_if_home_insurance_quote_is_requested, p_12, net)
    # petri_utils.add_arc_from_to(t_N2, p_12, net)
    petri_utils.add_arc_from_to(p_12, Send_home_insurance_quote, net)
    petri_utils.add_arc_from_to(p_12, Send_acceptance_pack, net)
    petri_utils.add_arc_from_to(Send_acceptance_pack, p_17, net)
    petri_utils.add_arc_from_to(p_17, Prepare_acceptance_pack2, net)
    petri_utils.add_arc_from_to(Prepare_acceptance_pack2, p_18, net)
    petri_utils.add_arc_from_to(p_18, Check_if_home_insurance_quote_is_requested2, net)
    petri_utils.add_arc_from_to(Check_if_home_insurance_quote_is_requested2, p_13, net)
    petri_utils.add_arc_from_to(Send_home_insurance_quote, p_13, net)
    petri_utils.add_arc_from_to(p_13, Verify_repayment_agreement, net)
    petri_utils.add_arc_from_to(Verify_repayment_agreement, p_14, net)
    petri_utils.add_arc_from_to(p_14, Cancel_application, net)
    petri_utils.add_arc_from_to(p_14, Approve_application, net)
    petri_utils.add_arc_from_to(Cancel_application, p_15, net)
    petri_utils.add_arc_from_to(Approve_application, p_16, net)
    petri_utils.add_arc_from_to(p_15, Loan__application_canceled, net)
    petri_utils.add_arc_from_to(p_16, Loan__application_approved, net)
    petri_utils.add_arc_from_to(Loan__application_canceled, sink, net)
    petri_utils.add_arc_from_to(Loan__application_approved, sink, net)
    petri_utils.add_arc_from_to(Loan_application_rejected, sink, net)
    # petri_utils.add_arc_from_to(p_17, t_N2, net)
    # petri_utils.add_arc_from_to(t_N2, sink, net)





    initial_marking = Marking()
    initial_marking[source] = 1
    final_marking = Marking()
    final_marking[sink] = 1

    from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
    pnml_exporter.apply(net, initial_marking, os.path.join(path, netName), final_marking=final_marking)

    #
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    gviz = pn_visualizer.apply(net, initial_marking, final_marking)
    # pn_visualizer.view(gviz)
    pn_visualizer.save(gviz,os.path.join(path,netpicName ))

    from Objects.conversion.wf_net import converter as wf_net_converter

    tree = wf_net_converter.apply(net, initial_marking, final_marking)

    from Objects.process_tree.exporter import exporter as ptml_exporter

    ptml_exporter.apply(tree,  os.path.join(path,treeName ) )

    from pm4py.visualization.process_tree import visualizer as pt_visualizer
    gviz = pt_visualizer.apply(tree)
    pt_visualizer.save(gviz,os.path.join(path,treepicName ))

    associatedTransition=set()
    basenet, baseinitial_marking, basefinal_marking =  pnml_importer.apply(basenetPath)
    for t in basenet.transitions:
        if t.name in associatedTransitionName:
            associatedTransition.add(t)


    decorations = {}
    color = '#FF0000'
    for tran in associatedTransition:
        decorations[tran] = {"label": tran.label, "color": color}

    gviz = visualize.apply(basenet, baseinitial_marking, basefinal_marking, parameters={"format": "svg"},
                           decorations=decorations)
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    pn_visualizer.save(gviz, os.path.join(path, driftTrainsitionpicName))
    with open(os.path.join(path, driftTrainsitionName), "w") as fp:
        fp.write( json.dumps(associatedTransitionName))

    with open(os.path.join(path, frInfoFileName), "w") as fp:
        fp.write( json.dumps(frequent_info))

if __name__ == '__main__':
    genNet()
