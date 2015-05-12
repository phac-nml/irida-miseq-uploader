import sys
sys.path.append("../Model")

from Sample import Sample
from os import walk, path
from fnmatch import filter as fnfilter
from csv import reader
from collections import OrderedDict
from copy import deepcopy

def camelCase(targStr):
	splitChars=[' ','_']
	
	wasSplit=False
	for c in splitChars:
		
		if c in targStr:
			wasSplit=True
			
			uTokens=targStr.split(c)
	
			uTokens[0]=uTokens[0].lower()
			for i in range(1,len(uTokens)):
				uTokens[i]=uTokens[i].title()#capitalize first char and lower rest
	
			targStr= "".join(uTokens)
			
	if wasSplit==False:
		targStr=targStr.lower()
	
	return targStr

def parseMetadata(dataDir):
	"""
		Parse all lines under [Header], [Reads] and [Settings] in .csv file
		All keys are turned in to camelCase
	"""
	
	metadataDict={}
	metadataDict["readLengths"]=[]
	
	csvReader=getCsvReader(dataDir)
	addNextLineToDict=False
	
	for line in csvReader:
		
		if any(["[Header]" in line, "[Reads]" in line, "[Settings]" in line ]):
			addNextLineToDict=True
		
		elif addNextLineToDict==True:
			
			if len(line)==2:
				metadataDict[ camelCase(line[0]) ]=line[1]
			
			elif len(line)==1:#case for "[Reads]"
				
				metadataDict["readLengths"].append(line[0])
				
				
			elif len(line)==0: #current line is blank; end of section
				addNextLineToDict=False
				
		elif "[Data]" in line:
			break
	
	return metadataDict

def parseSamples(dataDir):
	"""
		Parse all the lines under "[Data]" in .csv file
		Keys in camelCasedKeys are turned in to camelCase for uploading to REST API
		Sample_ID key is turned to sequencerSampleId
	"""
	csvReader=getCsvReader(dataDir)
	sampleDict=OrderedDict()#start with an ordered dictionary so that keys are ordered in the same way that they are inserted.
	samplesList=[]
	camelCasedKeys=["Sample_Name","Description","Sample_Project"]
	
	#initilize dictionary keys from first line (data headers/attributes)
	setAttributes=False
	for line in csvReader:
		
		if setAttributes==True:
			for item in line:
				sampleDict[item]=""
			break
		
		if "[Data]" in line:
			setAttributes=True
	
	#fill in values for keys
	for line in csvReader:
		
		i=0
		
		for key in sampleDict.keys():
			sampleDict[key]=line[i]#assumes values are never empty
			i=i+1
		
		samplesList.append( deepcopy(sampleDict) )
	
	#apply camelCasing and required changes to keys
	for sampleDict in samplesList[:]:#iterate through a copy
	
		for key in sampleDict.keys()[:]:#iterate through a copy
			
			if key in camelCasedKeys:
				sampleDict[camelCase(key)]=sampleDict[key]
				del sampleDict[key]
				
			elif key =="Sample_ID":
				sampleDict["sequencerSampleId"]=sampleDict[key]
				del sampleDict[key]
	
		sample=Sample(sampleDict)
		samplesList[samplesList.index(sampleDict)]=sample
		
		
	return samplesList
	

def parseOutSequenceFile(sample):
	"""
		Removes keys in argument "sample" that are not in sampleKeys and stores them in sequenceFileDict
	"""
	
	sampleKeys=["sampleName","description","sequencerSampleId","sampleProject"]
	sequenceFileDict={}
	sampleDict=sample.getDict()
	for key in sampleDict.keys()[:]:#iterate through a copy
		if key not in sampleKeys:
			sequenceFileDict[key]=sampleDict[key]
			del sampleDict[key]
			
	return sequenceFileDict
	
	
def getCsvReader(dataDir):
	csvFile=findCsvFile(dataDir)
	csvReader=reader( open(csvFile, "rb" ) ) #open and read file in binary then send it to be parsed by csv's reader
	return csvReader
	
def findCsvFile(dataDir):
	
	csvPattern="*.csv"
	resultList=recursiveFind(dataDir, csvPattern)
	
	if len(resultList)>0:
		csvFile=resultList[0]
	else:
		msg="No '.csv' file found in "+ dataDir
		raise IndexError(msg)
	
	return csvFile
	
def getPairFiles(dataDir, sampleID):
	
    
	pattern=sampleID+"*.fastq.gz"
	pairFileList=recursiveFind(dataDir, pattern)
	pairFileList.sort()
	if len(pairFileList)==0:
		msg="No sequence pair files found"
		raise IndexError(msg)

	return pairFileList
	
def recursiveFind(topDir, pattern):
	resultList=[]
	
	if path.isdir(topDir):
		for root, dirs, files in walk(topDir):
			for filename in fnfilter(files, pattern):
				resultList.append( path.join(root, filename)) 
	else:
		msg="Invalid directory "+ topDir
		raise IOError(msg)	
	
	return resultList