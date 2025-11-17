import os
import logging

logger = logging.getLogger('argument_test')

class argument_test:
        test_name = "Argument Test"
        test_description = "Test to test passing arguments into a test"
        ncpus = 1
        test_dependencies = None

        def run(self, env, result, srcDir, testDir, hpc=None, *args, **kwargs):
                logger.info(f"Argument test kwargs: {kwargs}")

                result.result = "PASSED"
                result.msg = "Succesfully compiled C and Fortran Programs"
                return 0
