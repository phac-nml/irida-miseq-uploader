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
		self.fileList.sort()
		return self.fileList
	
	def addFilesToUpload(self, fileList):
		self.fileList.extend(fileList)
	
	def addFileToUpload(self, newFile):
		self.fileList.append(newFile)
		
	def get(self,key):
		retVal=None
		if self.propertiesDict.has_key(key):
			retVal=self.propertiesDict[key]
		return retVal