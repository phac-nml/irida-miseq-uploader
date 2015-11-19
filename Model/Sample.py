import json
"""
A Sample will store (key: value) pairs using a dictionary.
e.g  {"sequencerSampleId": "01-1111"}
Keys: 'sampleName','description','sequencerSampleId','sampleProject'
"""


class Sample:

    def __init__(self, new_samp_dict):
        self.sample_dict = dict(new_samp_dict)
        self.seq_file = None

    def get_id(self):
        return self.get("sampleName")

    def get_project_id(self):
        return self.get("sampleProject")

    def get_dict(self):
        return self.sample_dict

    def __getitem__(self, key):
        ret_val = None
        if key in self.sample_dict:
            ret_val = self.sample_dict[key]
        return ret_val

    def get(self, key):
        return self.__getitem__(key)

    def get_sample_metadata(self):
        return self.seq_file.get_properties()

    def get_pair_files(self):
        return self.seq_file.get_pair_files()

    def get_pair_files_size(self):
        return self.seq_file.get_pair_files_size()

    def set_seq_file(self, seq_file):
        self.seq_file = seq_file

    def __str__(self):
        return str(self.sample_dict) + str(self.seq_file)

    class JsonEncoder(json.JSONEncoder):

        def default(self, obj):

            if isinstance(obj, Sample):
                sample_dict = dict(obj.get_dict())
                # get sample dict and make a copy of it
                sample_dict.pop("sampleProject")
                return sample_dict
            else:
                return json.JSONEncoder.default(self, obj)
