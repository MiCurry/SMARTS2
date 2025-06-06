

class Basic:
    test_name = "Basic MatLab Test"
    test_description = "Ensure Python can connect to MatLab"
    dependencies = []
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        
        print("Starting matlab engine...")
        import matlab.engine
        matlab.engine.start_matlab()

        result.result = "PASSED"
        result.msg = "Able to start MatLab from Python"
        return result.result