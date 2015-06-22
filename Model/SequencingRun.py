class SequencingRun:

    def __init__(self):
        self.sample_list = None
        self.metadata = None

    def get_all_metadata(self):
        return self.metadata

    def set_metadata(self, metadata_dict):
        self.metadata = metadata_dict

    def get_workflow(self):
        return self.metadata["workflow"]

    def get_sample_list(self):
        return self.sample_list

    def set_sample_list(self, sample_list):
        self.sample_list = sample_list

    def get_sample(self, sample_id):
        ret_val = None

        for sample in self.sample_list:
            if sample.get_id() == sample_id:
                ret_val = sample
                break

        return ret_val

    def set_pair_files(self, sample_id, pair_file_list):

        for sample in self.sample_list:
            if sample.get_id() == sample_id:
                sample.set_pair_files(pair_file_list)
                break

    def get_pair_files(self, sample_id):
        sample = self.get_sample(sample_id)
        return sample.get_pair_files()
