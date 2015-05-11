from Metadata import Metadata
from SamplesList import SamplesList

class SequencingRun:

	def __init__(self):
		self.samplesList=None
		self.metadata=None

	def getAllMetadata(self):
		return self.metadata.getAllMetadata()

	def setMetadata(self,metadataDict):
		self.metadata=Metadata(metadataDict)
		
	def getWorkflow(self):
		return self.metadata.getWorkflow()

	def getSamplesList(self):
		return self.samplesList.getList()

	def setSamplesList(self, samplesList):
		self.samplesList=SamplesList(samplesList)


	def getSample(self, sampleID):
		return self.samplesList.getSample(sampleID)
	
	def setPairFiles(self, sampleID, pairFileList):
		self.samplesList.setPairFiles(sampleID,pairFileList)
	
	def getPairFiles(self, sampleID):
		return self.samplesList.getPairFiles(sampleID)