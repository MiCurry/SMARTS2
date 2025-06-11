from dataclasses import dataclass
from smarts.utils import matlab_utils

import matlab

@dataclass
class ReadZResult:
    data : list[dict]
    header : str
    units : str
    isign : float
    origin : matlab.double
    size : matlab.double
    info : list[dict]



def do_ml_readZ(eng, fname):
    eng.workspace['fname'] = fname
    eng.evalc('[data, header, units, isign, origin, info] = readZ_3D(fname)')

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

    print('Info Size:', info_size, obj)
    for i in range(1, y+1):
        access_str = f'{obj}{{{i}}}'

        infos.append({
            'data' : eng.eval(f'{access_str}.data'),
            'err' : eng.eval(f'{access_str}.err'),
            'lat' : eng.eval(f'{access_str}.lat'), 
            'lon' : eng.eval(f'{access_str}.lon'), 
            'loc' : eng.eval(f'{access_str}.loc'), 
            'code' : matlab_utils.ml_n2m_to_pylist(eng, f'{access_str}.code'),
            'per' : eng.eval(f'{access_str}.per'), 
            'ncomp' : eng.eval(f'{access_str}.ncomp'),
            'comp' : matlab_utils.ml_n2m_to_pylist(eng, f'{access_str}.comp')
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
        siteChar = eng.eval(f'{access_str}.siteChar')
        Z = eng.eval(f'{access_str}.Z')
        Zerr = eng.eval(f'{access_str}.Zerr')
        origin = eng.eval(f'{access_str}.origin')
        orient = eng.eval(f'{access_str}.orient')
        lat = eng.eval(f'{access_str}.lat')
        lon = eng.eval(f'{access_str}.lon')
        compChar = matlab_utils.ml_n2m_to_pylist(eng, f'{access_str}.compChar') 

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
                'compChar' : compChar}

        allData.append(data)

    return allData


class ModEM_Data:
    def __init__(self, eng):
        eng = eng
