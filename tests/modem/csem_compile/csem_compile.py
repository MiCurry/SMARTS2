import os
import shutil
import subprocess

config_files = {}

def get_makefiles():
    makefiles = []
    for f in os.listdir('./'):
        if 'csem' in f and 'smarts' in f and 'log' not in f and 'Mod3DMT' not in f:
            makefiles.append(f)

    return makefiles
    

class csem_compile:
    test_name = "Compile CSEM ModEM Test"
    test_description = "Compile all ModEM configuration "
    dependencies = ['csem_config']
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        gnu_modsets = env.list_modsets(name="GNU")
        if not gnu_modsets:
            result.result = "FAILED"
            result.msg = "This env file had no modests with the name 'GNU'"
            return result.result

        print("Number of gnu_modsets: ", gnu_modsets)

        if not os.path.isdir(os.path.join(src_dir, 'f90')):
            result.result = "FAILED"
            result.msg = f"{src_dir} does not appear to a ModEM source directory"
            return result.result

        # Change directory to copy of ModEM in the test directory
        #os.chdir(os.path.join('/Users/mcurry/scratch/smarts-runs/ModEM-Model', 'src'))
        os.chdir(os.path.join('../csem_config/ModEM-Model/src'))

        makefiles = get_makefiles()

        for makefile in makefiles:
            if 'ifort' in makefile:
                print(f"Skipping Intel - {makefile}")
                continue

            for modset in gnu_modsets:
                if not env.load_modset(modset):
                    result.result = "FAILED"
                    result.msg = "Could not load gnu modset {modset}"
                    return result.result

                log_filename=f'log.make.{modset}.{makefile}.out'
                log_file=open(log_filename, 'w')

                print(f"Compiling: '{makefile}' with  {modset} - logging into: '{os.path.abspath(log_filename)}'")
                shutil.copy2(makefile, 'Makefile')

                print("CWD: ", os.getcwd())

                print("Running 'make clean'...", end=' ')
                try:
                    ierr = subprocess.run(['make', 'clean'], stdout=log_file, stderr=log_file, check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Error when calling 'make clean' on {makefile} - error in: {os.path.abspath(log_filename)}"
                    return result.result
                print("'make clean' passed!")

                print("Removing .mod files...", end=' ')
                ierr = subprocess.run(['rm', '*.mod'], stdout=log_file, stderr=log_file)
                print("'rm *.mod' passed!")
                ierr = subprocess.run(['rm', '-r', 'objs/'])

                print("CWD: ", os.getcwd())


                print("Running make...", end=' ', flush=True)
                try:
                    ierr = subprocess.run(['make'], stdout=log_file, stderr=log_file, check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Error when calling 'make' on {makefile} - error in: {os.path.abspath(log_filename)}"
                    return result.result

                print("make passed!", flush=True)

                if '3D' in makefile:
                    modem_exe_default = 'Mod3DMT'
                    executable_name = f'Mod3DMT.{modset}'.replace('.makefile.', '.')
                elif '2D' in makefile:
                    modem_exe_default = 'Mod2DMT'
                    executable_name = f'Mod2DMT.{modset}'.replace('.makefile.', '.')
                else:
                    modem_exe_default = 'Mod3DMT'
                    executable_name = f'Mod3DMT.{modset}'.replace('.makefile.', '.')


                if not os.path.isfile(modem_exe_default):
                    result.result = "FAILED"
                    result.msg = f"Could not find the default executable: {modem_exe_default} for {makefile}"
                    return result.result


                shutil.move(modem_exe_default, executable_name)
                print(f"PASSED - Succesfully compiled {makefile} with {modset} - exe: {executable_name}\n")

                try:
                    ierr = subprocess.run(['make', 'clean'], stdout=log_file, stderr=log_file, check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Error when calling 'make clean' on {makefile} - error in: {os.path.abspath(log_filename)}"
                    return result.result

                ierr = subprocess.run(['rm', '*.mod'], stdout=log_file, stderr=log_file)
                ierr = subprocess.run(['rm', '-r', 'objs/'])



        result.result = "PASSED"
        result.msg = "Successfully compiled all ModEM Versions"
