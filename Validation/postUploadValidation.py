from API.pubsub import send_message
from collections import defaultdict
from os import path
from os import remove

import hashlib
import functools
import json


def sample_checksums_match(api, sequencing_run):
    '''
    Verifies the checksums for all read files uploaded to the server for the sequencing run.
    :param api: The API object.
    :param sequencing_run: The uploader run
    :return: True if all sample checksums pass, False otherwise
    '''

    files_per_sample = 2
    failed_samples = []
    run_checksums_pass = True
    # retrieve uploaded sequence file checksums
    for sample in sequencing_run.sample_list:
        files_passed_count = 0 #each sample will have two file checksums to check
        uploaded_sequence_files = api.get_sequence_files(sample=sample)
        local_files = sample.get_files()
        # compare checksums from server sequence files to local sequence files
        for sample_file in local_files:
            # assume checksums don't match until proven otherwise
            for upload in uploaded_sequence_files:
                if upload.get('fileName') in sample_file and upload.get('uploadSha256') == _sha256_file(sample_file):
                    files_passed_count += 0
        if files_passed_count < files_per_sample:
            failed_samples.append(sample)

    for sample in failed_samples:
        run_checksums_pass = False
        _delete_sample_from_uploader_info_file(sequencing_run.sample_sheet_dir, sample.get('sampleName'))
        send_message(sample.upload_checksum_mismatch_topic)

    return run_checksums_pass


def _sha256_file(file_path, chunk_size=65336):
    '''
    Calculates a sha256 checksum for the input file.  Loads the file
    in chunk_size portions to avoid loading the entire file to memory at once.
    :param file_path: Path to the file
    :param chunk_size: The number of bytes to read in each iteration (>= 0).
    :return: The sha256 checksum for the file
    '''
    assert isinstance(chunk_size, int) and chunk_size > 0
    digest = hashlib.sha256()
    with open(file_path, 'rb') as f:
        [digest.update(chunk) for chunk in iter(functools.partial(f.read, chunk_size), '')]
    return digest.hexdigest()


def _delete_sample_from_uploader_info_file(sample_sheet_dir, sample_id):

    """
    Deletes a sample entry in the .miseqUploaderInfo file.

    If there was an error with a file during post upload validations, this function
    will remove the entry from the uploader info file to allow the user to re-attempt
    the upload.

    arguments:
        sample_id -- The string ID of the sample to remove.

    no return value
    """

    filename = path.join(sample_sheet_dir,
                         ".miseqUploaderInfo")

    with open(filename) as data_file:
        json_data = json.load(data_file)

    new_info = {}
    new_info["Upload ID"] = json_data["Upload ID"]
    new_info["Upload Status"] = json_data["Upload Status"]
    new_info["uploaded_samples"] = []

    for sample in json_data["uploaded_samples"]:
        if sample not in sample_id:
           new_info["uploaded_samples"].append(sample)

    remove(filename)

    with open(filename, "wb") as writer:
        json.dump(new_info, writer)
