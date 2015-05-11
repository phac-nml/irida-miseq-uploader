class SequencingRun:

	def __init__(self):
		self.samplesList=None
		self.metadata=None
		

	def getAllMetadata(self):
		return self.metadata

	def setMetadata(self,metadataDict):
		self.metadata=metadataDict
		
	def getWorkflow(self):
		return self.metadata["workflow"]

	def getSamplesList(self):
		return self.samplesList

	def setSamplesList(self, newSamplesList):
		self.samplesList=newSamplesList


	def getSample(self, sampleID):
		retVal=None
		
		for sample in self.samplesList:
			if sample.getID()==sampleID:
				retVal=sample
				break
				
		return retVal
		
	
	def setPairFiles(self, sampleID, pairFileList):
		
		for sample in self.samplesList:
			if sample.getID()==sampleID:
				sample.setPairFiles(pairFileList)
				break
		
	
	def getPairFiles(self, sampleID):
		sample=self.getSample(sampleID)
		return sample.getPairFiles()