import os
import logging

class SequencingRun(object):

    def __init__(self, metadata = None, sample_list = None, sample_sheet = None):
        self._sample_list = sample_list
        self._metadata = metadata

        if sample_sheet is None:
            raise ValueError("Sample sheet cannot be None!")
        self._sample_sheet = sample_sheet
        self._sample_sheet_dir = os.path.dirname(sample_sheet)
        self._sample_sheet_name = os.path.basename(self._sample_sheet_dir)

        for sample in self._sample_list:
            logging.info("Setting run.")
            sample.run = self

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata_dict):
        self._metadata = metadata_dict

    def get_workflow(self):
        return self._metadata["workflow"]

    @property
    def sample_list(self):
        return self._sample_list

    @sample_list.setter
    def sample_list(self, sample_list):
        self._sample_list = sample_list

    @property
    def uploaded_samples(self):
        return filter(lambda sample: sample.already_uploaded, self.sample_list)

    @property
    def samples_to_upload(self):
        return filter(lambda sample: not sample.already_uploaded, self.sample_list)

    def get_sample(self, sample_id):
        for sample in self._sample_list:
            if sample.get_id() == sample_id:
                return sample
        else:
            raise ValueError("No sample with id {} found!.".format(sample_id))

    def set_files(self, sample_id, file_list):
        for sample in self._sample_list:
            if sample.get_id() == sample_id:
                sample.set_files(file_list)
                break

    def get_files(self, sample_id):
        sample = self._get_sample(sample_id)
        return sample.get_files()

    @property
    def sample_sheet(self):
        return self._sample_sheet

    @sample_sheet.setter
    def sample_sheet(self, sample_sheet):
        self._sample_sheet = sample_sheet

    @property
    def sample_sheet_dir(self):
        return self._sample_sheet_dir

    @property
    def sample_sheet_name(self):
        return self._sample_sheet_name

    @property
    def upload_started_topic(self):
        return self._sample_sheet_name + ".upload_started"

    @property
    def upload_progress_topic(self):
        return self._sample_sheet_name + ".upload_progress"

    @property
    def upload_completed_topic(self):
        return self._sample_sheet_name + ".upload_completed"

    @property
    def upload_failed_topic(self):
        return self._sample_sheet_name + ".upload_failed"

    @property
    def offline_validation_topic(self):
        return self._sample_sheet_name + ".offline_validation"

    @property
    def online_validation_topic(self):
        return self._sample_sheet_name + ".online_validation"
