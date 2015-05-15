import sys
sys.path.append("../")

from csv import reader
from copy import deepcopy
from Parsers.miseqParser import getCsvReader
from Model.ValidationResult import ValidationResult

def validateSampleSheet(sampleSheetFile):
	""" 
	Checks if the given sampleSheetFile can be parsed
	Requires [Header] because it contains Workflow
	Requires [Data] for creating Sample objects and requires Sample_ID, Sample_Name, Sample_Project and Description table headers
	
	arguments:
		sampleSheetFile -- path to SampleSheet.csv
		
	returns boolean describing if sampleSheetFile meets requirements
	"""
	
	csvReader=getCsvReader(sampleSheetFile)
	
	vRes=ValidationResult()
	
	valid=False
	allDataHeadersFound=False
	dataSectionFound=False
	headerSectionFound=False
	checkDataHeaders=False
	
	#status of required data headers
	foundDataHeaders={
		"Sample_ID":False,
		"Sample_Name":False,
		"Sample_Project":False,
		"Description":False}
	
	for line in csvReader:
		
		if "[Data]" in line:
			dataSectionFound=True
			checkDataHeaders=True#next line contains data headers
			
		elif "[Header]" in line:
			headerSectionFound=True
			
		elif checkDataHeaders==True:
			
			for dataHeader in foundDataHeaders.keys():
				if dataHeader in line:
					foundDataHeaders[dataHeader]=True
			
			#if all required dataHeaders are found
			if all(foundDataHeaders.values()):
				allDataHeadersFound=True
			
			checkDataHeaders=False
	
	if all([headerSectionFound==True, dataSectionFound==True, allDataHeadersFound==True]):
		valid=True
		
	else:
		if headerSectionFound==False:
			vRes.addErrorMsg("[Header] section not found in SampleSheet")
			
		if dataSectionFound==False:
			vRes.addErrorMsg("[Data] section not found in SampleSheet")
			
		if allDataHeadersFound==False:
			missingStr=""
			for dataHeader in foundDataHeaders:
				if  foundDataHeaders[dataHeader]==False:
					missingStr=missingStr+dataHeader+", "
			
			missingStr=missingStr[:-2]# remove last ", "
			vRes.addErrorMsg("Missing required data header(s): " + missingStr)
	
	vRes.setValid(valid)
	
	return vRes

	
def validatePairFiles(fileList):
	"""
	Validate files in fileList to have a matching pair file. 
	R1 sequence file must have a match of R2 sequence file.
	All files in fileList must have a pair to be valid.
	
	arguments:
		fileList -- list containing fastq.gz files
		doesn't alter fileList
		
	returns boolean describing if all files in fileList having a matching pair
	"""
	
	validationFList=deepcopy(fileList)
	valid=False
	if len(validationFList)>0 and len(validationFList)%2==0:
		valid=True
		
		for file in validationFList:
			if 'R1' in file:
				matchingPairFile=file.replace('R1','R2')
			elif 'R2' in file:
				matchingPairFile=file.replace('R2','R1')
			else:
				valid=False
				break
				
			if matchingPairFile in validationFList:
				validationFList.remove(matchingPairFile)
				validationFList.remove(file)
				
			else:
				valid=False
				break
				
	return valid
	

def validateSampleList(samplesList):
	valid=False
	if len(samplesList) > 0:
		valid=True
		for sample in samplesList:
			res=validateSample(sample)
			if res==False:
				valid=False
				break
		
	return valid

	
def validateSample(sample):
	"""
	Checks if sample has project identifier attached to it
	"""
	valid=False
	
	sampleProj=sample.get("sampleProject")
	if sampleProj!=None and len(sampleProj)>0:
		valid=True
	return valid
	
