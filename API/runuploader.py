from Validation.onlineValidation import project_exists, sample_exists
from pubsub import pub
import logging

def upload_run_to_server(api, sequencing_run, progress_callback):
    # do online validation first.
    online_validation(api, sequencing_run)
    # then do actual uploading

    # for now, always create a new run instead of attempting to resume
    run_on_server = api.create_paired_seq_run(sequencing_run.metadata)
    run_id = run_on_server["resource"]["identifier"]

    pub.sendMessage("start_checking_samples")
    logging.info("Starting to check samples.")
    # only send samples that aren't already on the server
    samples_to_create = filter(lambda sample: not sample_exists(api, sample), sequencing_run.sample_list)
    logging.info("Sending samples to server: [{}].".format("".join(samples_to_create)))
    api.send_samples(samples_to_create)

    pub.sendMessage("start_uploading_samples", sheet_dir = sequencing_run.sample_sheet_dir)
    logging.info("About to start uploading samples.")
    api.send_pair_sequence_files(samples_list = sequencing_run.sample_list,
                                 callback = progress_callback, upload_id = run_id,
                                 prev_uploaded_samples = None,
                                 uploaded_samples_q = None)
    pub.sendMessage("finished_uploading_samples", sheet_dir = sequencing_run.sample_sheet_dir)
    api.set_pair_seq_run_complete(run_id)

def online_validation(api, sequencing_run):
    pub.sendMessage("start_online_validation")
    for sample in sequencing_run.sample_list:
        if not project_exists(api, sample.get_project_id()):
            pub.sendMessage("online_validation_failure", project_id=sample.get_project_id(), sample_id=sample.get_id())
            raise ProjectError("The Sample_Project: {pid} doesn't exist in IRIDA for Sample_Id: {sid}").format(
                    sid=sample.get_id(),
                    pid=sample.get_project_id())
