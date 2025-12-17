import os
import shutil
import subprocess
import logging
import itertools

logger = logging.getLogger("modem_cmake_compile")

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

description = """

Compile 

"""

    
class modem_cmake_compile:
    test_name = "Compile ModEM CMake Test"
    test_description = "Compile all ModEM with CMake"
    dependencies = []
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        print('kwargs:', kwargs)
        force = kwargs.get('force', False)

        all_modsets = env.list_modsets()
        if not all_modsets:
            result.result = "FAILED"
            result.msg = "This env file had no modests!"
            logger.failed(f"{result.msg}")
            return result.result

        if not os.path.isdir(os.path.join(src_dir, 'f90')):
            result.result = "FAILED"
            result.msg = f"{src_dir} does not appear to a ModEM source directory"
            logger.failed(f"{result.msg}")
            return result.result

        cmake_base_cmd = ['cmake', '-S', f'{src_dir}', '-B' './']

        forward_flavors = ['MF', 'SP', 'SP2']
        mpi = ['ON', 'OFF']
        fg = ['ON', 'OFF']
        debug = ['ON', 'OFF']
        use_c_timers = ['ON', 'OFF']

        combos = list(itertools.product(forward_flavors, 
                                        mpi, 
                                        fg,
                                        #debug, 
                                        use_c_timers))

        for modset in all_modsets:
            env.load_modset(modset)

            modset_details = env.env['Modsets'][modset]
            modset_dir_name = modset_details['Name']+"_builds"

            os.mkdir(modset_dir_name)
            os.chdir(modset_dir_name)

            print(modset_details['Compiler']['Name'])
            if modset_details['Compiler']['Name'] in ['gnu', 'gfortran', 'GNU', 'GFortran']:
                base_compiler = 'gfortran'
            elif modset_details['Compiler']['Name'] in ['intel', 'ifort', 'INTEL', 'Ifort']:
                base_compiler = 'ifort'
            else:
                result.result = "FAILED"
                result.msg = f"{modset_details['Compiler']['Name']} compiler is not supported by ModEM CMake build"
                logger.failed(f"{result.msg}")
                return result.result


            for combo in combos:
                forward_flavor = combo[0]
                mpi = combo[1]
                fg = combo[2]
                # debug = combo[3] # Debug is currently not avaliable for CMake...
                use_c_timers = combo[3]

                if fg == 'ON' and forward_flavor != 'SP2':
                    continue

                if fg == 'ON' and forward_flavor == 'SP2' and 'MPI' == 'OFF':
                    continue


                if mpi == 'ON':
                    compiler_exe = 'mpifort'
                else:
                    compiler_exe = base_compiler

                cmake_run_args = [
                    f'-DFORWARD_FLAVOR={forward_flavor}',
                    f'-DBUILD_MPI={mpi}',
                    f'-DFG={fg}',
                    #f'-DDEBUG={debug}', # See note above
                    f'-DUSE_C_TIMERS={use_c_timers}',
                    f'-DCMAKE_Fortran_COMPILER={compiler_exe}'
                ]

                cmake_run_args = cmake_base_cmd + cmake_run_args
                build_dir_name = f'build.{forward_flavor}.mpi-{mpi}.fg-{fg}.use_c_timers-{use_c_timers}'
                os.mkdir(build_dir_name)
                os.chdir(build_dir_name)

                logger.info("")
                logger.info(f"Testing CMake build with arguments: {' '.join(cmake_run_args)} ")
                logger.info(f'Running in: {os.path.abspath(build_dir_name)}')

                log_fname = f'log.cmake-build.out'

                logger.sub_test('cmake', 'running cmake')

                with open(log_fname, 'w') as log_file:
                    try:
                        cmake_call = subprocess.run(cmake_run_args,
                                            check=True,
                                            stdout=log_file,
                                            stderr=log_file
                                            )
                    except Exception as e:
                        result.result = "FAILED"
                        result.msg = f"Cmake subprocess called failed. Error in: {os.path.abspath(log_fname)}"
                        logger.failed(result.msg)
                        return result.msg

                logger.passed("Able to call CMake successfully")

                log_fname = f'log.make.out'

                expected_exe_name = f'Mod3DMT_{forward_flavor}'
                expected_exe_path = os.path.join('f90', expected_exe_name)

                logger.sub_test('make', f'Call make on Makefile CMake generated... expecting: {expected_exe_name}')

                with open(log_fname, 'w') as log_file:
                    try:

                        make_call = subprocess.run('make',
                                                   check=True,
                                                   stdout=log_file,
                                                   stderr=log_file
                                                   )
                    except Exception as e:
                        result.result = "FAILED"
                        result.msg = f"Make subprocess called failed. Error in: {os.path.abspath(log_fname)}"
                        logger.failed(result.msg)
                        return result.msg

                if not os.path.isfile(expected_exe_path):
                    result.result = "FAILED"
                    result.msg = f"Make did not make the expected file: {expected_exe_path}"
                    logger.failed(result.msg)
                    return result.result

                logger.passed("MAKE called succesfful!")


                os.chdir('..')


            # Back out of this modset
            os.chdir('..')


        result.result = "PASSED"
        result.msg = "Successfully compiled all ModEM Versions"
