import json
import logging
import os
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError
from Exceptions.SampleError import SampleError
from Validation.offlineValidation import validate_sample_sheet, validate_sample_list
from Parsers.miseqParser import parse_metadata, complete_parse_samples
from Model.SequencingRun import SequencingRun
from API.pubsub import send_message


class DirectoryScannerTopics(object):
    """Topics issued by `find_runs_in_directory`"""
    finished_run_scan = "finished_run_scan"
    run_discovered = "run_discovered"
    garbled_sample_sheet = "garbled_sample_sheet"
    missing_files = "missing_files"


def find_runs_in_directory(directory):
    """Find and validate all runs the specified directory.

    Filters out any runs in the directory that have already
    been uploaded. The filter is silent, so no warnings are emitted
    if there is an uploaded run that's found in the directory.

    Arguments:
    directory -- the directory to find sequencing runs

    Usage:
    Can be used on the directory containing the SampleSheet.csv file (a single run)
    Can be used on the directory containing directories with SampleSheet.csv files in them (a group of runs)

    Returns: a list of populated sequencing run objects found
    in the directory, ready to be uploaded.
    """

    def find_run_directory_list(run_dir):
        """Find and return all directories (including this one) in the specified directory.

        Arguments:
        directory -- the directory to find directories in

        Returns: a list of directories including current directory
        """

        # Checks if we can access to the given directory, return empty and log a warning if we cannot.
        if not os.access(run_dir, os.W_OK):
            logging.warning("Could not access directory while looking for samples {}".format(run_dir))
            return []

        dir_list = next(os.walk(run_dir))[1]  # Gets the list of directories in the directory
        dir_list.append(run_dir)  # Add the current directory to the list too
        return dir_list

    def dir_has_samples_not_uploaded(sample_dir):
        """Find and validate runs in the specified directory.

        Validates if run already has been uploaded, partially uploaded, or not uploaded

        Arguments:
        directory -- the directory to find sequencing runs

        Returns: Boolean,
            True:   Directory has samples not uploaded,
                    Directory has partially uploaded samples

            False:  Directory has no samples
                    Directory samples are already uploaded
                    Directory can not be read, permissions issue
        """

        # Checks if we can write to the directory, return false and log a warning if we cannot.
        if not os.access(sample_dir, os.W_OK):
            logging.warning("Could not access directory while looking for samples {}".format(sample_dir))
            return False

        file_list = next(os.walk(sample_dir))[2]  # Gets the list of files in the directory
        if 'SampleSheet.csv' in file_list:
            if '.miseqUploaderInfo' in file_list:  # Must check status of upload to determine if upload is completed
                uploader_info_file = os.path.join(sample_dir, '.miseqUploaderInfo')
                with open(uploader_info_file, "rb") as reader:
                    info_file = json.load(reader)
                    return info_file["Upload Status"] != "Complete"  # if True, has samples, not completed uploading

            else:  # SampleSheet.csv with no .miseqUploaderInfo file, has samples not uploaded yet
                return True

        return False  # No SampleSheet.csv, does not have samples

    logging.info("looking for sample sheet in {}".format(directory))

    sample_sheets = []
    directory_list = find_run_directory_list(directory)
    for d in directory_list:
        current_directory = os.path.join(directory, d)
        if dir_has_samples_not_uploaded(current_directory):
            sample_sheets.append(os.path.join(current_directory, 'SampleSheet.csv'))

    logging.info("found sample sheets (filtered): {}".format(", ".join(sample_sheets)))

    # Only appending sheets to the list that do not have errors
    # The errors are collected to create a list to show the user
    sequencing_runs = []
    for sheet in sample_sheets:
        try:
            sequencing_runs.append(process_sample_sheet(sheet))
        except SampleSheetError, e:
            logging.exception("Failed to parse sample sheet.")
            send_message(DirectoryScannerTopics.garbled_sample_sheet, sample_sheet=sheet, error=e)
        except SampleError, e:
            logging.exception("Failed to parse sample.")
            send_message(DirectoryScannerTopics.garbled_sample_sheet, sample_sheet=sheet, error=e)
        except SequenceFileError as e:
            logging.exception("Failed to find files for sample sheet.")
            send_message(DirectoryScannerTopics.missing_files, sample_sheet=sheet, error=e)

    send_message(DirectoryScannerTopics.finished_run_scan)

    return sequencing_runs


def process_sample_sheet(sample_sheet):
    """Create a SequencingRun object for the specified sample sheet.

    Arguments:
    sample_sheet -- a `SampleSheet.csv` file that refers to an Illumina
    MiSeq sequencing run.

    Returns: an individual SequencingRun object for the sample sheet,
    ready to be uploaded.
    """

    logging.info("going to parse metadata")
    run_metadata = parse_metadata(sample_sheet)

    logging.info("going to parse samples")
    samples = complete_parse_samples(sample_sheet)

    logging.info("going to build sequencing run")
    sequencing_run = SequencingRun(run_metadata, samples, sample_sheet)

    logging.info("going to validate sequencing run")
    validate_run(sequencing_run)

    send_message(DirectoryScannerTopics.run_discovered, run=sequencing_run)

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
        send_message(sequencing_run.offline_validation_topic, run=sequencing_run, errors=validation.get_errors())
        raise SampleSheetError('Sample sheet {} is invalid. Reason:\n {}'.format(sample_sheet, validation.get_errors()),
                               validation.error_list())

    validation = validate_sample_list(sequencing_run.sample_list)
    if not validation.is_valid():
        raise SampleError('Sample sheet {} is invalid. Reason:\n {}'.format(sample_sheet, validation.get_errors()),
                          validation.error_list())
