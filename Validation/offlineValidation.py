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
	requiredDataHeaders=[
		"Sample_ID",
		"Sample_Name",
		"Sample_Project",
		"Description"]
	
	availableDataHeaders=[False,False,False,False]
	
	for line in csvReader:
		
		if "[Data]" in line:
			dataSectionFound=True
			checkDataHeaders=True#next line contains data headers
			
		elif "[Header]" in line:
			headerSectionFound=True
			
		elif checkDataHeaders==True:
			
			
			availableDataHeaders=[dataHeader in line for dataHeader in requiredDataHeaders]#list containing boolean for each value in requiredDataHeaders that was found in line
			
			#check if all values in requiredDataHeaders are found in the line
			if all(availableDataHeaders):
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
			missingList=[]#list containing which data headers are missing
			for i in range(0,len(availableDataHeaders)):
				if availableDataHeaders[i]==False:
					missingList.append(requiredDataHeaders[i])
			
			missingStr=", ".join(map(str,missingList))
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
	
