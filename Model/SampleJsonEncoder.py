import json


class SampleJsonEncoder(json.JSONEncoder):

    def encode(self, obj):

        item = obj.pop("sampleProject")

        res = json.JSONEncoder.encode(self, obj)

        obj["sampleProject"] = item

        return res
