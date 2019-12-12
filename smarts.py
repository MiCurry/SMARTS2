""" SMARTs Command Line Runner """

from __future__ import absolute_import, division, print_function
import os
import sys
import argparse
from smarts.env import Environment
from smarts.testRunner import TestRunner



def print_tests(test_directory, valid_tests, invalid_tests):
    # SMARTS Command Line API print tests function - Print the list of valid 
    # and invalid lists to the tests
    print("Tests found in: ", test_directory, ":", sep='')

    if len(valid_tests) > 0:
        print("Valid tests:")
        for tests in valid_tests:
            print("  -", tests[0], "--", tests[1])

    print()
    
    if len(invalid_tests) > 0:
        print("Invalid tests: (These tests were not able to be loaded)")
        for tests in invalid_tests:
            print("  x", tests[0], "--", tests[1])
        print()
    elif len(valid_tests) == 0 and len(invalid_tests) == 0:
        print("ERROR: No tests found in this directory!")
        print("ERROR: Was the right test directory given or were the")
        print("ERROR: tests created correctly?")
        return -1

    return 0

def print_modsets(modsets, envName):
    # SMARTS Command Line API print modset function - Print the list of modsets
    # found in the enviornment.yaml file
    print("Avaliable Modsets on:", envName)
    for mods in modsets:
        print('-', mods['name'], '\t', mods['compiler']['version'])


def print_test_info(tests):
    # SMARTS Command Line API print test info - Print the infromation of
    # a specific tests
    pass


def setup_smarts(envFile=None, testDir=None, srcDir=None):
    # Helper function to Initalize SMARTs classes, specifically the
    # TestRunner, and the Environment class. If any of the files specified above
    # do not exists or can't be found, the program will fail

    if not os.path.isfile(envFile):
        print("ERROR: The environment.yaml file does not exist!")
        print("ERROR: Was it specified correctly?")
        print("ERROR: ", envFile)
        sys.exit(-1)
    if not os.path.isdir(testDir):
        print("ERROR: The test directory does not exist!")
        print("ERROR: Was it specified correctly?")
        print("ERROR: ", testDir)
        sys.exit(-1)
    if srcDir:
        if not os.path.isdir(srcDir):
            print("ERROR: The source directory does not exist!")
            print("ERROR: Was it specified correctly?")
            print("ERROR: ", srcDir)
            sys.exit(-1)

    env = Environment(envFile)
    env.parse_file()  # TODO: Handle/report env.yaml file parsing errors here
    test_handler = TestRunner(env, testDir, srcDir)

    return env, test_handler


def list_cmd(args):
    # SMARTS Command Line API for listing out tests, test-suites, modsets, 
    # and test infromation

    # TODO: For listing tests or modsets, we don't need the src dir, so make it optional here

    testDir = args.dir[0] 
    testDir = os.path.abspath(testDir) # Convert relative path into an absolute path
    envFile = args.env[0]
    envFile = os.path.abspath(envFile)
    
    #print("TEST DIR: ", testDir)
    #print("ENV FILE: ", envFile)

    env, test_handler = setup_smarts(envFile, testDir)

    if len(args.items) == 1:
        # TODO: Handle ambigous arguments with this command
        if args.items[0] == 'tests':
            valid_tests, invalid_tests = test_handler.list_tests()
            print_tests(testDir, valid_tests, invalid_tests)
            return 0
        elif args.items[0] == 'test-suites':
            test_handler.list_testSuites()
            return 0
        elif args.items[0] == 'modsets':
            # List out all the avaliable modsets
            modsets = env.list_modsets()
            print_modsets(modsets, env.name)
            return 0
    if len(args.items) > 1:
        # Print infromation of a specific item, either tests or modsets
        if args.items[0] == 'test':
            print("Calling test_handler.list_test")
            test = test_handler.list_test(args.items)
            print_test_info(tests)
            return 0
        elif args.items[0] == 'modset':
            # Print out the infromation for a single modset
            pass
    
    return 0


def run_cmd(args):
    """ Parse the run command """
    testDir = args.dir[0] # The directory that contains each test
    srcDir = args.src[0]  # The directory that contains the code to be tested
    envFile = args.env[0] # The environment.yaml file
    tests = list(set(args.items))
    # tests = args.items)

    env, test_handler = setup_smarts(envFile, testDir, srcDir)

    print("Running tests: ", tests)
    test_handler.run_tests(tests, env)

    return 0


if __name__ == "__main__":
    """ SMARTs Command Line Argument Parsing """


    parser = argparse.ArgumentParser(prog="smarts",
                                      description="A regression testing system for MPAS",
                                      epilog="Don't Panic (This is the Epilog Area)"
                                    )

    parser.add_argument('-e', '--env-file',
                        dest='env',
                        help='The location of the env.yaml file',
                        metavar='env.yaml',
                        required=True,
                        default=None,
                        nargs=1)
    # TODO: We don't need the src dir for specified calls, so make it optional. But we will need to
    # do some of our own coding to make it required in some areas
    parser.add_argument('-s', '--src-dir',
                        dest='src',
                        help='The directory that holds the code to test changes (MPAS-Model)',
                        metavar='dir',
                        required=False,
                        default=None,
                        nargs=1)
    parser.add_argument('-t', '--test-dir',
                        dest='dir',
                        help='The location of the test directory',
                        metavar='dir',
                        required=True,
                        default=None,
                        nargs=1)
    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        help="Output debug level",
                        type=int,
                        metavar='level',
                        default=0,
                        nargs=1)


    subparsers = parser.add_subparsers(dest='command',
                                       required=True,
                                       description='command description',
                                       help='Sub-command help message')

    # List subcommand
    # TODO: Rename parserList to listParser
    parserList = subparsers.add_parser('list',
                                       help="List SMART's tests, test suites and compilers",
                                       description='Description for list sub-command',
                                       epilog='Epilog for list sub-command')
    parserList.add_argument('items', 
                             help='List items help message',
                             nargs='+')
    parserList.set_defaults(func=list_cmd)

    # Run subcommand
    # TODO: Rename parserRun to runParser
    parserRun = subparsers.add_parser('run',
                                     help="Run a test or a test-suite by name",
                                     description='Description for run sub-command',
                                     epilog='Epilog for run sub-command')
    parserRun.add_argument('items',
                            help='Run items help message',
                            nargs='+')
    parserRun.set_defaults(func=run_cmd)

    args = parser.parse_args()

    # TODO: Also do this for the following:
    # list tests - Only need the test directory
    # list modsets - Only need the environment file
    if args.command == 'run' and args.src is None:
        print("ERROR: Please provide a src directory when using the `run` command")
        sys.exit(-1)

    # In conjuction with the .set_defaults(func=x) command, for both the parserList,
    # and parserRun, the argparser will call the function x, depending on what command
    # was passed in to the argparser.
    args.func(args)
