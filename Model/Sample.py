"""
    A Sample will store (key: value) pairs using a dictionary.
    e.g  {"sampleID": "01-1111"}
"""

class Sample:
	def __init__(self, newSampleDict):
		self.sampleDict=dict(newSampleDict)
		
	def getID(self):
		return self.get("sampleID")

	def getPairFiles(self):
		return self.get("pairFiles")

	def setPairFiles(self, pairFileList):
		self.sampleDict["pairFiles"]=pairFileList

	def getDict(self):
		return self.sampleDict

	def get(self,key):
		retVal=None
		if self.sampleDict.has_key(key):
			retVal=self.sampleDict[key]
		return retVal

	def __str__(self):
		return str(self.sampleDict)