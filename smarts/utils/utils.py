import os

from typing import List

def save_run_command(fname: str, cmd: List[str]):
    if os.path.isfile(fname):
        return False

    with open(fname, 'w') as file:
        output = " ".join(cmd)
        file.write(output)
        file.write('\n')

     
    return True
