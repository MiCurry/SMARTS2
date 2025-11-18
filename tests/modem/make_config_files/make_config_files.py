import os
import shutil
import subprocess
import itertools

config_files = {}

class make_config_files:
    test_name = "ModEM Create Make files from Config Scripts"
    test_description = "Create configuration files for 2D/3D MF, SP, SP2"
    dependencies = None
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        
        if not os.path.isdir(os.path.join(src_dir, 'f90')):
            result.result = "FAILED"
            result.msg = f"{src_dir} does not appear to a ModEM source directory"
            return result.result

        # Copy the ModEM source into its own directory in the current run directory
        modem_src_copy = os.path.join('./', 'ModEM-Model')
        shutil.copytree(src_dir, modem_src_copy)

        if not os.path.isdir(modem_src_copy):
            result.result = "FAILED"
            result.msg = "ModEM source directory was not copied succesfully!"
            return result.result

        # Change directory to copy of ModEM in the test directory
        os.chdir(os.path.join(modem_src_copy, 'f90'))

        CONFIG_DIR = './CONFIG'

        compilers = ['gfortran', 'ifort']
        debug_level = ['Debug', 'Release']
        nprocs = ['Serial', 'MPI']
        fwd_solvers = ['MF', 'SP', 'SP2']

        combinations = list(itertools.product(compilers, debug_level, nprocs, fwd_solvers))

        csem_selection = 0

        config_exe = 'configure'

        for combo in combinations:
            compiler = combo[0]
            debug_or_release = combo[1]
            mpi_or_serial = combo[2]
            forward_type = combo[3]

            makefile_name = f"Makefile.modset:{compiler}.{debug_or_release}.{mpi_or_serial}.{forward_type}"

            config_exe_cmd = [config_exe, 
                              compiler,
                              makefile_name, 
                              debug_or_release, 
                              mpi_or_serial,
                              forward_type]

            print("")
            print(f"Testing configuration creation for {' '.join(config_exe_cmd)}")

            log_fname = f'log.{makefile_name}'
            log_file=open(log_fname, 'w')

            try:
                ierr = subprocess.run(config_exe_cmd, check=True, stdout=log_file, stderr=log_file)
                pass
            except subprocess.CalledProcessError as e:
                result.result = "FAILED"
                result.msg = f"Error when trying to create: {makefile_name}. Log in {os.path.abspath(log_fname)}"
                return result.result

            if not os.path.isfile(makefile_name):
                result.result = "FAILED"
                result.msg = f"Did not make the makefile: '{makefile_name}"
                return result.result

            print("PASSED - Able to create configuration file")
            
        result.result = "PASSED"
        result.msg = "Succsfully created all CSEM Makefiles"
        return result.result
