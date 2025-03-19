import os
import shutil
import subprocess

config_files = {}

def get_makefiles():
    makefiles = []
    for f in os.listdir('./'):
        if 'smarts' in f:
            makefiles.append(f)

    return makefiles
    

class inverse_mf:
    test_name = "Matrix-Free Inverse Test"
    test_description = "Test inverse for all compiled versions of 3D Matrix Free"
    dependencies = ['modem_compile', 'forward_mf']
    ncpus = 4

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
        os.chdir(os.path.join('../make_config_files/ModEM-Model', 'f90'))

        makefiles = get_makefiles()

        for makefile in makefiles:
            if 'HDF5' in makefile:
                print(f"Skipping HDF5 - {makefile}")
                continue

            for modset in gnu_modsets:
                if not env.load_modset(modset):
                    result.result = "FAILED"
                    result.msg = "Could not load gnu modset {modset}"
                    return result.result

                log_filename=f'../../log.make.{modset}.{makefile}.out'
                log_file=open(log_filename, 'w')

                print(f"Compiling: '{makefile}' with  {modset} - logging into: '{log_filename}'")
                shutil.copyfile(makefile, 'Makefile')
                
                try:
                    ierr = subprocess.run(['make', 'clean'], stdout=log_file, stderr=log_file, check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Error when calling 'make clean' on {makefile} - error in: {os.path.absPath(log_filename)}"
                    return result.result

                try:
                    ierr = subprocess.run(['make'], stdout=log_file, stderr=log_file, check=True)
                except subprocess.CalledProcessError as e:
                    result.result = "FAILED"
                    result.msg = f"Error when calling 'make' on {makefile} - error in: {os.path.absPath(log_filename)}"
                    return result.result



        result.result = "PASSED"
        result.msg = "Successfully created configuration files"
