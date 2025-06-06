import os

class MatLab_Test:
    test_name = "MatLab Test"
    test_description = "Test to facilitating testing out things in matLab"
    dependencies = []
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        self.test_dir = test_dir
        self.src_dir = src_dir
        
        print("Starting matlab engine...")
        import matlab.engine
        self.eng = matlab.engine.start_matlab()

        self.addpath()

        fname = os.path.join(self.test_dir, '1000ohms.25.6km.rho')
        self.eng.workspace['model'] = self.eng.llmodel.read(fname, 'modem', False)

        self.eng.eval('model.uiplot()', nargout=0)
        self.eng.saveas(self.eng.gcf(nargout=1), 'uiplot.png', nargout=0)

        result.result = "PASSED"
        result.msg = "Able to start MatLab from Python"
        return result.result

    def addpath(self):
        print("Adding ModEM-Tool folders to matlab..")
        self.eng.addpath(self.eng.genpath(self.src_dir))