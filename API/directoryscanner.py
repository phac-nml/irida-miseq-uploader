import os
from fnmatch import filter as fnfilter
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError
from Exceptions.SampleError import SampleError
from Validation.offlineValidation import validate_sample_sheet, validate_sample_list, validate_pair_files
from Parsers.miseqParser import parse_metadata, complete_parse_samples
from Model.SequencingRun import SequencingRun

def find_runs_in_directory(directory):
    """Find and validate all runs the specified directory.
    
    Filters out any runs in the directory that have already
    been uploaded. The filter is silent, so no warnings are emitted
    if there is an uploaded run that's found in the directory.
    
    Arguments:
    directory -- the directory to find sequencing runs
    
    Returns: a list of populated sequencing run objects found
    in the directory, ready to be uploaded. 
    """
    sample_sheets = find_file_by_name(directory, 'SampleSheet.csv')
	
    # filter directories that have been completely uploaded
    sheets_to_upload = filter(lambda dir: not find_file_by_name(dir, '.miseqUploaderComplete'), sample_sheets)
    sequencing_runs = [process_sample_sheet(sheet) for sheet in sheets_to_upload]

    return sequencing_runs
	
def process_sample_sheet(sample_sheet):
    """Create a SequencingRun object for the specified sample sheet.
    
    Arguments:
    sample_sheet -- a `SampleSheet.csv` file that refers to an Illumina
    MiSeq sequencing run.
    
    Returns: an individual SequencingRun object for the sample sheet,
    ready to be uploaded.
    """
    run_metadata = parse_metadata(sample_sheet)
    samples = complete_parse_samples(sample_sheet)
       
    sequencing_run = SequencingRun(run_metadata, samples, sample_sheet)
    
    validate_run(sequencing_run)
    
    return sequencing_run
    
def validate_run(sequencing_run):
    """Do the validation on a run, its samples, and files.
    
    This function is kinda yucky because the validators should be raising
    exceptions instead of returning validation objects...
    
    Arguments:
    sequencing_run -- the run to validate
    """
    
    sample_sheet = sequencing_run.sample_sheet
    
    validation = validate_sample_sheet(sequencing_run.sample_sheet)
    if not validation.is_valid():
        raise SampleSheetError('Sample sheet {} is invalid. Reason: {}'.format(sample_sheet, validation.get_errors()))
    
    validation = validate_sample_list(sequencing_run.sample_list)    
    if not validation.is_valid():
        raise SampleError('Sample sheet {} is invalid. Reason: {}'.format(sample_sheet, validation.get_errors()))

    validations = [validate_pair_files(sample.get_pair_files(), sample.get_id()) for sample in sequencing_run.sample_list]
    for validation in validations:
        if not validation.is_valid():
            raise SequenceFileError('Sample sheet {} is invalid. Reason: {}'.format(sample_sheet, validation.get_errors()))
	
def find_file_by_name(top_dir, ss_pattern):
	"""Find a file by a name pattern in a directory
    
	Traverse through a directory and a level below it searching for
		a file that matches the given SampleSheet pattern.

	Arguments:
	top_dir -- top level directory to start searching from
	ss_pattern -- SampleSheet pattern to try and match
	              using fnfilter/ fnmatch.filter

	Returns: list containing files that match pattern
	"""

	result_list = []

	if os.path.isdir(top_dir):
		for root, dirs, files in walklevel(top_dir, level=2):
			for filename in fnfilter(files, ss_pattern):
				result_list.append(os.path.join(root, filename))

	return result_list

def walklevel(some_dir, level=1):
    """Descend into a directory, but only to the specified depth.
    
    This method is gracelessly borrowed from:
    http://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
    
    Arguments:
    some_dir -- the directory in which to start the walk
    level -- the depth to descend into the directory.
    
    Returns: a generator for directories in under the top level directory.
    """
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
			