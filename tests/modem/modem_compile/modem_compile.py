import os
import shutil
import subprocess

from smarts.utils import utils

config_files = {}

def get_makefiles():
    makefiles = []
    for f in os.listdir('./'):
        if 'smarts' in f:
            makefiles.append(f)

    return makefiles

def extract_modset(executable: str) -> str:
    executable = executable.lower()
    split = executable.split('.')

    for itm in split:
        if 'modset' in itm:
            return itm.split(':')[1]

    return False
    
class modem_compile:
    test_name = "Compile ModEM Test"
    test_description = "Compile all ModEM configurations (Except HDF5)"
    dependencies = ['make_config_files']
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):

        gnu_modsets = env.list_modsets(name="GNU")
        if not gnu_modsets:
            result.result = "FAILED"
            result.msg = "This env file had no modests with the name 'GNU'"
            return result.result

        if not os.path.isdir(os.path.join(src_dir, 'f90')):
            result.result = "FAILED"
            result.msg = f"{src_dir} does not appear to a ModEM source directory"
            return result.result

        # Change directory to copy of ModEM in the test directory
        os.chdir(os.path.join('..', 'make_config_files', './ModEM-Model', 'f90'))
        makefiles = utils.all_matches(os.listdir('.'), ['Makefile', 'modset'], ['.f90', 'log'])
        print(os.listdir('.'))

        print(f"Makefiles: ", makefiles)

        if len(makefiles) == 0:
            result.result = "FAILED"
            result.msg = "Found no makefile!"
            return result.result

        for makefile in makefiles:
            if 'HDF5' in makefile:
                print(f"Skipping HDF5 - {makefile}")
                continue

            modset = extract_modset(makefile)

            print(f"Testing makefile: '{makefile}'...")

            if 'gfortran' in modset:
                modset_name = 'GNU'
            elif 'ifort' in modset:
                modset_name = 'INTEL'


            modsets = env.list_modsets(name=modset_name)

            if modsets is None:
                print(f"Modset '{modset_name}' is not on this enviorment. Skipping this makefile")
                continue

            print(modsets)

            for modset in modsets:
                print(f"Loading modset: {modset}")
                if not env.load_modset(modset):
                    result.result = "FAILED"
                    result.msg = "Could not load gnu modset {modset}"
                    return result.result

                log_filename=f'../../log.make.{modset}.{makefile}.out'
                log_file=open(log_filename, 'w')

                print(f"Compiling: '{makefile}' with  {modset} - logging into: '{os.path.abspath(log_filename)}'")
                shutil.copy2(makefile, 'Makefile')
                
                try:
                    ierr = subprocess.run(['make', 'clean'], stdout=log_file, stderr=log_file, check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Error when calling 'make clean' on {makefile} - error in: {os.path.abspath(log_filename)}"
                    return result.result

                try:
                    ierr = subprocess.run(['make'], stdout=log_file, stderr=log_file, check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Error when calling 'make' on {makefile} - error in: {os.path.abspath(log_filename)}"
                    return result.result

                if '3D' in makefile:
                    modem_exe_default = 'Mod3DMT'
                    executable_name = f'Mod3DMT.Modset:{modset}.{makefile}'.replace('.makefile.', '.')
                elif '2D' in makefile:
                    modem_exe_default = 'Mod2DMT'
                    executable_name = f'Mod2DMT.Modset:{modset}.{makefile}'.replace('.makefile.', '.')
                else:
                    modem_exe_default = 'Mod3DMT'
                    executable_name = f'Mod3DMT.Modset:{modset}.{makefile}'.replace('.makefile.', '.')

                if not os.path.isfile(modem_exe_default):
                    result.result = "FAILED"
                    result.msg = f"Could not find the default executable: {modem_exe_default} for {makefile}"
                    return result.result

                shutil.move(modem_exe_default, executable_name)
                print(f"PASSED - Succesfully compiled {makefile} with {modset} - exe: {executable_name}\n")


        result.result = "PASSED"
        result.msg = "Successfully compiled all ModEM Versions"
