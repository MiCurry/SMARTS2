import os
from smarts.testManager import Test

class config_test(Test):
    test_name = "Config Test"
    test_description = "Check to see if SMARTS2 configuration is working"
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        result.result = "PASSED"
        result.msg = "Configuration was correct!"

        if self.config['setup']['mesh'] != 'x1.10242.grid.nc':
            result.result="Failed"
            result.msg = "setup.mesh was not x1.10242.grid.nc"

        if self.config['Section2']['var1'] != 'var2':
            result.result="Failed"
            result.msg = "setup.mesh was not x1.10242.grid.nc"


        return 0
