from typing import List


def ml_n2m_to_pylist(eng, ml_obj : str) -> List[str]:
    size = eng.eval(f"size({ml_obj})")[0]

    n = int(size[0])
    m = int(size[1])

    arry = []
    for i in range(1, n+1):
        arry.append(eng.eval(f'{ml_obj}({i},:)'))

    return arry

