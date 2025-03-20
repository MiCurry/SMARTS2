import os
import shutil
import subprocess

from smarts.utils import utils

config_files = {}

def timing_report_in_log(log_filename):
    log_file = open(log_filename, 'r')
    if 'ModEM Run Report' in log_file.read():
        return True
    else:
        return False

def get_executables(path, compiled_by):
    executables = []
    for f in os.listdir(path):
        if 'Mod3DMT' in f and '.f90' not in f and 'SP' not in f and compiled_by in f:
            executables.append(f)

    return executables
    

mesh_location = '/Users/mcurry/meshes/'
real_mesh = 'real.25.6km.rho'
data_file = 'save.196s.3p.dat'
control_file = 'forward.qmr.ctrl'
fwd_dat_save_fname = 'fwd.dat'
esol_fname = 'fwd.esol'
MODSET_NAME = 'GNU-MPICH'

class forward_mf_mpich:
    test_name = "Forward Matrix-Free ModEM Test with MPICH"
    test_description = "Test forward for all compiled versions of 3D Matrix Free with MPICH"
    dependencies = None
    ncpus = 4

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        gnu_modsets = env.list_modsets(name=MODSET_NAME)
        if not gnu_modsets:
            result.result = "FAILED"
            result.msg = "This env file had no modests with the name 'GNU'"
            return result.result

        if MODSET_NAME not in gnu_modsets:
            result.result = "FAILED"
            result.msg = "Could not find a 'GNU-MPICH' Modset - need an MPICH modset for this test "
            return result.result
        
        print(f"Loading {gnu_modsets[0]}")
        env.load_modset(gnu_modsets[0])

        executables = get_executables(os.path.join(src_dir, 'f90'), 'MPICH')

        for exe in executables:

            # Create a new directory, and copy the file into it
            forward_dir = f'forward.{exe}'
            os.makedirs(forward_dir)
            os.chdir(forward_dir)

            shutil.copy2(os.path.join(src_dir, 'f90', exe), os.getcwd())
            shutil.copy(os.path.join(test_dir, self.__class__.__name__, control_file), os.getcwd())
            shutil.copy(os.path.join(mesh_location, real_mesh), os.getcwd())
            shutil.copy(os.path.join(mesh_location, data_file), os.getcwd())

            modem_arguments = [f'./{exe}', f'-F',
                                    f'{real_mesh}',
                                    f'{data_file}',
                                    f'{fwd_dat_save_fname}',
                                    f'{esol_fname}', f'{control_file}']

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


            log_fname = f'log.forward.out'
            log_file = open(log_fname, 'w')

            print(f"Running MPICH MF forward: '{exe_launch}' logging to '{os.path.abspath(log_fname)}'")
            try:
                ierr = subprocess.run(exe_launch, stdout=log_file, stderr=log_file, check=True)
                subprocess.run(exe_launch, check=True, stdout=log_file, stderr=log_file)
            except subprocess.CalledProcessError as e:
                result.result = "FAILED"
                result.msg = f"Error when running forward for {exe} see log: {os.path.abspath(log_fname)}"
                return result.result

            log_file.close()

            if not os.path.isfile(fwd_dat_save_fname):
                result.result = "FAILED"
                result.msg = f"'{fwd_dat_save_fname}' was not created for {exe} see log: {os.path.abspath(log_fname)}"
                return result.result

            if not os.path.isfile(esol_fname):
                result.result = "FAILED"
                result.msg = f"'{esol_fname}' was not created for {exe} see log: {os.path.abspath(log_fname)}"
                return result.result
    
            if not timing_report_in_log(log_fname):
                result.result = "FAILED"
                result.msg = f"No timing report at the end of the log for {exe}: {os.path.abspath(log_fname)}"
                return result.result

            print(f"Passed - succsfully ran {exe}!\n")

            os.chdir('..')


        result.result = "PASSED"
        result.msg = "Successfully ran Matrix-Free forward with MPICH"
