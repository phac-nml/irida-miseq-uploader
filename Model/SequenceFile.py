from os import path
"""
Holds files and Sample metadata:
samplePlate
sampleWell
i7IndexID
index
i5IndexID
index2
etc.
"""


class SequenceFile:

    def __init__(self, properties_dict, file_list):
        self.properties_dict = properties_dict  # Sample metadata
        self.file_list = file_list
        self.file_list.sort()

    def get_properties(self):
        return self.properties_dict

    def get(self, key):
        retVal = None
        if self.properties_dict in key:
            retVal = self.properties_dict[key]
        return retVal

    def get_files_size(self):
        return sum([path.getsize(file) for file in self.file_list])

    def get_files(self):
        return self.file_list

    def __str__(self):
        return str(self.properties_dict) + str(self.file_list)
