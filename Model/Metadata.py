"""
    Metadata will store (key: value) using a dictionary.
    e.g  {"IEMFileVersion": "4"}
"""
class Metadata:
	def __init__(self, newMetadataDict):
		self.metadataDict=newMetadataDict

	def get(self,key):
		retVal=None
		if self.metadataDict.has_key(key):
			retVal=self.metadataDict[key]
		return retVal
	
	def getWorkflow(self):
		return self.get("Workflow")
		
	def getAllMetadata(self):
		return self.metadataDict

	def __str__(self):
		return str(self.metadataDict)