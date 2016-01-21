from copy import deepcopy
from urlparse import urlparse
from os import path

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

            missing = sample_has_req_keys(sample)
            if len(missing) > 0:
                valid = False
                v_res.add_error_msg(
                    ("{sid} missing {required_val}").format(
                        sid=sample.get_id(),
                        required_val=",".join(missing)))

    else:
        v_res.add_error_msg(
            "The given list of samples is empty." +
            "\nRequires atleast 1 sample in list.")

    v_res.set_valid(valid)
    return v_res


def sample_id_name_match(sample):

    """
    arguments:
            sample -- Sample object

    returns status of Sample_ID and Sample_Name being equal
    """

    return sample.get_id() == sample.get("sampleName")


def sample_has_req_keys(sample):

    """
    Checks if sample has the required keys:
    Sample_Name, Sample_Project and Sample_Id

    arguments:
            sample -- Sample object

    return True if all required keys exist else False
    """

    missing = []
    sample_proj = sample.get("sampleProject")
    sample_name = sample.get("sampleName")
    sample_id = sample.get_id()

    if sample_proj is None or len(sample_proj) == 0:
        missing.append("Sample_Project")
    if sample_name is None or len(sample_name) == 0:
        missing.append("Sample_Name")
    if sample_id is None or len(sample_id) == 0:
        missing.append("Sample_Id")
    return missing


def validate_URL_form(url):

    """
        offline 'validation' of url. parse through url and see if its malformed
    """

    valid = False

    parsed = urlparse(url)

    if len(parsed.scheme) > 0:
        valid = True

    return valid
