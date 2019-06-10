import SimPy.Simulation
import LogModel_CSER
import init_CSER
import DataMonitor
import random
import time


def model(header=None,row=None):
#    print "----------------------------------"
#    print header, row
    sim = SimPy.Simulation.Simulation()
    sim.initialize()
    my_init = init_CSER.initialize_scenario_variables()
    if header:
        my_init = init_CSER.update_inputs(my_init,header=header,row=row,key="part_name")
    print my_init
    sim.g,branch0,branch1 = init_CSER.assign_sim_variables(my_init)

    sim.g.id_gen = LogModel_CSER.counter_generator()
    
    vlist = LogModel_CSER.make_vehicles(sim=sim,num=sim.g.fleetsize,branch=sim.g.branchTuple[1])
    crewchief = LogModel_CSER.make_workers(sim.g.n_crewchief)
    refuelers = LogModel_CSER.make_workers(sim.g.n_refueler)
    weapons_specialists = LogModel_CSER.make_workers(sim.g.n_weapon_sp)
    maintenance_specialists_debrief = LogModel_CSER.make_workers(sim.g.n_debrief)
    maintenance_specialists_phased = LogModel_CSER.make_workers(sim.g.n_phase_insp)
    maintenance_specialists_repair = LogModel_CSER.make_workers(sim.g.n_repair)

    for v in vlist:
        v.flight_hours = LogModel_CSER.fnRandom(**sim.g.init_phase_inspection)

    name = 'CSER'
    vStore_init = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: Vehicle Initialization", initialBuffered = vlist)
    vStore = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: Working A/C")
    vStore_postgate =SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: Working A/C post timed gate")
    vStore_failure_check1 = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: preflight failure check")
    vStore_refuel = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C refuel")
    vStore_weapons = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C weapons rearm")
    vStore_preflight = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C preflight checks")
    vStore_postgate_T =SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: Working A/C post timed gate TAT")
    vStore_failure_check1_T = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: preflight failure check TAT")
    vStore_refuel_T = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C refuel TAT")
    vStore_weapons_T = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C weapons rearm TAT")
    vStore_preflight_T = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C preflight checks TAT")
    vStore_failure_check2 = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: LRU check pre-takeoff")
    vStore_takeoff = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C ready for takeoff")
    vStore_failure_check2b = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: LRU check post-takeoff")
    vStore_flight = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: A/C ready to fly")
    vStore_failure_check2c = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: LRU check post flight")
    vStore_landing = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: landing")
    vStore_postflight = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: post landing")
    vStore_maintenance = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: maintenance area")
    vStore_unscheduled = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: unscheduled maintenance area")
    vStore_failure_check3 = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: check if part failure")
    vStore_opscheck =  SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: Ops Check etc")
    vStore_replace = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: Replace Part")
    vStore_replace2 = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: Replace Part 2")
    vStore_scheduled = SimPy.Simulation.Store(sim=sim,name=name+"Store [V]: scheduled maintenance area")
    list_of_vStores = [vStore_init,vStore,vStore_postgate,vStore_failure_check1,vStore_refuel,vStore_weapons, vStore_preflight,
                       vStore_failure_check2,vStore_takeoff,vStore_failure_check2b,vStore_flight,
                       vStore_landing,vStore_postflight,vStore_maintenance,
                       vStore_unscheduled,vStore_failure_check3,vStore_opscheck,vStore_replace,vStore_replace2,
                       vStore_scheduled]
    list_of_vStores = [vStore]
    
    depot_inventory = LogModel_CSER.make_inventory(sim,sim.g.pNames,branch0.pAmount,sim.g.pLifeDictList,sim.g.pRepair,sim.g.pReplace,
                               sim.g.pTransfer)
    for s in depot_inventory.values():
        s.name = '(branch0)'+s.name
    local_inventory = LogModel_CSER.make_inventory(sim,sim.g.pNames,branch1.pAmount,sim.g.pLifeDictList,sim.g.pRepair,sim.g.pReplace,
                               sim.g.pTransfer)
    pStore_broken = SimPy.Simulation.Store(sim=sim,name=name+"Store [P]: Broken Parts")
    list_of_pStores = []
    for x in depot_inventory.values():
        x.name = name+x.name
    for x in local_inventory.values():
        x.name = name+x.name
    list_of_pStores.extend(depot_inventory.values())
    list_of_pStores.extend(local_inventory.values())
    
    wStore_crewchief = SimPy.Simulation.Store(sim=sim,name=name+"Store [W]: Crew Chief",initialBuffered = crewchief)
    wStore_refuelers = SimPy.Simulation.Store(sim=sim,name=name+"Store [W]: Refuelers",initialBuffered = refuelers)
    wStore_weapons = SimPy.Simulation.Store(sim=sim,name=name+"Store [W]: Weapons",initialBuffered = weapons_specialists)
    wStore_debrief = SimPy.Simulation.Store(sim=sim,name=name+"Store [W]: Debriefers",initialBuffered = maintenance_specialists_debrief)
    wStore_phased = SimPy.Simulation.Store(sim=sim,name=name+"Store [W]: Phased Maintenance",initialBuffered = maintenance_specialists_phased)
    wStore_repair = SimPy.Simulation.Store(sim=sim,name=name+"Store [W]: Repair",initialBuffered = maintenance_specialists_repair)
    dict_of_wStores = {'crewchief':wStore_crewchief,
                       'refuel':wStore_refuelers,
                       'weapons':wStore_weapons,
                       'preflight':wStore_crewchief,
                       'park recover':wStore_crewchief,
                       'servicing':wStore_crewchief,
                       'debrief':wStore_debrief,
                       'phased':wStore_phased,
                       'troubleshoot':wStore_repair,
                       'ops check':wStore_repair,
                       'signoff':wStore_repair,
                       'corr action':wStore_repair,
                       'removal':wStore_repair,
                       'repair':wStore_repair,
                       'refuel TAT':wStore_refuelers,
                       'weapons TAT':wStore_weapons,
                       'preflight TAT':wStore_crewchief}
    list_of_wStores = [wStore_crewchief, wStore_refuelers, wStore_weapons, wStore_debrief,
                       wStore_phased, wStore_repair]
    print len(list_of_wStores), [x.name for x in list_of_wStores]
    
    
    mStore_pre = SimPy.Simulation.Store(sim=sim,name=name+"Store [M]: Missions")
    mStore_post = SimPy.Simulation.Store(sim=sim,name=name+"Store [M]: post Missions")
    list_of_mStores = [mStore_pre,mStore_post]
    
    resource_taxiway = SimPy.Simulation.Resource(sim=sim,capacity=sim.g.n_taxiway, name=name+'Taxiway')
    resource_runway = SimPy.Simulation.Resource(sim=sim,capacity=sim.g.n_runway,name=name+'Runway')

    listOfStoresToMonitor = []

    if branch1.rollover_missions_bool:
        mStore_canceled = None
    else:
        mStore_canceled = mStore_post

    '''=== Define Process Blocks ==='''
    process_dict = {}
    process_dict['vAssembler'] = LogModel_CSER.VehiclePartAssembler(sim=sim,name=name+"Vehicle Assembler",
                                                               getVehicleStore = vStore_init,
                                                               getInventoryDict=depot_inventory,
                                                               putStore=vStore)
    process_dict['time gate'] = LogModel_CSER.TimedObjectRelease(sim=sim,name=name+"Vehicle Time Gate",
                                                             getStore=vStore,
                                                             putStore=vStore_postgate,
                                                             list_of_times=[8,10,12,14],
                                                             list_of_numbers=[4,4,4,4])
    # If there are more aircraft than missions, put vehicles back into standby state
    process_dict['time gate undo'] = LogModel_CSER.TimedObjectRelease(sim=sim,name=name+"Vehicle Time Gate",
                                                             getStore=vStore_postgate,
                                                             putStore=vStore,
                                                             list_of_times=[15],
                                                             list_of_numbers=[sim.g.fleetsize])
    process_dict['mGenerator'] = LogModel_CSER.MissionGenerator(sim=sim,name=name+"Mission Generator",putStore=mStore_pre,
                                                           putCanceledMissionStore=None,**branch1.campaign_parameters)
    process_dict['mManager'] =  LogModel_CSER.MissionManager(sim=sim,name=name+"Mission Manager",getStoreMissions=mStore_pre,
                                                        getStoreVehicles=vStore_postgate,
                                                        putStore=vStore_failure_check1)
    def fn_failure_check1(veh):
        r = random.random()
        if r < sim.g.preflight_fail_rate:
#            print 'failed', r, sim.g.preflight_fail_rate
            sim.g.preflight_failure +=1
            return 1
        else:
            return 0
    process_dict['Failure Check 1'] = LogModel_CSER.GenericDecisionProcess(sim=sim,name=name+"Failure Check 1",
                                                             getStore=vStore_failure_check1,
                                                             putStoreList=[vStore_preflight,vStore_unscheduled],
                                                             conditionFn=fn_failure_check1)
    process_dict['preflight'] = LogModel_CSER.ActivitySequence(sim=sim,name=name+"Preflight Sequence",
                                                          getVehicleStore=vStore_preflight,
                                                          putVehicleStore=vStore_takeoff,
                                                          activityNameList=['refuel','weapons','preflight'],
                                                          storeDict=dict_of_wStores,waitTimesDict=sim.g.t_dict)
#    process_dict['refuel'] = LogModel_CSER.GenericActivityWithStore(sim=sim,name=name+'Refuel',
#                                                                 getVehicleStore=vStore_refuel,
#                                                                 putVehicleStore=vStore_weapons,
#                                                                 equipmentStore=dict_of_wStores['refuel'],
#                                                                 processTime=sim.g.t_dict['refuel'])
#    process_dict['weapons'] = LogModel_CSER.GenericActivityWithStore_AddTime2Parts(sim=sim,name=name+'Weapons Rearm',
#                                                                             getVehicleStore=vStore_weapons,
#                                                                             putVehicleStore=vStore_preflight,
#                                                                             equipmentStore=dict_of_wStores['weapons'],
#                                                                             processTime=sim.g.t_dict['weapons'])
#    process_dict['preflight'] = LogModel_CSER.GenericActivityWithStore_AddTime2Parts(sim=sim,name=name+'Preflight Inspection',
#                                                                             getVehicleStore=vStore_preflight,
#                                                                             putVehicleStore=vStore_failure_check2,
#                                                                             equipmentStore=dict_of_wStores['preflight'],
#                                                                             processTime=sim.g.t_dict['preflight'])
#    def fn_check_failure_2(veh):
#        veh.updateMCStatus()
#        if len(veh.maintenanceChecklist) > 0:
#            sim.g.air_aborts +=1
#            return 1
#        else:
#            return 0
#    process_dict['Failure Check 2'] = LogModel_CSER.GenericDecisionProcess(sim=sim,name=name+'Failure Check 2',
#                                                                      getStore=vStore_failure_check2,
#                                                                      putStoreList=[vStore_takeoff,vStore_unscheduled],
#                                                                      conditionFn=fn_check_failure_2)
    process_dict['takeoff'] = LogModel_CSER.TakeoffSequence(sim=sim,name=name+'Takeoff Sequence',
                                                       getVehicleStore=vStore_takeoff,
                                                       putVehicleStore=vStore_failure_check2b,
                                                       putVehUnscheduled = vStore_unscheduled,
                                                       taxi=resource_taxiway,runway=resource_runway,
                                                       t_taxi=sim.g.t_dict['engine etc'],
                                                       t_takeoff=sim.g.t_dict['takeoff'])
    def fn_check_failure_2b(veh):
        veh.updateMCStatus()
        if len(veh.maintenanceChecklist) > 0:
            sim.g.air_aborts +=1
            return 1
        else:
            return 0
    process_dict['Failure Check 2b'] = LogModel_CSER.GenericDecisionProcess(sim=sim,name=name+'Failure Check 2b',
                                                                      getStore=vStore_failure_check2b,
                                                                      putStoreList=[vStore_flight,vStore_unscheduled],
                                                                      conditionFn=fn_check_failure_2b)
    process_dict['Flight'] = LogModel_CSER.MissionExecutor(sim=sim,name=name+'Mission Executor',
                                                         getStore=vStore_flight,
                                                         putVehicleStore=vStore_failure_check2c,
                                                         putMissionStore=mStore_post)
    process_dict["mAssess"]  = LogModel_CSER.MissionAssessment(sim=sim, name=name+"Mission Assessment",
                                             categoryList=[sim.g.mission_dict.keys(), ["Success","Aborted","Incomplete"]],
                                             categoryName=['missionType','success'], 
                                             getMissionStore=mStore_canceled)
    def fn_failure_check2c(veh):
        veh.updateMCStatus()
#        if veh.mission_success == False:
#            print '+++ check failure 2b: ',veh.myID, round(sim.now(),2), veh.partSet.remainingLife()
        if len(veh.maintenanceChecklist) > 0:
            sim.g.air_aborts += 1
            return 1
        else:
            sim.g.sorties_flown += 1
            return 0
    process_dict['Failure Check 2c'] = LogModel_CSER.GenericDecisionProcess(sim=sim,name=name+'Failure Check 2c',
                                                                       getStore=vStore_failure_check2c,
                                                                       putStoreList=[vStore_landing,vStore_unscheduled],
                                                                       conditionFn=fn_failure_check2c)
    process_dict['land taxi'] = LogModel_CSER.GenericActivityWithResource_AddTime2Parts(sim=sim,name=name+'Landing and Taxiing',
                                                                   getVehicleStore=vStore_landing,
                                                                   putVehicleStore=vStore_postflight,
                                                                   equipmentResource=resource_runway,
                                                                   processTime=sim.g.t_dict['land taxi'])
    process_dict['postflight'] = LogModel_CSER.ActivitySequence(sim=sim, name=name+'Postflight Sequence',
                                                           getVehicleStore=vStore_postflight, 
                                                           putVehicleStore=vStore_maintenance, 
                                                           activityNameList=['park recover','servicing','debrief'],
                                                           storeDict=dict_of_wStores,
                                                           waitTimesDict=sim.g.t_dict)
    def fn_maintenance_decision(veh):
        veh.updateMCStatus()
#        print round(sim.now(),1), veh.myID, veh.partSet.remainingLife()
        if len(veh.maintenanceChecklist) > 0:
            sim.g.ground_aborts += 1
            return 1
        else:
            return 0
    process_dict['maintenance'] = LogModel_CSER.GenericDecisionProcess(sim=sim,name=name+'Maintenance Decision',
                                                                 getStore=vStore_maintenance,
                                                                 putStoreList=[vStore_scheduled,vStore_unscheduled],
                                                                 conditionFn=fn_maintenance_decision)
    process_dict['troubleshoot'] = LogModel_CSER.GenericActivityWithStore(sim=sim,name=name+'Troubleshooting',
                                                                     getVehicleStore=vStore_unscheduled,
                                                                     putVehicleStore=vStore_failure_check3,
                                                                     equipmentStore=dict_of_wStores['troubleshoot'],
                                                                     processTime=sim.g.t_dict['troubleshoot'])
    def fn_check_part_failure(myObj):
        if len(myObj.maintenanceChecklist)>0:
            return 1
        else:
            return 0
    process_dict['failure check'] = LogModel_CSER.GenericDecisionProcess(sim=sim,name=name+'Check for Part Failure',
                                                                    getStore=vStore_failure_check3,
                                                                    putStoreList=[vStore_opscheck,vStore_replace],
                                                                    conditionFn=fn_check_part_failure)
    process_dict['replace LRU 1'] = LogModel_CSER.MaintenanceManager(sim=sim,name=name+'Maintenance Manager',
                                                                getVehicleStore=vStore_replace,
                                                                getInventoryDict=local_inventory,
                                                                putStore=vStore_replace2,
                                                                getWorkerStore=wStore_repair)
    process_dict['replace LRU 2'] = LogModel_CSER.PostRepair(sim=sim,name=name+'Post Replace',
                                                        getStore=vStore_replace2,
                                                        putVehicleStore=vStore_opscheck,
                                                        putBrokenStore=pStore_broken,
                                                        putWorkerStore=wStore_repair)
    process_dict['ops check'] = LogModel_CSER.ActivitySequence(sim=sim,name=name+'Ops Check',
                                                          getVehicleStore=vStore_opscheck,
                                                          putVehicleStore=vStore_scheduled,
                                                          activityNameList=['ops check','signoff','corr action'],
                                                          storeDict=dict_of_wStores,waitTimesDict=sim.g.t_dict)
    process_dict['scheduled'] = LogModel_CSER.ScheduledMaintenance(sim=sim,name=name+'Scheduled Maintenance',
                                                              getVehicleStore=vStore_scheduled,
                                                              putVehicleStore=vStore,
                                                              t_maintenance=sim.g.t_phase_maint,
                                                              getWorkerStore=wStore_phased,
                                                              n_worker=8)
    process_dict['part repair'] = LogModel_CSER.PartRepair(sim=sim, name=name+"Part Repair", 
                                                      getPartStore=pStore_broken,
                                                      putInventoryDict=depot_inventory)
    process_dict['part allocator'] = LogModel_CSER.SingleInventoryManager(sim=sim,name=name+'Part Allocator',
                                                                     mainInventoryDict=depot_inventory,
                                                                     branchInventoryDict=local_inventory,
                                                                     branch=branch1)
    '''/// TAT Process ///'''
    process_dict['time gate T'] = LogModel_CSER.TimedObjectRelease(sim=sim,name=name+"Vehicle Time Gate T",
                                                             getStore=vStore,
                                                             putStore=vStore_postgate_T,
                                                             list_of_times=[20],
                                                             list_of_numbers=[sim.g.n_turnaround])
    # If there are more aircraft than missions, put vehicles back into standby state
    process_dict['time gate undo'] = LogModel_CSER.TimedObjectRelease(sim=sim,name=name+"Vehicle Time Gate",
                                                             getStore=vStore_postgate,
                                                             putStore=vStore,
                                                             list_of_times=[22],
                                                             list_of_numbers=[sim.g.fleetsize])
    process_dict['mManager T'] =  LogModel_CSER.MissionManager(sim=sim,name=name+"Mission Manager T",
                                                          getStoreMissions=mStore_pre,
                                                          getStoreVehicles=vStore_postgate_T,
                                                          putStore=vStore_failure_check1_T)
    process_dict['Failure Check 1 T'] = LogModel_CSER.GenericDecisionProcess(sim=sim,name=name+"Failure Check 1 T",
                                                             getStore=vStore_failure_check1_T,
                                                             putStoreList=[vStore_preflight_T,vStore_unscheduled],
                                                             conditionFn=fn_failure_check1)
    process_dict['preflight TAT'] = LogModel_CSER.ActivitySequence(sim=sim,name=name+"Preflight Sequence",
                                                          getVehicleStore=vStore_preflight_T,
                                                          putVehicleStore=vStore_takeoff,
                                                          activityNameList=['refuel TAT','weapons TAT','preflight TAT'],
                                                          storeDict=dict_of_wStores,waitTimesDict=sim.g.t_dict)
#    process_dict['refuel T'] = LogModel_CSER.GenericActivityWithStore(sim=sim,name=name+'Refuel T',
#                                                                 getVehicleStore=vStore_refuel_T,
#                                                                 putVehicleStore=vStore_weapons_T,
#                                                                 equipmentStore=dict_of_wStores['refuel'],
#                                                                 processTime=sim.g.t_dict['refuel TAT'])
#    process_dict['weapons T'] = LogModel_CSER.GenericActivityWithStore_AddTime2Parts(sim=sim,name=name+'Weapons Rearm T',
#                                                                             getVehicleStore=vStore_weapons_T,
#                                                                             putVehicleStore=vStore_preflight_T,
#                                                                             equipmentStore=dict_of_wStores['weapons'],
#                                                                             processTime=sim.g.t_dict['weapons TAT'])
#    process_dict['preflight T'] = LogModel_CSER.GenericActivityWithStore_AddTime2Parts(sim=sim,name=name+'Preflight Inspection T',
#                                                                             getVehicleStore=vStore_preflight_T,
#                                                                             putVehicleStore=vStore_takeoff,
#                                                                             equipmentStore=dict_of_wStores['preflight'],
#                                                                             processTime=sim.g.t_dict['preflight TAT'])
    
    for v in process_dict.values():
        sim.activate(v,v.Run())

    
    """===== Monitor Setup ====="""
    # Set Up Parts List to Monitor
    myPartsList = None
    if True:
        myPartsList = []
        myInv0 = depot_inventory
        myInv1 = local_inventory
        for k in myInv0.keys():
            pl = []
            pl.extend(myInv0[k].theBuffer)
            pl.extend(myInv1[k].theBuffer)
            print "Parts List for ", k, len(pl)
            myPartsList.extend(pl)
        print "Total Parts List ", len(myPartsList)

    # Set up Store Watch
    stoWatch = list_of_vStores
    stoWatch.extend(list_of_wStores)
    stoWatch.extend(depot_inventory.values())
    stoWatch.extend(local_inventory.values())
    
    # Main Monitor
    if True:
        myMonitors = DataMonitor.masterWatch(sim=sim,name="MasterWatch",vehWatch=vlist,stoWatch=stoWatch,
                                 parWatch=myPartsList,filename=sim.g.output_filenames[1])
        sim.activate(myMonitors,myMonitors.Run(),at=0.001)
    else:
        myMonitors = False
    
    # Setup other watch
    proc_dict_list = [process_dict]
    oWatch_list = []
    ma = sorted(["Success","Aborted","Incomplete"])
    ty = sorted(["A2A","A2S","ISR","training"])
    ti = [y+" "+x for y in ty for x in ma]
    for di in proc_dict_list:
        mName = ",".join([di["mAssess"].name+' '+x for x in ti])
        mMethod = di["mAssess"].output_recursive_dictionary
        oWatch_list.extend([(mName,mMethod)])
    for a,b in oWatch_list:
        print "Printing oWatch_list----"
        print a, b()

    # Daily Watch
    if True:
        myMonitors_daily = DataMonitor.masterWatch(sim=sim,name="MasterWatch Daily",otherWatch=oWatch_list,
                                        filename=sim.g.output_filenames[2])
    #                                   filename="output_daily.txt")
        sim.activate(myMonitors_daily,myMonitors_daily.Run(hold_time=24.0),at=0.001) 
#        sim.g.main_process_dict["myMonitorDaily"]=myMonitors_daily
    else:
        myMonitors_daily = False

    sim.debug = False
    """===== Begin Simulation ====="""
    sim.simulate(until=sim.g.tSimulationHrs)
    """===== End Simulation ====="""

#    if myMonitors:
##        myMonitors.printcsv()
##        myMonitors.printcsv2(keys_list_of_inventory)
#        myMonitors.printcsv2()
##    myMonitors.reset()
    if myMonitors_daily:
        myMonitors_daily.printcsv2()
        myMonitors_daily.reset()
    
    print 'Sorties Scheduled: ', sim.g.sorties_scheduled
    print 'Sorties Flown: ', sim.g.sorties_flown
    print 'Hours Flown: ', sim.g.hours_flown
    print 'Air Aborts: ', sim.g.air_aborts
    print 'Ground Aborts: ', sim.g.ground_aborts
    print 'Preflight Failure: ', sim.g.preflight_failure

    
    t1,y1 = myMonitors.theTandY('(Branch 1)Vehicle: Mission Capable')
    t2,y2 = myMonitors.theTandY('(Branch 1)Vehicle: Flying')
    t3,y3 = myMonitors.theTandY('(Branch 1)Vehicle: Non Mission Capable')
    t4,y4 = myMonitors.theTandY('(Branch 1)Vehicle: Post Mission')
    
    y_mc = [x1+x2 for x1,x2 in zip(y1,y2)]
#    y_nm = [x1+x2 for x1,x2 in zip(y3,y4)]
#    y_tt = [x1+x2 for x1,x2 in zip(y_mc,y_nm)]
#    y_ao = [x1/x2 for x1,x2 in zip(y_mc,y_tt)]
    y_ao = [x1/16. for x1 in y_mc]
    y_ao_ave = float(sum(y_ao))/float(len(y_ao))
    
    myMonitors.reset()
    
    return [y_ao_ave]
    
if __name__ == '__main__':
    random.seed(100)
    print model()
    print 'Merry Christmas'
    