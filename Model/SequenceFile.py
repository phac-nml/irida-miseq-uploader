"""
	Holds files to be uploaded and Sample metadata:	
    samplePlate
    sampleWell
    i7IndexID
    index
    i5IndexID
    index2

"""
class SequenceFile:
	def __init__(self):
		self.propertiesDict={}
		self.fileList=[] #files to upload
	
	def getProperties(self):
		self.propertiesDict
	
	def setProperties(self, newPropertiesDict):
		self.propertiesDict=newPropertiesDict
	
	def getFilesToUpload(self):
		return self.fileList

	def addFileToUpload(self, newFile):
		self.fileList.append(newFile)
		
	def get(self,key):
		retVal=None
		if self.propertiesDict.has_key(key):
			retVal=self.propertiesDict[key]
		return retVal