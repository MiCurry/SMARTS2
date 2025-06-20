from dataclasses import dataclass

from typing import Any, Dict, List, Tuple
import numpy as np
from smarts.utils import matlab_utils
import matlab

@dataclass
class ExpectedDataData:
    T : float

    Cmplx : int

    units : str
    signConvention : int
    nComp : int

    siteLoc : np.ndarray
    siteLoc_size : int

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
    type : str

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
    type : str

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

@dataclass
class ReadZResult:
    data : list[dict]
    header : str
    units : str
    isign : float
    origin : matlab.double
    size : matlab.double
    info : list[dict]

def read_into_expected_datatypes(eng, fname : str, apres=False) -> dict:
    return convert_read_into_expected_datatype(do_ml_readZ(eng, fname, apres=apres))

def convert_read_into_expected_datatype(read) -> dict:

    data : ExpectedData

    infos : List[ExpectedDataInfo] = []
    for info in read['info']:

        data = np.array(info['data'])
        err = np.array(info['err'])
        lat = np.array(info['lat'])
        lon = np.array(info['lon'])
        loc = np.array(info['loc'])
        code = np.array(info['code'])
        per = np.array(info['per'])
        dataType = info['type']

        infos.append(ExpectedDataInfo(
            data=data,
            data_size=data.shape,
            err=err,
            err_size=err.shape,
            lat=lat,
            lat_size=lat.shape,
            lon=lon,
            lon_size=lon.shape,
            loc=loc,
            loc_size=loc.shape,
            code=code,
            code_size=code.shape,
            per=per,
            ncomp=info['ncomp'],
            comp=info['comp'],
            type=dataType
        ))

    datas : List[ExpectedDataData] = []
    for data in read['data']:

        siteLoc = np.array(data['siteLoc'])
        Z = np.array(data['Z'])
        Zerr = np.array(data['Zerr'])
        lat = np.array(data['lat'])
        lon = np.array(data['lon'])


        datas.append(ExpectedDataData(
            T = data['T'],
            Cmplx=data['Cmplx'],
            units=data['units'],
            signConvention=data['signConvention'],
            nComp=data['nComp'],

            siteLoc=siteLoc[0],
            siteLoc_size=siteLoc.shape,

            siteChar=data['siteChar'],
            siteChar_size=siteLoc.shape,

            Z=Z,
            Z_size=Z.shape,

            Zerr=Zerr,
            Zerr_size=Zerr.shape,

            origin=np.array(data['origin']),
            orient=data['orient'],

            lat=lat,
            lat_size=lat.shape,

            lon=lon,
            lon_size=lon.shape,
            compChar=data['compChar'],
            type=data['type']
        ))

    data = ExpectedData(
        data=datas,
        data_size=len(datas),
        header=read['header'],
        units=read['units'],
        isign=read['isign'],
        origin=read['origin'],
        info=infos,
        info_size=len(infos),
        expected_periods=np.array(read['info'][0]['per'])
    )

    return data


def do_ml_readZ(eng, fname, units='', onetype='', nanvalue=None, apres=False) -> dict:
    eng.workspace['fname'] = fname
    eng.workspace['newunits'] = units
    eng.workspace['onetype'] = onetype
    if nanvalue is None:
        eng.evalc('nanvalue = NaN')
    else:
        eng.workspace['nanvalue'] = nanvalue

    if apres:
        eng.evalc('[data, header, units, isign, origin, info] = readApres_3D(fname, newunits, onetype)')
    else:
        eng.evalc('[data, header, units, isign, origin, info] = readZ_3D(fname, newunits, onetype, nanvalue)')

    header = eng.workspace['header']
    units = eng.workspace['units']
    isign = eng.workspace['isign']
    origin = eng.workspace['origin']
    size = eng.eval('size(info{1}.code)')
    data = convert_ml_data_to_py(eng, 'data')
    info = convert_ml_info_to_py(eng, 'info')

    return {
        'data' : data,
        'header' : header,
        'units' : units,
        'isign' : isign,
        'origin' : origin,
        'size' : size,
        'info' : info
    }

def convert_ml_info_to_py(eng, obj: str) -> list[dict]:
    infos = []
    info_size = eng.eval(f'size({obj})')[0]
    x = int(info_size[0])
    y = int(info_size[1])

    for i in range(1, y+1):
        access_str = f'{obj}{{{i}}}'

        print("Access_string: ", access_str)

        infos.append({
            'data' : eng.eval(f'{access_str}.data'),
            'err' : eng.eval(f'{access_str}.err'),
            'lat' : eng.eval(f'{access_str}.lat'), 
            'lon' : eng.eval(f'{access_str}.lon'), 
            'loc' : eng.eval(f'{access_str}.loc'), 
            'code' : matlab_utils.ml_n2m_to_pylist(eng, f'{access_str}.code'),
            'per' : eng.eval(f'{access_str}.per'), 
            'ncomp' : eng.eval(f'{access_str}.ncomp'),
            'comp' : matlab_utils.ml_n2m_to_pylist(eng, f'{access_str}.comp'),
            'type' : eng.eval(f'{access_str}.type')
        })

    return infos

def convert_ml_data_to_py(eng, obj: str) -> list[dict]:
    data_size = eng.eval(f'size({obj})')[0]
    x = int(data_size[0])
    y = int(data_size[1])

    allData = []
    for i in range(1, y + 1):
        # For format strings, you can escape {} by {{}}.
        # Here we need to escape the first set of curley braces for matlab: data{}
        # then we need to use another set of {} to access the specific: i.e. data{i}
        access_str = f'{obj}{{{i}}}'

        t = eng.eval(f'{access_str}.T')
        cmplx = eng.eval(f'{access_str}.Cmplx')
        units = eng.eval(f'{access_str}.units')
        signConvention = eng.eval(f'{access_str}.signConvention')
        nComp = eng.eval(f'{access_str}.nComp')
        siteLoc = eng.eval(f'{access_str}.siteLoc')
        try:
            siteChar = eng.eval(f'{access_str}.siteChar')
        except Exception as e:
            siteChar = matlab_utils.ml_n2m_to_pylist(eng, f'{access_str}.siteChar')


        Z = eng.eval(f'{access_str}.Z')
        Zerr = eng.eval(f'{access_str}.Zerr')
        origin = eng.eval(f'{access_str}.origin')
        orient = eng.eval(f'{access_str}.orient')
        lat = eng.eval(f'{access_str}.lat')
        lon = eng.eval(f'{access_str}.lon')
        compChar = matlab_utils.ml_n2m_to_pylist(eng, f'{access_str}.compChar') 
        dataType = eng.eval(f'{access_str}.type')

        data = {'T' : t,
                'Cmplx' : cmplx,
                'units' : units,
                'signConvention' : signConvention,
                'nComp' : nComp,
                'siteLoc' : siteLoc,
                'siteChar' : siteChar,
                'Z' : Z,
                'Zerr' : Zerr,
                'origin' : origin,
                'orient' : orient,
                'lat' : lat,
                'lon' : lon,
                'compChar' : compChar,
                'type' : dataType}

        allData.append(data)

    return allData




class ModEM_Data:
    def __init__(self, eng):
        eng = eng
