import os
import shutil
import subprocess

from smarts.utils import utils

MODSET_NAME = 'GNU-OPENMPI'

def timing_report_in_log(log_filename):
    log_file = open(log_filename, 'r')
    if 'ModEM Run Report' in log_file.read():
        return True
    else:
        return False

def get_executables(path, compiled_by):
    executables = []
    for f in os.listdir(path):
        if 'Mod3DMT' in f and '.f90' not in f and 'SP' in f and compiled_by in f:
            executables.append(f)

    return executables
    
mesh_location = '/Users/mcurry/meshes/'
pr_mesh='1000ohms.25.6km.rho'

forward_ctrl_file = 'forward.qmr.ctrl'
inverse_ctrl_file = 'inverse.2itr.ctrl'
synthetic_data = 'synth_error.dat'

inverse_output_extentions = ['dat', 'rho', 'prm']
expected_files = ['NLCG_000', 'NLCG_001', 'NLCG_002']

class inverse_sp_openmpi:
    test_name = "Inverse Sparse Matrix ModEM Test with OpenMPI"
    test_description = "Test inverse for all compiled versions of 3D Sparse Matrix with OpenMPI (2 NLCG Itrs)"
    dependencies = None
    ncpus = 7

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        gnu_modsets = env.list_modsets(name=MODSET_NAME)
        if not gnu_modsets:
            result.result = "FAILED"
            result.msg = "This env file had no modests with the name 'GNU'"
            return result.result

        if MODSET_NAME not in gnu_modsets:
            result.result = "FAILED"
            result.msg = "Could not find a 'GNU-OPENMPI' Modset - need an OpenMPI modset for this test "
            return result.result
        
        print(f"Loading {gnu_modsets[0]}")
        env.load_modset(gnu_modsets[0])

        executables = get_executables(os.path.join(src_dir, 'f90'), 'OPENMPI')

        for exe in executables:

            # Create a new directory, and copy the file into it
            inverse_dir= f'inverse.{exe}'
            os.makedirs(inverse_dir)
            os.chdir(inverse_dir)

            shutil.copy2(os.path.join(src_dir, 'f90', exe), os.getcwd())
            shutil.copy(os.path.join(test_dir, self.__class__.__name__, forward_ctrl_file), os.getcwd())
            shutil.copy(os.path.join(test_dir, self.__class__.__name__, inverse_ctrl_file), os.getcwd())
            shutil.copy(os.path.join(test_dir, self.__class__.__name__, synthetic_data), os.getcwd())
            shutil.copy(os.path.join(mesh_location, pr_mesh), os.getcwd())

            modem_arguments = [f'./{exe}', f'-I', 'NLCG',
                                    f'{pr_mesh}',
                                    f'{synthetic_data}',
                                    f'{inverse_ctrl_file}',
                                    f'{forward_ctrl_file}'
                                    ]

            if 'release' in exe:
                exe_launch = modem_arguments
            elif 'mpi' in exe:
                exe_launch = ['mpiexec', '-n', f'{self.ncpus}']
                exe_launch.extend(modem_arguments)
            else:
                result.result = 'FAILED'
                result.msg = "Bad exe"
                return result.result


            utils.save_run_command(f'run.save.{exe}.sh', exe_launch)


            log_fname = f'log.inverse.out'
            log_file = open(log_fname, 'w')

            print(f"Running OpenMPI SP inverse: '{exe_launch}' logging to '{os.path.abspath(log_fname)}'")
            try:
                ierr = subprocess.run(exe_launch, stdout=log_file, stderr=log_file, check=True)
                subprocess.run(exe_launch, check=True, stdout=log_file, stderr=log_file)
            except subprocess.CalledProcessError as e:
                result.result = "FAILED"
                result.msg = f"Error when running inverse for {exe} see log: {os.path.abspath(log_fname)}"
                return result.result

            log_file.close()
            
            files = os.listdir(os.getcwd())

            for expected_file in expected_files:
                for extension in inverse_output_extentions:

                    # No PRM file for 000
                    if 'prm' in extension and 'NLCG_000' in expected_file:
                        continue

                    expected_fname = f'smarts_{expected_file}.{extension}'
                    if expected_fname not in files:
                        result.result = "FAILED"
                        result.msg = f"Could not find expected file: {expected_fname}"
                        return result.result

    
            if not timing_report_in_log(log_fname):
                result.result = "FAILED"
                result.msg = f"No timing report at the end of the log for {exe}: {os.path.abspath(log_fname)}"
                return result.result

            print(f"Passed - Inverse succsfully ran {exe} for OpenMPI SP!\n")

            os.chdir('..')


        result.result = "PASSED"
        result.msg = "Successfully ran Sprase Matrix inverse with OpenMPI"
