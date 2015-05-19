"""
    A Sample will store (key: value) pairs using a dictionary.
    e.g  {"sequencerSampleId": "01-1111"}
	Keys: 'sampleName','description','sequencerSampleId','sampleProject'
"""

class Sample:
	def __init__(self, newSampleDict):
		self.sampleDict=dict(newSampleDict)
		self.seqFile=None
	
	def getID(self):
		return self.get("sequencerSampleId")

	def getDict(self):
		return self.sampleDict

	def get(self,key):
		retVal=None
		if self.sampleDict.has_key(key):
			retVal=self.sampleDict[key]
		return retVal
	
	def getSampleMetadata(self):
		return self.seqFile.getProperties()
	
	def getPairFiles(self):
		return self.seqFile.getPairFiles()
	
	def setSeqFile(self, newSeqFile):
		self.seqFile=newSeqFile
	
	def __str__(self):
		return str(self.sampleDict) + str(self.seqFile)