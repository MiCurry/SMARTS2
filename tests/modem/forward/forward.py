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

def extract_modset(executable: str) -> str:
    split = executable.split('.')
    for itm in split:
        if 'Modset' in itm:
            return itm.split(':')[1]

    return False

mesh_location = '/Users/mcurry/meshes/'
real_mesh = 'real.25.6km.rho'
data_file = 'save.196s.3p.dat'
control_file = 'forward.qmr.ctrl'
fwd_dat_save_fname = 'fwd.dat'
esol_fname = 'fwd.esol'
MODSET_NAME = 'GNU-MPICH'

class forward:
    test_name = "ModEM Forward"
    test_description = "Test Forward for Mod3DMT executable"
    dependencies = []
    ncpus = 4

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        modset = kwargs.get('modset', None)
        mpi = kwargs.get('mpi', False)


        executables = utils.all_matches(os.listdir(os.path.join(src_dir, 'f90')), ['Mod3DMT'], ['.f90'])

        print("Found Executables: ", executables, f'Using Modset: {modset}')

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


            if modset is None:
                print("Attempting to extract modset from filename...")
                if (modset := extract_modset(exe)) == False:
                    result.result = 'FAILED'
                    result.msg = "Could not find `Modset:<Modset-Name>' in the executable"
                    return result.result

            if modset not in env.list_modsets():
                print(f"This modset ({modset}) is not in this enviorment, failing")
                result.result ='FAILED'
                result.msg = f"This modset ({modset}) is not in this enviorment, failing"
                return result.result

            print(f"Modset is: {modset}... Loading it!")
            env.load_modset(modset)

            if not mpi:
                if 'release' in exe:
                    exe_launch = modem_arguments
                elif 'mpi' in exe:
                    exe_launch = ['mpiexec', '-n', f'{self.ncpus}']
                    exe_launch.extend(modem_arguments)
                else:
                    result.result = 'FAILED'
                    result.msg = "Bad exe"
                    return result.result
            else:
                exe_launch = ['mpiexec', '-n', f'{self.ncpus}']
                exe_launch.extend(modem_arguments)

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
