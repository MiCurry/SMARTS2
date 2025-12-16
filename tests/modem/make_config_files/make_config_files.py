import os
import shutil
import subprocess
import itertools

import logging
logger = logging.getLogger("make_config_files")

config_files = {}


description = """

Create configuration files for 3D ModEM. Does complete combinations with:

- Solver Type: MF/SP/SP2
- Compiler: gfortran/ifort
- MPI: MPI/serial
- Debug: debug/release
- Spherical and Non-Spherical Models 

Generates a **ton** of makefiles, which modem_compile can parse and load the
appropriate modset for.

"""

class make_config_files:
    test_name = "ModEM Create Make files from Configure script"
    test_description = description
    dependencies = ['configure_test']
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

        compilers = ['gfortran', 'ifort']
        debug_level = ['Debug', 'Release']
        nprocs = ['Serial', 'MPI']
        fwd_solvers = ['MF', 'SP', 'SP2']
        spherical = [True, False]

        combinations = list(itertools.product(compilers, debug_level, nprocs, fwd_solvers, spherical))

        config_exe = os.path.join('./configure')

        for combo in combinations:
            compiler = combo[0]
            debug_or_release = combo[1]
            mpi_or_serial = combo[2]
            forward_type = combo[3]
            spherical = combo[4]

            config_exe_cmd = [config_exe,
                              f'-g {debug_or_release}',
                              f'-m {mpi_or_serial}',
                              f'-l {forward_type}']

            if spherical == True:
                config_exe_cmd.append(f'-s')

            if spherical == True:
                makefile_name = f"Makefile.modset:{compiler}.{debug_or_release}.{mpi_or_serial}.spherical.{forward_type}"
            else:
                makefile_name = f"Makefile.modset:{compiler}.{debug_or_release}.{mpi_or_serial}.{forward_type}"

            config_exe_cmd.append(makefile_name)
            config_exe_cmd.append(compiler)

            logger.info("")
            logger.info(f"Testing configuration creation for {' '.join(config_exe_cmd)}")

            log_fname = f'log.{makefile_name}'
            log_file=open(log_fname, 'w')

            try:
                ierr = subprocess.run(config_exe_cmd,
                                      check=True,
                                      stdout=log_file,
                                      stderr=log_file,
                                      input='y'.encode('utf-8'))
                pass
            except subprocess.CalledProcessError as e:
                result.result = "FAILED"
                result.msg = f"Error when trying to create: {makefile_name}. Log in {os.path.abspath(log_fname)}"
                return result.result

            if not os.path.isfile(makefile_name):
                result.result = "FAILED"
                result.msg = f"Did not make the makefile: '{makefile_name}"
                return result.result

            logger.passed("Able to create configuration file")
            
        result.result = "PASSED"
        result.msg = "Succsfully created all CSEM Makefiles"
        return result.result
