'''
Created on Jun 27, 2012

@author: ciwata
'''
#from LogModel_CSER import reverseDict2, EmptyClass, fnRandom
import LogModel_CSER
import csv
import openpyxl
import os
import CSER_modules
#from LogModel_CSER import fnRandom

def csv_to_columns(filename):
    """ Takes a csv filename as an input. Outputs a dictionary with column headers as keys,
        column values as a list. The values are also evaluated (eval()). """
    f = open(filename,'r')
    c = csv.reader(f,delimiter=',',quotechar='"')
    c0 = c.next()
    for i,x in enumerate(c0):
        c0[i] = x.strip()
    myOut = {}
    for k in c0:
        myOut[k] = []
    myEval = lambda x: eval(x)  # This is necessary in case an entry in the csv has the same name as varaibles in this function
    for r in c:
#        print r
        for i,k in enumerate(c0):
#            print r[i]
            try:
                val = myEval(r[i])
            except (NameError, SyntaxError):
                val = r[i].strip()
#                print val
            myOut[k].append(val)
    return myOut

def arrange_dict_by_key(D,k):
    ''' Arranges a "matrix" dictionary into a 2 level dictionary using the provided key as the new key'''
    l = len(D[k])
    D2 = {}
    D2.update(D)
    nm = D2.pop(k)
    D_out = {}
    for i in range(l):
        D_temp = {}
        for key in D2.keys():
            D_temp[key] = D2[key][i]
        D_out[nm[i]]=D_temp
    myOut = D_out
    return myOut

def undo_arrange_dict_by_key(D,nm="name"):
    ''' Transforms a 2 level dictionary into a "matrix" dictionary '''
    D_out={}
    nm_key = sorted(D.keys())
    att_key = sorted(D[D.keys()[1]])
    D_out[nm]=nm_key
    for i in att_key:
        att = []
        for key in nm_key:
            att.append(D[key][i])
        D_out[i] = att
    myOut = D_out
    return myOut

def make_campaign(D):
    ''' Creates a dictionary in the campaign format '''
    D2 = {}
    D3 = {}
    D2.update(D)
    n_seg = D2.pop("segments")
    D_out = {"campaign":[]}
    for key in D2.keys():
        if len(D2[key]) == 1:
            D2[key] = D2[key]*n_seg
        print D2[key]
    D3.update(D2)
    D3.pop("duration")
    D3.pop("n_flights")
    for i in range(n_seg):
        seg_i = []
        seg_i.append(D2["duration"][i])
        seg_i.append(D2["n_flights"][i])
        sorties_defn = {}
        for key in D3.keys():
            sorties_defn[key] = D3[key][i]
        seg_i.append(sorties_defn)
        D_out["campaign"].append(tuple(seg_i))
    myOut = D_out
    return myOut

def ensure_dir(f):
    ''' Checks if a directory exists and if it doesn't, it makes one '''
    # src: http://stackoverflow.com/questions/273192/python-best-way-to-create-directory-if-it-doesnt-exist-for-file-write
    d = os.path.dirname(f)
    if d:
        if not os.path.exists(d):
            os.makedirs(d)

def initialize_scenario_variables():
    ''' Initializes scenario variables as a dictionary '''
    sim_var_dict = {}
    sim_var_dict.update({'refuel':{'type':'triangular','low':8./60,'mode':10./60,'high':12./60}})
    sim_var_dict.update({'refuel TAT':{'type':'triangular','low':4./60,'mode':5./60,'high':6./60}})
    sim_var_dict.update({'rearm': {'type':'triangular','low':25./60,'mode':30./60,'high':35./60}})
    sim_var_dict.update({'rearm TAT':{'type':'triangular','low':10./60,'mode':15./60,'high':20./60}})
    sim_var_dict.update({'preflight':{'type':'triangular','low':50./60,'mode':60./60,'high':70./60}})
    sim_var_dict.update({'preflight TAT':{'type':'triangular','low':5./60,'mode':10./60,'high':15./60}})
    sim_var_dict.update({'engine start etc':{'type':'triangular','low':7./60,'mode':10./60,'high':12./60}})
    sim_var_dict.update({'takeoff':{'type':'triangular','low':2./60,'mode':3./60,'high':4./60}})
    sim_var_dict.update({'flight time':{'type':'bounded normal','mean':1.,'sd':0.5,'lower_bound':0.25}})
    sim_var_dict.update({'land and taxi':{'type':'triangular','low':14./60,'mode':15./60,'high':16./60}})
#    sim_var_dict.update({'land and taxi':{'type':'triangular','low':100,'mode':200,'high':300}})
    sim_var_dict.update({'park and recovery':{'type':'triangular','low':5./60,'mode':7./60,'high':9./60}})
    sim_var_dict.update({'servicing':{'type':'triangular','low':45./60,'mode':60./60,'high':75./60}})
    sim_var_dict.update({'debrief':{'type':'triangular','low':10./60,'mode':15./60,'high':20./60}})
    sim_var_dict.update({'number of taxiways':4})
    sim_var_dict.update({'number of runways':1})
    sim_var_dict.update({'number of missions per day':16})
    sim_var_dict.update({'number of turnaround per day':2})
    
    # Manning variables
    sim_var_dict.update({'number of refuelers':8})
    sim_var_dict.update({'number of weapons specialists':8})
#    sim_var_dict.update({'number of refuelers':16})
#    sim_var_dict.update({'number of weapons specialists':16})
    sim_var_dict.update({'number of crewchief':16})
    sim_var_dict.update({'number of maintenance specialist for debrief':16})
    sim_var_dict.update({'number of maintenance specialist for phase maintenance':16})
#    sim_var_dict.update({'number of maintenance specialist for phase maintenance':200})
    sim_var_dict.update({'number of maintenance specialist for repair':4})
    
    sim_var_dict.update({'phase maintenance length':{'type':'triangular','low':5*24,'mode':6.5*24,'high':8*24}})
    sim_var_dict.update({'troubleshooting':{'type':'triangular','low':20./60,'mode':24./60,'high':30./60}})
    sim_var_dict.update({'operational check':{'type':'triangular','low':15./60,'mode':20./60,'high':25./60}})
    sim_var_dict.update({'signoff discrepancy':{'type':'triangular','low':5./60,'mode':10./60,'high':15./60}})
    sim_var_dict.update({'document corrective action':{'type':'triangular','low':5./60,'mode':10./60,'high':15./60}})
    
    sim_var_dict.update({'part removal':{'type':'triangular','low':45./60,'mode':60./60,'high':70./60}})
    sim_var_dict.update({'part issue wait':{'type':'triangular','low':0.5,'mode':2.,'high':2.5}})
    sim_var_dict.update({'paperwork':{'type':'triangular','low':5./60,'mode':10./60,'high':15./60}})
    sim_var_dict.update({'replace LRU':{'type':'triangular','low':1.,'mode':84./60,'high':2.}})
    
    sim_var_dict.update({'part_transit_from_depot':{'type':'triangular','low':0.1*24,'mode':0.3*24,'high':0.5*24}})
#    sim_var_dict.update({'part_transit_from_depot':{'type':'triangular','low':2*24,'mode':2.1*24,'high':2.2*24}})

    sim_var_dict.update({'backhaul for truck':{'type':'uniform','low':0.25*24,'high':0.5*24}})
    
    sim_var_dict.update({'time between phase maintenance':300})
    sim_var_dict.update({'initial time since last phase inspection':{'type':'uniform','low':0,'high':300}})
    sim_var_dict.update({'preflight inspection failure rate':0.05})
    
#    sim_var_dict.update({'filename':'test.txt'})
    sim_var_dict.update({'warmup_hrs':24 * 0})
    sim_var_dict.update({'presim_hrs':24 * 0})
    sim_var_dict.update({'postsim_hrs':24 * 0})
    sim_var_dict.update({'main_hrs':24*1250})
    
    sim_var_dict.update({'fleetsize':16})
    
    sim_var_dict.update({'output_filename':"output.txt"})
    sim_var_dict.update({'output_filefolder':"temp"})
#    sim_var_dict.update({'parts_data_filename':"parts_baseline.csv"})
    sim_var_dict.update({'parts_data_filename':"parts_mod.csv"})

    parts_dict = initialize_part_variables(sim_var_dict['parts_data_filename'])
    sim_var_dict.update(parts_dict)
    
    return sim_var_dict

def initialize_part_variables(filename):
    ''' Creates a dictionary with part variables from an Excel Spreadsheet input'''
    return csv_to_columns(filename)

def update_part_variables(D, part, key):
    print '-----', D, part, key
    D2 = arrange_dict_by_key(D,key)
    if len(part) > 1:
        raise RuntimeError('This function only takes a 2-level dictionary of length 1')
    k = part.keys()[0]
    if k not in D2.keys():
        raise RuntimeError('This part does not exist', k)
    else:
        print '^^^^^^^^',k,part[k],D2
        D2[k].update(part[k])
    D_out = undo_arrange_dict_by_key(D2, nm=key)
    print '++++++', D_out
    return D_out

def update_inputs(D, **kwargs):
    ''' This function updates the input dictionary variables. It accomodates changes to the
        part files. The header on the input csv file need to match the variables names used
        in the dictionary inputs. To update the parts, the header needs to be called 
        "part_update" and subsequent ones are numbered "part_update 2", etc. The values to
        update the parts must be in this dict format: {'name':{'attribute1': value, ...}} '''
    myEval = lambda x: eval(x)
    D_out = {}
    D_out.update(D)
    if "filename" in kwargs:
        pass
    elif ("header" in kwargs) and ("row" in kwargs):
        header = kwargs["header"]
        row = kwargs["row"]
        if header:
            for i9 in range(len(header)):
                header[i9] = header[i9].strip()
                try:
                    row[i9] = myEval(row[i9])
                except (NameError, SyntaxError):
                    row[i9] = row[i9].strip()
            myDtemp = dict(zip(header, row))
        print 'myDtemp', myDtemp
    if 'parts_data_filename' in myDtemp:
        pF = myDtemp['parts_data_filename']
        D_out.update(initialize_part_variables(pF))
    print D['parts_data_filename']
    print 'here', D_out
    if "part_update" in myDtemp:
        print D['parts_data_filename']
        parts_dict = initialize_part_variables(D['parts_data_filename'])
        print 'parts_dict',parts_dict
        if "key" in kwargs:
            nm = kwargs['key']
        else:
            nm = 'name'
        for k in myDtemp.keys():
            if "part_update" == k[:11]:
                part_update = myDtemp.pop(k)
                parts_dict = update_part_variables(parts_dict, part_update, nm)
        print 'parts_dict',parts_dict
        myDtemp.update(parts_dict)
    D_out.update(myDtemp)
    return D_out

def assign_sim_variables(sim_var_dict={}):
    # Note: By making this initialization into a function, it avoids package issues somehow
    #       I think it's because the function is run in the main module and pulls from the
    #       imports in that module. Also, the variables are not floating in global space.
    if sim_var_dict == {}:
        sim_var_dict = initialize_scenario_variables()
    myGlobal = LogModel_CSER.EmptyClass()
    myGlobal.ground_aborts = 0
    myGlobal.air_aborts = 0
    myGlobal.preflight_failure = 0
    myGlobal.sorties_scheduled = 0
    myGlobal.sorties_flown = 0
    myGlobal.hours_flown = 0
    
    ''' Mission Variables '''
    
    # Times for sortie generation
    myGlobal.t_refuel =     sim_var_dict['refuel']
    myGlobal.t_refuel_TAT = sim_var_dict['refuel TAT']
    myGlobal.t_rearm =      sim_var_dict['rearm']
    myGlobal.t_rearm_TAT =  sim_var_dict['rearm TAT']
    myGlobal.t_preflight =  sim_var_dict['preflight']
    myGlobal.t_preflight_TAT= sim_var_dict['preflight TAT']
    myGlobal.t_engine_etc = sim_var_dict['engine start etc']
    myGlobal.t_takeoff =    sim_var_dict['takeoff']
    myGlobal.t_flight =     sim_var_dict['flight time']
    myGlobal.t_land_taxi =  sim_var_dict['land and taxi']
    myGlobal.t_park_recover=sim_var_dict['park and recovery']
    myGlobal.t_service =    sim_var_dict['servicing']
    myGlobal.t_debrief =    sim_var_dict['debrief']
    

    # Times for Maintenance
    myGlobal.t_phase_maint= sim_var_dict['phase maintenance length']
    myGlobal.t_troubleshooting = sim_var_dict['troubleshooting']
    myGlobal.t_ops_check =  sim_var_dict['operational check']
    myGlobal.t_signoff =    sim_var_dict['signoff discrepancy']
    myGlobal.t_corr_action= sim_var_dict['document corrective action']
    myGlobal.t_part_removal=sim_var_dict['part removal']
    myGlobal.t_part_issue = sim_var_dict['part issue wait']
    myGlobal.t_paperwork =  sim_var_dict['paperwork']
    myGlobal.t_replace_LRU= sim_var_dict['replace LRU']

    myGlobal.t_dict = {}
    myGlobal.t_dict['refuel'] =     sim_var_dict['refuel']
    myGlobal.t_dict['refuel TAT'] = sim_var_dict['refuel TAT']
    myGlobal.t_dict['weapons'] =    sim_var_dict['rearm']
    myGlobal.t_dict['weapons TAT']= sim_var_dict['rearm TAT']
    myGlobal.t_dict['preflight'] =  sim_var_dict['preflight']
    myGlobal.t_dict['preflight TAT']=sim_var_dict['preflight TAT']
    myGlobal.t_dict['engine etc'] = sim_var_dict['engine start etc']
    myGlobal.t_dict['takeoff'] =    sim_var_dict['takeoff']
    myGlobal.t_dict['flight'] =     sim_var_dict['flight time']
    myGlobal.t_dict['land taxi'] = sim_var_dict['land and taxi']
    myGlobal.t_dict['park recover']=sim_var_dict['park and recovery']
    myGlobal.t_dict['servicing'] =  sim_var_dict['servicing']
    myGlobal.t_dict['debrief'] =    sim_var_dict['debrief']    

    myGlobal.t_dict['phased'] =     sim_var_dict['phase maintenance length']
    myGlobal.t_dict['troubleshoot']=sim_var_dict['troubleshooting']
    myGlobal.t_dict['ops check'] =  sim_var_dict['operational check']
    myGlobal.t_dict['signoff'] =    sim_var_dict['signoff discrepancy']
    myGlobal.t_dict['corr action']= sim_var_dict['document corrective action']
    myGlobal.t_dict['removal'] =    sim_var_dict['part removal']
    myGlobal.t_dict['issue wait'] = sim_var_dict['part issue wait']
    myGlobal.t_dict['paperwork'] =  sim_var_dict['paperwork']
    myGlobal.t_dict['replace LRU']= sim_var_dict['replace LRU']

    # Sim Obj Numbers
    myGlobal.n_taxiway =    sim_var_dict['number of taxiways']
    myGlobal.n_runway =     sim_var_dict['number of runways']
    myGlobal.n_refueler =   sim_var_dict['number of refuelers']
    myGlobal.n_weapon_sp =  sim_var_dict['number of weapons specialists']
    myGlobal.n_crewchief =  sim_var_dict['number of crewchief']
    myGlobal.n_debrief =    sim_var_dict['number of maintenance specialist for debrief'] 
    myGlobal.n_phase_insp = sim_var_dict['number of maintenance specialist for phase maintenance']
    myGlobal.n_repair =     sim_var_dict['number of maintenance specialist for repair']
    myGlobal.fleetsize =    sim_var_dict['fleetsize']
    myGlobal.n_missions =   sim_var_dict['number of missions per day']
    myGlobal.n_turnaround = sim_var_dict['number of turnaround per day']
    
    # Other
    myGlobal.t_part_transit=sim_var_dict['part_transit_from_depot']
    myGlobal.t_backhaul =   sim_var_dict['backhaul for truck']
    myGlobal.t_time_bet_phase_maintenance = sim_var_dict['time between phase maintenance']
    myGlobal.init_phase_inspection = sim_var_dict['initial time since last phase inspection']
    myGlobal.preflight_fail_rate = sim_var_dict['preflight inspection failure rate']
    
    myGlobal.output_filenames = []
    f = sim_var_dict['output_filename']
    fo = sim_var_dict['output_filefolder']
    if fo:
        fo += '/'
    myGlobal.output_filenames = ['']*4
    myGlobal.output_filenames[0] = fo
    myGlobal.output_filenames[1] = fo+f[:-4]+"_main"+f[-4:]
    myGlobal.output_filenames[2] = fo+f[:-4]+"_daily"+f[-4:]
    myGlobal.output_filenames[3] = fo+f[:-4]+"_early"+f[-4:]
    ensure_dir(myGlobal.output_filenames[1])
    
    '''Scenario Variables'''
    T_warmup = sim_var_dict['warmup_hrs']
    T_pre = sim_var_dict['presim_hrs']
    T_post = sim_var_dict['postsim_hrs']
    T_total_mission = sim_var_dict['main_hrs']

    myGlobal.simLengthInDays = T_warmup / 24 + T_pre / 24 + T_total_mission/24+ T_post / 24
    myGlobal.tSimulationHrs = myGlobal.simLengthInDays * 24

    
    ''' Part Characteristics '''    
    myGlobal.pNames = sim_var_dict["part_name"]
    myGlobal.pLifeDictList = sim_var_dict["part_life"]
    myGlobal.pRepair = sim_var_dict["repair_dict"]
    myGlobal.pTransfer = sim_var_dict["part_transfer_dict"]
    myGlobal.pReplace = sim_var_dict["replace_dict"]
    myGlobal.pMaintGroup = sim_var_dict["maintenance_group"]
    myGlobal.pMissions = sim_var_dict["missions_tuple"]
    myGlobal.pCritical = sim_var_dict["critical_tuple"]

    
    ''' Checking for missing data '''
    print "--- Checking for missing data ---"
    if '' in myGlobal.pLifeDictList:
        raise RuntimeError
    if '' in myGlobal.pRepair:
        raise RuntimeError
    if '' in myGlobal.pTransfer:
        raise RuntimeError
    if '' in myGlobal.pReplace:
        raise RuntimeError
#    if '' in myGlobal.pMaintGroup:
#        raise RuntimeError
    if '' in myGlobal.pMissions:
        raise RuntimeError
#    if '' in myGlobal.pCritical:
#        raise RuntimeError
    
    ''' Making sure time units are correct '''
            
    myGlobal.revMESL = dict(zip(myGlobal.pNames,myGlobal.pMissions))
    myGlobal.MESL = LogModel_CSER.reverseDict2(myGlobal.revMESL)
    myGlobal.part_name_to_maint_group_dict = dict(zip(myGlobal.pNames,myGlobal.pMaintGroup))
    for k,v in myGlobal.part_name_to_maint_group_dict.items():
        if v == '':
            myGlobal.part_name_to_maint_group_dict[k] = ("a",)
    myGlobal.part_maint_group_to_name_dict = LogModel_CSER.reverseDict2(myGlobal.part_name_to_maint_group_dict)
    myGlobal.part_name_to_critical_dict = dict(zip(myGlobal.pNames,myGlobal.pCritical))
    myGlobal.part_critical_to_name_dict = LogModel_CSER.reverseDict2(myGlobal.part_name_to_critical_dict)
    myGlobal.vehicleStatusList = ["Vehicle: Initiated","Vehicle: Mission Capable",
                                  "Vehicle: Non Mission Capable","Vehicle: Post Mission",
                                  "Vehicle: Flying","Vehicle: Turnaround"]
    myGlobal.partStatusList = ["Part: Initiated","Part: Installed",
                               "Part: Repairing", "Part: Repaired"]
    myGlobal.branchTuple = ("(Main Branch)","(Branch 1)")
    if myGlobal.branchTuple > 1:
        myGlobal.vehicleStatusList = [y+x for x in myGlobal.vehicleStatusList for y in myGlobal.branchTuple]
    myGlobal.partStatusList = [x+y for x in myGlobal.pNames for y in myGlobal.partStatusList]
    
    
    
    
    # Setting up variables to iterate
    n_branches = 2
    tStart = [0, 0]
    tDuration = [myGlobal.tSimulationHrs]*2
    tEnd = [x+y for x,y in zip(tStart,tDuration)]

    pAmount = [sim_var_dict["branch0_amount"],
               sim_var_dict["branch1_amount"]]
    nVehicles = [0, myGlobal.fleetsize]
    nVehiclesNow = [0,myGlobal.fleetsize]   # consider removing this
    nGrabVehicles = [0]*2
    nWorkers = [0]*2
    nWorkStations = [0]*2
    rollover_boolean = [False]*2

    branches = []
    for i in range(n_branches):
        branch = LogModel_CSER.EmptyClass()
        branch.name = myGlobal.branchTuple[i]
        branch.tStart = tStart[i]
        branch.tEnd = tEnd[i]
        branch.pAmount = pAmount[i]
        branch.nVehicles = nVehicles[i]
        branch.nVehiclesNow = nVehiclesNow[i]
        branch.nGrabVehicles = nGrabVehicles[i]
        branch.nWorkers = nWorkers[i]
        branch.nWorkStations = nWorkStations[i]
        branch.rollover_missions_bool = rollover_boolean[i]
        branches.append(branch)
    branch0, branch1 = branches
    
    ''' ====== Branch 0 (Main) ======'''
    
    ''' Campaign Parameters can be specified in 3 ways:
        1st Method: dictionary --> {random variable type (e.g. constant, normal), 
                                    associated parameters(e.g. mean, standard dev.)}
                    Note - Default number of missions per day is 100
        2nd Method: dictionary --> {number of missions per day,
                                    random variable type, associated parameters}
                           e.g.--> {"nMissions":10,"type":"triangular","low":1,"mode":2,"high":3}
        3rd Method: mixed --> {"campaign": [(duration of segment in days, 
                                             number of missions per day, 
                                             {random var. type, associated parameters}),...]
        You can also specify either the type of mission (e.g. A2A, A2S, ISR) using "mission_type",
        which has its own dictionary that defines the mission length and parameters or directly 
        specify the mission length and parameters. In the latter case, the mission will default to A2A.
        Finally, you can also specify the ratio of missions with "mission_ratio".
    '''
    
    branch0.campaign_parameters = None

    ''' ====== Branch 1 ======'''
    
    branch1.campaign_parameters = {'nMissions':myGlobal.n_missions+myGlobal.n_turnaround,'mission_type':('training',)}
    branch1.campaign_parameters.update(myGlobal.t_flight)
    
    n = 1000
#    branch1.campaign_parameters = CSER_modules.adv_make_campaign('sine', myGlobal.tSimulationHrs/n,
#                                                                 min_max=[0,myGlobal.n_missions+myGlobal.n_turnaround],
#                                                                 variability=0, n_cycles=n, 
#                                                                 mission_type=('training',))
    n_missions = myGlobal.n_missions+myGlobal.n_turnaround
    branch1.campaign_parameters = CSER_modules.adv_make_campaign('triangle', myGlobal.tSimulationHrs/n,
                                                                 min_max=[n_missions-5,n_missions+5],
                                                                 variability=0, n_cycles=n, 
                                                                 mission_type=('training',))
    myGlobal.mission_dict = {'training':myGlobal.t_flight}

    branch1.nominal_inv_req_dict= {}
    for k,v in zip(sim_var_dict["part_name"],sim_var_dict["branch1_amount"]):
        branch1.nominal_inv_req_dict[k] = v
    branch1.min_inv_req_dict = {}
    for k,v in zip(sim_var_dict["part_name"],sim_var_dict["branch1_min"]):
        branch1.min_inv_req_dict[k] = v
    branch1.part_transit_dict = {}
    for k,v in zip(sim_var_dict["part_name"],sim_var_dict["branch1_transit_time"]):
        if isinstance(v, dict):
            branch1.part_transit_dict[k] = lambda : LogModel_CSER.fnRandom(**v)
        else:
            branch1.part_transit_dict[k] = lambda : float(v)

    return myGlobal, branch0,branch1

if __name__ == "__main__":
    assign_sim_variables()
    print 'done'