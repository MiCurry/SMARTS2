import os
import sys
import shutil
import subprocess
import itertools

from smarts.utils import utils

MODSET_NAME = 'GNU-MPICH'

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

class csem_config:
    test_name = "CSEM Makefile Creation"
    test_description = "Create a whole lotta CSEM makefiles"
    dependencies = None
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        if not os.path.isdir(os.path.join(src_dir, 'src', 'CONFIG')):
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

        os.chdir('./ModEM-Model/src')

        config_fname = "./CONFIG/Configure"

        if not os.path.isfile( os.path.join(config_fname)):
            result.result = "FAILED"
            result.msg = f"Could not find configuration file: {config_fname}"
            return result.result

        compilers = ['gfortran', 'ifort']
        debug_level = ['Debug', 'Release']
        nprocs = ['Serial', 'MPI']
        fwd_solvers = ['MF', 'SP', 'SP2']
        method = ['MT', 'MT+CSEM']
        CSEM_version = ['Dipole1D', 'EM1D', 'Dipole1D+EM1D']

        combinations = list(itertools.product(compilers, debug_level, nprocs, fwd_solvers, method))

        csem_selection = 0

        # Load a GNU modset, as we need the location to the FFTW variable
        env.load_modset("GNU-MPICH")

        for combo in combinations:

            compiler = combo[0]
            debug_or_release = combo[1]
            mpi_or_serial = combo[2]
            forward_type = combo[3]
            mt_or_csem = combo[4]

            if mt_or_csem == "MT+CSEM":
                csem_type = CSEM_version[csem_selection]
                csem_selection += 1
                if csem_selection == len(CSEM_version):
                    csem_selection = 0
            else:
                csem_type = ""

            makefile_name = "Makefile." + ".".join(combo) + '.' + 'smarts' + '.' + 'csem' + '.' + csem_type

            config_exe_cmd = [config_fname, 
                              compiler,
                              makefile_name, 
                              debug_or_release, 
                              mpi_or_serial,
                              forward_type,
                              mt_or_csem,
                              csem_type]

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
