from dataclasses import dataclass
import os
from typing import Any, Dict, List, Tuple
import math 

import numpy as np
import matlab
from smarts.utils import ModEM_Utils, matlab_utils

dims = 'dims'
nzAir = 'nzAir'
resType = 'resType'
origin = 'origin'
orientatino = 'orientation'
rho = 'rho'

MACKIES_FORMAT = 1
WS3D_FORMAT = 2

# TODO: Need Full_Interstation_TF

expected_info_types = {
    'data' : matlab.double,
    'err' : matlab.double,
    'lat' : matlab.double,
    'lon' : matlab.double,
    'loc' : matlab.double,
    'code' : list,
    'per' : matlab.double,
    'ncomp' : float,
    'comp' : list
}

expected_data_types = {
    'T' : float,
    'Cmplx' : float,
    'units' : str,
    'signConvention' : float,
    'nComp' : float,
    'siteLoc' : matlab.double,
    'siteChar' : list,
    'Z' : matlab.double,
    'Zerr' : matlab.double,
    'origin' : matlab.double,
    'orient' : float,
    'lat' : matlab.double,
    'lon' : matlab.double,
    'compChar' : list
}

@dataclass
class ExpectedDataData:
    T : float

    Cmplx : int

    units : str
    signConvention : int
    nComp : int

    siteLoc : np.ndarray
    siteLoc_size : Tuple[int, int]

    siteChar : List[str]
    siteChar_size : Tuple[int, int]

    Z : np.ndarray
    Z_size : Tuple[int, int]
    Zerr : np.ndarray
    Zerr_size : Tuple[int, int]

    origin : np.ndarray
    orient : float

    lat : np.ndarray
    lat_size : Tuple[int, int]
    lon : np.ndarray
    lon_size : Tuple[int, int]

    compChar : List[str]

@dataclass
class ExpectedDataInfo:
    data : np.ndarray
    data_size : list[int]

    err : np.ndarray
    err_size : list[int]

    lat : np.ndarray
    lat_size : list[int]

    lon : np.ndarray
    lon_size : list[int]
    loc : np.ndarray
    loc_size : list[int]

    code : list
    code_size : list[int]

    per : np.ndarray

    ncomp : float
    comp : list[str]

@dataclass
class ExpectedData:
    data : list[ExpectedDataData]
    data_size : int
    header : str
    units : str
    isign : int
    origin : np.ndarray
    info : list[ExpectedDataInfo]
    info_size : int
    expected_periods : list[float]

class ReadWriteData:
    test_name = "Test Read/Write Datafile"
    test_description = "Test reading and writing ModEM Data types"
    dependencies = []
    ncpus = 1

    def addpath(self):
        print("Adding ModEM-Tool folders to matlab..")
        self.eng.addpath(self.eng.genpath(self.src_dir))

    def check_if_file_present(self, fname, result):
        if not os.path.isfile(fname):
            result.result = "FAILED"
            result.msg = f"Could not find data file {fname}"
            return result

        result.result = "PASSED"
        return result

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):
        self.src_dir = src_dir
        self.test_dir = test_dir
        self.result = result

        print("Starting matlab engine...")
        import matlab.engine
        self.eng = matlab.engine.start_matlab()
        self.addpath()

        result = self.test_read_full_impedance(result)
        if result.result == "FAILED":
            return result


    def test_read_full_impedance(self, result):
        result.result = "FAILED"
        result.msg = f"Could not read full impedance"

        print("Testing: readZ_3D...")

        full_impedance_fname = os.path.abspath(os.path.join(self.test_dir, 'ReadWriteData', 'full_impedance_only.dat'))
        #full_impedance_fname = os.path.abspath(os.path.join(self.test_dir, 'ReadWriteData', 'full_imp_n_vert_comp.dat'))
        self.check_if_file_present(full_impedance_fname, result)
        if result.result == 'FAILED':
            return result

        read_result = ModEM_Utils.do_ml_readZ(self.eng, full_impedance_fname)

        print(read_result['header'])

        self.assert_readZ_return_types(result, read_result)
        if result.result == "FAILED":
            return result

        print("Info lenght: ", len(read_result['info']))
        print("data lenght: ", len(read_result['data']))

        expected_periods = [0.56, 1.8, 5.6, 18.0, 56.0, 180.0, 560.0, 1800.0, 5600.0]

        for d in read_result['data']:
            print(d['T'])

        expected_data_info = []
        for info in range(0, 2):
            expected_data_info.append(ExpectedDataInfo(
                data = None,
                data_size = [100, 9, 4],
                err = None,
                err_size = [100, 9, 4],
                lat=None,
                lat_size=[1, 100],
                lon=None,
                lon_size=[1,100],
                loc=None,
                loc_size=[100, 3],
                code=None,
                code_size=[100, 3],
                per=expected_periods,
                ncomp=8,
                comp=['ZXX', 'ZXY', 'ZYX', 'ZYY']
            ))

        expected_data_data = []
        for period in expected_periods:
            expected_data_data.append(ExpectedDataData(
                T = period,
                Cmplx = 1,
                units = 'Ohm',

                signConvention = 1,
                nComp = 8,
                siteLoc = None,
                siteLoc_size = [100, 3],

                siteChar = None,
                siteChar_size = [1, 100],

                Z = None,
                Z_size = [100, 4],

                Zerr = None,
                Zerr_size = [100, 4],

                origin = [0.0, 0.0],
                orient = 0.0,

                lat = None,
                lat_size = [100, 1],

                lon = None,
                lon_size = [100, 1],
                compChar=['ZXX', 'ZXY', 'ZYX', 'ZYY']
        ))

        expected_data = ExpectedData(
            data = expected_data_data,
            data_size=9,
            header='# Synthetic data set DSM1 from Dublin Institute (2008)',
            units='Ohm',
            isign=1,
            origin=[0.0, 0.0],
            info = expected_data_info,
            info_size=1,
            expected_periods=expected_periods
        )

        self.assert_readZ(result, read_result, expected_data)
        if result.result == "FAILED":
            return result


        result.result = "PASSED"
        result.msg = f"Could read full_impedance"
        return result
    
    def assert_readZ(self, result, readZ3d_result, expected : ExpectedData):
        # Struct return types
        datas = readZ3d_result['data']
        data_size = len(datas)
        print(data_size)
        infos = readZ3d_result['info']
        info_size = len(infos)
        print(info_size)

        # Main return types
        header = readZ3d_result['header']
        units = readZ3d_result['units']
        isign = readZ3d_result['isign']
        origin = readZ3d_result['origin']

        if data_size != expected.data_size:
            result.result = "FAILED"
            result.msg = f"Expected 'data_size' to be {expected.data_size} instead got {data_size}"
            return result

       # Header is currently empty
       # if header != expected.header:
       #     result.result = "FAILED"
       #     result.msg = f"Expected 'header' to be {expected.header} instead got {header}"
       #     return result

        if units != expected.units:
            result.result = "FAILED"
            result.msg = f"Expected 'units' to be {expected.units} instead got {units}"
            return result

        if isign != expected.isign:
            result.result = "FAILED"
            result.msg = f"Expected 'isign' to be {expected.isgn} instead got {isign}"
            return result

        origin = np.array(origin)
        expected.origin = np.array(expected.origin)

        if (origin != expected.origin).all():
            result.result = "FAILED"
            result.msg = f"Expected 'origin' to be {expected.origin} instead got {origin}"
            return result

        if info_size != expected.info_size:
            result.result = "FAILED"
            result.msg = f"Expected 'info' to be {expected.info_size} instead got {info_size}"
            return result

        #
        # Test data structure
        #
        print(datas)
        print("Going into data testing")
        datas : list[ExpectedDataData]
        for idx, data in enumerate(datas):
            period = data['T']
            if data['T']  not in expected.expected_periods:
                result.result = "FAILED"
                result.msg = f"Period '{data['T']}' was not in the list of expected periods: {expected.expected_periods}"
                return result

            if data['Cmplx'] != expected.data[idx].Cmplx:
                result.result = "FAILED"
                result.msg = f"Expected 'Cmplx' for period {period} to be {expected.data[idx].Cmplx} instead got {data['Cmplx']}"
                return result

            if data['units'] != expected.data[idx].units:
                result.result = "FAILED"
                result.msg = f"Expected 'units' for period {period} to be {expected.data[idx].units} instead got {data['units']}"
                return result

            if data['signConvention'] != expected.data[idx].signConvention:
                result.result = "FAILED"
                result.msg = f"Expected 'signConvention' for period {period} to be {expected.data[idx].signConvention} instead got {data['signConventionl']}"
                return result

            if data['nComp'] != expected.data[idx].nComp:
                result.result = "FAILED"
                result.msg = f"Expected 'nComp' for period {period} to be {expected.data[idx].nComp} instead got {data['nComp']}"
                return result

            if data['siteComp'] != expected.data[idx].nComp:
                result.result = "FAILED"
                result.msg = f"Expected 'nComp' for period {period} to be {expected.data[idx].nComp} instead got {data['nComp']}"
                return result




        #
        # Test info structure
        #






    def assert_readZ_return_types(self, result, readZ3d_result):
        # Struct return types
        data = readZ3d_result['data']
        info = readZ3d_result['info']

        # Main return types
        header = readZ3d_result['header']
        units = readZ3d_result['units']
        isign = readZ3d_result['isign']
        origin = readZ3d_result['origin']
        size = readZ3d_result['size']

        ml_data_type = self.eng.eval('class(data)')
        if ml_data_type != 'cell':
            result.result = "FAILED"
            result.msg = f'Expected \'data\' to be of type \'cell\' instead got \'{ml_data_type}\''
            return result

        if type(header) != str:
            result.result = "FAILED"
            result.msg = f"Expected 'header' to be of type 'str' instead got: {type(header)}"
            return result

        if type(units) != str:
            result.result = "FAILED"
            result.msg = f"Expected 'untis' to be of type 'str' instead got: {type(units)}"
            return result

        if type(isign) != float:
            result.result = "FAILED"
            result.msg = f"Expected 'isign' to be of type 'str' instead got: {type(isign)}"
            return result

        if type(origin) != matlab.double:
            result.result = "FAILED"
            result.msg = f"Expected 'isign' to be of type 'origin' instead got: {type(origin)}"
            return result

        if type(size) != matlab.double:
            result.result = "FAILED"
            result.msg = f"Expected 'isign' to be of type 'size' instead got: {type(size)}"
            return result

        #
        # Test type in info struct
        #
        for i in info:
            for key in i.keys():
                if type(i[key]) != expected_info_types[key]:
                    result.result = "FAILED"
                    result.msg = f"Expected '{key}' in info to be of type '{expected_info_types[key]} instead got: {type(i[key])}'"

        ml_info_type = self.eng.eval('class(info)')
        if ml_info_type != 'cell':
            result.result = "FAILED"
            result.msg = f'Expected \'info\' to be of type \'cell\' instead got \'{ml_info_type}\''
            return result
        info_code_type = self.eng.eval('class(info{1}.code)')
        if info_code_type != 'char':
            result.result = "FAILED"
            result.msg = f"Expected 'info{{1}}.code' to be of type 'char' instead got: {info_code_type}"
            return result

        info_comp_type = self.eng.eval('class(info{1}.comp)')
        if info_code_type != 'char':
            result.result = "FAILED"
            result.msg = f"Expected 'info{{1}}.comp' to be of type 'char' instead got: {info_comp_type}"
            return result

        # Data Struct testing
        for d in data:
            for key in d.keys():
                if type(d[key]) != expected_data_types[key]:
                    result.result = "FAILED"
                    result.msg = f"Expected '{key}' in data to be of type '{expected_info_types[key]} instead got: {type(i[key])}'"

        data_compChar_type = self.eng.eval('class(data{1}.compChar)')
        if data_compChar_type != 'char':
            result.result = "FAILED"
            result.msg = f"Expected 'data{{1}}.compChar' to be of type 'char' instead got: {data_compChar_type}"
            return result

        result.result = "PASSED"
        result.msg = "Types okay"
        return result
