import re
from os import path, listdir
from fnmatch import translate as fn_translate
from csv import reader
from collections import OrderedDict
from copy import deepcopy
import logging

from Model.Sample import Sample
from Model.SequenceFile import SequenceFile
from Exceptions.SampleSheetError import SampleSheetError
from API.fileutils import find_file_by_name


def parse_metadata(sample_sheet_file):

    """
    Parse all lines under [Header], [Reads] and [Settings] in .csv file
    Lines under [Reads] are stored in a list with key name "readLengths"
    All other key names are translated according to the
        metadata_key_translation_dict

    arguments:
            sample_sheet_file -- path to SampleSheet.csv

    returns a dictionary containing the parsed key:pair values from .csv file
    """

    metadata_dict = {}
    metadata_dict["readLengths"] = []

    csv_reader = get_csv_reader(sample_sheet_file)
    add_next_line_to_dict = False

    metadata_key_translation_dict = {
        'Assay': 'assay',
        'Description': 'description',
        'Application': 'application',
        'Investigator Name': 'investigatorName',
        'Adapter': 'adapter',
	'AdapterRead2': 'adapterread2',
        'Workflow': 'workflow',
        'ReverseComplement': 'reversecomplement',
        'IEMFileVersion': 'iemfileversion',
        'Date': 'date',
        'Experiment Name': 'experimentName',
        'Chemistry': 'chemistry',
        'Project Name': 'projectName'
    }

    for line in csv_reader:

        if any(["[Header]" in line, "[Reads]" in line, "[Settings]" in line]):
            add_next_line_to_dict = True

        elif add_next_line_to_dict:

            if len(line) == 2:
                key_name = metadata_key_translation_dict[line[0]]
                metadata_dict[key_name] = line[1]

            elif len(line) == 1:  # case for "[Reads]"

                metadata_dict["readLengths"].append(line[0])

            elif len(line) == 0:  # current line is blank; end of section
                add_next_line_to_dict = False

        elif "[Data]" in line:
            break

    # currently sends just the larger readLengths
    if len(metadata_dict["readLengths"]) > 0:
        if len(metadata_dict["readLengths"]) == 2:
            metadata_dict["layoutType"] = "PAIRED_END"
        else:
            metadata_dict["layoutType"] = "SINGLE_END"
        metadata_dict["readLengths"] = max(metadata_dict["readLengths"])
    else:
        # this is an exceptional case, you can't have no read lengths!
        raise SampleSheetError("Sample sheet must have read lenghts!")

    return metadata_dict


def complete_parse_samples(sample_sheet_file):

    """
    Creates a complete Sample object:
    Sample dict will only have the required (and already translated) keys:
        'sampleName', 'description', 'sequencerSampleId' 'sampleProject'.
    SequenceFile parsed out and holds Sample metadata (other keys) +
        pair files for the sample.
    SequenceFile is then set as an attribute of Sample
    These Sample objects will be stored in a list.

    arguments:
            sample_sheet_file -- path to SampleSheet.csv

    returns list containing complete Sample objects
    """

    sample_list = parse_samples(sample_sheet_file)
    data_dir = path.dirname(sample_sheet_file)
    fastq_files = find_file_by_name(directory = data_dir,
                                    name_pattern = '.*.fastq.*')
    for sample in sample_list:
        properties_dict = parse_out_sequence_file(sample)
        # this is the Illumina-defined pattern for naming fastq files, from:
        # http://support.illumina.com/content/dam/illumina-support/help/BaseSpaceHelp_v2/Content/Vault/Informatics/Sequencing_Analysis/BS/swSEQ_mBS_FASTQFiles.htm
        # and also referred to in BaseSpace:
        # http://blog.basespace.illumina.com/2014/08/18/fastq-upload-in-now-available-in-basespace/
        file_pattern = re.escape(sample.get_id()) + "_S\\d+_L\\d{3}_R(\\d+)_\\S+\\.fastq.*$"
        pf_list = find_file_by_name(directory = data_dir,
                                    name_pattern = file_pattern)
        sq = SequenceFile(properties_dict, pf_list)

        sample.set_seq_file(deepcopy(sq))

    return sample_list


def parse_samples(sample_sheet_file):

    """
    Parse all the lines under "[Data]" in .csv file
    Keys in sample_key_translation_dict have their values changed for
        uploading to REST API
    All other keys keep the same name that they have in .csv file

    arguments:
            sample_sheet_file -- path to SampleSheet.csv

    returns	a list containing Sample objects that have been created by a
        dictionary from the parsed out key:pair values from .csv file
    """

    csv_reader = get_csv_reader(sample_sheet_file)
    # start with an ordered dictionary so that keys are ordered in the same
    # way that they are inserted.
    sample_dict = OrderedDict()
    sample_list = []

    sample_key_translation_dict = {
        'Sample_Name': 'sampleName',
        'Description': 'description',
        'Sample_ID': 'sequencerSampleId',
        'Sample_Project': 'sampleProject'
    }

    parse_samples.sample_key_translation_dict = sample_key_translation_dict

    # initilize dictionary keys from first line (data headers/attributes)
    set_attributes = False
    for line in csv_reader:

        if set_attributes:
            for item in line:

                if item in sample_key_translation_dict:
                    key_name = sample_key_translation_dict[item]
                else:
                    key_name = item

                sample_dict[key_name] = ""

            break

        if "[Data]" in line:
            set_attributes = True

    # fill in values for keys. line is currently below the [Data] headers
    for line in csv_reader:

        i = 0

        if len(sample_dict.keys()) != len(line):
            """
            if there is one more Data header compared to the length of
            data values then add an empty string to the end of data values
            i.e the Description will be empty string
            assumes the last Data header is going to be the Description
            this handles the case where the last trailing comma is trimmed

            Shaun said this issue may come up when a user edits the
            SampleSheet from within the MiSeq software
            """
            if len(sample_dict.keys()) - len(line) == 1:
                line.append("")
            else:
                raise SampleSheetError(
                    "Number of values doesn't match number of " +
                    "[Data] headers. " +
                    ("Number of [Data] headers: {data_len}. " +
                     "Number of values: {val_len}").format(
                        data_len=len(sample_dict.keys()),
                        val_len=len(line)
                    )
                )

        for key in sample_dict.keys():
            sample_dict[key] = line[i]  # assumes values are never empty
            i = i + 1

        if len(sample_dict["sampleName"]) == 0:
            sample_dict["sampleName"] = sample_dict["sequencerSampleId"]

        sample = Sample(deepcopy(sample_dict))
        sample_list.append(sample)

    return sample_list


def parse_out_sequence_file(sample):

    """
    Removes keys in argument sample that are not in sample_keys and
        stores them in sequence_file_dict

    arguments:
            sample -- Sample object
            the dictionary inside the Sample object is changed

    returns a dictionary containing keys not in sample_keys to be used to
        create a SequenceFile object
    """

    sample_keys = ["sampleName", "description",
                   "sequencerSampleId", "sampleProject"]
    sequence_file_dict = {}
    sample_dict = sample.get_dict()
    for key in sample_dict.keys()[:]:  # iterate through a copy
        if key not in sample_keys:
            sequence_file_dict[key] = sample_dict[key]
            del sample_dict[key]

    return sequence_file_dict


def get_csv_reader(sample_sheet_file):

    """
    tries to create a csv.reader object which will be used to
        parse through the lines in SampleSheet.csv
    raises an error if:
            sample_sheet_file is not an existing file
            sample_sheet_file contains null byte(s)

    arguments:
            data_dir -- the directory that has SampleSheet.csv in it

    returns a csv.reader object
    """

    if path.isfile(sample_sheet_file):
        csv_file = open(sample_sheet_file, "rb")
        # strip any trailing newline characters from the end of the line
        # including Windows newline characters (\r\n)
        csv_lines = [x.rstrip('\n') for x in csv_file]
        csv_lines = [x.rstrip('\r') for x in csv_lines]
        # strip any trailing commas added by excel from the end of the line.
        csv_lines = [re.sub(',{2,}$', '', x) for x in csv_lines]

        # open and read file in binary then send it to be parsed by csv's
        # reader
        csv_reader = reader(csv_lines)
    else:
        msg = sample_sheet_file + " is not a valid SampleSheet file (it's"
        msg += "not a valid CSV file)."
        raise SampleSheetError(msg)

    return csv_reader


def get_all_fastq_files(data_dir):
    """
    recursively go down data_dir and get all fastq files

    arguments:
            data_dir -- the directory that has SampleSheet.csv in it

    return list containing path for fastq files
    """

    pattern = fn_translate("*.fastq.*")
    fastq_files_path = path.join(data_dir, "Data", "Intensities", "BaseCalls")

    try:
        file_list = listdir(fastq_files_path)
        fastq_file_list = [path.join(fastq_files_path, file)
                           for file in file_list if re.match(pattern, file)]
        fastq_file_list.sort()

    except OSError:
        msg = "Invalid directory " + fastq_files_path
        raise OSError(msg)

    return fastq_file_list


def get_pair_files(fastq_file_list, sample_id):

    """
    find the pair sequence files for the given sample_id
    raises an error if no sequence pair files found

    arguments:
            fastq_file_list -- list containing path for fastq files
            sample_id -- ID of the sample for the pair files


    returns a list containing the path of the pair files
    """

    pair_file_list = []

    pattern = re.escape(sample_id) + "_S\\d+_L\\d{3}_R(\\d+)_\\S+\\.fastq.*$"
    # this is the Illumina-defined pattern for naming fastq files, from:
    # http://support.illumina.com/content/dam/illumina-support/help/BaseSpaceHelp_v2/Content/Vault/Informatics/Sequencing_Analysis/BS/swSEQ_mBS_FASTQFiles.htm
    # and also referred to in BaseSpace:
    # http://blog.basespace.illumina.com/2014/08/18/fastq-upload-in-now-available-in-basespace/

    for fastq_file in fastq_file_list:
        match = re.search(pattern, fastq_file)
        if match is not None:
            pair_file_list.append(fastq_file)
            pair_file_list.sort()

    return pair_file_list
