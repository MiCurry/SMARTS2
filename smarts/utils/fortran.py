def namelist_editor(namelistPath, replacements=None, additions=None):
    """ edit_namelist - Edit the namelist at namelistPath.
        
    Given a valid location of a namelist and a dictionary of key, value pairs, if key appears as a
    namelist member name (in any namelist group) then value will replace that member name's value.

    Additions to a namelistPath must be given as a dictionary of dictionary in the additions
    argument where the keys of the first dictionary are the group names (with amersands) of which
    member will be added. The value of each group dictionary should be another dictionary the keys
    of which being the member names and the value of each key being the member values (i.e. the
    same as in replacements). WARNING: This program does not check to see if a member is already
    within a group, so using this function may result in duplicate members. Example:

    # Replace 'config_dt' with '42' and set 'config_apply_lbcs' to 'true' ('config_dt' and
    # 'config_apply_lbcs' are in different groups).
    replacements = {'config_dt' : 42,
                    'config_apply_lbcs' : 'true'}

    # Add months and config_o3climatology to the physics group:
    additions = { '&physics' : { 'months' : '300',
                                 'config_o3climatology' : 'false' },
                  '&io' : {'config_restart_timestamp_name' : 'new_name'}}
    

    Upon succesfully writing the new namelist file with all members replaced, than the path of the
    new namelist will be returned. If additions and replacements are both None, False will be
    returned.

    """
    if not (replacements and additions):
        return False

    namelistFile = open(namelistPath, 'r')

    newNamelistFile = ""
    
    for line in namelistFile.readlines():
        # Replace any namelist items
        for key in replacements.keys():
            if key in line:
                line = line.split('=')
                lhs = line[0]
                rhs = replacements[key]
                line = '{0} = {1}\n'.format(lhs, rhs)

        newNamelistFile += line

        # Add new namelist items into a namelist group
        for group in additions.keys():
            if group in line and '=' not in line:
                for key in additions[group].keys():
                    line = "\t{0} = {1}\n".format(str(key), str(additions[group][key]))
                    newNamelistFile += line


    namelistFile.close()
    namelistFile = open(namelistPath, 'w')
    namelistFile.write(newNamelistFile)
    namelistFile.close()
    return namelistPath
