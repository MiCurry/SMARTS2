


class Path:
    test_name = "Path MatLab Test"
    test_description = "Ensure Python can add ModEM-Tool paths to MatLab"
    dependencies = ['Basic']
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        
        print("Starting matlab engine...")

        import matlab.engine
        eng = matlab.engine.start_matlab()

        print("Adding ModEM-Tool folders to matlab..")
        eng.addpath(eng.genpath(src_dir))

        result.result = "PASSED"
        result.msg = "Able to add Paths to MatLab from Python"
        return result.result
