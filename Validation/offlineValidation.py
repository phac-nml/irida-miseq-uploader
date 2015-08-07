from csv import reader
from copy import deepcopy
from urlparse import urlparse

from Parsers.miseqParser import get_csv_reader
from Model.ValidationResult import ValidationResult


def validate_sample_sheet(sample_sheet_file):

    """
    Checks if the given sample_sheet_file can be parsed
    Requires [Header] because it contains Workflow
    Requires [Data] for creating Sample objects and requires
        Sample_ID, Sample_Name, Sample_Project and Description table headers

    arguments:
            sample_sheet_file -- path to SampleSheet.csv

    returns ValidationResult object - stores bool valid and
        list of string error messages
    """

    csv_reader = get_csv_reader(sample_sheet_file)

    v_res = ValidationResult()

    valid = False
    all_data_headers_found = False
    data_sect_found = False
    header_sect_found = False
    check_data_headers = False

    # status of required data headers
    found_data_headers = {
        "Sample_ID": False,
        "Sample_Name": False,
        "Sample_Project": False,
        "Description": False}

    for line in csv_reader:

        if "[Data]" in line:
            data_sect_found = True
            check_data_headers = True  # next line contains data headers

        elif "[Header]" in line:
            header_sect_found = True

        elif check_data_headers:

            for data_header in found_data_headers.keys():
                if data_header in line:
                    found_data_headers[data_header] = True

            # if all required dataHeaders are found
            if all(found_data_headers.values()):
                all_data_headers_found = True

            check_data_headers = False

    if all([header_sect_found, data_sect_found, all_data_headers_found]):
        valid = True

    else:
        if header_sect_found is False:
            v_res.add_error_msg("[Header] section not found in SampleSheet")

        if data_sect_found is False:
            v_res.add_error_msg("[Data] section not found in SampleSheet")

        if all_data_headers_found is False:
            missing_str = ""
            for data_header in found_data_headers:
                if found_data_headers[data_header] is False:
                    missing_str = missing_str + data_header + ", "

            missing_str = missing_str[:-2]  # remove last ", "
            v_res.add_error_msg("Missing required data header(s): " +
                                missing_str)

    v_res.set_valid(valid)

    return v_res


def validate_pair_files(file_list):

    """
    Validate files in file_list to have a matching pair file.
    R1 sequence file must have a match of R2 sequence file.
    All files in file_list must have a pair to be valid.

    arguments:
            file_list -- list containing fastq.gz files
            doesn't alter file_list

    returns ValidationResult object - stores bool valid and
        list of string error messages
    """

    v_res = ValidationResult()
    validation_file_list = deepcopy(file_list)
    valid = False
    if len(validation_file_list) > 0 and len(validation_file_list) % 2 == 0:
        valid = True

        for file in validation_file_list:
            if 'R1' in file:
                matching_pair_file = file.replace('R1', 'R2')
            elif 'R2' in file:
                matching_pair_file = file.replace('R2', 'R1')
            else:
                valid = False
                v_res.add_error_msg(
                    file + " doesn't contain either 'R1' or 'R2' in filename" +
                    ".\nRequired for identifying sequence files.")
                break

            if matching_pair_file in validation_file_list:
                validation_file_list.remove(matching_pair_file)
                validation_file_list.remove(file)

            else:
                valid = False
                v_res.add_error_msg("No pair sequence file found for: " +
                                    file +
                                    "\nRequired matching sequence file: " +
                                    matching_pair_file)
                break

    else:
        v_res.add_error_msg(
            "The given file list has an odd number of files." +
            "\nRequires an even number of files in order for each " +
            "sequence file to have a pair.\n" +
            "Given file list:\n " + "\n ".join(file_list))

    v_res.set_valid(valid)
    return v_res


def validate_sample_list(sample_list):

    """
    Iterates through given samples list and tries to validate each sample via
        validate_sample method - sample must have a "sampleProject" key

    arguments:
            sample_list -- list containing Sample objects

    returns ValidationResult object - stores bool valid and
        list of string error messages
    """

    valid = False
    v_res = ValidationResult()
    if len(sample_list) > 0:
        valid = True
        for sample in sample_list:

            res = sample_has_req_keys(sample)
            if res is False:
                valid = False
                v_res.add_error_msg(
                    ("{sid} is missing at least one of the required values: " +
                    "Sample_Name, Sample_Project or Sample_Id").format(
                        sid=sample.get_id()))
                break

            # Sample_ID and Sample_Name must be equal
            res = sample_id_name_match(sample)
            if res is False:
                valid = False
                v_res.add_error_msg(sample.get_id() +
                                    " does not match Sample_Name: " +
                                    sample.get("sampleName"))
                break

    else:
        v_res.add_error_msg(
            "The given list of samples is empty." +
            "\nRequires atleast 1 sample in list.")

    v_res.set_valid(valid)
    return v_res


def sample_id_name_match(sample):

    """
    returns status of Sample_ID and Sample_Name being equal
    """

    return sample.get_id() == sample.get("sampleName")

def sample_has_req_keys(sample):

    """
    Checks if sample has the required keys
    Sample_Name, Sample_Project and Sample_Id
    """

    sample_proj = sample.get("sampleProject")
    sample_name = sample.get("sampleName")
    sample_id = sample.get_id()
    return (sample_proj is not None and
            len(sample_proj) > 0 and
            sample_name is not None and
            len(sample_name) > 0 and
            sample_id is not None and
            len(sample_id) > 0)

def validate_URL_form(url):

    """
        offline 'validation' of url. parse through url and see if its malformed
    """

    valid = False

    parsed = urlparse(url)

    if len(parsed.scheme) > 0:
        valid = True

    return valid
