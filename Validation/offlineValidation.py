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

	returns ValidationResult object - stores bool valid and list of string error messages
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

	returns ValidationResult object - stores bool valid and list of string error messages
	"""

	vRes=ValidationResult()
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
				vRes.addErrorMsg(file + " doesn't contain either 'R1' or 'R2' in filename.\nRequired for identifying sequence files.")
				break

			if matchingPairFile in validationFList:
				validationFList.remove(matchingPairFile)
				validationFList.remove(file)

			else:
				valid=False
				vRes.addErrorMsg("No pair sequence file found for:" + file + "\nRequired matching sequence file: " + matchingPairFile)
				break

	else:
		vRes.addErrorMsg("The given file list has an odd number of files.\nRequires an even number of files in order for each sequence file to have a pair.")

	vRes.setValid(valid)
	return vRes


def validateSampleList(samplesList):
	"""
	Iterates through given samples list and tries to validate each sample via validateSample method - sample must have a "sampleProject" key

	arguments:
		samplesList -- list containing Sample objects

	returns ValidationResult object - stores bool valid and list of string error messages
	"""
	valid=False
	vRes=ValidationResult()
	if len(samplesList) > 0:
		valid=True
		for sample in samplesList:
			res=validateSample(sample)
			if res==False:
				valid=False
				vRes.addErrorMsg( "No sampleProject found for sample with ID: " + sample.getID() )
				break

	else:
		vRes.addErrorMsg("The given list of samples is empty.\nRequires atleast 1 sample in list.")

	vRes.setValid(valid)
	return vRes


def validateSample(sample):
	"""
	Checks if sample has project identifier attached to it
	"""
	valid=False

	sampleProj=sample.get("sampleProject")
	if sampleProj!=None and len(sampleProj)>0:
		valid=True
	return valid
