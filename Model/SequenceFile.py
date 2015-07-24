from os import path
"""
Holds pair files and Sample metadata:
samplePlate
sampleWell
i7IndexID
index
i5IndexID
index2
etc.
"""


class SequenceFile:

    def __init__(self, properties_dict, pair_file_list):
        self.properties_dict = properties_dict  # Sample metadata
        self.pair_file_list = pair_file_list
        self.pair_file_list.sort()

    def get_properties(self):
        return self.properties_dict

    def get(self, key):
        retVal = None
        if self.properties_dict in key:
            retVal = self.properties_dict[key]
        return retVal

    def get_pair_files_size(self):
        return sum([path.getsize(file) for file in self.pair_file_list])

    def get_pair_files(self):
        return self.pair_file_list

    def __str__(self):
        return str(self.properties_dict) + str(self.pair_file_list)
