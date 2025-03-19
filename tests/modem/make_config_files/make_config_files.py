import os
import shutil
import subprocess


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

        configurations = [['Configure.2D_MT.OSU.GFortran', 'release'],
                        ['Configure.3D_MT.MAC.GFortran', 'mpi', 'release'],
                        ['Configure.SP.MAC.GFortran', 'mpi', 'release'],
                        ['Configure.SP2.MAC.GFortran', 'mpi'],
                        ['Configure.3D_MT.HDF5.MAC.GFortran', 'mpi', 'release'],
                        ['Configure.SP2.HDF5.MAC.GFortran', 'mpi']]

        for configuration in configurations:
            config_name = configuration[0]
            versions = configuration[1:]
            config_exe = os.path.join(CONFIG_DIR, config_name)

            if not os.path.isfile(config_exe):
                result.result = "FAILED"
                result.msg = f"Configuration file {config_exe} did not exist!"
                return result.result

            for v in versions:
                makefile_name = config_name.replace('Configure', 'smarts.makefile')+'_'+v
                print(f'Creating configuration file: {config_exe} naming makefile: {makefile_name} {v}')
                log_filename = f'../../log.{makefile_name}'
                config_log = open(log_filename, 'w')

                print(f'Logging stdout and stderr to: {os.path.abspath(log_filename)}\n')
                try:
                    process = subprocess.run([config_exe, makefile_name, v], 
                                             stdout=config_log,
                                             stderr=config_log,
                                             check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Makefile {makefile_name} was not created for config {config_name} for {v} - see {os.path.abspath(log_filename)}"
                    return result.result


                if not os.path.isfile(makefile_name):
                    result.result = "FAILED"
                    result.msg = f"Makefile {makefile_name} was not created for config {config_name} for {v}"
                    return result.result

        result.result = "PASSED"
        result.msg = "Successfully created configuration files"
