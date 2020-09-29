import xml.etree.ElementTree as ET

""" MPAS Utilities - Helpful MPAS Variables and Functions """

""" Default Formats of timestamps used by MPAS which can be used by
datetime.datetime.strftime and datetime.datetime.strptime. """
MPAS_TIME_FORMAT = "%Y-%m-%d_%H:%M:%S"
RESTART_FILE_FORMAT = "restart.%Y-%m-%d_%H.%M.%S.nc"
HISTORY_FILE_FORMAT = "history.%Y-%m-%d_%H.%M.%S.nc"
DIAG_FILE_FORMAT = "diag.%Y-%m-%d_%H.%M.%S.nc"


def check_log(log):
    """ Check an MPAS Log - Given the path to an MPAS log file, scan through the log file and
    create lists of all warnings, errors and critical log messages. This function will then return
    the complete contents of the log file (as a string), the list of all warnings found, the list
    of all errors found and the list of all critical log messages found.
    """
    log_f = open(log, 'r')

    warnings = []
    errors = []
    criticals = []

    for line in log_f.readlines():
        if 'WARNING:' in line:
            warnings.append(line)

        if 'ERROR:' in line and not 'CRITICAL' in line:
            errors.append(line)

        if 'CRITICAL ERROR:' in line:
            criticals.append(line)

    # Move the cursor back to the file so it we can return it in its entirety
    log_f.seek(0)
    return log_f.read(), warnings, errors, criticals


def edit_stream(stream, replacements):
    """ Given the path to a MPAS streams file and a dictionary of dictionary, 
    replacements, replace the value of specified attributes of a stream. NOTE: 
    This function will replace the file located at stream.

    TODO: Add the ability to add attributes that are not there.
    
    stream - String, or Path object - Location of string file to rewrite
    replacements - Dictionary of dictionaries - The first dictionary should contain 
                   the 'name' of the stream that is desired to be changed as each key of the
                   dictionary. For instance this could be 'input', 'restart' etc.. The keys for the
                   second dictionary should than consist of name of the attributes desired to be
                   changed and the value will be used to replace the attribute value.
                   
                   Example:
                     
                     rep = {'restart' : {'output_interval'  : '1_00:00:00'},
                            'output' : {'output_interval'   : '02:00:00', 
                                        'filename_template' : 'output.$Y-$M-$D_$h.$m.$s.nc'}
                           } 

                    The above dictionary will replace the 'output_interval' of the 'restart' stream
                    to 1 day ('1_00:00:00'), the 'output_interval' of the 'output' stream to 2
                    hours ('02:00:00') and the will change the name of the 'filename_template' to
                    'output.$Y-$M-$D_$h.$m.$s.nc' for the 'output' stream.
    
    TODO: Add an argument that enables the ability to change the key of the xml member chosen,
    currently it is 'name'. This might be useful for other xml files that do not use 'name' as an
    identifier.
    """
    tree = ET.parse(stream)
    root = tree.getroot()

    for child in root:
        for names in replacements.keys():
            if names in child.attrib['name']:
                for rep in replacements[names].keys():
                    child.attrib[rep] = replacements[names][rep]

    tree.write(stream)
