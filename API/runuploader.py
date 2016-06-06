from Validation.onlineValidation import project_exists, sample_exists
from Exceptions.ProjectError import ProjectError
from API.pubsub import send_message

from os import path
from wx.lib.pubsub import pub

import json
import logging
import threading

class RunUploaderTopics(object):
    start_online_validation = "start_online_validation"
    online_validation_failure = "online_validation_failure"
    start_checking_samples = "start_checking_samples"
    start_uploading_samples = "start_uploading_samples"
    finished_uploading_samples = "finished_uploading_samples"

class RunUploader(threading.Thread):
    def __init__(self, api, runs, name='RunUploaderThread'):
        self._stop_event = threading.Event()
        self._sleep_period = 1.0
        self._api = api
        self._runs = runs
        threading.Thread.__init__(self, name=name)

    def run(self):
        for run in self._runs:
            upload_run_to_server(api=self._api, sequencing_run=run, progress_callback=None)

    def join(self, timeout=None):
        logging.info("Going to try killing connections on exit.")
        self._api._kill_connections()
        threading.Thread.join(self, timeout)

def upload_run_to_server(api, sequencing_run, progress_callback):
    """Upload a single run to the server.

    Arguments:
    api -- the API object to use for interacting with the server
    sequencing_run -- the run to upload to the server
    progress_callback -- the function to call for indicating upload progress

    Publishes messages:
    start_online_validation -- when running an online validation (checking project ids) starts
    online_validation_failure (params: project_id, sample_id) -- when the online validation fails
    start_checking_samples -- when initially checking to see which samples should be created on the server
    start_uploading_samples (params: sheet_dir) -- when actually initiating upload of the samples in the run
    finished_uploading_samples (params: sheet_dir) -- when uploading the samples has completed
    """

    filename = path.join(sequencing_run.sample_sheet_dir,
                         ".miseqUploaderInfo")


    def _handle_upload_sample_complete(sample):
        """Handle the event that happens when a sample has finished uploading.

        """

        with open(filename, "rb") as reader:
            uploader_info = json.load(reader)
            logging.info(uploader_info)
            if not 'uploaded_samples' in uploader_info:
                uploader_info['uploaded_samples'] = list()

            uploader_info['uploaded_samples'].append(sample.get_id())
        with open(filename, 'wb') as writer:
            json.dump(uploader_info, writer)
        logging.info("Finished updating info file.")

    def _sample_already_uploaded(sample):
        """Check whether or not a sample was already uploaded
        """
        with open(filename, "rb") as reader:
            uploader_info = json.load(reader)
            logging.info(uploader_info)
            try:
                logging.info("Checking if {} was already uploaded in {}.".format(sample.get_id(), uploader_info['uploaded_samples']))
                return sample.get_id() in uploader_info['uploaded_samples']
            except KeyError:
                logging.info("sample {} was not uploaded.".format(sample.get_id()))
                return False

    # do online validation first.
    _online_validation(api, sequencing_run)
    # then do actual uploading

    if not path.exists(filename):
        logging.info("Going to create a new sequencing run on the server.")
        run_on_server = api.create_seq_run(sequencing_run.metadata)
        run_id = run_on_server["resource"]["identifier"]
        _create_miseq_uploader_info_file(sequencing_run.sample_sheet_dir, run_id, "Uploading")
    else:
        logging.info("Resuming upload.")
        with open(filename, "rb") as reader:
            uploader_info = json.load(reader)
            run_id = uploader_info['Upload ID']

    send_message(RunUploaderTopics.start_checking_samples)
    logging.info("Starting to check samples. [{}]".format(len(sequencing_run.sample_list)))
    # only send samples that aren't already on the server
    samples_to_create = filter(lambda sample: not sample_exists(api, sample), sequencing_run.sample_list)
    logging.info("Sending samples to server: [{}].".format(", ".join([str(x) for x in samples_to_create])))
    api.send_samples(samples_to_create)

    pub.subscribe(_handle_upload_sample_complete, 'completed_uploading_sample')

    samples_to_upload = filter(lambda sample: not _sample_already_uploaded(sample), sequencing_run.sample_list)
    skipped_samples = filter(lambda sample: _sample_already_uploaded(sample), sequencing_run.sample_list)

    send_message("start_uploading_samples", sheet_dir = sequencing_run.sample_sheet_dir,
                                               skipped_sample_ids = [sample.get_id() for sample in skipped_samples],
                                               run_id = run_id)
    send_message(sequencing_run.upload_started_topic)

    logging.info("About to start uploading samples.")
    api.send_sequence_files(samples_list = samples_to_upload,
                                 callback = progress_callback, upload_id = run_id)
    send_message("finished_uploading_samples", sheet_dir = sequencing_run.sample_sheet_dir)
    send_message(sequencing_run.upload_completed_topic)
    api.set_seq_run_complete(run_id)
    _create_miseq_uploader_info_file(sequencing_run.sample_sheet_dir, run_id, "Complete")


def _online_validation(api, sequencing_run):
    """Do online validation for the specified sequencing run.

    Arguments:
    api -- the API object to use for interacting with the server
    sequencing_run -- the run to validate

    Publishes messages:
    start_online_validation -- when running online validation
    online_validation_failure (params: project_id, sample_id) -- when the online validation fails
    """
    send_message("start_online_validation")
    for sample in sequencing_run.sample_list:
        if not project_exists(api, sample.get_project_id()):
            send_message("online_validation_failure", project_id=sample.get_project_id(), sample_id=sample.get_id())
            raise ProjectError("The Sample_Project: {pid} doesn't exist in IRIDA for Sample_Id: {sid}".format(
                    sid=sample.get_id(),
                    pid=sample.get_project_id()))

def _create_miseq_uploader_info_file(sample_sheet_dir, upload_id, upload_status):

    """
    creates a .miseqUploaderInfo file
    Contains Upload ID and Upload Status
    Upload ID is is the SequencingRun's identifier in IRIDA
    Upload Status will either be "Complete" or the last sequencing file
    that was uploaded.
    If there was an error with the upload then the last sequencing file
    uploaded will be written so that the program knows from which point to
    resume when the upload is restarted

    arguments:
        upload_status -- string that's either "Complete" or
                         string list of completed sequencing file path
                         uploads if upload was interrupted
                         used to know which files still need to be uploaded
                         when resuming upload

    no return value
    """

    filename = path.join(sample_sheet_dir,
                         ".miseqUploaderInfo")
    info = {
        "Upload ID": upload_id,
        "Upload Status": upload_status
    }
    with open(filename, "wb") as writer:
        json.dump(info, writer)
