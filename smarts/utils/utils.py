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

def matches_in_str(string: str, matches: List[str], discards=None) -> bool:
    """ Return True, if all matches are in string, otherwise return False. 


    discards (optional) - any matches in discard will return False
    """
    for match in matches:
        if match not in string:
            return False

    for d in discards:
        if d in string:
            return False

    return True

def all_matches(strs: List[str], matches: List[str], discards=None) -> List[str]:
    """ Given a list of strings, return the strings that match all the strings in matches. 

    If the strs contain any matches to discard (optional), then that string will be discarded.
    """

    matched = []
    for f in strs:
        if matches_in_str(f, matches, discards):
            matched.append(f)


    return matched
