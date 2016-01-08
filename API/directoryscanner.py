import os
from fnmatch import filter as fnfilter
from Exceptions import SampleSheetError
from Validation.offlineValidation import validate_sample_sheet
from Parsers.miseqParser import parse_metadata, complete_parse_samples
from Model.SequencingRun import SequencingRun

def find_runs_in_directory(directory):
	sample_sheets = find_file_by_name(directory, 'SampleSheet.csv')
	
	# filter directories that have been completely uploaded
	sheets_to_upload = filter(lambda dir: not find_file_by_name(dir, '.miseqUploaderComplete'), sample_sheets)
	sequencing_runs = [process_sample_sheet(sheet) for sheet in sheets_to_upload]

	return sequencing_runs
	
def process_sample_sheet(sample_sheet):
	
	run_metadata = parse_metadata(sample_sheet)
	samples = complete_parse_samples(sample_sheet)
	
	sequencing_run = SequencingRun(run_metadata, samples, sample_sheet)
	
	return sequencing_run 
	
def find_file_by_name(top_dir, ss_pattern):

	"""
	Traverse through a directory and a level below it searching for
		a file that matches the given SampleSheet pattern.

	arguments:
		top_dir -- top level directory to start searching from
		ss_pattern -- SampleSheet pattern to try and match
						using fnfilter/ fnmatch.filter

	returns list containing files that match pattern
	"""

	result_list = []

	if os.path.isdir(top_dir):
		for root, dirs, files in walklevel(top_dir, level=2):
			for filename in fnfilter(files, ss_pattern):
				result_list.append(os.path.join(root, filename))

	return result_list

## This method is gracelessly borrowed from:
## http://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
			
if __name__ == "__main__":
	scan_directory('.')