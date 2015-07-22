from threading import Thread
from Validation.onlineValidation import project_exists, sample_exists


class UploadThread(Thread):

    def __init__(self, main_frame_obj):
        Thread.__init__(self)
        self.mf = main_frame_obj
        self.start()

    def run(self):

        """
        uploads each SequencingRun in self.seq_run_list to irida web server

        each SequencingRun will contain a list of samples and each sample
        from the list of samples will contain a pair of sequence files

        for each sample in the sample list, we check if the project_id
        that it's supposed to be uploaded to already exists and
        raises an error if it doesn't

        we then check if the sample's id exists for it's given project_id
        if it doesn't exist then create it

        finally we create a thread which runs api.send_pair_sequence_files()
        and send it the list of samples and our callback function:
        self.pair_upload_callback()

        no return value
        """

        api = self.mf.api
        for sr in self.mf.seq_run_list:

            for sample in sr.get_sample_list():
                if project_exists(api, sample.get_project_id()) is False:
                    raise ProjectError("Project ID: {id} doesn't exist".format(
                                        id=sample.get("sampleProject")))

                if sample_exists(api, sample) is False:
                    api.send_samples(sr.get_sample_list())

            thread = Thread(target=api.send_pair_sequence_files,
                            args=(sr.get_sample_list(),
                                  self.mf.pair_upload_callback,))
            thread.start()

            self.mf.seq_run_list.remove(sr)
