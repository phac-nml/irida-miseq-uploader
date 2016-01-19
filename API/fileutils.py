import os
import re

def find_file_by_name(directory, name_pattern, depth=-1):
    """Find a file by a name pattern in a directory

    Traverse through a directory and a level below it searching for
        a file that matches the given SampleSheet pattern.

    Arguments:
    directory -- top level directory to start searching from
    name_pattern -- SampleSheet pattern to try and match
                    using fnfilter/ fnmatch.filter
    depth -- optional, the max depth to descend into the directory. a depth of
             -1 implies no limit.

    Returns: list containing files that match pattern
    """
    if depth == -1:
        walk = lambda directory, depth: os.walk(directory)
    else:
        walk = lambda directory, depth: walklevel(directory, depth)

    result_list = []

    if os.path.isdir(directory):
        for root, dirs, files in walk(directory, depth):
            for filename in filter(lambda file: re.search(name_pattern, file), files):
                result_list.append(os.path.join(root, filename))

    return result_list

def walklevel(directory, depth):
    """Descend into a directory, but only to the specified depth.

    This method is gracelessly borrowed from:
    http://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below

    Arguments:
    directory -- the directory in which to start the walk
    depth -- the depth to descend into the directory.

    Returns: a generator for directories in under the top level directory.
    """
    directory = directory.rstrip(os.path.sep)
    assert os.path.isdir(directory)
    num_sep = directory.count(os.path.sep)
    for root, dirs, files in os.walk(directory):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + depth <= num_sep_this:
            del dirs[:]
