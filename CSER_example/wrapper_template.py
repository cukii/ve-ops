'''
Created on Oct 12, 2012

@author: ciwata
'''

## Imports -------------------------------------------------------
# Parallel Processing Imports
import pp

# Socket Imports
from socket import *
import marshal

# Other Imports
import csv
import time

class SerialSimulator(object):
    def __init__(self, name, sim_model, fInput, fOutput=None, mc=1):
        self.name = name
        self.sim_model = sim_model
        self.fInput = fInput
        if fOutput:
            self.fOutput = fOutput
        else:
            self.fOutput = 'output_' + fInput
        self.mc=mc
    def Run(self):
        # Setup input via csv
        csv.register_dialect('line terminator', lineterminator='\n')
        csvfile = csv.reader(open(self.fInput), delimiter=',')
#        if csv.Sniffer().has_header(file(self.fInput).read(1024)):
        myHeader = csvfile.next()
        
        # Setup output
        f = csv.writer(open(self.fOutput, 'w'), 'line terminator')
        myHeader2 = [myHeader[x1].replace(' ','_') for x1 in range(len(myHeader))]
        f.writerow(myHeader2)

        # Execute Runs
        for row in csvfile:
            print row
            for i in range(self.mc):
                f.writerow(self.sim_model(header=myHeader,row=row))
        print "Done"


class ParallelSimulator(object):
    def __init__(self, name, sim_model, packages_tuple, fInput, fOutput=None, mc=1):
        self.name = name
        self.sim_model = sim_model
        self.packages_tuple = packages_tuple
        self.fInput = fInput
        if fOutput:
            self.fOutput = fOutput
        else:
            self.fOutput = 'output_' + fInput
        self.mc=mc
    def Run(self):
        # Setup parallel servers
        jobServer = pp.Server(ppservers=())
        
        # Setup input via csv
        csv.register_dialect('line terminator', lineterminator='\n')
        csvfile = csv.reader(open(self.fInput), delimiter=',')
#        if csv.Sniffer().has_header(file(self.fInput).read(1024)):
#            myHeader = csvfile.next()
        myHeader = csvfile.next()
        
        # Setup output
        f = csv.writer(open(self.fOutput, 'w'), 'line terminator')
        myHeader2 = [myHeader[x1].replace(' ','_') for x1 in range(len(myHeader))]
        f.writerow(myHeader2)

        # Execute Runs
        jobs = []
        myCounter = 0
        for row in csvfile:
            myCounter += 1
            print row
            for i in range(self.mc):
                jobs.append(jobServer.submit(self.sim_model,(myHeader,row,),(),
                                             self.packages_tuple))
            # print results
            if self.mc > 1:
                for job in jobs:
                    f.writerow(job())
                jobs = []
                
            if myCounter > 1:
                for job in jobs:
                    f.writerow(job())
                jobs = []
                myCounter = 0
                
        for job in jobs:
            f.writerow(job())
        jobs = []
        
if __name__ == '__main__':
    tStart= time.time()
    
    ''' Run Multicore '''
    from SimPy.Simulation import *
#    sim = ParallelSimulator
    
    ''' Print End Time '''
    print tStart
    print time.time() - tStart
    
    
    
    
    