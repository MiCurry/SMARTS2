import os
import shutil

class pbs_test:
        test_name = "Test HPC.launch_job - PBS"
        test_description = "Launch a PBS job via HPC.launch_job"
        ncpus = 1
        test_dependencies = None

        def run(self, env, result, srcDir, testDir, hpc):
                print("PBS_TEST: Starting pbs_test ...")

                if hpc != 'PBS':
                    result.result = "FAILED"
                    result.msg = "The HPC type was not 'PBS'"
                    return

                # Copy the executable from the test directory into the test's run directory
                shutil.copy(os.path.join(testDir, 'pbs_test', 'sleep30.sh'), './sleep30.sh')
                       
                executable = ['printf "starting job\\n"', 
                              "./sleep30.sh", 
                              'printf "job finished\\n"']
                name = "PBS_Test"
                wallTime = "00:00:35"
                queue = "share"
                nNodes = "1"
                ncpus = "1"
                procs = "1"
                options = env.env['PBS_OPTIONS']

                print("PBS_TEST: launching pbs job via hpc.launch_job ...")
                hpc_result = hpc.launch_job(executable, name, wallTime, queue, nNodes, ncpus, procs, 
                                            pbs_options=options,
                                            script_name="my_script.pbs")
                print("PBS_TEST: HPC job finished... checking results")

                if not hpc_result:
                    result.result = "FAILED"
                    result.msg = "Failed to launch HPC job"
                    return
                    
                if not os.path.isfile('log'):
                    result.result = "FAILED"
                    result.msg = "Log file was not present after pbs run"
                    return

                log = open('./log', 'r')
                if log.read() != 'success':
                    result.result = "FAILED"
                    result.msg = "File did not contain 'success'"
                    return

                result.result = "PASSED"
                result.msg = "PBS HPC.launch_job was succesful"
                return
