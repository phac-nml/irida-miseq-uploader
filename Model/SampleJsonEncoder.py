import json
from copy import deepcopy

class SampleJsonEncoder(json.JSONEncoder):

    def encode(self, obj):

        new_obj = deepcopy(obj)
        new_obj.pop("sampleProject")

        return json.JSONEncoder.encode(self, new_obj)
