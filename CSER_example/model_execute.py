'''
Created on Oct 17, 2012

@author: ciwata
'''

import wrapper_template
import model_setup_CSER as model_setup
import cProfile

def run_model(mode="baseline"):
    if mode == "baseline":
        print model_setup.model()
    elif mode == "serial":
        input_filename = "batch_inputs.csv"
#        input_filename = "doe_batch_input_table.csv"
#        input_filename = "doe_batch_input_table_calibrated.csv"
#        input_filename = "doe_table_investigative.csv"
        output_filename = "batch_outputs.csv"
        serial_runs = wrapper_template.SerialSimulator(name="Serial Execution",
                                                       sim_model=model_setup.model,
                                                       fInput=input_filename,
                                                       fOutput=output_filename,
                                                       mc=1)
        serial_runs.Run()
    elif mode == "parallel":
        packages = ("SimPy.Simulation","model_setup_CSER","LogModel_CSER","init_CSER","DataMonitor",
                    "random","time","piecewise","collections","copy","csv","os","openpyxl")
        input_filename = "batch_inputs.csv"
#        input_filename = "0_calibrating/calibration_run_doe.csv"
#        input_filename = "0_calibrating/calibration_run_doe_part2.csv"
#        input_filename = "1_memory_testing/memory_test_1.csv"
#        input_filename = "doe_batch_input_table_calibrated.csv"
#        input_filename = "doe_batch_input_table_calibrated_part2.csv"
#        input_filename = "doe_batch_input_table_calibrated_first1000.csv"
#        input_filename = "doe_table_investigative_3.csv"
        output_filename = "batch_outputs.csv"
        parallel_runs = wrapper_template.ParallelSimulator(name="Parallel Execution", 
                                                           sim_model=model_setup.model, 
                                                           packages_tuple=packages, 
                                                           fInput=input_filename, 
                                                           fOutput=output_filename, 
                                                           mc=1)
        parallel_runs.Run()
    elif mode == "server":
        pass
    else:
        raise TypeError("model_execute.run_model: run mode type not recognized")
    print 'Done',mode
    
if __name__ == "__main__":
#    run_model(mode = "baseline")
#    run_model(mode = "serial")
#    run_model(mode = "parallel")
    cProfile.run('run_model(mode="baseline")')