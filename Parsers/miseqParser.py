import re
from os import path, listdir, walk
from fnmatch import translate as fn_translate
from csv import reader
from collections import OrderedDict
from copy import deepcopy
import logging
import json

from Model.Sample import Sample
from Model.SequenceFile import SequenceFile
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError


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

    section = None

    for line in csv_reader:
        if "[Header]" in line or "[Settings]" in line:
            section = "header"
            continue
        elif "[Reads]" in line:
            section = "reads"
            continue
        elif "[Data]" in line:
            break
        elif line and line[0].startswith("["):
            section = "unknown"
            continue

        if not line or not line[0]:
            continue

        if not section:
            raise SampleSheetError("This sample sheet doesn't have any sections.",
                                   ["The sample sheet is missing important sections: no sections were found."])
        elif section is "header":
            try:
                key_name = metadata_key_translation_dict[line[0]]
                metadata_dict[key_name] = line[1]
            except KeyError:
                logging.info("Unexpected key in header: [{}]".format(line[0]))
        elif section is "reads":
            metadata_dict["readLengths"].append(line[0])

    # currently sends just the larger readLengths
    if len(metadata_dict["readLengths"]) > 0:
        if len(metadata_dict["readLengths"]) == 2:
            metadata_dict["layoutType"] = "PAIRED_END"
        else:
            metadata_dict["layoutType"] = "SINGLE_END"
        metadata_dict["readLengths"] = max(metadata_dict["readLengths"])
    else:
        # this is an exceptional case, you can't have no read lengths!
        raise SampleSheetError("Sample sheet must have read lengths!",
                               ["The sample sheet is missing important sections: no [Reads] section found."])

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

    def validate_pf_list(file_list):
        """
        Checks if list of files is valid:

        arguments:
                file_list -- list of file names that are grouped together

        returns:
                True: 1 file in list
                True: 2 files in list, where one contains `R1` in the correct position and the other contains `R2`
                False: Number of files <1 or >2, or 2 files do not contain `R1`/`R2` correctly
        """

        if len(file_list) > 2:  # We should never expect more than 2 files, a forward & backwards read
            return False
        elif len(file_list) == 1:  # single read, valid
            return True
        else:
            # check if one file is R1 and other is R2
            regex_filter = ".*_S\\d+_L\\d{3}_R(\\d+)_\\S+\\.fastq.*$"
            n1 = int(re.search(regex_filter, file_list[0]).group(1))
            n2 = int(re.search(regex_filter, file_list[1]).group(1))
            return (n1 != n2) and (n1 == 1 or n1 == 2) and (n2 == 1 or n2 == 2)

    sample_list = parse_samples(sample_sheet_file)
    sample_sheet_dir = path.dirname(sample_sheet_file)
    data_dir = path.join(sample_sheet_dir, "Data", "Intensities", "BaseCalls")
    data_dir_file_list = next(walk(data_dir))[2]  # Create a file list of the data directory, only hit the os once
    uploader_info_file = path.join(sample_sheet_dir, ".miseqUploaderInfo")

    try:
        with open(uploader_info_file, "rb") as info_reader:
            uploader_info = json.load(info_reader)
    except IOError:
        uploader_info = None

    for sample in sample_list:
        properties_dict = parse_out_sequence_file(sample)
        # this is the Illumina-defined pattern for naming fastq files, from:
        # http://blog.basespace.illumina.com/2014/08/18/fastq-upload-in-now-available-in-basespace/
        file_pattern = "{sample_name}_S{sample_number}_L\\d{{3}}_R(\\d+)_\\S+\\.fastq.*$".format(
            sample_name=re.escape(sample.sample_name), sample_number=sample.sample_number)
        logging.info("Looking for files with pattern {}".format(file_pattern))
        regex = re.compile(file_pattern)
        pf_list = filter(regex.search, data_dir_file_list)
        if not pf_list:
            # OK. So we didn't find any files using the **correct** file name
            # definition according to Illumina. Let's try again with our deprecated
            # behaviour, where we didn't actually care about the sample number:
            file_pattern = "{sample_name}_S\\d+_L\\d{{3}}_R(\\d+)_\\S+\\.fastq.*$".format(
                sample_name=re.escape(sample.get_id()))
            logging.info("Looking for files with pattern {}".format(file_pattern))

            regex = re.compile(file_pattern)
            pf_list = filter(regex.search, data_dir_file_list)

            if not pf_list:
                # we **still** didn't find anything. It's pretty likely, then that
                # there aren't any fastq files in the directory that match what
                # the sample sheet says...
                raise SequenceFileError(
                    ("The uploader was unable to find an files with a file name that ends with "
                     ".fastq.gz for the sample in your sample sheet with name {} in the directory {}. "
                     "This usually happens when the Illumina MiSeq Reporter tool "
                     "does not generate any FastQ data.").format(
                        sample.get_id(), data_dir), ["Sample {}".format(sample.get_id())])

        # List of files may be invalid if directory searching in has been modified by user
        if not validate_pf_list(pf_list):
            raise SequenceFileError(
                ("The following file list {} found in the directory {} is invalid. "
                 "Please verify the folder containing the sequence files matches the SampleSheet file").format(
                    pf_list, data_dir), ["Sample {}".format(sample.get_id())])

        # Add the dir to each file to create the full path
        for i in xrange(len(pf_list)):
            pf_list[i] = path.join(data_dir, pf_list[i])

        sq = SequenceFile(properties_dict, pf_list)
        sample.set_seq_file(deepcopy(sq))

        if uploader_info is not None:
            try:
                sample.already_uploaded = sample.get_id() in uploader_info['uploaded_samples']
                logging.info("Sample {} was already uploaded.".format(sample.get_id()))
            except KeyError:
                logging.info("Sample {} was not already uploaded.".format(sample.get_id()))
                pass

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
    for sample_number, line in enumerate(csv_reader):

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
                    ), [("Your sample sheet is malformed. I expected to find {} "
                         "columns the [Data] section, but I only found {} columns "
                         "for line {}.".format(len(sample_dict.keys()), len(line), line))]
                )

        for index, key in enumerate(sample_dict.keys()):
            sample_dict[key] = line[index].strip()  # assumes values are never empty

        if len(sample_dict["sampleName"]) == 0:
            sample_dict["sampleName"] = sample_dict["sequencerSampleId"]

        sample = Sample(deepcopy(sample_dict), sample_number=sample_number+1)
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

        # open and read file in binary then send it to be parsed by csv's
        # reader
        csv_reader = reader(csv_lines)
    else:
        msg = sample_sheet_file + " is not a valid SampleSheet file (it's"
        msg += "not a valid CSV file)."
        raise SampleSheetError(msg, ["SampleSheet.csv cannot be parsed as a CSV file because it's not a regular file."])

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
        fastq_file_list = [path.join(fastq_files_path, f)
                           for f in file_list if re.match(pattern, f)]
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
