import json
import logging
from os import path
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError
from Exceptions.SampleError import SampleError
from Validation.offlineValidation import validate_sample_sheet, validate_sample_list
from Parsers.miseqParser import parse_metadata, complete_parse_samples
from Model.SequencingRun import SequencingRun
from API.fileutils import find_file_by_name

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
    sample_sheets = find_file_by_name(directory = directory,
                                      name_pattern = 'SampleSheet.csv',
                                      depth = 2)

    # filter directories that have been completely uploaded
    sheets_to_upload = filter(lambda dir: not run_is_uploaded(path.dirname(dir)), sample_sheets)
    sequencing_runs = [process_sample_sheet(sheet) for sheet in sheets_to_upload]

    return sequencing_runs

def run_is_uploaded(run_directory):
    """Check if a run has already been uploaded.

    This function checks for the existence of a file `.miseqUploaderInfo`, then
    evaluates the status of the run by looking at the "Upload Status" field.

    Arguments:
    run_directory -- the sequencing run directory

    Returns: true if the run has already been uploaded, false if it has not.
    """
    uploader_info_file = find_file_by_name(run_directory, '.miseqUploaderInfo')

    if uploader_info_file:
        with open(uploader_info_file[0], "rb") as reader:
            info_file = json.load(reader)
            return info_file["Upload Status"] == "Complete"

    return False

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

    # required fields on sequencing_run are:


    validation = validate_sample_sheet(sequencing_run.sample_sheet)
    if not validation.is_valid():
        raise SampleSheetError('Sample sheet {} is invalid. Reason: {}'.format(sample_sheet, validation.get_errors()))

    validation = validate_sample_list(sequencing_run.sample_list)
    if not validation.is_valid():
        raise SampleError('Sample sheet {} is invalid. Reason: {}'.format(sample_sheet, validation.get_errors()))
