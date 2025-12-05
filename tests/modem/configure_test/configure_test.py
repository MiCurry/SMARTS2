import os
import shutil
import subprocess
import itertools

import logging
logger = logging.getLogger("configure_test")

config_files = {}

description = """ Configure Test - Check edge cases for configuration files

    This test just checks the edge error cases with the configuration tool.
    
    Also see `make_config_files`.
"""

class configure_test:
    test_name = "Configure Test"
    test_description = description
    dependencies = None
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        self.result = result
        if not os.path.isdir(os.path.join(src_dir, 'f90')):
            result.result = "FAILED"
            result.msg = f"{src_dir} does not appear to a ModEM source directory"
            return result.result

        # Copy the ModEM source into its own directory in the current run directory
        modem_src_copy = os.path.join('./', 'ModEM-Model')
        shutil.copytree(src_dir, modem_src_copy)

        self.log_fname = 'out.configure.log'
        self.log_file = open(self.log_fname, 'w')

        if not os.path.isdir(modem_src_copy):
            result.result = "FAILED"
            result.msg = "ModEM source directory was not copied succesfully!"
            return result.result

        # Change directory to copy of ModEM in the test directory
        os.chdir(os.path.join(modem_src_copy, 'f90'))

        CONFIG_DIR = './CONFIG'
        self.config_exe = os.path.join('./CONFIG', 'configure')

        logger.info("")

        if not self.test_no_makefile_name():
            return self.result.result

        logger.info("")

        if not self.test_compiler_options():
            return self.result.result

        logger.info("")

        if not self.test_debug_options():
            return self.result.result

        logger.info("")

        if not self.test_mpi_options():
            return self.result.result

        logger.info("")

        if not self.test_solver_options():
            return self.result.result

        logger.info("")

        if not self.test_spherical_option():
            return self.result.result

        logger.info("")

        if not self.test_fg_option():
            return self.result.result

        logger.info("")

        #Usage: ./CONFIG/Configure [-h] [-u] [-g release|debug] [-m mpi|serial] [-l solver] [-f] makefile-name compiler
            
        result.result = "PASSED"
        result.msg = "Succsfully Completed All Configuration Tests"
        logger.passed(f"{result.msg}")
        return result.result

    def test_no_makefile_name(self):
        logger.sub_test('test_no_makefile_name', "Test if not passing a makefile returns an error")

        test_cmd = [self.config_exe]

        was_error = False

        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            was_error = True

        if not was_error:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to "
            logger.failed(f"{self.result.msg}")
            return False

        self.result.msg = "Error created succsefully when makefile name was not present"
        self.result.result = "PASSED"
        logger.passed(f"test_no_makefile_name - PASSED {self.result.msg}")
        return True

    def test_compiler_options(self):
        logger.sub_test('test_compiler_options', "Test compiler options < gfortran | ifort | error >")

        """ Test gfortran compiler """

        logger.sub_test('test_compiler_options.gfortran', "Works with gfortran options?")
        test_cmd = [self.config_exe, 'Makefile.test', 'gfortran']
        was_error = False
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'gfortran' compiler name"
            logger.failed(f"{self.result.msg}")
            return False

        self.result.msg = "Works with 'gfortran' compiler options"
        self.result.result = "PASSED"
        logger.passed(f"test_no_makefile_name.gfortran - {self.result.msg}")

        """ Test ifort compiler """

        logger.sub_test('test_compiler_options.intel', "Works with intel options?")
        test_cmd = [self.config_exe, 'Makefile.test', 'intel']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'gfortran' compiler name"
            logger.failed(f"{self.result.msg}")
            return False

        self.result.msg = "Works with 'ifort' compiler options"
        self.result.result = "PASSED"
        logger.passed(f"test_compiler_options.ifort- {self.result.msg}")

        """ Test unkonwn/unsupported compiler """

        logger.sub_test('test_compiler_options.unkown', "Fails with an unkown compiler?")
        test_cmd = [self.config_exe, 'Makefile.test', 'foobar']
        was_error = False
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            was_error = True

        if not was_error:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to produce error when passing in a uknown compiler"
            logger.failed(f"{self.result.msg}")
            return False

        self.result.msg = "Error generated succesfully with unkown compiler"
        self.result.result = "PASSED"
        logger.passed(f"test_compiler_options.unkown - {self.result.msg}")

        self.result.msg = "test_compiler_options - all tests PASSED!"
        self.result.result = "PASSED"
        logger.passed(self.result.msg)

        return True

    def test_debug_options(self):
        logger.sub_test('test_debug_options', "Test debug options < debug | serial | error >")

        """ Test debug option """
        test_cmd = [self.config_exe, '-g', 'debug', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'debug' option name"
            logger.failed(f"{self.result.msg}")
            return False

        test_cmd = [self.config_exe, '-g', 'release', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'release' option name"
            logger.failed(f"{self.result.msg}")
            return False

        test_cmd = [self.config_exe, '-g', 'foobar', 'makefile.test', 'gfortran']
        was_error = False
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            was_error=True

        if not was_error:
            self.result.result = "failed"
            self.result.msg = f"failed create error with unkown debug options"
            logger.failed(f"{self.result.msg}")
            return False

        self.result.msg = "All debug options test passed"
        self.result.result = "PASSED"
        logger.passed(f"test_debug_options - {self.result.msg}")
        return True

    def test_mpi_options(self):
        logger.sub_test('test_mpi_options', "Test mpi options < mpi | serial | error >")

        """ Test mpi option """
        test_cmd = [self.config_exe, '-m', 'mpi', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'mpi' option name"
            logger.failed(f"{self.result.msg}")
            return False

        test_cmd = [self.config_exe, '-m', 'serial', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'serial' option name"
            logger.failed(f"{self.result.msg}")
            return False

        test_cmd = [self.config_exe, '-m', 'foobar', 'makefile.test', 'gfortran']
        was_error = False
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            was_error=True

        if not was_error:
            self.result.result = "Failed"
            self.result.msg = f"Failed create error with unkown mpi options"
            logger.failed(f"{self.result.msg}")
            return False
        
        logger.passed(f"test_mpi_options - {self.result.msg}")
        return True

    def test_solver_options(self):
        logger.sub_test('test_solver_options', "Test solver options < mf | sp | sp2 | error >")

        """ Test mf option """
        test_cmd = [self.config_exe, '-l', 'mf', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'mf' option name"
            logger.failed(f"{self.result.msg}")
            return False 

        """ Test sp option """
        test_cmd = [self.config_exe, '-l', 'sp', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'sp' option name"
            logger.failed(f"{self.result.msg}")
            return False 

        """ Test sp2 option """
        test_cmd = [self.config_exe, '-l', 'sp2', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with 'sp2' option name"
            logger.failed(f"{self.result.msg}")
            return False 

        test_cmd = [self.config_exe, '-l', 'foobar', 'makefile.test', 'gfortran']
        was_error = False
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            was_error=True

        if not was_error:
            self.result.result = "Failed"
            self.result.msg = f"Failed create error with unkown solver options"
            logger.failed(f"{self.result.msg}")
            return False

        logger.passed(f"test_solver_options - {self.result.msg}")
        return True

    def test_spherical_option(self):
        logger.sub_test('test_spherical_options', "Test spherical options < -s >")

        """ Test mf option """
        test_cmd = [self.config_exe, '-s', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd,
                                  input='y'.encode('utf-8'),
                                  stdout=self.log_file,
                                  stderr=self.log_file,
                                  check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with '-s' option"
            logger.failed(f"{self.result.msg}")
            return False 

        warning_message = [ 
            "WARNING - You are making a Makefile for the spherical version of ModEM ('-s')!",
            "WARNING - The spherical version of ModEM is NOT YET fully tested/validated",
            "WARNING - and we cannot gaurentee correct results."]

        with open(os.path.join('..', '..', self.log_fname), 'r') as file:
            contents = file.read()

            for message in warning_message:
                if message not in contents:
                    self.result.result = "FAILED"
                    self.result.msg = f"The spherical warning message {message} was not outputed in {self.log_fname}"
                    logger.failed(f"{self.result.msg}")
                    return False


        logger.sub_test("test passing n for spherical build", "Test exit if passed 'n' for spherical build")
        was_error = False
        try:
            ierr = subprocess.run(test_cmd,
                                  input='n'.encode('utf-8'),
                                  stdout=self.log_file,
                                  stderr=self.log_file,
                                  check=True)
        except subprocess.CalledProcessError as e:
            was_error = True

        if not was_error:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to exit when NOT given a (Yes/yes/y/Y)"
            logger.failed(f"{self.result.msg}")
            return False 

        logger.passed("test_spherical_options - Passed!")
        return True

    def test_fg_option(self):
        logger.sub_test('test_fg_options', "Test fg options < -f >")

        """ Test fg option with default """
        test_cmd = [self.config_exe, '-f', 'Makefile.test', 'gfortran']
        try:
            ierr = subprocess.run(test_cmd, stdout=self.log_file, stderr=self.log_file, check=True)
        except subprocess.CalledProcessError as e:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to work with '-f' option"
            logger.failed(f"{self.result.msg}")
            return False 

        """ Test fg option with MF """
        test_cmd = [self.config_exe, '-s', 'mf', '-f', 'Makefile.test', 'gfortran']
        was_error = False
        try:
            ierr = subprocess.run(test_cmd,
                                  input='y'.encode('utf-8'),
                                  stdout=self.log_file,
                                  stderr=self.log_file,
                                  check=True)
        except subprocess.CalledProcessError as e:
            was_error = True

        was_dfg_in_makefile = False
        with open('Makefile.test', 'r') as file:
            for line in file:
                if '-DFG' in line:
                    was_dfg_in_makefile = True

        if was_dfg_in_makefile == False:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to add in -DFG with 'SP2' option with '-f' option"
            logger.failed(f"{self.result.msg}")
            return False

        if not was_error:
            self.result.result = "FAILED"
            self.result.msg = f"Failed to get an error with '-f' and 'mf' option"
            logger.failed(f"{self.result.msg}")
            return False 
        

        logger.passed("test_fg_grained_options - Passed!")
        return True

