import os.path
from pathlib import Path
from drift_detection import drift_detectionHelper2
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.log.importer.xes import importer as xes_importer
ROOT_DIR = Path(__file__).parent

def drift_detection(logPath, netPath, windowSize =200,appearSP=40,disappearSP=20,alpha =0.2, beta =0.2, gamma = 5, filterrate=0.05):

    net, initial_marking, final_marking = pnml_importer.apply(os.path.join('data',netPath))
    log = xes_importer.apply(os.path.join('data',logPath))


    CPLIST,localfilenameList,actualfilenameList,explanationList= drift_detectionHelper2(net, initial_marking, final_marking, log, windowSize, appearSP, disappearSP, alpha, beta, gamma, filterrate)

    return {'CP':CPLIST,'localization':localfilenameList,'repairedWN':actualfilenameList,'explanation':explanationList}

if __name__ == '__main__':
    logPath=os.path.join(ROOT_DIR,'example','recurring_sudden_noise0.0_500-10_ORI.xes')
    netPath=os.path.join(ROOT_DIR,'example','BaselinePetriNet.pnml')
    res = drift_detection(logPath,netPath)
    for k,v in res.items():
        print('{}:{}'.format(k,v))