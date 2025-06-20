from dataclasses import dataclass
import os
from typing import Any, Dict, List, Tuple
import copy

import numpy as np
import matlab
from smarts.utils import ModEM_Utils, matlab_utils

from PyModEM import ModEMData

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
    'comp' : list,
    'type' : list
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
    'compChar' : list,
    'type' : list
}



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

        print()
        print("Testing read_full_impedance...")
        result = self.test_read_full_impedance(result)
        if result.result == "FAILED":
            return result
    
        print()
        print("Testing read_imp_n_vert_comp...")
        result = self.test_read_imp_n_vert_comp(result)
        if result.result == "FAILED":
            return result

        print()
        print("Tesing read_one_data_type for onetype='Full_Impedance'")
        result = self.test_read_one_data_type(result)
        if result.result == "FAILED":
            return result

        print()

        print("Testing read_one_data_type_failed with one that that is not present")
        result = self.test_read_one_data_type_failed(result)
        if result.result == "FAILED":
            return result

        print()
        print("Testing read_off_diag_rho_phase...")
        result = self.test_read_off_diag_rho_phase(result)
        if result.result == "FAILED":
            return result

    def test_read_imp_n_vert_comp(self, result):
        result.result = "FAILED"
        result.msg = f"Could not read full impedance"

        fname= os.path.abspath(os.path.join(self.test_dir, 'ReadWriteData', 'full_imp_n_vert_comp.dat'))
        print(f"Testing: readZ_3D... on {fname}")
        self.check_if_file_present(fname, result)
        if result.result == 'FAILED':
            return result

        expected_periods = np.array([11.63636, 25.6, 53.89474, 102.4, 215.5789,
                                     409.6, 862.3158, 1638.4, 4681.143, 18724.57
                                    ])

        expected_full_imp_comp_chars = ModEMData.DATA_TYPE_COMPONENT_MAP['Full_Impedance']
        expected_vert_comp_comp_chars = ModEMData.DATA_TYPE_COMPONENT_MAP['Full_Vertical_Components']
        expected_txtypes = ['Full_Impedance', 'Full_Vertical_Components']
        ncomps = [8, 4]
        expected_units='[]'
        total_comps = ncomps[0] + ncomps[1]
        expected_comps = [expected_full_imp_comp_chars, expected_vert_comp_comp_chars]
        expected_data_info = []

        data_sizes=[(109,10,4,), (109,10,2)]

        for info in range(0, 2):
            expected_data_info.append(
                ModEM_Utils.ExpectedDataInfo(
                    data=None,
                    data_size=data_sizes[info],
                    err=None,
                    err_size=data_sizes[info],
                    lat=None,
                    lat_size=(1,109),
                    lon=None,
                    lon_size=(1,109),
                    loc=None,
                    loc_size=(1, 109),
                    code=None,
                    code_size=(109,),
                    per=expected_periods,
                    ncomp=ncomps[info],
                    comp=expected_comps[info],
                    type=[expected_txtypes[info]]
                )
            )

        all_comps =[]
        all_comps.extend(expected_full_imp_comp_chars)
        all_comps.extend(expected_vert_comp_comp_chars)

        origin = np.array([45.2760, -119.6340, 0])
        expected_data_data = []
        for period in expected_periods:
            expected_data_data.append(ModEM_Utils.ExpectedDataData(
                T=period,
                Cmplx=1,
                units=expected_units,

                signConvention=1,
                nComp=total_comps,

                siteLoc=None,
                siteLoc_size=(109, 3),

                siteChar = None,
                siteChar_size= (109, 1,),

                Z=None,
                Z_size=(109,),

                Zerr=None,
                Zerr_size=(109,),

                origin = origin,
                orient = 0.0,

                lat = None,
                lat_size = (109,),

                lon = None,
                lon_size = (109,),

                compChar=np.array(all_comps),
                type=''
            ))

        expected_data = ModEM_Utils.ExpectedData(
            data=expected_data_data,
            data_size=10,
            header='',
            units=expected_units,
            isign=1,
            origin=origin,
            info=expected_data_info,
            info_size=len(expected_data_info),
            expected_periods=expected_periods
        )


        read_result = ModEM_Utils.do_ml_readZ(self.eng, fname, units=expected_units)
        read_result_plain = copy.deepcopy(read_result)

        for r in read_result_plain['data']:
            r['nanvalue'] = 999999

        self.assert_readZ(result, read_result, expected_data)
        if result.result == "FAILED":
            return result

        header = '# Smarts write tests'
        #write_fname = 'test.write.full_imp_n_vert_comp.dat'
        write_fname = 'test.foobar.dat'


        self.eng.workspace['fname'] = write_fname
        self.eng.workspace['header'] = header
        self.eng.workspace['units'] = expected_units
        self.eng.workspace['isign'] = 1

        self.eng.eval('disp("hello world I am here")', nargout=0)

        print(f"Testing writeZ_3d with {write_fname}")
        self.eng.evalc('[status] = writeZ_3D_MC_fixes(fname, data, header, units, 1)')
        status = self.eng.workspace['status']

        if status != 0:
            result.result = "FAILED"
            result.msg = f"Calling writeZ_3D_MC_fixes on {write_fname} returned a non-zero status code from ML: {status}"
            return result

        print(f"Rereading {write_fname} and checking it against read_result")
        re_read = ModEM_Utils.read_into_expected_datatypes(self.eng, write_fname)
        self.assert_readZ(result, read_result_plain, re_read)
        if result.result == "FAILED":
            return result


        result.result = "PASSED"
        result.msg = "Able to read/write full_imp_n_vert_comp.dat"
        return result

    def test_read_one_data_type(self, result):
        result.result = "FAILED"
        result.msg = f"Could not read full impedance"

        fname= os.path.abspath(os.path.join(self.test_dir, 'ReadWriteData', 'full_imp_n_vert_comp.dat'))
        print(f"Testing: readZ_3D... on {fname}")
        self.check_if_file_present(fname, result)
        if result.result == 'FAILED':
            return result

        expected_periods = np.array([11.63636, 25.6, 53.89474, 102.4, 215.5789,
                                     409.6, 862.3158, 1638.4, 4681.143, 18724.57
                                    ])

        expected_full_imp_comp_chars = ModEMData.DATA_TYPE_COMPONENT_MAP['Full_Impedance']
        expected_txtypes = ['Full_Impedance']
        ncomps = [8,]
        expected_units='[mV/km]/[nT]'
        total_comps = ncomps[0]
        expected_comps = [expected_full_imp_comp_chars]
        expected_data_info = []

        data_sizes=[(109,10,4,)]

        for info in range(0, 1):
            expected_data_info.append(
                ModEM_Utils.ExpectedDataInfo(
                    data=None,
                    data_size=data_sizes[info],
                    err=None,
                    err_size=data_sizes[info],
                    lat=None,
                    lat_size=(1,109),
                    lon=None,
                    lon_size=(1,109),
                    loc=None,
                    loc_size=(1, 109),
                    code=None,
                    code_size=(109,),
                    per=expected_periods,
                    ncomp=ncomps[info],
                    comp=expected_comps[info],
                    type=[expected_txtypes[info]]
                )
            )

        all_comps =[]
        all_comps.extend(expected_full_imp_comp_chars)

        origin = np.array([45.2760, -119.6340, 0])
        expected_data_data = []
        for period in expected_periods:
            expected_data_data.append(ModEM_Utils.ExpectedDataData(
                T=period,
                Cmplx=1,
                units=expected_units,

                signConvention=1,
                nComp=total_comps,

                siteLoc=None,
                siteLoc_size=(109, 3),

                siteChar = None,
                siteChar_size= (109, 1,),

                Z=None,
                Z_size=(109,),

                Zerr=None,
                Zerr_size=(109,),

                origin = origin,
                orient = 0.0,

                lat = None,
                lat_size = (109,),

                lon = None,
                lon_size = (109,),

                compChar=np.array(all_comps),
                type=''
            ))

        expected_data = ModEM_Utils.ExpectedData(
            data=expected_data_data,
            data_size=10,
            header='',
            units=expected_units,
            isign=1,
            origin=origin,
            info=expected_data_info,
            info_size=len(expected_data_info),
            expected_periods=expected_periods
        )


        read_result = ModEM_Utils.do_ml_readZ(self.eng, fname, onetype='Full_Impedance')
        read_result_plain = copy.deepcopy(read_result)

        for r in read_result_plain['data']:
            r['nanvalue'] = 999999

        self.assert_readZ(result, read_result, expected_data)
        if result.result == "FAILED":
            return result

        header = '# Smarts write tests'
        write_fname = 'test.write.full_imp_n_vert_comp.dat'
        print(f"Testing writeZ_3d with {write_fname}")
        status = self.eng.writeZ_3D_MC_fixes(write_fname, read_result_plain['data'], header, expected_units, 1, nargout=1)
        if status != 0:
            result.result = "FAILED"
            result.msg = f"Calling writeZ_3D_MC_fixes on {write_fname} returned a non-zero status code from ML: {status}"
            return result

        print(f"Rereading {write_fname} and checking it against read_result")
        re_read = ModEM_Utils.read_into_expected_datatypes(self.eng, write_fname)
        self.assert_readZ(result, read_result_plain, re_read)
        if result.result == "FAILED":
            return result


        result.result = "PASSED"
        result.msg = "Able to read/write full_imp_n_vert_comp.dat"
        return result

    def test_read_one_data_type_failed(self, result):

        exception_caught = False
        try:
            ModEM_Utils.do_ml_readZ(self.eng, 'Full_Impedance_only.dat', onetype='Full_Vertical_Components')
        except Exception as e:
            exception_caught = True

        if not exception_caught:
            result.result = "FAILED"
            result.msg = "Expected an error to occur, but instead did not"
            return result

        result.result = "PASSED"
        result.msg = ""
        return result

    def test_read_off_diag_rho_phase(self, result):
        result.result = "FAILED"
        result.msg = f"Could not read full impedance"

        fname= os.path.abspath(os.path.join(self.test_dir, 'ReadWriteData', 'off_diag_rho_phase.dat'))
        print(f"Testing: readZ_3D... on {fname}")
        self.check_if_file_present(fname, result)
        if result.result == 'FAILED':
            return result

        expected_periods = np.array([0.010, 0.0215, 0.0464, 0.1, 0.2154, 0.4642,
            1.0, 2.1544, 4.6416, 10.0, 21.5443, 46.4159, 100.0, 2.15444e2,
            4.64159e2, 1000.0])

        expected_comps = ModEMData.DATA_TYPE_COMPONENT_MAP['Off_Diagonal_Rho_Phase']
        ncomps = [4]
        expected_units=''
        total_comps = 4
        expected_comps = [expected_comps]
        expected_data_info = []

        data_sizes=[(100,16,4,)]

        for info in range(0, 1):
            expected_data_info.append(
                ModEM_Utils.ExpectedDataInfo(
                    data=None,
                    data_size=data_sizes[info],
                    type='Off_Diagonal_Rho_Phase',
                    err=None,
                    err_size=data_sizes[info],
                    lat=None,
                    lat_size=(1,100),
                    lon=None,
                    lon_size=(1,100),
                    loc=None,
                    loc_size=(1, 100),
                    code=None,
                    code_size=(100,),
                    per=expected_periods,
                    ncomp=ncomps[info],
                    comp=expected_comps[info]
                )
            )

        all_comps =[]
        all_comps.extend(expected_comps)

        origin = np.array([0, 0, 0])
        expected_data_data = []
        for period in expected_periods:
            expected_data_data.append(ModEM_Utils.ExpectedDataData(
                T=period,
                Cmplx=0,
                units=expected_units,

                signConvention=1,
                nComp=total_comps,

                siteLoc=None,
                siteLoc_size=(100, 3),

                siteChar = None,
                siteChar_size= (100,),

                Z=None,
                Z_size=(100,),

                Zerr=None,
                Zerr_size=(100,),

                origin = origin,
                orient = 0.0,

                lat = None,
                lat_size = (100,),

                lon = None,
                lon_size = (100,),

                compChar=np.array(all_comps),
                type='Off_Diagonal_Rho_Phase'
            ))

        expected_data = ModEM_Utils.ExpectedData(
            data=expected_data_data,
            data_size=16,
            header='',
            units=expected_units,
            isign=1,
            origin=origin,
            info=expected_data_info,
            info_size=len(expected_data_info),
            expected_periods=expected_periods
        )


        read_result = ModEM_Utils.do_ml_readZ(self.eng, fname, apres=True)
        read_result_plain = copy.deepcopy(read_result)

        for r in read_result_plain['data']:
            r['nanvalue'] = 999999

        self.assert_readZ(result, read_result, expected_data)
        if result.result == "FAILED":
            return result

        header = '# Smarts write tests'
        write_fname = 'test.write.off_diag_rho_phase.dat'
        print(f"Testing writeZ_3d with {write_fname}")
        status = self.eng.writeZ_3D_MC_fixes(write_fname, read_result_plain['data'], header, expected_units, 1, False, nargout=1)
        if status != 0:
            result.result = "FAILED"
            result.msg = f"Calling writeZ_3D_MC_fixes on {write_fname} returned a non-zero status code from ML: {status}"
            return result

        print(f"Rereading {write_fname} and checking it against read_result")
        re_read = ModEM_Utils.read_into_expected_datatypes(self.eng, write_fname, apres=True)
        self.assert_readZ(result, read_result_plain, re_read)
        if result.result == "FAILED":
            return result

        result.result = "PASSED"
        result.msg = "Able to read/write full_imp_n_vert_comp.dat"
        return result

    def test_read_full_impedance(self, result):
        result.result = "FAILED"
        result.msg = f"Could not read full impedance"

        full_impedance_fname = os.path.abspath(os.path.join(self.test_dir, 'ReadWriteData', 'full_impedance_only.dat'))
        print(f"Testing: readZ_3D... on {full_impedance_fname}")
        self.check_if_file_present(full_impedance_fname, result)
        if result.result == 'FAILED':
            return result

        expected_periods = np.array([0.56, 1.8, 5.6, 18.0, 56.0, 180.0, 560.0, 1800.0, 5600.0])

        expected_data_info = []
        for info in range(0, 2):
            expected_data_info.append(ModEM_Utils.ExpectedDataInfo(
                data = None,
                data_size = (100, 9, 4),
                err = None,
                err_size = (100, 9, 4),
                lat=None,
                lat_size=(1, 100),
                lon=None,
                lon_size=(1, 100),
                loc=None,
                loc_size=(1, 100),
                code=None,
                code_size=(100,),
                per=expected_periods,
                ncomp=8,
                comp=['ZXX', 'ZXY', 'ZYX', 'ZYY'],
                type='Full_Impedance'
            ))

        expected_data_data = []
        for period in expected_periods:
            expected_data_data.append(ModEM_Utils.ExpectedDataData(
                T = period,
                Cmplx = 1,
                units = 'Ohm',

                signConvention = 1,
                nComp = 8,
                siteLoc = None,
                siteLoc_size = (100, 3),

                siteChar = None,
                siteChar_size = (100, 1),

                Z = None,
                Z_size = (100,),

                Zerr = None,
                Zerr_size = (100,),

                origin = [0.0, 0.0, 0.0],
                orient = 0.0,

                lat = None,
                lat_size = (100,),

                lon = None,
                lon_size = (100,),
                compChar=['ZXX', 'ZXY', 'ZYX', 'ZYY'],
                type='Full_Impedance'
        ))

        expected_data = ModEM_Utils.ExpectedData(
            data=expected_data_data,
            data_size=9,
            header='# Synthetic data set DSM1 from Dublin Institute (2008)',
            units='Ohm',
            isign=1,
            origin=[0.0, 0.0],
            info = expected_data_info,
            info_size=1,
            expected_periods=expected_periods
        )

        read_result_og = ModEM_Utils.do_ml_readZ(self.eng, full_impedance_fname)
        print(read_result_og['info'][0].keys())
        read_result = copy.deepcopy(read_result_og)

        self.assert_readZ_return_types(result, read_result)
        if result.result == "FAILED":
            return result

        self.assert_readZ(result, read_result, expected_data)
        if result.result == "FAILED":
            return result

        header = "# SMARTS writz test"
        write_fname = 'test.write.full_imp.dat'
        print(f"Testing writeZ_3D_MC_fixes with '{write_fname}'")
        status = self.eng.writeZ_3D_MC_fixes(write_fname, read_result_og['data'], header, 'ohm', 1, nargout=1)

        if status != 0:
            result.result = "FAILED"
            result.msg = f"Calling writeZ_3D_MC_fixes on {write_fname} returned a non-zero status code from ML: {status}"
            return result

        full_imp_fname = os.path.abspath(os.path.join(self.test_dir, 'ReadWriteData', 'full_impedance_only.dat')) 
        read_expected = ModEM_Utils.convert_read_into_expected_datatype(read_result)
        full_imp_read = ModEM_Utils.read_into_expected_datatypes(self.eng, full_imp_fname)

        self.assert_readZ(result, read_result, full_imp_read)
        if result.result == "FAILED":
            return result


        result.result = "PASSED"
        result.msg = f"Could read full_impedance"
        return result


    
    def assert_readZ(self, result, readZ3d_result, expected : ModEM_Utils.ExpectedData):
        # Struct return types
        datas = readZ3d_result['data']
        data_size = len(datas)
        infos = readZ3d_result['info']
        info_size = len(infos)

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
        datas : list[ModEM_Utils.ExpectedDataData]
        for idx, data in enumerate(datas):
            period = float(data['T'])
            
            if period not in expected.expected_periods:
                result.result = "FAILED"
                result.msg = f"Period here '{period}' was not in the list of expected periods: {expected.expected_periods}"
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

            data['siteLoc'] = np.array(data['siteLoc'])
            if expected.data[idx].siteLoc is not None:
                if (data['siteLoc'] != expected.data[idx].siteLoc).all():
                    result.result = "FAILED"
                    result.msg = f"Expected 'siteLoc' for period {period} to be {expected.data[idx].siteLoc} instead got {data['siteLoc']}"
                    return result

            if data['siteLoc'].shape != expected.data[idx].siteLoc_size:
                result.result = "FAILED"
                result.msg = f"Expected size of 'siteLoc_size' for period {period} to be {expected.data[idx].siteLoc_size} instead got {data['siteLoc'].shape}"
                return result

            data['siteChar'] = np.array(data['siteChar'])
            if expected.data[idx].siteChar is not None:
                if (data['siteChar'] != expected.data[idx].siteChar).all():
                    result.result = "FAILED"
                    result.msg = f"Expected 'siteChar' for period {period} to be {expected.data[idx].siteChar} instead got {data['siteChar']}"
                    return result

            if data['siteChar'].shape[0] != expected.data[idx].siteChar_size[0]:
                result.result = "FAILED"
                result.msg = f"Expected 'siteChar_size' for period {period} to be {expected.data[idx].siteChar_size[0]} instead got {data['siteChar'].shape}"
                return result

            data['Z'] = np.array(data['Z'])
            if expected.data[idx].Z is not None:
                if (data['Z'] != expected.data[idx].Z).all():
                    result.result = "FAILED"
                    result.msg = f"Expected 'Z' for period {period} to be {expected.data[idx].Z} instead got {data['Z']}"
                    return result

            if len(data['Z']) != expected.data[idx].Z_size[0]:
                result.result = "FAILED"
                result.msg = f"Expected 'Z_size' for period {period} to be {expected.data[idx].Z_size} instead got {len(data['Z'])}"
                return result

            data['origin'] = np.array(data['origin'])
            expected.data[idx].origin = np.array(expected.data[idx].origin)

            if (data['origin'] != expected.data[idx].origin).all():
                result.result = "FAILED"
                result.msg = f"Expected 'origin' for period {period} to be {expected.data[idx].origin} instead got {data['origin']}"
                return result

            data['orient'] = np.array(data['orient'])
            if (data['orient'] != expected.data[idx].origin).all():
                result.result = "FAILED"
                result.msg = f"Expected 'orient' for period {period} to be {expected.data[idx].orient} instead got {data['orient']}"
                return result

            data['lat'] = np.array(data['lat'])
            if expected.data[idx].lat is not None:
                expected.data[idx].lat = np.array(expected.data[idx].lat)
                if (data['lat'] != expected.data[idx].lat).all():
                    result.result = "FAILED"
                    result.msg = f"Expected 'lat' for period {period} to be {expected.data[idx].lat} instead got {data['lat']}"
                    return result

            if data['lat'].shape[0] != expected.data[idx].lat_size[0]:
                result.result = "FAILED"
                result.msg = f"Expected 'lat_size' for period {period} to be {expected.data[idx].lat_size} instead got {data['lat'].shape}"
                return result

            data['lon'] = np.array(data['lon'])
            if expected.data[idx].lon is not None:
                expected.data[idx].lon = np.array(expected.data[idx].lon)
                if (data['lon'] != expected.data[idx].lon).all():
                    result.result = "FAILED"
                    result.msg = f"Expected 'lon' for period {period} to be {expected.data[idx].lon} instead got {data['lon']}"
                    return result

            if data['lon'].shape[0] != expected.data[idx].lat_size[0]:
                result.result = "FAILED"
                result.msg = f"Expected 'lon_size' for period {period} to be {expected.data[idx].lon_size} instead got {data['lon'].shape}"
                return result

            data['compChar'] = np.array(data['compChar'])
            for compChar in data['compChar']:
                if compChar not in expected.data[idx].compChar:
                    result.result = "FAILED"
                    result.msg = f"Expected 'compChar' for period {period} to be in {expected.data[idx].compChar} instead got {compChar}"
                    return result
                
        #
        # Test info structure
        #
        for idx, info in enumerate(infos):
            info['data'] = np.array(info['data'])
            if expected.info[idx].data is not None:
                expected.info[idx].data = np.array(expected.info[idx].data)
                info['data'] = np.array(info['data'])
                if (info['data'] != expected.info[idx].data).all():
                    result.result = "FAILED"
                    result.msg = F"Expected 'info.data' to be {expected.info[idx].data} instead got {info['data']}"
                    return result


            if info['data'].shape != expected.info[idx].data_size:
                result.result = "FAILED"
                result.msg = f"Expected 'info.data' size to be {expected.info[idx].data_size} instead got {info['data'].shape}"
                return result

            info['err'] = np.array(info['err'])
            if expected.info[idx].err is not None:
                expected.info[idx].err = np.array(expected.info[idx].err)

                if (info['err'] != expected.info[idx].err).all():
                    result.result = "FAILED"
                    result.msg = F"Expected 'info.err' to be {expected.info[idx].err} instead got {info['err']}"
                    return result

            if info['err'].shape != expected.info[idx].err_size:
                result.result = "FAILED"
                result.msg = f"Expected 'info.err' size to be {expected.info[idx].err_size} instead got {info['err'].shape}"
                return result

            info['lat'] = np.array(info['lat'])
            if expected.info[idx].lat is not None:
                expected.info[idx].lat = np.array(expected.info[idx].lat)

                if (info['lat'] != expected.info[idx].lat).all():
                    result.result = "FAILED"
                    result.msg = F"Expected 'info.lat' to be {expected.info[idx].lat} instead got {info['lat']}"
                    return result

            info['lon'] = np.array(info['lon'])
            if info['lon'].shape != expected.info[idx].lon_size:
                result.result = "FAILED"
                result.msg = f"Expected 'info.lon' size to be {expected.info[idx].lon_size} instead got {info['lon'].shape}"
                return result

            if expected.info[idx].lon is not None:
                expected.info[idx].lon = np.array(expected.info[idx].lon)

                if (info['lon'] != expected.info[idx].lon).all():
                    result.result = "FAILED"
                    result.msg = F"Expected 'info.lon' to be {expected.info[idx].lon} instead got {info['lon']}"
                    return result

            if info['lat'].shape != expected.info[idx].lat_size:
                result.result = "FAILED"
                result.msg = f"Expected 'info.lat' size to be {expected.info[idx].lat_size} instead got {info['lat'].shape}"
                return result

            info['code'] = np.array(info['code'])
            if expected.info[idx].code is not None:
                expected.info[idx].code = np.array(expected.info[idx].code)
                if (info['code'] != expected.info[idx].code).all():
                    result.result = "FAILED"
                    result.msg = F"Expected 'info.code' to be {expected.info[idx].code} instead got {info['code']}"

            if info['code'].shape != expected.info[idx].code_size:
                result.result = "FAILED"
                result.msg = f"Expected 'info.code' size to be {expected.info[idx].code_size} instead got {info['code'].shape}"
                return result

            info['per'] = np.array(info['per'])
            expected.info[idx].per = np.array(expected.info[idx].per)

            if (info['per'] != expected.info[idx].per).all():
                result.result = "FAILED"
                result.msg = f"Expected period 'info.per' to be {expected.info[idx].per} but instead got: {info['per']}"
                return result

            if float(info['ncomp']) != expected.info[idx].ncomp:
                result.result = "FAILED"
                result.msg = f"Expected 'ncomp' to be {expected.info[idx].ncomp} instead got ({info['ncomp']})"
                return result

            for comp in info['comp']:
                if comp not in expected.info[idx].comp:
                    result.result = "FAILED"
                    result.msg = F"Expected 'info.comp' to be one of: {expected.info[idx].comp} instead got '{comp}'"
                    return result

        result.result = "PASSED"
        result.msg = "Assert readZ succesfull"
        return result



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
