""" SMARTs Command Line Runner """

import os
import sys
import argparse
import logging
from typing import Tuple

from smarts.utils.utils import BLUE, GREEN, RED, RESET

logging.basicConfig(
    level=logging.DEBUG,
    format=f'{BLUE}%(name)s:{RESET} %(message)s'
)

PASSED_LOG_LEVEL = logging.DEBUG + 5

logging.addLevelName(PASSED_LOG_LEVEL, 'PASSED')

def passed(self, message, *args, **kwargs):
    message = GREEN + "PASSED! " + message + RESET
    if self.isEnabledFor(PASSED_LOG_LEVEL):
        self._log(PASSED_LOG_LEVEL, message, args, **kwargs)

logging.Logger.passed = passed

logger = logging.getLogger('SMARTS')


from smarts.config import CommandLineConfig, SmartsCFConfig, SmartsConfig, SmartscfType
from smarts.env import Environment
from smarts.testManager import TestManager

def print_tests(test_directory, valid_tests, invalid_tests):
    """ Command line routine to retrive valid and invalid tests and print
    them out to the terminal """

    logger.info(f"Tests found in: {test_directory}:")

    if len(valid_tests) > 0:
        logger.info("Valid tests:")
        for tests in valid_tests:
            logger.info(f"  - {tests[0]} -- {tests[1]}")

    logger.info("")

    if len(invalid_tests) > 0:
        logger.info("Invalid tests: (These tests were not able to be loaded)")
        for tests in invalid_tests:
            logger.info("  x", tests[0], "--", tests[1])
        logger.info()
    elif len(valid_tests) == 0 and len(invalid_tests) == 0:
        logger.error("error: No tests found in this directory!")
        logger.error("error: Was the right test directory given or were the")
        logger.error("error: tests created correctly?")
        return -1

    return 0

def print_modsets(modsets, envName):
    """ Retrive and print the modsets in the environment file specified with -e/--env """
    # SMARTS Command Line API print modset function - Print the list of modsets
    # found in the enviornment.yaml file
    logger.info(f"Avaliable Modsets on: {envName}")
    for mods in modsets:
        logger.info(f"-, {mods['name']} \t {mods['compiler']['version']}")


def print_test_info(tests):
    """ Retrive and print the infromation of a specifiec test, including its name,
    description, number of cpus and other information """

    tests = sorted(tests, key=lambda t: t['runName'])

    for test in tests:
        if 'error' in test.keys():
            logger.error(f"error LOADING: {test['runName']}")
            logger.error(f"{test['error']}")
        else:
            logger.info(f"    Run name: {test['runName']}")
            logger.info(f"   Long name: {test['longName']}")
            logger.info(f" Description: {test['description']}")
            logger.info(f"       ncpus: {test['ncpus']}")
            logger.info(f"Dependencies: {test['dependencies']}")

        if len(tests) != 1:
            print('------------------------------------------------------')

    return 0


def setup_smarts(envFile=None, testDir=None, srcDir=None, options=None) -> Tuple[Environment, TestManager]:
    """ Helper function to intialize the smarts Environment class and
    smarts TestManager - Will fail if any of the above files or directories
    do not exist """

    if not os.path.isfile(envFile):
        logger.error("error: The environment.yaml file does not exist!")
        logger.error("error: Was it specified correctly?")
        logger.error(f"error: {envFile}")
        sys.exit(-1)
    if not os.path.isdir(testDir):
        logger.error("error: The test directory does not exist!")
        logger.error("error: Was it specified correctly?")
        logger.error(f"error: {testDir}")
        sys.exit(-1)
    if srcDir:
        if not os.path.isdir(srcDir):
            logger.error("error: The source directory does not exist!")
            logger.error("error: Was it specified correctly?")
            logger.error(f"error: {srcDir}")
            sys.exit(-1)

    env = Environment(envFile)
    if env.parse_file() == -1:
        sys.exit(-1)

    test_handler = TestManager(env, testDir, srcDir, test_options=options)

    return env, test_handler


def list_cmd(args):
    """ SMARTS Command Line API for handling the list command passed in to
    the argparser. """

    testDir = args.config.test_dir
    envFile = args.config.env_file
    srcDir = args.config.src_dir

    env, test_handler = setup_smarts(envFile, testDir)

    if len(args.items) == 1:
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
        elif args.items[0] == 'config':
            logger.info('\n=== Smarts Configuration ===\n')
            logger.info(f'Enviornment File: {envFile}')
            logger.info(f'Test Direcotry: {testDir}')
            logger.info(f'Source File: {srcDir}')
            logger.info(f'Verbosity: {args.config.verbose}')
            logger.info('')
            return 0
        else:
            logger.error(f"error: Unkown subcommand: {args.items[1]}")
            args.listParser.print_help()
            sys.exit(-1)
    if len(args.items) > 1:
        # Print infromation of a specific item, either tests or modsets
        if args.items[0] == 'test' or args.items[0] == 'tests':
            tests = test_handler.list_test(args.items)
            print_test_info(tests)
            return 0
        elif args.items[0] == 'modset':
            # Print out the infromation for a single modset
            pass

    return 0


def run_cmd(args):
    """ SMARTS Command Line API for handling the run command passed in to
    the argparser. """
    testDir = args.config.test_dir
    srcDir = args.config.src_dir
    envFile = args.config.env_file
    tests = list(set(args.items))
    options = None

    if args.options is not None:
        options = args.options

    logger.debug("Test Directory: {testDir} - Source Dir: {srcDir} - envFile: {envFile} - options: {options}")

    env, test_handler = setup_smarts(envFile=envFile, testDir=testDir, srcDir=srcDir, options=options)
    test_handler.run_tests(tests, env)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="SMARTS",
                                     description="A regression testing system for MPAS",
                                     epilog=None)


    config = SmartsConfig(parser)

    subparsers = parser.add_subparsers(dest='command',
                            description='command description',
                            help='Sub-command help message')

    # List subcommand
    listParser = subparsers.add_parser('list',
                                    help="List SMART's tests, test suites and compilers",
                                    description='Description for list sub-command',
                                    epilog='Epilog for list sub-command')
    listParser.add_argument('items',
                            help='List items - either \'test\', \'env\' (not yet implemented), or \'config\'',
                            nargs='+')
    listParser.set_defaults(func=list_cmd)

    # Run subcommand
    runParser = subparsers.add_parser('run',
                                    help="Run a test or a test-suite by name",
                                    description='Description for run sub-command',
                                    epilog='Epilog for run sub-command')
    runParser.add_argument('items',
                        help='Selection of test names to run (use `smarts.py list tests` to find a list of tests)',
                        nargs='*')

    runParser.add_argument('-o', '--options', 
                            help='Options for each test',
                            default=None,
                            action='append')
    runParser.set_defaults(func=run_cmd)

    args = parser.parse_args()
    args.parser = parser
    args.listParser = listParser
    args.runParser = runParser
    args.config = config

    config.parse_command_line_args(args)

    if args.command is None:
        parser.print_help()
        sys.exit(-1)

    try:
        args.config.test_dir
    except ValueError as ve:
        parser.print_help()
        sys.exit(-1)
    
    try:
        args.config.src_dir
    except ValueError as ve:
        parser.print_help()
        sys.exit(-1)

    try:
        args.config.env_file
    except ValueError as ve:
        parser.print_help()
        sys.exit(-1)


    args.func(args)