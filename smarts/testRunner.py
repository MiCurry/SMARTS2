""" SMARTs Test Runner - With Test Manager and Test Scheduler """
import os
import string
import sys
import datetime

from importlib import import_module
from multiprocessing import Process
from multiprocessing.managers import BaseManager, NamespaceProxy

NOT_IMPLEMENTED_ERROR = "IS NOT YET IMPLEMENTED"

INITIALIZED = "INITIALIZED"
SCHEDULED = "SCHEDULED"
UNSCHEDULED = "UNSCHEDULED"
RUNNING = "RUNNING"
FINISHED = "FINISHED"
JOINED = "JOINED"
ERROR = "ERROR" 

class TestBaseClass:
    # This might not be necessary!
    def __init__(self):
        pass


class TestRunner:
    def __init__(self, env, testDir, srcDir, *args, **kwargs):
        # The test directory is the directory that holds each test's implementation , not where
        # they are ran.
        self.env = env
        self.testDir= testDir
        self.srcDir = srcDir
        _debug_ = 0

        # Based on if the env we have is an HPC or not, initalize the HPC
        if env.hpc == True:
            # Initalize HPC
            raise NotImplementedError("HPC COMPATABLITY IS NOT YET IMPLEMENTED")
            pass
        else:
            self.hpc = None

        # At a Python's program startup, sys.path is set to PYTHONPATH (and not 
        # the normal PATH variable). Similar to the PATH environment, it is the locations
        # Python will search for importing Python modules.
        # To find the user created tests, append it to the front.
        if _debug_ > 0:
            print("TestRunner: Test directory is: ", self.testDir)

        sys.path.insert(0, self.testDir)

        self.manager = TestManager(self.testDir)
        self.scheduler = TestScheduler(self, self.testDir, self.srcDir, *args, **kwargs)

    def list_tests(self, *args, **kwargs):
        # List all tests
        return self.manager.list_tests()

    def list_test(self, tests, *args, **kwargs):
        # List a single test
        print("List test!")
        return self.manager.list_test(tests)

    def run_tests(self, tests, env, *args, **kwargs):
        self.scheduler.run_tests(tests)


class TestManager:
    def __init__(self, test_directory, *args, **kwargs):
        self.test_directory = test_directory

    def list_tests(self, *args, **kwargs):
        # Return a list all the valid and invalid tests
        verbose = kwargs.get('verbose', 0)

        if verbose > 0:
            print("TestManager: list_tests() - Listing tests found in:", self.test_directory)

        valid_tests = []
        invalid_tests = []
        for tests in os.listdir(self.test_directory):
            if os.path.isdir(os.path.join(self.test_directory, tests)):

                testFile = os.path.join(tests, tests).replace('/', '.')
                runName = testFile

                # Translate the directory path into what Python wants for its import_module command
                if '.' in runName:
                    runName = testFile.split('.')[0]

                try:
                    mod = import_module(testFile)
                    try:
                        test = getattr(mod, tests)
                        valid_tests.append([runName, test.test_name])
                    except:
                        invalid_tests.append([runName, "Could not load this test's attributes"])
                except Exception as e:
                    invalid_tests.append([testFile, e])

        return valid_tests, invalid_tests

    def list_test_suites(self, **kwargs):
        # List all of the available test-suites
        raise NotImplementedError("TestManager.list_test_suites "+NOT_IMPLEMENTED_ERROR)

    def list_test(self, tests, **kwargs):
        # Return the information about a single test or test-suite as a (dictionary or object?)
        raise NotImplementedError("TestManager.list_test "+NOT_IMPLEMENTED_ERROR)

    def check_test(self, test, **kwargs):
        # Check to see if the test suite and test name are on the system
        raise NotImplementedError("TestManager.check_test"+NOT_IMPLEMENTED_ERROR)


""" Class TestSubProcess - Wrapper for individual tests

"""
class TestSubProcess(Process):
    """ Wrapper around tests which will enable them to be launched as subprocess """
    def __init__(self, test_launch_name, test,
                                         env,
                                         srcDir,
                                         testDir,
                                         hpc,
                                         *args, **kwargs):
        Process.__init__(self) # We can pass in arguments here ??
        self.test = test
        self.test_launch_name = test_launch_name
        self.srcDir = os.path.abspath(srcDir)
        self.testDir = os.path.abspath(testDir)
        self.env = env
        self.hpc = hpc
        self.args = args
        self.kwargs = kwargs
        self.status = INITIALIZED
    
    def run(self):
        print("DEBUG: Creating directory for:", self.test_launch_name)
        os.mkdir(self.test_launch_name)

        if not os.path.isdir(self.test_launch_name):
            print("ERROR: Can not find directory: ", self.test_launch_name)
            sys.exit(-1)

        os.chdir(self.test_launch_name)
        self.status = RUNNING
        self.test.run(self.env, self.srcDir, self.testDir, hpc=self.hpc)
        self.status = FINISHED
        return

    def isInitialized(self):
        pass

    def isRunning(self):
        # TODO: Make this use self.is_alive()
        if self.status == RUNNING:
            return True
        else:
            return False

    def isFinished(self):
        if self.exitcode != None:
            return True
        else:
            False

    def isJoined(self):
        pass

    def isScheduled(self):
        if self.status == SCHEDULED:
            return True
        else:
            return False

    def getTestResults(self):
        pass




""" """
class TestProxy(NamespaceProxy):
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__', 'run')

    def run(self, env, srcDir, testDir, hpc=None):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('run', (env, srcDir, testDir,), {'hpc' : hpc})


""" """
class TestScheduler:

    def __init__(self, testRunner, testDir, srcDir, *args, **kwargs):
        self.manager = testRunner.manager
        self.env = testRunner.env
        print("Environment is: ", self.env)
        self.ncpus = testRunner.env.ncpus
        self.testDir = testDir
        self.srcDir = srcDir

    def _setup_tests(): # Possible function to set up test to take stuff out of run tests
        pass
       

    def _create_run_directory(self):
        # If all tests are able to be ran, then create the test directory
        # smarts.year-mm-dd_hh.mm.ss
        run_directory = 'run-smarts-'
        now = datetime.datetime.now()
        run_directory += now.strftime('%Y-%m-%d-%H.%M.%S')
        os.mkdir(run_directory)
        if not os.path.isdir(run_directory):
            print("ERROR: Could not create run_directory: ", run_directory)
            return False

        return run_directory
        
    def _get_depends_status(self, test, loaded_tests):
        # TODO: Perhaps change this name ?? (get_depends_status(...) 
        # TODO: See if this returns the correct amount of bools
        # TODO: Need to explore what happens when a dependency fails, and how to communicate that
        # to each tests.
        # Return a list of booleans that corrospond test's dependencies status (currently either
        # joined or not)
        dependency_status = []

        if hasattr(test.test, 'dependencies'):
            if test.test.dependencies == None:
                return [True]
            else: # If this test has dependencies
                for dependency in test.test.dependencies:
                    # Check to see if the dependency is running or not
                    for tests in loaded_tests:
                        test_name = tests.test.__class__.__name__
                        if test_name == dependency:
                            if tests.status != JOINED:
                                dependency_status.append(False)
                            else:
                                dependency_status.append(True)
        else:
            return [True]

        return dependency_status


    def _update_dependencies(self, test, loaded_tests):
        # If test has dependencies, then update them with its results
        test_name = test.test_launch_name

        print("DEBUG: Updating the dependencies for ", test_name, dir(test.test))

        if test.test.status == "FAILED":
            for t in loaded_tests:
                if test_name in t.test.dependencies:
                    test.status = UNSCHEDULED
                    print(test.test.test_name, " set to UNSCHEDULED")


    def run_tests(self, tests, *args, **kwargs):
        """ 

        """
        num_tests = len(tests)
        finished = 0
        avaliable_cpus = self.ncpus
        self.hpc = None
        run = True
        requested_test_names = tests


        """ Check to see if all the tests are valid tests """
        avaliable_tests, invalid_tests = self.manager.list_tests()
        launch_names = [t[0] for t in avaliable_tests]
        test_names = [t[1] for t in avaliable_tests]

        for test in tests:
            if test not in launch_names and test not in test_names:
                print("ERROR: '", test, "' is not a valid test! Quitting!", sep="")
                sys.exit(-1)


        """ Import and initialize each test - Exit if any Test requested is fails to be 
        initialized """
        loaded_tests = []
        for test_launch_name in tests:
            # TODO: Try except here
            module = import_module(test_launch_name+'.'+test_launch_name)
            test = getattr(module, test_launch_name) # get the test from the module
            #test = test() # Initialize the test

            """ Test Shared Object (SO) Server """
            class TestSOServer(BaseManager): pass

            TestSOServer.register('test', test, TestProxy)
            testSOManager = TestSOServer()
            testSOManager.start()

            item = testSOManager.test()
            testProcess = TestSubProcess(test_launch_name, 
                                         testSOManager.test(),
                                         self.env,
                                         self.srcDir,
                                         self.testDir,
                                         self.hpc)
            testProcess.status = INITIALIZED
            loaded_tests.append(testProcess)


        """ Check to see if this tests dependencies (if it has any) are scheduled to run """
        for test in loaded_tests:
            if hasattr(test.test, 'dependencies'):
                if not test.test.dependencies: # test.test.dependencies == None
                    continue

                for dep in test.test.dependencies:
                    if dep not in requested_test_names:
                        print("ERROR: The dependency '", dep, "' was not requested to run!", sep="")
                        print("ERROR: Please specify it to run!")
                        sys.exit(-1)
                    else:
                        continue
            else:
                continue


        """ Check to see if this test does not require more resources then whats available """
        for test in loaded_tests:
            if test.test.nCPUs > avaliable_cpus:
                print("ERROR: The test '", test.test.test_name, " requires more cpus the available!", sep='')
                print("ERROR: The machine: '", self.env.name, "' has ", avaliable_cpus, " cpus available", sep='')
                print("ERROR: And '", test.test.test_name, "' requested: ", test.test.nCPUs, sep='')
                sys.exit(-1)


        """ If tests pass all the checks above, then set its status to SCHEDULED """
        for test in loaded_tests:
            test.status = SCHEDULED

        
        """ Since all tests pass the above checks, create the run directory and change to that
        directory  """
        self.run_directory = self._create_run_directory()
        if not self.run_directory:
            print("ERROR: There was a problem creating the run directory!")
            sys.exit(-1)
        os.chdir(self.run_directory)


        ################
        # Test Scheduler - TODO: Maybe have this in a new function TestScheduler.scheduler(..) ?
        ################
        """ Test Scheduler

        """
        while ( run ):
            """ Start tests 
            If we have enough CPUs, and the test is scheduled and its dependencies have all run,
            then start it
            """
            for test in loaded_tests:
                if (test.test.nCPUs <= avaliable_cpus and test.isScheduled()):
                    # Check dependencies
                    if all(self._get_depends_status(test, loaded_tests)):
                        print("DEBUG: trying to start: ", test.test.test_name, test.status)
                        avaliable_cpus -= test.test.nCPUs
                        test.start() # TODO: Try Accept here ??
                        test.status = RUNNING
                        print("DEBUG: ", test.test.test_name, test.status, "has started!\n")


            """ Join tests """
            for test in loaded_tests:
                if test.isRunning():
                    if test.isFinished():
                        test.join(.01)
                        test.status = JOINED
                        avaliable_cpus += test.test.nCPUs
                        print("DEBUG: Joined with ", test.test.test_name, "!")

                        results = test.getTestResults()

                        # See if this test fails or not. If it fails, then update any tests that have
                        # it as a dependency as UNSCHEDULED
                        print("DEBUG: Tests status: ", test.test.status)
                        self._update_dependencies(test, loaded_tests)

                        """ Report tests results here """
                        # reporter.report(test, results)

            """ Determine if we are finished running tests or not 
            We have finished running tests when there is no more tests marked as either RUNNING or
            as SCHEDULED. """
            running = [True for test in loaded_tests if test.status == RUNNING]
            scheduled = [True for test in loaded_tests if test.status == SCHEDULED]

            if any(running) or any(scheduled):
                continue
            else:
                print("DEBUG: All tests are completed - Exiting the scheduler!")
                run = False

        return
