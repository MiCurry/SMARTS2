import os
import logging
import shutil
import subprocess

from smarts.utils.ModEM_Utils import do_modem_config


logger = logging.getLogger('fast_compile')
file_logger = logging.getLogger('compile_log')
    

class modem_fast_compile:
    test_name = "ModEM Fast Compile"
    test_description = '''Compile ModEM for MF/SP/SP2 Versions given specific arguments
                        Options: 
                            compiler = gfortran* | ifort
                            config = MF* | SP| SP2
                            mpi = True* | False
                            debug = Debug | Release*
                        '''
    dependencies = []
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        compiler = kwargs.get('compiler', 'gfortran')
        mpi = kwargs.get('mpi', 'True')
        config = kwargs.get('config', 'MF')
        debug = kwargs.get('debug', 'Release')

        file_handler = logging.FileHandler('./configure.log', mode='w')
        file_handler.setLevel(logging.INFO)
        file_logger.addHandler(file_handler)

        if compiler not in ['gfortran', 'ifort']:
            raise ValueError(f'{compiler} is not a valid compiler - please choose either: gfortran | ifort')

        if compiler == 'gfortran':
            modset = env.list_modsets('GNU')
        elif compiler == 'ifort':
            modset = env.list_modsets('INTEL')
            
        logger.info(f"Loading modset: {modset[0]}")
        env.load_modset(modset[0])

        if mpi in ['True', 'true', 't', 'T']:
            mpi = "MPI"
        elif mpi == ['False', 'false', 'f', 'F']:
            mpi = "Serial"
        else:
            raise ValueError(f'{mpi} is not a valid MPI chooice - choose either: True | False')

        if config not in ['MF', 'SP', 'SP2']:
            raise ValueError(f'{config} is not a valid ModEM version - choose from: MF | SP | SP2')

        if debug not in ['Debug', 'Release']:
            raise ValueError(f'{debug} is not a valid debug option - choose either: Release | Debug')

        makefile_name = f'Makefile.{compiler}.{mpi}.{config}'

        try:
            do_modem_config(file_logger,
                            src_dir,
                            compiler=compiler,
                            makefile_name=makefile_name,
                            debug_or_release=debug,
                            mpi_or_serial=mpi,
                            forward_type=config
                            )
        except subprocess.CalledProcessError as e:
            result.result = "FAILED"
            result.msg = f"Error when calling configure"
            return result.result

        logger.passed("Makefile was created succsfully!")

        file_handler = logging.FileHandler('./out.make.log', mode='w')
        file_handler.setLevel(logging.INFO)
        file_logger.addHandler(file_handler)

        logger.info("Calling make clean (not doing)")
        try:
            process = subprocess.run(['make', '-f', makefile_name, 'clean'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    check=True)
        except subprocess.CalledProcessError as e:
            pass
            #result.result = "FAILED"
            #result.msg = f"Error when calling 'make clean' on {makefile_name} - error in: {os.path.abspath('./out.make.log')}"
            #return result.result

        logger.passed("Make clean was called succesfully")
        file_logger.info(process.stdout.decode('utf-8'))


        logger.info(f"Calling make -f {makefile_name}")
        try:
            process = subprocess.run(['make', '-f', makefile_name],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  check=True)
        except subprocess.CalledProcessError as e:
            file_logger.info(process.stdout.decode('utf-8'))
            result.result = "FAILED"
            result.msg = f"Error when calling 'make' on {makefile_name} - error in: {os.path.abspath('./out.make.log')}"
            return result.result

        file_logger.info(process.stdout.decode('utf-8'))
        logger.passed("ModEM Compiled succsfully")

        

        result.result = "PASSED"
        result.msg = "Successfully compiled all ModEM Versions"
