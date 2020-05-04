import os
import shutil

class pbs_test_script:
        test_name = "Launch Script Test - PBS"
        test_description = "PBS Test Script - Submit a PBS job via HPC.launch_script"
        nCPUs = 1
        test_dependencies = None

        def run(self, env, result, srcDir, testDir, hpc):
                print("PBS_TEST_SCRIPT: Starting test...")

                if hpc != 'PBS':
                    result.result = "FAILED"
                    result.msg = "The HPC type was not 'PBS'"
                    return

                # Copy the executable from the test directory into the test's run directory
                shutil.copy(os.path.join(testDir, 'pbs_test_script', 'script.pbs'), './script.pbs')
                shutil.copy(os.path.join(testDir, 'pbs_test_script', 'sleep30.sh'), './sleep30.sh')
            
                print("PBS_TEST_SCRIPT: Launching PBS job via hpc.launch_script ...")
                hpc = hpc.launch_script('./script.pbs')
                print("PBS_TEST_SCRIPT: Job finished ... checking results")
                if not hpc:
                    result.result = "FAILED"
                    result.msg = "Problem launching HPC job"
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
                result.msg = "PBS script test was succesful"
                return
