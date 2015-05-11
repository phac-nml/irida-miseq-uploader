import sys
sys.path.append("../Model")

from os import walk, path
from fnmatch import filter as fnfilter
from csv import reader
from collections import OrderedDict

from Sample import Sample

def parseMetadata(dataDir):
	metadataDict={}
	metadataDict["readLengths"]=[]
	
	csvReader=getCsvReader(dataDir)
	addNextLineToDict=False
	
	for line in csvReader:
		
		if any(["[Header]" in line, "[Reads]" in line, "[Settings]" in line ]):
			addNextLineToDict=True
		
		elif addNextLineToDict==True:
			
			if len(line)==2:
				metadataDict[line[0]]=line[1]
			
			elif len(line)==1:#case for "[Reads]"
				
				metadataDict["readLengths"].append(line[0])
				
				
			elif len(line)==0: #current line is blank; end of section
				addNextLineToDict=False
				
		elif "[Data]" in line:
			break
			
	
	return metadataDict

def parseSamples(dataDir):
	csvReader=getCsvReader(dataDir)
	sampleDict=OrderedDict()#start with an ordered dictionary so that keys are ordered in the same way that they are inserted.
	samplesList=[]
	
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
		
		
		sample=Sample(sampleDict)
		samplesList.append( sample )
	
	return samplesList
	
	
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