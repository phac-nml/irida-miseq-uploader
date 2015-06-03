import sys
sys.path.append("../")

from Model.Sample import Sample
from Model.SequenceFile import SequenceFile
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError
from os import walk, path
from fnmatch import filter as fnfilter
from csv import reader
from collections import OrderedDict
from copy import deepcopy


def parseMetadata(sampleSheetFile):
	"""
	Parse all lines under [Header], [Reads] and [Settings] in .csv file
	Lines under [Reads] are stored in a list with key name "readLengths"
	All other key names are translated according to the metadataKeyTranslationDictionary

	arguments:
		sampleSheetFile -- path to SampleSheet.csv

	returns a dictionary containing the parsed key:pair values from .csv file
	"""

	metadataDict={}
	metadataDict["readLengths"]=[]

	csvReader=getCsvReader(sampleSheetFile)
	addNextLineToDict=False

	metadataKeyTranslationDictionary = {
		'Assay': 'assay',
		'Description': 'description',
		'Application': 'application',
		'Investigator Name' : 'investigatorName',
		'Adapter':'adapter',
		'Workflow':'workflow',
		'ReverseComplement':'reversecomplement',
		'IEMFileVersion': 'iemfileversion',
		'Date':'date',
		'Experiment Name':'experimentName',
		'Chemistry':'chemistry'
	}

	for line in csvReader:

		if any(["[Header]" in line, "[Reads]" in line, "[Settings]" in line ]):
			addNextLineToDict=True

		elif addNextLineToDict==True:

			if len(line)==2:
				keyName=metadataKeyTranslationDictionary[line[0]]
				metadataDict[ keyName ]=line[1]

			elif len(line)==1:#case for "[Reads]"

				metadataDict["readLengths"].append(line[0])


			elif len(line)==0: #current line is blank; end of section
				addNextLineToDict=False

		elif "[Data]" in line:
			break

	return metadataDict

def completeParseSamples(sampleSheetFile):
	"""
	Creates a complete Sample object:
	Sample dict will only have the required (and already translated) keys: 'sampleName', 'description', 'sequencerSampleId' 'sampleProject'.
	SequenceFile parsed out and holds Sample metadata (other keys) + pair files for the sample.
	SequenceFile is then set as an attribute of Sample
	These Sample objects will be stored in a list.

	arguments:
		sampleSheetFile -- path to SampleSheet.csv

	returns list containing complete Sample objects
	"""

	samplesList=parseSamples(sampleSheetFile)
	dataDir=path.dirname(sampleSheetFile)
	for sample in samplesList:

		propertiesDict=parseOutSequenceFile(sample)
		pfList=getPairFiles(dataDir, sample.getID())
		sq=SequenceFile(propertiesDict, pfList)

		sample.setSeqFile( deepcopy (sq) )

	return samplesList

def parseSamples(sampleSheetFile):
	"""
	Parse all the lines under "[Data]" in .csv file
	Keys in sampleKeyTranslationDictionary have their values changed for uploading to REST API
	All other keys keep the same name that they have in .csv file

	arguments:
		sampleSheetFile -- path to SampleSheet.csv

	returns	a list containing Sample objects that have been created by a dictionary from the parsed out key:pair values from .csv file
	"""

	csvReader=getCsvReader(sampleSheetFile)
	sampleDict=OrderedDict()#start with an ordered dictionary so that keys are ordered in the same way that they are inserted.
	samplesList=[]

	sampleKeyTranslationDictionary = {
		'Sample_Name': 'sampleName',
		'Description': 'description',
		'Sample_ID': 'sequencerSampleId',
		'Sample_Project' : 'sampleProject'
	}

	#initilize dictionary keys from first line (data headers/attributes)
	setAttributes=False
	for line in csvReader:

		if setAttributes==True:
			for item in line:

				if item in sampleKeyTranslationDictionary:
					keyName=sampleKeyTranslationDictionary[item]
				else:
					keyName=item

				sampleDict[keyName]=""

			break

		if "[Data]" in line:
			setAttributes=True

	#fill in values for keys
	for line in csvReader:

		i=0

		for key in sampleDict.keys():
			sampleDict[key]=line[i]#assumes values are never empty
			i=i+1

		sample=Sample( deepcopy(sampleDict) )
		samplesList.append( sample )


	return samplesList


def parseOutSequenceFile(sample):
	"""
	Removes keys in argument sample that are not in sampleKeys and stores them in sequenceFileDict

	arguments:
		sample -- Sample object
		the dictionary inside the Sample object is changed

	returns a dictionary containing keys not in sampleKeys to be used to create a SequenceFile object
	"""

	sampleKeys=["sampleName","description","sequencerSampleId","sampleProject"]
	sequenceFileDict={}
	sampleDict=sample.getDict()
	for key in sampleDict.keys()[:]:#iterate through a copy
		if key not in sampleKeys:
			sequenceFileDict[key]=sampleDict[key]
			del sampleDict[key]

	return sequenceFileDict


def getCsvReader(sampleSheetFile):
	"""
	tries to create a csv.reader object which will be used to parse through the lines in SampleSheet.csv
	raises an error if:
		sampleSheetFile is not an existing file
		sampleSheetFile contains null byte(s)

	arguments:
		dataDir -- the directory that has SampleSheet.csv in it

	returns a csv.reader object
	"""

	csvFile=sampleSheetFile
	if path.isfile(csvFile) and '\0' not in open(csvFile).read():

		csvReader=reader( open(csvFile, "rb" ) ) #open and read file in binary then send it to be parsed by csv's reader
	else:
		msg=sampleSheetFile + " is not a valid SampleSheet file"
		raise SampleSheetError(msg)

	return csvReader


def getPairFiles(dataDir, sampleID):
	"""
	find the pair sequence files for the given sampleID
	raises an error if no sequence pair files found

	arguments:
		dataDir -- the directory that has SampleSheet.csv in it
		sampleID -- ID of the sample for the pair files


	returns a list containing the path of the pair files starting from dataDir...
	"""

	pattern=sampleID+"*.fastq.gz"
	pairFileList=recursiveFind(dataDir, pattern)
	pairFileList.sort()

	return pairFileList

def recursiveFind(topDir, pattern):
	"""
	Traverse through a directory and its subdirectories looking for files that match given pattern

	arguments:
		topDir -- top level directory to start searching from
		pattern -- pattern to try and match using fnfilter/ fnmatch.filter

	returns list containing files that match pattern
	"""
	resultList=[]

	if path.isdir(topDir):
		for root, dirs, files in walk(topDir):
			for filename in fnfilter(files, pattern):
				res=path.join(root, filename)
				res=res.replace("/","\\")# windows paths give dir\\subDir\\ vs unix paths: dir/subDir
				resultList.append( res )
	else:
		msg="Invalid directory "+ topDir
		raise IOError(msg)

	return resultList
