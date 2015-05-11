"""
    SampleList class has a list containing a Sample.
    A Sample will store (key: value) pairs using a dictionary.
    e.g  {"Sample_ID": "01-1111"}
"""

class SamplesList:
	def __init__(self, newSamplesList):
		self.samplesList=newSamplesList

	def get(self,sampleID,key):
		retVal=None
		sample=getSample(sampleID)

		if sample!=None and sample.has_key(key):
			retVal=sample[key]
			
		return retVal

	def getPairFiles(self, sampleID):
		retVal=None
		sample=self.getSample(sampleID)
		
		if sample!=None:
			retVal=sample.getPairFiles()

		return retVal
	
	def setPairFiles(self, sampleID, pairFileList):
		sample=self.getSample(sampleID)
		if sample!=None:
			sample.setPairFiles(pairFileList)

	def getSample(self,sampleID):
		retVal=None
		
		for sample in self.samplesList:
			if sample.getID()==sampleID:
				retVal=sample
				break
		return retVal

	def getList(self):
		return self.samplesList

	def __str__(self):
		retStr=""
		for sample in self.samplesList:
			retStr=retStr+str(sample)+"\n"
		return retStr