from SimPy.Simulation import *
#from DataMonitor import *
#import DataMonitor
#import random
#import init
import piecewise
import collections
#import time
import copy

'''=== Process Classes ==='''
class VehiclePartAssembler(Process):
    ''' This Process is part of the initialization step. It assigns a set of parts 
        to the vehicle. It pulls from the Initial Vehicle Store and Part Store,
        assigns the parts, and puts the vehicle in the Working Vehicle Store.
        This Process only runs at the beginning of the simulation.'''
    def __init__(self,sim,name,getVehicleStore,getInventoryDict,putStore):
        super(VehiclePartAssembler,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.getInventoryDict = getInventoryDict
        self.putStore = putStore
    def Run(self):
        # Check to see if there are enough parts
        nrVeh = self.getVehicleStore.nrBuffered
        numOfParts = [x.nrBuffered for x in self.getInventoryDict.itervalues()]
        if min(numOfParts) < nrVeh:
            print "Initialize: Vehicle-Part Assembler: There's not enough parts!!!"
        # Install Parts on Vehicles
        for i in xrange(nrVeh):
            yield get,self,self.getVehicleStore,1
            veh = self.got[0]
            parts = {}                                   # Parts store as dictionary
            for partStore in self.getInventoryDict.itervalues():
                yield get,self,partStore,1
                part = self.got[0]
                part.updateStatus("Part: Installed")
                parts[part.name] = part
            veh.partSet = DESPartSet(myID=i,name="Part Set",parts=parts)
            veh.updateStatus("Vehicle: Mission Capable")
            yield put,self,self.putStore,[veh]
        if self.sim.debug:
            print self.name, ': Completed'

class MissionGenerator(Process):
    ''' This Process generates missions and places it into the Mission Store. 
        For a constant campaign profile, you can provide the type of
        distribution and associated parameters. The campaign can be specified by
        passing a keyword argument "campaign", which is a list with [(duration
        of segment in days, number of missions per day, {mission type,
        associated parameters}),...]. The arguments include random variable
        specifications.
    '''
    def __init__(self, sim, name, putStore, putCanceledMissionStore = None,
                 **missionParametersDict):
        super(MissionGenerator,self).__init__(sim=sim,name=name)
        self.putStore = putStore
        self.putCanceledStore = putCanceledMissionStore
        self.missionParametersDict = missionParametersDict
    def Run(self):
        ''' There are 2 major settings (4 modes).
            Setting 1: Do the missions rollover?
            Setting 2: Is it campaign mode?
        '''
        if isinstance(self.putCanceledStore, Store):
            if "campaign" in self.missionParametersDict:
                campaign_list = self.missionParametersDict["campaign"]
                for dur,n_missions,kwargs in campaign_list:
                    for i in range(dur):
                        mission_list = make_missions(self.sim,n_missions,**kwargs)
                        yield put,self,self.putStore,mission_list
                        yield hold,self,24
                        yield get,self,self.putStore,self.putStore.nrBuffered
                        for i in range(len(self.got)):
                            self.got[i].success = "Incomplete"
#                            print "Incomplete!!"
                        yield put,self,self.putCanceledStore,self.got
            else:
                if "nMissions" in self.missionParametersDict:
                    number_of_missions_per_day = self.missionParametersDict["nMissions"]
                else:
                    number_of_missions_per_day = 100
                while True:
                    mission_list = make_missions(self.sim,number_of_missions_per_day,**self.missionParametersDict)
                    yield put,self,self.putStore,mission_list
                    yield hold,self,24
                    yield get,self,self.putStore,self.putStore.nrBuffered
                    yield put,self,self.putCanceledStore,self.got
        else:
            if "campaign" in self.missionParametersDict:
                campaign_list = self.missionParametersDict["campaign"]
                for dur,n_missions,kwargs in campaign_list:
#                    print dur, n_missions, kwargs
                    for i in range(dur):
                        mission_list = make_missions(self.sim,n_missions,**kwargs)
                        yield put,self,self.putStore,mission_list
                        yield hold,self,24
            else:
                if self.sim.debug:
                    print self.name, ": Running"
                if "nMissions" in self.missionParametersDict:
                    number_of_missions_per_day = self.missionParametersDict["nMissions"]
                else:
                    number_of_missions_per_day = 100
                while True:
                    mission_list = make_missions(self.sim,number_of_missions_per_day,**self.missionParametersDict)
                    yield put,self,self.putStore,mission_list
                    yield hold,self,24


class MissionManager(Process):
    ''' This Process combines the vehicle with a mission. It grabs from the Working 
        Vehicle Store and the Mission Store and assigns the mission to the vehicle. '''
    def __init__(self, sim, name, getStoreMissions, getStoreVehicles, putStore):
        super(MissionManager,self).__init__(sim=sim,name=name)
        self.getStoreM = getStoreMissions
        self.getStoreV = getStoreVehicles
        self.putStore = putStore
        self.type = None
        self.filterFunc = lambda x: self.__filterMissions(x)
    def Run(self):
        if self.sim.debug:
            print self.name, ": Running"
        while True:
            mission = []
            # Pull a mission from Mission Store
            yield get,self,self.getStoreM, 1
            mission = self.got[0]
            if mission.length<=0:
                print 'mission manager',mission
#            if mission.myID > 847:
#                print self.name, mission.myID, mission.name, mission.length
            self.type = (mission.missionType,)
            # Pull a vehicle that can fly that mission
            yield get,self,self.getStoreV,self.filterFunc
            veh = self.got[0]
            veh.mission=mission
            yield put,self,self.putStore,[veh]
            self.sim.g.sorties_scheduled += 1
#            yield (get,self,self.getStoreV,self.filterFunc),(hold,self,.1)
#            if self.acquired(self.getStoreV):
#                veh = self.got[0]
#                veh.mission=mission
#                yield put,self,self.putStore,[veh]
##                if veh.name == "vehicle 39" and self.sim.g.veh_print:
##                    print round(self.sim.now(),0), veh.name, "in", self.name
#            else:
#                yield put,self,self.getStoreM,[mission]
    def __filterMissions(self,queue):
        ''' Returns the first vehicle that is capable of flying the mission. '''
        returnList = []
        for entry in queue:
            if entry.missionCapableList[self.type[0]]:
                returnList.append(entry)
                break
        return returnList
    def giveMeMissionCapability(self):
        buff = self.getStoreV.buffered
        list_of_missions = sorted(self.sim.g.mission_dict.keys())
        outcome = []
        for v in buff:
            the_category = 0
#            print 'list of missions:', list_of_missions
#            print 'mission capable list:', v.missionCapableList
            for i,m in enumerate(list_of_missions):
                the_category += v.missionCapableList[m]*2**i
            the_category -= 1
#            print v.missionCapableList, the_category
            outcome.append(self.sim.g.mission_capable_chart[the_category])
#            print v.missionCapableList, self.sim.g.mission_capable_chart[the_category]
        final_outcome = dict(zip(self.sim.g.mission_capable_chart,[0]*len(self.sim.g.mission_capable_chart)))
        final_outcome.update(collections.Counter(outcome))
        ke = sorted(final_outcome.keys())
#        print ke, final_outcome
#        print final_outcome
        myout = []
        for k in ke:
            myout.append(str(final_outcome[k]))
        myout_str = ",".join(myout)
#        print self.sim.now(), final_outcome, outcome
#        print myout_str
        return myout_str

class MissionExecutor(Process):
    ''' This Process is responsible for "executing" the mission. It grabs a vehicle
        and assesses the mission. It will check for mission aborts. It schedules
        another process to simulate the vehicle executing the mission. '''
    def __init__(self,sim,name,getStore,putVehicleStore,putMissionStore):
        super(MissionExecutor,self).__init__(sim=sim,name=name)
        self.getStore = getStore
        self.putVehicleStore = putVehicleStore
        self.putMissionStore = putMissionStore
    def Run(self):
        while True:
            yield get,self,self.getStore,1
            veh = self.got[0]
#            if veh.name == "vehicle 39" and self.sim.g.veh_print:
#                print round(self.sim.now(),0), veh.name, "in", self.name
            veh = self.abortCheck(veh)
            mission = veh.mission
            veh.mission = []
#            print self.name, mission.myID, mission.name, mission.length
            runMission = DESDelay2(sim=self.sim,callingFunction=self.name,
                                  holdTime=mission.length,objectList=[veh,mission],
                                  putStoreList=[self.putVehicleStore,self.putMissionStore],
                                  preFn=(veh.updateStatus,),preFnArg=("Vehicle: Flying",),
                                  postFn=(veh.partSet.addFlightHoursAll,veh.addFlightHours,veh.updateStatus),
                                  postFnArg=(mission.length,mission.length,"Vehicle: Post Mission"))
            self.sim.activate(runMission, runMission.Run())
            self.sim.g.hours_flown += mission.length
    def abortCheck(self,veh):
#        if veh.mission.length < 0:
#            print veh.mission.myID, veh.mission.length
#        minRemainingLife = veh.partSet.minRemainingLifeCritical(veh.mission.missionType)
        minRemainingLife = veh.partSet.minRemainingLife()
#        L1 = veh.mission.length + 10
#        L2 = veh.mission.length + 10
        veh.mission.abort = False
        if minRemainingLife < veh.mission.length: 
            veh.mission.abort = True
            L1 = minRemainingLife
            veh.mission.success = "Aborted"
            veh.mission.length = L1
#            self.sim.g.air_aborts += 1
            veh.mission_success = False
#            print '--- aborted: ', veh.myID, round(self.sim.now(),2), minRemainingLife, veh.partSet.remainingLife()
#            print '=== aborted:',veh.myID,veh.name,veh.mission.length
#        if veh.flight_hours + veh.mission.length >= veh.mfhbme:
#            veh.mission.abort = True
#            veh.mission.length = veh.mfhbme - veh.flight_hours
#            L2 = veh.mfhbme - veh.flight_hours
#            veh.mission.length = veh.mfhbme
#            veh.mission.success = "Aborted"
#            veh.maintenance_event = True
#        if veh.mission.myID == 445:
#            print '--->',L1, L2, minRemainingLife
#            print veh.partSet.partLife()
#            print veh.mission.missionType,veh.partSet.minLife(),minRemainingLife
#        if veh.mission.abort == True:
#            veh.mission.length = min(L1,L2)
#            print 'mission abort', veh.mission.length
        else:
            veh.mission.success = "Success"
            veh.mission_success = True
#        if veh.mission.length == 0:
#            print round(self.sim.now(),2),veh.name,veh.mission.success,minRemainingLife,veh.mission.length,veh.mfhbme,veh.flight_hours
#            print veh.partSet.parts["CatchAll"].myID
#            print "here" 
#        print veh.mission.success, [round(x - veh.mission.length,2) for x in veh.partSet.remainingLife()]
#        print veh.name,veh.mission.success,minRemainingLife,veh.mission.length,veh.mfhbme,veh.flight_hours
#        if veh.name == "vehicle 39" and self.sim.g.veh_print:
#            print round(self.sim.now(),0), veh.name, "in", self.name, veh.mission.length, veh.flight_hours, veh.mission.success, veh.maintenance_event, minRemainingLife
#        if veh.mission.length < 0:
#            print veh.mission.length
#            print round(self.sim.now(),2), veh.name, minRemainingLife, veh.mfhbme, veh.flight_hours
        return veh

class MissionAssessment(Process):
    def __init__(self,sim,name,categoryList,categoryName,getMissionStore,getAbortStore=None):
        super(MissionAssessment,self).__init__(sim=sim,name=name)
        self.categoryList = categoryList
        self.categoryName = categoryName
        self.getMissionStore = getMissionStore
        self.getAbortStore = getAbortStore
        self._data_dict = self.make_recursive_dictionary(categoryList)
        self.data_dict = copy.deepcopy(self._data_dict)
        self.tot_num_of_missions = 0
        self.num_of_missions = 0
    def Run(self):
        while True:
            yield get,self,self.getMissionStore,1
            theMission = self.got[0]
            self.tot_num_of_missions += 1
            self.num_of_missions += 1
            ls = self.make_property_list(theMission)
            self.increment_val_recursive_dict(self.data_dict, ls)
    def make_property_list(self,m):
        myOut = []
        for nm in self.categoryName:
            myOut.append(m.__dict__[nm])
        return myOut
    def make_recursive_dictionary(self,cat,lvl=0):
        myD = {}
#        print "level: ",lvl
        lvl_ = lvl+1
        for c in cat[lvl]:
            if lvl_ < len(cat):
                myD[c] = self.make_recursive_dictionary(cat,lvl_)
            else:
                myD[c] = 0
        return myD
    def assign_val_recursive_dict(self,D,cn,val):
        nm = cn.pop(0)
        if len(cn) > 0:
            self.assign_val_recursive_dict(D[nm],cn,val)
        else:
            D[nm]=val  
    def increment_val_recursive_dict(self,D,cn):
        nm = cn.pop(0)
        if len(cn) > 0:
            self.increment_val_recursive_dict(D[nm],cn)
        else:
            D[nm]+= 1
    def read_val_recursive_dict(self,D,cn):
        nm = cn.pop(0)
        if len(cn) > 0:
            return self.read_val_recursive_dict(D[nm],cn)
        else:
            return D[nm]
    def output_recursive_dictionary(self,D=None):
        if D == None:
            D = self.data_dict
        myOut = []
        ke = sorted(D.keys())
        for k in ke:
            if isinstance(D[k], dict):
                myOut.append(self.output_recursive_dictionary(D[k]))
            else:
                myOut.append(str(D[k]))
#        print myOut
        self.reset()
        return ",".join(myOut)
    def reset(self):
        self.num_of_missions = 0
        self.data_dict = copy.deepcopy(self._data_dict)
        return []

class GenericPasser(Process):
    def __init__(self,sim,name,getStore,putStore):
        super(GenericPasser,self).__init__(sim=sim,name=name)
        self.getStore=getStore
        self.putStore=putStore
    def Run(self):
        while True:
            yield get,self,self.getStore,1
            yield put,self,self.putStore,self.got

class GenericActivityWithStore(Process):
    def __init__(self,sim,name,getVehicleStore,putVehicleStore,equipmentStore,processTime):
        super(GenericActivityWithStore,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.putVehicleStore = putVehicleStore
        self.equipmentStore = equipmentStore
        self.processTime = processTime
    def Run(self):
        while True:
            yield get,self,self.getVehicleStore,1
            activity = GenericActivityWithStore(self.sim,self.name,self.getVehicleStore,
                                                     self.putVehicleStore,self.equipmentStore,
                                                     self.processTime)
            self.sim.activate(activity,activity._Run(self.got[0]))
    def _Run(self,veh):
        yield get,self,self.equipmentStore,1
        equipment = self.got[0]
        if isinstance(self.processTime,dict):
            twait = fnRandom(**self.processTime)
#            print twait
        else:
            twait = self.processTime
        yield hold,self,twait
        yield put,self,self.equipmentStore,[equipment]
        yield put,self,self.putVehicleStore,[veh]

class GenericActivityWithStore_AddTime2Parts(Process):
    def __init__(self,sim,name,getVehicleStore,putVehicleStore,equipmentStore,processTime):
        super(GenericActivityWithStore_AddTime2Parts,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.putVehicleStore = putVehicleStore
        self.equipmentStore = equipmentStore
        self.processTime = processTime
    def Run(self):
        while True:
            yield get,self,self.getVehicleStore,1
            activity = GenericActivityWithStore_AddTime2Parts(self.sim,self.name,self.getVehicleStore,
                                                     self.putVehicleStore,self.equipmentStore,
                                                     self.processTime)
            self.sim.activate(activity,activity._Run(self.got[0]))
    def _Run(self,veh):
        yield get,self,self.equipmentStore,1
        equipment = self.got[0]
        if isinstance(self.processTime,dict):
            twait = fnRandom(**self.processTime)
        else:
            twait = self.processTime
        yield hold,self,twait
        veh.partSet.addFlightHoursAll(twait)
        yield put,self,self.equipmentStore,[equipment]
        yield put,self,self.putVehicleStore,[veh]
        
class GenericActivityWithResource(Process):
    def __init__(self,sim,name,getVehicleStore,putVehicleStore,equipmentResource,processTime):
        super(GenericActivityWithResource,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.putVehicleStore = putVehicleStore
        self.equipmentResource = equipmentResource
        self.processTime = processTime
    def Run(self):
        while True:
            yield get,self,self.getVehicleStore,1
            activity = GenericActivityWithResource(sim=self.sim,name=self.name,
                                                   getVehicleStore=self.getVehicleStore,
                                                   putVehicleStore=self.putVehicleStore,
                                                   equipmentResource=self.equipmentResource,
                                                   processTime=self.processTime)
            self.sim.activate(activity,activity._Run(self.got[0]))
    def _Run(self,veh):
        yield request,self,self.equipmentResource
        if isinstance(self.processTime,dict):
            twait = fnRandom(**self.processTime)
        else:
            twait = self.processTime
        yield hold,self,twait
        yield release,self,self.equipmentResource
        yield put,self,self.putVehicleStore,[veh]

class GenericActivityWithResource_AddTime2Parts(Process):
    def __init__(self,sim,name,getVehicleStore,putVehicleStore,equipmentResource,processTime):
        super(GenericActivityWithResource_AddTime2Parts,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.putVehicleStore = putVehicleStore
        self.equipmentResource = equipmentResource
        self.processTime = processTime
    def Run(self):
        while True:
            yield get,self,self.getVehicleStore,1
            activity = GenericActivityWithResource_AddTime2Parts(sim=self.sim,name=self.name,
                                                   getVehicleStore=self.getVehicleStore,
                                                   putVehicleStore=self.putVehicleStore,
                                                   equipmentResource=self.equipmentResource,
                                                   processTime=self.processTime)
            self.sim.activate(activity,activity._Run(self.got[0]))
    def _Run(self,veh):
        yield request,self,self.equipmentResource
        if isinstance(self.processTime,dict):
            twait = fnRandom(**self.processTime)
        else:
            twait = self.processTime
        yield hold,self,twait
        yield release,self,self.equipmentResource
#        print 'before: ', veh.partSet.remainingLife()
        veh.partSet.addFlightHoursAll(twait)
#        print 'after : ', veh.partSet.remainingLife()
        yield put,self,self.putVehicleStore,[veh]
        

class GenericDecisionProcess(Process):
    def __init__(self,sim,name,getStore,putStoreList,conditionFn):
        super(GenericDecisionProcess,self).__init__(sim=sim,name=name)
        self.getStore=getStore
        self.putStoreList = putStoreList
        self.condition = conditionFn
        assert isinstance(putStoreList,list)
        assert hasattr(conditionFn,'__call__')
    def Run(self):
        while True:
            yield get,self,self.getStore,1
            myObj = self.got[0]
            myLoc = self.condition(myObj)
            yield put,self,self.putStoreList[myLoc],[myObj]
        
class ActivitySequence(Process):        
    def __init__(self,sim,name,getVehicleStore,putVehicleStore,activityNameList,
                 storeDict,waitTimesDict):
        super(ActivitySequence,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.putVehicleStore = putVehicleStore
        self.activityNameList = activityNameList
        assert isinstance(storeDict, dict)
        self.storeDict = storeDict
        self.waitTimesDict = waitTimesDict
    def Run(self):
        while True:
            yield get,self,self.getVehicleStore,1
            veh = self.got[0]
            preflight_ops = ActivitySequence(sim=self.sim, name='_'+self.name,
                                             getVehicleStore=self.getVehicleStore,
                                             putVehicleStore=self.putVehicleStore,
                                             activityNameList=self.activityNameList,
                                             storeDict=self.storeDict,
                                             waitTimesDict=self.waitTimesDict)
            self.sim.activate(preflight_ops,preflight_ops._Run(veh))
    def _Run(self,veh):
        for nm in self.activityNameList:
            tm = fnRandom(**self.waitTimesDict[nm])
            if nm in self.storeDict:
                st = self.storeDict[nm]
                assert isinstance(st,Store)
                yield get,self,st,1
                yield hold,self,tm
                yield put,self,st,self.got

            else:
                print 'this shouldnt get triggered: ',nm, self.storeDict.keys()
                yield hold,self,tm
        yield put,self,self.putVehicleStore,[veh]

class TakeoffSequence(Process):
    def __init__(self,sim,name,getVehicleStore,putVehicleStore,putVehUnscheduled,
                 taxi,runway,t_taxi,t_takeoff):
        super(TakeoffSequence,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.putVehicleStore = putVehicleStore
        self.putVehUnscheduled = putVehUnscheduled
        self.taxi = taxi
        self.runway = runway
        self.t_taxi = t_taxi
        self.t_takeoff = t_takeoff
    def Run(self):
        while True:
            yield get,self,self.getVehicleStore,1
            takeoff = TakeoffSequence(sim=self.sim,name=self.name,
                                      getVehicleStore=self.getVehicleStore,
                                      putVehicleStore=self.putVehicleStore,
                                      putVehUnscheduled=self.putVehUnscheduled,
                                      taxi=self.taxi,
                                      runway=self.runway,
                                      t_taxi=self.t_taxi,
                                      t_takeoff=self.t_takeoff)
            self.sim.activate(takeoff,takeoff._Run(self.got[0]))
    def _Run(self,veh):
        t_taxi = fnRandom(**self.t_taxi)
        t_takeoff = fnRandom(**self.t_takeoff)
        yield request,self,self.taxi
        yield hold,self,t_taxi
        veh.partSet.addFlightHoursAll(t_taxi)
        veh.updateMCStatus()
        if len(veh.maintenanceChecklist) > 0:
            yield release,self,self.taxi
            yield put,self,self.putVehUnscheduled,[veh]
            veh.updateStatus("Vehicle: Non Mission Capable")
            self.sim.g.ground_aborts += 1
        else:
            yield request,self,self.runway
            yield release,self,self.taxi
            yield hold,self,t_takeoff
            yield release,self,self.runway
            yield put,self,self.putVehicleStore,[veh]
            veh.updateStatus("Vehicle: Flying")
            veh.partSet.addFlightHoursAll(t_takeoff)

class MaintenanceManager(Process):
    ''' This Process creates the work package to replace a broken part on a vehicle.
        It pulls from the Broken Vehicle Store, Parts Inventory, Worker Store, and
        Work Station Store. The repair is executed. The set of vehicle, parts, 
        workers, and work stations is put in the Post Store. '''
    def __init__(self,sim,name,getVehicleStore,getInventoryDict,
                 putStore,getWorkerStore=None,getWorkStationStore=None):
        super(MaintenanceManager,self).__init__(sim=sim,name=name)
        self.getVehicleStore = getVehicleStore
        self.getInventoryDict = getInventoryDict
        self.putStore = putStore
        self.getWorkerStore = getWorkerStore
        self.getWorkStationStore = getWorkStationStore
        if getWorkerStore is not None:
            self.worker = True
        else:
            self.worker = False
        if getWorkStationStore is not None:
            self.station = True
        else:
            self.station = False
    def Run(self):
        ''' This version of Run accounts for maintenance groups '''
        while True:
            yield get,self,self.getVehicleStore,1
            run_maint = MaintenanceManager(sim=self.sim,name=self.name,
                                           getVehicleStore=self.getVehicleStore,
                                           getInventoryDict=self.getInventoryDict,
                                           putStore=self.putStore,
                                           getWorkerStore=self.getWorkerStore,
                                           getWorkStationStore=self.getWorkStationStore)
            self.sim.activate(run_maint,run_maint._Run(self.got[0]))
    def _Run(self,veh):
        # 0 Setup
        veh.updateStatus("Vehicle: Non Mission Capable")
        grp = []
        for partName in veh.maintenanceChecklist:
            grp.extend(self.sim.g.part_name_to_maint_group_dict[partName])
        grp = list(set(grp))
        if len(grp) > 1:
            veh.still_repairing = True
        else:
            veh.still_repairing = False
        grpList = self.sim.g.part_maint_group_to_name_dict[grp[0]]
        fixList = set(grpList) & set(veh.maintenanceChecklist)
        #nParts = len(fixList)
        parts = []
        replaceTime = []
        worker = None
        work_station = None
        
        # 1 Part Removal
        if self.worker:
            yield get,self,self.getWorkerStore,1
            worker = self.got
        if self.station:
            yield get,self,self.getWorkStationStore,1
            work_station = self.got
        yield hold,self,fnRandom(**self.sim.g.t_dict['removal'])
        if self.worker:
            yield put,self,self.getWorkerStore,worker
        # 2 Issue Wait
        yield hold,self,fnRandom(**self.sim.g.t_dict['issue wait'])
        for partName in fixList:
            inv = self.getInventoryDict[partName]
            yield get,self,inv,1
            part = self.got[0]
            parts.append(part)
            replaceTime.append(part.replaceTime())
        # 3 Paperwork
        yield hold,self,fnRandom(**self.sim.g.t_dict['paperwork'])
        if self.worker:
            yield get,self,self.getWorkerStore,1
            worker = self.got
#        yield get,self,self.getWorkStationStore,1
#        workStation = self.got
        # 4 Replace
        repairPackage = DESRepairPackage(myID=1,name="RepairPackage",veh=veh,newPart=parts,
                                         worker=worker,workStation=work_station)
        replace = MaintenanceExecutionDelay(sim=self.sim,callingFunction="MaintenanceManager",
                           holdTime=max(replaceTime),objectList=[repairPackage],
                           putStoreList=[self.putStore], postFn=(repairPackage.replacePart,))
        self.sim.activate(replace,replace.Run())



class PostRepair(Process):
    ''' This process evaluates the repair. The vehicle can then go to either the 
        Working Vehicle Store or back to the Broken Vehicle Store to replace 
        other parts. Broken parts go to the Broken Inventory. '''
    def __init__(self,sim,name,getStore,putVehicleStore,
                 putBrokenStore,putWorkerStore=None,putWorkStationStore=None):
        super(PostRepair,self).__init__(sim=sim,name=name)
        self.getStore=getStore
        self.putVehicleStore = putVehicleStore
        self.putBrokenStore = putBrokenStore
        self.putWorkerStore = putWorkerStore
        self.putWorkStationStore = putWorkStationStore
    def Run(self):
        while True:
            yield get,self,self.getStore,1
            repairPackage = self.got[0]
            veh = repairPackage.veh
            veh.updateMCStatus()
#            if veh.name == "vehicle 39" and self.sim.g.veh_print:
#                print round(self.sim.now(),0), veh.name, "in", self.name
            yield put,self,self.putVehicleStore,[veh]
            for part in repairPackage.brokenPart:
                yield put,self,self.putBrokenStore,[part]
            if self.putWorkerStore is not None:
                yield put,self,self.putWorkerStore,repairPackage.worker
            if self.putWorkStationStore is not None:
                yield put,self,self.putWorkStationStore,repairPackage.workStation
            del repairPackage

class ScheduledMaintenance(Process):
    def __init__(self,sim,name,getVehicleStore,putVehicleStore,t_maintenance=0,
                 getWorkerStore=None,getWorkStationStore=None,n_worker=0):
        super(ScheduledMaintenance,self).__init__(sim=sim,name=name)
        self.getVehicleStore=getVehicleStore
        self.t_maintenance = t_maintenance
        self.getVehicleStore = getVehicleStore
        self.putVehicleStore = putVehicleStore
        self.getWorkerStore = getWorkerStore
        self.getWorkStationStore = getWorkStationStore
        self.n_worker = n_worker
        if getWorkerStore is not None:
            if n_worker == 0:
                self.n_worker = 1
    def Run(self):
        while True:
            yield get,self,self.getVehicleStore,1
            scheduled = ScheduledMaintenance(sim=self.sim,name=self.name,
                                             getVehicleStore=self.getVehicleStore,
                                             putVehicleStore=self.putVehicleStore,
                                             t_maintenance=self.t_maintenance,
                                             getWorkerStore=self.getWorkerStore,
                                             getWorkStationStore=self.getWorkStationStore,
                                             n_worker=self.n_worker)
            self.sim.activate(scheduled,scheduled._Run(self.got[0]))
    def _Run(self,veh):
        veh.updateStatus("Vehicle: Non Mission Capable")
        if veh.flight_hours >= self.sim.g.t_time_bet_phase_maintenance:
            workers = None
            station = None
            if self.getWorkerStore is not None:
                yield get,self,self.getWorkerStore,self.n_worker
                workers = self.got
            if self.getWorkStationStore is not None:
                yield get,self,self.getWorkStationStore,1
                station = self.got
            yield hold,self,fnRandom(**self.t_maintenance)
            if workers is not None:
                yield put,self,self.getWorkerStore,workers
            if station is not None:
                yield put,self,self.getWorkStationStore,station
            veh.resetFlightHours()
        veh.updateStatus("Vehicle: Mission Capable")
        yield put,self,self.putVehicleStore,[veh]
            
class PartRepair(Process):
    ''' This Process repairs the parts. It pulls from the Broken Parts Inventory and
        schedules a wait time which simulates the part being fixed. The part is then 
        placed into the inventory. '''
    def __init__(self,sim,name,getPartStore,putInventoryDict):
        super(PartRepair,self).__init__(sim=sim,name=name)
        self.getPartStore = getPartStore
        self.putInventoryDict = putInventoryDict
    def Run(self):
        while True:
            yield get,self,self.getPartStore,1
            myPart = self.got[0]
            rep = DESDelay2(sim=self.sim,callingFunction=self.name,
                           holdTime=myPart.repairTime()+myPart.transferTime()*2.0,
                           objectList=[myPart],putStoreList=[self.putInventoryDict[myPart.name]],
                           preFn=(myPart.updateStatus,), preFnArg=("Part: Repairing",),
                           postFn=(myPart.reset,myPart.updateStatus), postFnArg=((),"Part: Repaired"))
            self.sim.activate(rep,rep.Run())

class SingleInventoryManager(Process):
    def __init__(self,sim,name,mainInventoryDict,branchInventoryDict,branch):
        super(SingleInventoryManager,self).__init__(sim=sim,name=name)
        self.mainInventoryDict = mainInventoryDict
        self.branchInventoryDict = branchInventoryDict
        self.branch = branch
        self.in_transit = {}
        for k in mainInventoryDict.keys():
            self.in_transit[k] = 0
    def Run(self):
        transit_and_stores = {}
        num_to_transit = 0
        while True:
            yield hold,self,24
            for partStoreName in self.branchInventoryDict.keys():
                transit_and_stores = 0
                num_to_transit = 0
                transit_and_stores = self.branchInventoryDict[partStoreName].nrBuffered + self.in_transit[partStoreName]
                if transit_and_stores <= self.branch.min_inv_req_dict[partStoreName]:
                    num_to_transit = self.branch.min_inv_req_dict[partStoreName] - transit_and_stores + 1
                    for i in range(num_to_transit):
                        yield get,self,self.mainInventoryDict[partStoreName],1
#                        transfer_time = self.branch.part_transit_dict[partStoreName]()
                        transfer_time = fnRandom(**self.sim.g.t_part_transit)
                        transfer_part = DESDelay3(sim=self.sim,
                                                 callingFunction="SingleInventoryManager",
                                                 holdTime=transfer_time,objectList=self.got,
                                                 putStoreList=[self.branchInventoryDict[partStoreName]],
                                                 preFn=(self.add_in_transit,),
                                                 preFnArg=((partStoreName,1),),
                                                 postFn=(self.subtract_in_transit,),
                                                 postFnArg=((partStoreName,1),))
                        self.sim.activate(transfer_part,transfer_part.Run())
    def add_in_transit(self,part_name,num=1):
        self.in_transit[part_name] += num
    def subtract_in_transit(self,part_name,num=1):
        self.in_transit[part_name] -= num

class DESDelay(Process):
    ''' This is a generic wait Process this is used to schedule a hold for individual 
        DESObject such as for a mission or repair. It takes the hold time, a list of 
        objects that need to be held, and a list of stores to put the objects after the
        hold is completed. '''
    def __init__(self,sim,callingFunction,holdTime,objectList,putStoreList):
        super(DESDelay,self).__init__(sim=sim,name="Delay Process")
        self.callingFunction = callingFunction
        self.holdTime = holdTime
        self.objectList = objectList
        self.putStoreList = putStoreList
        self.check()
    def Run(self):
        # Check to make sure the length of objectList and storeList are equal
        yield hold,self,self.holdTime
        for i,obj in enumerate(self.objectList):
            yield put,self,self.putStoreList[i],[obj]
        return
    def check(self):
        # Check to make sure the length of objectList and storeList are equal
        if len(self.objectList) != len(self.putStoreList):
            raise RuntimeError(self.name, " called by ", self.callingFunction, 
                               ": len(self.objectList) != len(self.storeList)")        

class DESDelay2(DESDelay):
    ''' This expands DESDelay so that it takes a list of functions and its parameters that can be run
        before and after the wait. '''
    def __init__(self,sim,callingFunction="None",holdTime=0,objectList=[],putStoreList=[],
                 preFn=(lambda: emptyFn,),preFnArg=((),),
                 postFn=(lambda: emptyFn,),postFnArg=((),)):
        super(DESDelay2,self).__init__(sim,callingFunction,holdTime,objectList,putStoreList)
        self.preFn = preFn
        self.preFnArg = preFnArg
        self.postFn = postFn
        self.postFnArg = postFnArg
    def Run(self):
        self.run_functions(self.preFn, self.preFnArg)
        yield hold,self,self.holdTime
        self.run_functions(self.postFn, self.postFnArg)
        for i,obj in enumerate(self.objectList):
            yield put,self,self.putStoreList[i],[obj]
        return
    def run_functions(self,fnTuple,fnArgTuple):
        for i,fn in enumerate(fnTuple):
            if fnArgTuple[i]:
                fn(fnArgTuple[i])
            else:
                fn()

class DESDelay3(DESDelay2):
    def run_functions(self,fnTuple,fnArgTuple):
        for i,fn in enumerate(fnTuple):
            if isinstance(fnArgTuple[i],tuple):
                fn(*fnArgTuple[i])
            elif isinstance(fnArgTuple[i],dict):
                fn(**fnArgTuple[i])
            else:
                fn()

class MaintenanceExecutionDelay(DESDelay2):
    ''' This is a special delay class for maintenance operations. It incorporates worker schedules. '''
    def __init__(self,*args,**kwargs):
        super(MaintenanceExecutionDelay,self).__init__(*args,**kwargs)
        self.fixTime = self.holdTime
        if not isinstance(self.objectList[0],DESRepairPackage):
            raise TypeError("MaintenanceExecutionDelay: Called by " + self.callingFunction 
                            + ": Did not receive DESRepairPackage object")
    def Run(self):
        self.run_functions(self.preFn, self.preFnArg)
#        print sim.now(), give_me_hour_of_day(sim.now()), self.fixTime, self.calculate_repair_time()
        yield hold,self,self.calculate_repair_time()
        self.run_functions(self.postFn, self.postFnArg)
        for i,obj in enumerate(self.objectList):
            yield put,self,self.putStoreList[i],[obj]
        return
    def calculate_repair_time(self):
        workingHours = self.objectList[0].worker[0].workingHours
        if workingHours[0] == 0.0 and workingHours[1] == 24.0:
            return self.fixTime
        tNow = give_me_hour_of_day(self.sim.now())
        fixTime = self.fixTime
        simHoldTime = 0
        while fixTime > 0:
            if tNow < workingHours[0]:
                simHoldTime = workingHours[0] - tNow
                tNow = workingHours[0]
            if tNow >= workingHours[1]:
                simHoldTime += 24 - tNow + workingHours[0]
                tNow = workingHours[0]
            hoursLeft = workingHours[1] - tNow
            if fixTime < hoursLeft:
                simHoldTime += fixTime
                tNow += fixTime
                fixTime = 0
            else:
                simHoldTime += hoursLeft
                tNow = workingHours[1]
                fixTime -= hoursLeft
        return simHoldTime

class TimedObjectRelease(Process):
    ''' Grabs and puts resources from getStore to putStore based on the inputs.
        It functions as a timed gate and works on its own 24 hour clock.
        It will only release up to the specified number of objects. If there are
        less than specified, it will release what is in getStore and no more.
        
        getStore - Store object to get from
        putStore - Store object to put to
        list_of_times - a list of the hour of day to initiate a "get"
        list_of_numbers - a list of number of objects to grab from getStore at specified time
    '''
    def __init__(self,sim,name,getStore,putStore,list_of_times,list_of_numbers):
        super(TimedObjectRelease,self).__init__(sim=sim,name=name)
        self.getStore=getStore
        self.putStore=putStore
        assert len(list_of_numbers) == len(list_of_times)
        self.list_of_times=list_of_times
        self.list_of_numbers=list_of_numbers
    def Run(self):
        while True:
            for t,n in zip(self.list_of_times,self.list_of_numbers):
                release = TimedObjectRelease(sim=self.sim,name=self.name,
                                             getStore=self.getStore,
                                             putStore=self.putStore,
                                             list_of_times=self.list_of_times,
                                             list_of_numbers=self.list_of_numbers)
                self.sim.activate(release,release._Run(n),delay=t)
            yield hold,self,24
    def _Run(self,n):
        buffered = self.getStore.nrBuffered
        yield get,self,self.getStore,min(n,buffered)
        yield put,self,self.putStore,self.got

''' === Simulation Object Classes === '''
class DESObject(object):
    def __init__(self,myID,name):
        super(DESObject,self).__init__()
        self.myID = myID
        self.name = name
        self.location = 'Initiated'
    def _update_location(self,loc):
        self.location = loc
    def _get_location(self):
        return self.location

class DESMission(DESObject):
#    """ This is the mission object class variable. This contains
#        values that describe the mission and functions to manipulate
#        its internal variables.
#    """
    def __init__(self,myID=None,name='',missionType='',length=0):
        super(DESMission, self).__init__(myID,name)
        self.missionType = missionType
        self.length = length
        self.success = ""
        self.abort = False
    def setLength(self, **kwargs):
        if len(kwargs)< 2:
            self.length = 1
            print "Mission Length not set properly"
        else:
            self.length = fnRandom(**kwargs)

class DESVehicle(DESObject):
#    """ This is the vehicle object class. It holds the variables for vehicles and has
#        functions to manipulate its values. """
    def __init__(self,myID=None,name='',missionCapableList=[],
                 MESL={},revMESL={},turnaround_dict={},branch=""):
        super(DESVehicle, self).__init__(myID,name)
        self.missionCapableList = {}
        self.missionCapableList.update(missionCapableList)
        self.MESL = MESL
        self.revMESL = revMESL
        self.turnaround_dict = turnaround_dict
        self.branchName = branch
        self.partSet = {}
        self.mission = []
        self.maintenanceChecklist = []      # List of part names, Parts that need replacing
        self.currentStatus = "Vehicle: Initiated"
        self.flight_hours = 0
        self.cumulative_flight_hours = 0
        self.number_of_flights = 0
        self.cumulative_number_of_flights = 0
        self.maintenance_event = False
        self.still_repairing = False
        self.mission_success = None
        self.resetFlightHours()
    def changeMissionCapable(self,dictUpdate):
        for myKey in dictUpdate.keys():
            if myKey in self.missionCapableList:
                self.missionCapableList[myKey] = dictUpdate[myKey]
    def degradeMissionCapable(self,maintenanceList):
        if maintenanceList == []:
            pass
        else:
#            self.maintenanceChecklist = maintenanceList
            capabilityNames = []
            for partName in maintenanceList:
                capabilityNames.extend(self.revMESL[partName])
            capabilityNames = set(capabilityNames)
            for nm in capabilityNames:
                self.missionCapableList[nm] = False
#        print self.name, maintenanceList, self.missionCapableList
    def updateMCStatus(self):
        self.maintenanceChecklist = []
        self.maintenanceChecklist.extend(self.partSet.flagBroken())
        for k in self.missionCapableList.keys():
            self.missionCapableList[k] = True
        self.degradeMissionCapable(self.maintenanceChecklist)
    def removePart(self,partName):
        if partName in self.partSet.parts:
            removedPart = self.partSet.parts.pop(partName)
#            self.partSet.parts[partName] = []
#            self.partSet.parts.pop(partName)
            return removedPart
        else:
            print "DES Vehicle, removePart: part does not exist"
            return 0
    def installPart(self,part):
        self.partSet.parts[part.name] = part
        part.updateStatus("Part: Installed")
        return
    def replacePart(self,part):
        brokenPart = self.removePart(part.name)
        self.installPart(part=part)
        return brokenPart
    def updateStatus(self,myStatus):
        self.currentStatus = myStatus
    def getStatus(self):
        if self.branchName:
            return self.branchName+self.currentStatus
        else:
            return self.currentStatus
    def turnaround(self):
        tat = fnRandom(**self.turnaround_dict)
        return tat
    def updateBranch(self,branch):
        self.branchName = branch
    def addFlightHours(self,hrs):
        self.flight_hours += hrs
        self.cumulative_flight_hours += hrs
        self.number_of_flights += 1
        self.cumulative_number_of_flights += 1
    def resetFlightHours(self):
        self.flight_hours = 0
        self.number_of_flights = 0

class DESPart(DESObject):
    ''' The role of DESPart is to hold, read, and modify characteristics of the part. '''
    def __init__(self,myID=None,name='',lifeDict={},repairDict={},replaceDict={},
                 transferDict={},critical=[]):
        super(DESPart,self).__init__(myID,name)
        self.lifeDict = lifeDict
        self.repairDict = repairDict
        self.replaceDict = replaceDict
        self.transferDict = transferDict
        self.life = 0
        self.flightHoursFlown = 0
        self.number_of_flights_flown = 0
        self.reset()
        self.repairFlag = False
        self.lifeRemaining = lambda: self.life - self.flightHoursFlown
        self.currentStatus = "Part: Initiated"
        self.critical = critical
    def replaceTime(self):
        return fnRandom(**self.replaceDict)
    def repairTime(self):
        return fnRandom(**self.repairDict)
    def transferTime(self):
        return fnRandom(**self.transferDict)
    def reset(self):
        self.life = fnRandom(**self.lifeDict)
        self.repairFlag = False
        self.flightHoursFlown = 0
        self.number_of_flights_flown = 0
    def addFlightHours(self,t):
        self.flightHoursFlown += t
        self.number_of_flights_flown += 1
    def updateStatus(self,myStatus):
        self.currentStatus = myStatus
    def getStatus(self):
        return self.name+self.currentStatus

class DESWorker(DESObject):
    def __init__(self,myID=None,name='',schedule=(0.0,24.0)):
        super(DESWorker,self).__init__(myID,name)
#        self.workingHours = []
        self.workingHours = schedule
        self.skills = []

class DESWorkStation(DESObject):
    def __init__(self,myID=None,name=''):
        super(DESWorkStation,self).__init__(myID,name)
        self.type = []

class DESPartSet(DESObject):
    ''' The role of DESPartSet is to perform actions on the set of parts on the aircraft. '''
    def __init__(self,myID=None,name='',parts={}):
        super(DESPartSet,self).__init__(myID,name)
        self.parts = parts
    def partLife(self):
        mL = []
        for part in self.parts.values():
            mL.append(part.life)
        return mL
    def minLife(self):
        return min(self.partLife())
    def maxLife(self):
        return max(self.partLife())
    def remainingLife(self):
        mL = []
        for part in self.parts.values():
            mL.append(part.lifeRemaining())
        return mL
    def minRemainingLife(self):
        return min(self.remainingLife())
    def minRemainingLifeCritical(self,mission):
        mL = []
        for part in self.parts.values():
            if mission in part.critical:
                mL.append(part.lifeRemaining())
#        print self.name, mL
        return min(mL)
    def maxRemainingLife(self):
        return max(self.remainingLife())
    def addFlightHoursAll(self,t):
        for part in self.parts.values():
            part.addFlightHours(t)
    def findBroken(self):
        bL = []
        for part in self.parts.values():
            if part.lifeRemaining() <= 0:
                bL.append(part.name)
        return bL
    def flagBroken(self,bL = []):
        if bL == []:
            bL = self.findBroken()
        if bL == []:
            return bL
        else:
            for partName in bL:
#                print type(self.parts), bL
                self.parts[partName].repairFlag = True
            return bL

class DESRepairPackage(DESObject):
    def __init__(self,myID=None,name='',veh=None,newPart=[],worker=[],workStation=[]):
        super(DESRepairPackage,self).__init__(myID,name)
        self.veh = veh
        self.worker = worker
        self.workStation = workStation
        self.newPart = newPart
        self.brokenPart = []
    def replacePart(self):
        for part in self.newPart:
            self.brokenPart.append(self.veh.replacePart(part))
        return

class EmptyClass(object):
    pass
        
''' === Functions === '''

def make_missions(sim,num=10,**kwargs):
    mlist = list()
    # Check to see if mission types are specified, defaults to A2A
    if "mission_type" in kwargs.keys():
        mission_type_tuple=kwargs["mission_type"]
    else:
        mission_type_tuple=("A2A",)
    # Check to see if mission ratios are specified
    if "mission_ratio" in kwargs.keys():
        mission_ratio_tuple=kwargs["mission_ratio"]
        fn_random_choice = lambda : mission_type_tuple[weighted_random_choice(mission_ratio_tuple)]
    elif ("mission_type" in kwargs.keys()) and (len(kwargs["mission_type"]) == 1):
        fn_random_choice = lambda : mission_type_tuple[0]
    else:
        fn_random_choice = lambda : random.choice(mission_type_tuple)
    # check if there is a distribution associated with the mission
    if "type" in kwargs.keys():
        for i in range(num):
            nm = "mission " + str(i)
            m_type = fn_random_choice()
            t = DESMission(myID=sim.g.id_gen.next(), name=nm, missionType=m_type, length=1)
            t.setLength(**kwargs)
            if sim.debug:
                print '---', t.length, kwargs
            mlist.append(t)
    else:
        for i in range(num):
            nm = "mission " + str(i)
#            m_type = random.choice(mission_type_tuple)
            m_type = fn_random_choice()
            t = DESMission(myID=sim.g.id_gen.next(), name=nm, missionType=m_type, length=1)
            t.setLength(**sim.g.mission_dict[m_type])
            mlist.append(t)
#    if mlist:
#        print 'make_missions',[(x.myID,round(x.length,2)) for x in mlist]
    return mlist

def make_vehicles(sim,num=10,branch=""):
    vlist = list()
    mission_capability = dict([(k,True) for k in sim.g.MESL.keys()])
    for i in range(num):
        nm = "vehicle " + str(i)
        t = DESVehicle(i,nm,mission_capability,sim.g.MESL,sim.g.revMESL,branch=branch)
        vlist.append(t)
    return vlist

#def makeParts(num=10,pNames):
#    plist= []
##    pNames = ["partA","partB","partC"]
#    ptemp = {}
#    for i in range(num):
#        for j in range(2):
#            nm = pNames[j]
#            ptemp[pNames[j]] = DESPart(i,nm,life=10)
#        plist.append(ptemp)
#        ptemp = {}
#    return plist

def make_inventory(sim,pNames,pAmount,pLifeDictList,pRepair,pReplace,pTransfer):
    ''' This makes the multi-part inventory. pAmount must be nonzero, otherwise it makes a 
        "Broken Inventory". '''
    inventory = {}
    for i,nm in enumerate(pNames):
        if len(pAmount)>0:
            plist = []
            for j in range(pAmount[i]):
                pnm = nm
                t = DESPart(sim.g.id_gen.next(),pnm,lifeDict=pLifeDictList[i],repairDict=pRepair[i],
                            replaceDict=pReplace[i],transferDict=pTransfer[i],
                            critical=sim.g.part_name_to_critical_dict[pnm])
                plist.append(t)
            s = Store(sim=sim,name="Inventory: " + nm,initialBuffered=plist)
        else:
            s = Store(sim=sim,name="Broken Inventory: " + nm)
        inventory[nm]=s
    return inventory

def make_workers(num=10,**kwargs):
    wlist = []
    for i in range(num):
        nm = "worker " + str(i)
        t = DESWorker(i,nm,**kwargs)
        wlist.append(t)
    return wlist

def make_work_stations(num=10):
    wslist = []
    for i in range(num):
        nm = "work station " + str(i)
        t = DESWorkStation(i,nm)
        wslist.append(t)
    return wslist

def dict_val_set(D):
    ''' Returns the unique set of values in a dictionary's values '''
    v = D.values()[0]
    myV = list()
    if isinstance(v, tuple) or isinstance(v,list):
        for x in D.values():
            myV.extend(list(x))
    else:
        for x in D.values():
            myV.append(x)
    myV = sorted(list(set(myV)))
    return myV

def reverseDict(D):
    masterD = {}
    for (k,v) in D.items():
        tempTuple = [(val,k) for (val) in v]
        masterD.update(tempTuple)
#        print tempTuple
    return masterD    

def reverseDict2(D):
    test = D.values()[0]
    if not isinstance(test, basestring):
        v_set = dict_val_set(D)
        newDict = dict([(x,[]) for x in v_set])
        for k,v in D.items():
            for w in v:
                newDict[w].append(k)
        if isinstance(test,tuple):
            for k,v in newDict.items():
                newDict[k] = tuple(v)
    else:
        newDict = dict([(y,x) for x,y in D.items()])
    return newDict

def fnRandom(**kwargs):
#    print random.random()
    myType = kwargs["type"]
    if not isinstance(myType, str):
        raise TypeError('fnRandom: type is not string')
    if myType == "constant" or myType == "Constant":
        myVal = kwargs["val"]
    elif myType == "uniform" or myType == "Uniform":
        low = kwargs["low"]
        high = kwargs["high"]
        myVal = random.uniform(low,high)
    elif myType == "triangular" or myType == "Triangular":
        low = kwargs["low"]
        high = kwargs["high"]
        mode = kwargs["mode"]
        myVal = random.triangular(low,high,mode)
    elif myType == "beta" or myType == "Beta":
        alpha = kwargs["alpha"]
        beta = kwargs["beta"]
        myVal = random.betavariate(alpha,beta)
    elif myType == "expovariate" or myType == "Expovariate":
        if 'lambd' in kwargs:
            lambd = kwargs["lambd"]
        elif 'ave' in kwargs:
            lambd = 1./float(kwargs['ave'])
        myVal = random.expovariate(lambd)
    elif myType == "lognormal" or myType == "Lognormal":
        mu = kwargs["mean"]
        sigma = kwargs["sd"]
        myVal = random.lognormvariate(mu,sigma)
    elif myType == "normal" or myType == "Normal":
        mu = kwargs["mean"]
        sigma = kwargs["sd"]
        myVal = random.normalvariate(mu,sigma)
    elif myType == "bounded normal" or myType == "Bounded Normal":
        mu = kwargs["mean"]
        sigma = kwargs["sd"]
        if "lower_bound" in kwargs.keys():
            lb = kwargs["lower_bound"]
        else:
            lb = mu - 10*sigma
        if "upper_bound" in kwargs.keys():
            ub = kwargs["upper_bound"]
        else:
            ub = mu + 10*sigma
        myVal = abs(ub)*2
        while myVal < lb or myVal > ub:
            myVal = random.normalvariate(mu,sigma)
    elif myType == "piecewise":
#        print kwargs
        myVal = piecewise.piecewise(kwargs)
    else:
        raise KeyError("fnRandom: random type '" + myType + "' is not supported")
    
#    if ("units" in kwargs) and ("output units" in kwargs):
#        # time units in seconds, below is read as X seconds in an day/hour/minutes
#        myUnits = {"days": 24*60*60, "hours": 60*60, "minutes": 60, "seconds": 1}
#        myVal = myVal * myUnits[kwargs["units"]] / myUnits[kwargs["output units"]]
#        print kwargs, myVal
    return myVal


def weighted_random_choice(weights):
    # Code taken from http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
    rnd = random.random() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i

def give_me_hour_of_day(t):
    hr = t%24.0
    return round(hr, 1)

def counter_generator():
    i = 0
    while True:
        i+=1
        yield i

def emptyFn():
    pass

if __name__ == '__main__':
    print 'hello world'