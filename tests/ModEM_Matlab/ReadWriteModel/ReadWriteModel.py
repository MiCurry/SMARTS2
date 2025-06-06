import os
from typing import Any, Dict, List
import math 

import numpy as np
import matlab 

dims = 'dims'
nzAir = 'nzAir'
resType = 'resType'
origin = 'origin'
orientatino = 'orientation'
rho = 'rho'

MACKIES_FORMAT = 1
WS3D_FORMAT = 2

class ReadWriteModel:
    test_name = "Test Read/Write Model"
    test_description = "Test reading and writing ModEM Model Type (WSINV3DMT (WS3D) model types)"
    dependencies = []
    ncpus = 1

    def addpath(self):
        print("Adding ModEM-Tool folders to matlab..")
        self.eng.addpath(self.eng.genpath(self.src_dir))

    def make_model_dict(self, dims : tuple[List[float], List[float], List[float]] = None,
                        ndims : tuple[int, int, int] = None,
                        nzAir : float = 0.0,
                        resType : str = 'LOGE',
                        origin : tuple[float, float, float] = [0.0, 0.0, 0.0],
                        orientation : float = 0.0,
                        rho : np.ndarray = None,
                        units : str = 'km',
                        airCond : float = math.log(1e-10)) -> Dict[Any, Any]:

        if dims is not None:
            dims = {'x' : np.array(dims[0]),
                    'y' : np.array(dims[1]),
                    'z' : dims[2]}

        if ndims is not None:
            ndims = {'nx' : ndims[0],
                     'ny' : ndims[1],
                     'nz' : ndims[2]}

        if resType == 'LOG10':
            airCond = math.log(1e-10, 10)
        elif resType == 'LINEAR':
            airCond = 1e-10

        return { 'dims' : dims,
                 'ndims' : ndims,
                 'nzAir' : nzAir,
                 'resType' : resType,
                 'origin' : np.array(origin),
                 'orientation' : orientation,
                 'rho' : rho,
                 'units' : units,
                 'airCond' : airCond
               }

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        self.src_dir = src_dir
        self.test_dir = test_dir
        self.result = result
        good_fname = os.path.join(self.test_dir, '1000ohms.25.6km.rho')
        bad_fname = os.path.join(self.test_dir,  '1000ohms.25.6km.error.rho')
        out_fname_ws3d = 'out.write_WS3D.1000ohms.25.6km.rho'
        out_fname_cond = 'out.write_cond.1000ohms.25.6km.rho'

        self.expected_model = self.make_model_dict(ndims=[42,42,60],
                                                   nzAir=6.0,
                                                   resType='LOGE',
                                                   origin=[-1034126.425,  -814638.367, 0.],
                                                   orientation=0.0,
                                                   rho=None)

        if not os.path.isfile(good_fname):
            result.result = "FAILED"
            result.msg = f"Could not find model file {good_fname}"
            return result

        print("Starting matlab engine...")
        import matlab.engine
        self.eng = matlab.engine.start_matlab()
        self.addpath()

        '''
            Testing test_read_WS3D...
        '''
        result, model = self.test_read_WS3D(good_fname, result, self.expected_model)
        if result.result == "FAILED":
            return result.result

        # This test should fail... unit test of the unit test..
        result, _ = self.test_read_WS3D(bad_fname, result, self.expected_model)
        if result.result != "FAILED":
            return result.result

        # Testing Write
        result, _ = self.test_write_WS3D(out_fname_ws3d, model, model, result)
        if result.result == "FAILED":
            return result.result


        '''
            Testing test_readCond_3D...
        '''
        result, model = self.test_readCond_3D(good_fname, result, self.expected_model)
        if result.result == "FAILED":
            return result.result

        # This test should fail... unit test of the unit test..
        result, _ = self.test_readCond_3D(bad_fname, result, self.expected_model)
        if result.result != "FAILED":
            return result.result

        result, _ = self.test_write_Cond3D(out_fname_cond, model, model, result)
        if result.result == "FAILED":
            return result.result
            
        result.result = "PASSED"
        result.msg = "Able to Read/Write Model Files"
        return result.result

    def assert_model(self, model, expected, result):
        result.result = "FAILED"
        result.msg = "default message"

        # Test nx
        if model['ndims']['nx'] != expected['ndims']['nx']:
            result.result = "FAILED"
            result.msg = f"Expected number of dimensions in the x direction to be '{expected['ndims']['nx']}' "\
                         f"instead got {model['ndims']['nx']}"
            return result

        # Test ny
        if model['ndims']['ny'] != expected['ndims']['ny']:
            result.result = "FAILED"
            result.msg = f"Expected number of dimensions in the y direction to be '{expected['ndims']['ny']}' "\
                         f"instead got {model['ndims']['nz']}"
            return result

        # Test nz
        if model['ndims']['nz'] != expected['ndims']['nz']:
            result.result = "FAILED"
            result.msg = f"Expected number of dimensions in the z direction to be '{expected['ndims']['nz']}' "\
                         f"instead got {model['ndims']['nz']}"
            return result

        # Test nzAir
        if model['nzAir'] != expected['nzAir']:
            result.result = "FAILED"
            result.msg = f"Expected nzAir to be '{expected['nzAir']}' but instead got '{model['nzAir']}'"
            return result

        # Test restType
        if model['resType'] != expected['resType']:
            result.result = "FAILED"
            result.msg = f"Expected resType to be '{expected['resType']}' but instead got '{model['resType']}'"
            return result

        # Test Origin
        if (model['origin'] != expected['origin']).all():
            result.result = "FAILED"
            result.msg = f"Expected origin to be '{expected['origin']}' instead got '{model['origin']}'"
            return result

        # Test Orientation
        if model['orientation'] != expected['orientation']:
            result.result = "FAILED"
            result.msg = f"Expected rotation to be '{expected['orientation']}' instead got '{model['orientation']}'"
            return result

        result.result = "PASSED"
        result.msg = "Assertion succesfull"
        return result

    def test_readCond_3D(self, fname, result, expected):
        print("Testing readCond_3D with:", fname)
        cond = self.eng.readCond_3D(fname, WS3D_FORMAT, nargout=1)

        if type(cond) != dict:
            result.result = "FAILED"
            result.msg = f"Expected type of 'readCond_3D' to be 'dict' instead got: {type(cond)}"
            return result, None

        resType = cond['paramType']
        rho = cond['v']
        airCond = cond['AirCond']
        grid = cond['grid']
        dims = [ grid['dx'], grid['dy'], grid['dz'] ]
        ndims = [ grid['Nx'], grid['Ny'], grid['NzEarth'] ]
        nzAir = grid['NzAir']
        origin = grid['origin']
        orientation = grid['rotation']
        units = grid['units']


        # Test dim type
        for d, dim in enumerate(dims):
            if type(dim) != matlab.double:
                result.result = "FAILED"
                result.msg = f"Expected dim '{d}' to be of type 'matlab.double' instead got: {type(dim)}"
                return result, None

        # Test nDim type
        for d, ndim in enumerate(ndims):
            if type(ndim) != float:
                result.result = "FAILED"
                result.msg = f"Expected ndim '{d}' to be of type 'float' instead got: {type(ndim)}"
                return result, None

        if type(resType) != str:
            result.result = "FAILED"
            result.msg = f"Expected resType to be of type 'str' instead got: {type(resType)}"
            return result, None

        if type(nzAir) != float:
            result.result = "FAILED"
            result.msg = f"Expected nzAir to be of type 'float' instead got: {type(nzAir)}"
            return result, None

        if type(origin) != matlab.double:
            result.result = "FAILED"
            result.msg = f"Expected 'origin' to be of type 'matlab.double' instead got: {type(origin)}"
            return result, None

        if type(orientation) != float:
            result.result = "FAILED"
            result.msg = f"Expected orientation to be of type 'float' instead got: {type(orientation)}"
            return result, None

        if type(units) != str:
            result.result = "FAILED"
            result.msg = f"Expected units to be of type 'str' instead got: {type(units)}"
            return result, None

        model = self.make_model_dict(dims=dims,
                                     ndims=ndims,
                                     nzAir=nzAir,
                                     resType=resType,
                                     origin=origin,
                                     orientation=orientation,
                                     rho=rho,
                                     units=units,
                                     airCond=airCond)

        result = self.assert_model(model, expected, result)
        if result.result == "FAILED":
            return result, None

        result.result = "PASSED"
        result.msg = "Able to Read using readCond_3D"
        return result, model

    def test_read_WS3D(self, fname, result, expected):
        print(f"Testing read_WS3d_model with: '{fname}'")

        ret = [self.eng.read_WS3d_model(fname, nargout=8)][0]

        if len(ret) != 8:
            result.result = "FAILED"
            result.msg = f"Expected 8 return arguments from 'read_WS3d_model', but instead got: {len(ret)}"
            return result, None

        x = ret[0]; nx = len(x)
        if type(x) != matlab.double:
            result.result = "FAILED"
            result.msg = f"Expected x dimension to be type 'matlab.double' instead got type: {type(x)}"
            return result, None

        y = ret[1]; ny = len(y)
        if type(y) != matlab.double:
            result.result = "FAILED"
            result.msg = f"Expected y dimension to be type 'matlab.double' instead got type: {type(y)}"
            return result, None

        z = ret[2]; nz = len(z)
        if type(z) != matlab.double:
            result.result = "FAILED"
            result.msg = f"Expected z dimension to be type 'matlab.double' instead got type: {type(z)}"
            return result, None

        rho = np.array(ret[3])

        nzAir = ret[4]
        if type(nzAir) != float:
            result.result = "FAILED"
            result.msg = f"Expected 'nzAir' to be type 'float' instead got type: {type(nzAir)}"
            return result, None

        resType = ret[5]
        if type(resType) != str:
            result.result = "FAILED"
            result.msg = f"Expected resType dimension to be type 'str' instead got type: {type(resType)}"
            return result, None

        origin = np.squeeze(np.array(ret[6]))
        if len(origin) != 3:
            result.result = "FAILED"
            result.msg= f"Expected origin to be of size '3' instead got size '{len(origin)}'"
            return result, None
        
        rotation = ret[7]
        if type(rotation) != float:
            result.result = "FAILED"
            result.msg= f"Expected orientation to be of type 'float' instead got size '{type(rotation)}'"
            return result, None

        model = self.make_model_dict(dims=[x, y, z],
                                     ndims=[nx, ny, nz],
                                     nzAir=nzAir,
                                     resType=resType,
                                     origin=origin,
                                     orientation=rotation,
                                     rho=rho
                                     )

        result = self.assert_model(model, expected, result)
        if result.result == "FAILED":
            return result, None


        result.result = "PASSED"
        result.msg = "Can read model file..."
        return result, model
        
    def test_write_WS3D(self, fname, model, expected, result):
        print(f"Testing write_WS3d_model... in file: '{fname}'")

        result.result = "FAILED"
        result.msg = "Failed to succesfully write WS3d"

        status = self.eng.write_WS3d_model(fname,
                                           model['dims']['x'],
                                           model['dims']['y'],
                                           model['dims']['z'],
                                           model['rho'],
                                           model['nzAir'],
                                           model['resType'],
                                           model['origin'],
                                           model['orientation'],
                                           nargout=1)
        if status != 0:
            result.result = "FAILED"
            result.msg = f"write_WS3d_model did not return status of '0' instead got: {status}"
            return result

        # Then call self.test_read_WS3D ...
        self.test_read_WS3D(fname, result, expected)
        if result.result == "FAILED":
            return result.result

        result.result = "PASSED"
        result.msg = "Can write write_WS3d_model"
        return result, None

    def test_write_Cond3D(self, fname, model, expected, result):
        print(f"Testing write_Cond3D... in file: '{fname}'")
        result.result = "FAILED"
        result.msg = "Failed to succesfully write_Cond3D"

        grid = {
                'dx' : model['dims']['x'],
                'dy' : model['dims']['y'],
                'dz' : model['dims']['z'],
                'Nx' : model['ndims']['nx'],
                'Ny' : model['ndims']['ny'],
                'NzEarth' : model['ndims']['nz'],
                'NzAir' : model['nzAir'],
                'origin' : model['origin'],
                'rotation' : model['orientation'],
                'units' : model['units']
        }

        cond = {
            'paramType' : model['resType'],
            'v' : model['rho'],
            'AirCond' : model['airCond'],
            'grid' : grid
        }

        status = self.eng.writeCond_3D(fname, cond, WS3D_FORMAT, nargout=1)
        if status != 0:
            result.result = "FAILED"
            result.msg = f"writeCond_3D did not return status of '0' instead got: {status}"
            return result

        self.test_readCond_3D(fname, result, model)
        if result.result == "FAILED":
            result.result = "FAILED"
            result.msg = f"writeCond_3D did not return status of '0' instead got: {status}"
            return result

        result.result = "PASSED"
        result.msg = "Can write using write_Cond3D"
        return result, None