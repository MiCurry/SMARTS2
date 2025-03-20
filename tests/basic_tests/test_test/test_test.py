import os

class test_test:
        test_name = "Test Test"
        test_description = "A test for testing things outs"
        ncpus = 1
        test_dependencies = None

        """ This test will load a GNU modset, create a Hello World C and Fortram program and
        compile it with the GNU compile we loaded """

        def run(self, env, result, srcDir, testDir, hpc=None):

            mpich_modset = env.list_modsets(name='GNU-MPICH')

            if mpich_modset is None:
                result.result = "FAILED"
                result.msg = "There are no modsets"
                return result.result

            if 'GNU-MPICH' not in mpich_modset:
                result.result = "FAILED"
                result.msg = "There is no MPICH modset"
                return result.result

            mpich_modset = mpich_modset[0]

            env.load_modset(mpich_modset)


            files = os.listdir('/Users/mcurry/meshes')
            print(files)


            result.result = "PASSED"
            result.msg = "Passed"
            return result.result

                        
