from copy import deepcopy
from collections import OrderedDict
from os import listdir, path, walk
from fnmatch import filter as fnfilter

class Samples:
    def __init__(self,csvReader,dataDir):
        self.samplesList=[]
        self.samplesList=self.__parseSamples__(csvReader)
        self.samplesList=self.__findPairFiles__(dataDir)
    
    def __parseSamples__(self, csvReader):
        sampleDict=OrderedDict()
        
        #initilize dictionary keys from first line
        for line in csvReader:
            for item in line:
                sampleDict[item]=""
            break
        
        #fill in values for keys
        for line in csvReader:
            #assumes values are never empty
            i=0
            for key in sampleDict.keys():
                sampleDict[key]=line[i]
                i=i+1
            
            
            self.samplesList.append( deepcopy( dict(sampleDict)) )
        
        return self.samplesList #returning just for readability
        
    def __findPairFiles__(self, dataDir):
        for sample in self.samplesList:
            pattern=sample["Sample_ID"]+"*.fastq.gz"
            sample["pairFiles"]=[]
            for root, dirs, files in walk(dataDir):
                for filename in fnfilter(files, pattern):
                    sample["pairFiles"].append( path.join(root, filename)) 
                
        
        return self.samplesList
    
    
        
    
    def getSample(self,sampleID):
        retVal=None
        for sample in self.samplesList:
            if sample["Sample_ID"]==sampleID:
                retVal=sample
        return retVal
    
    def getSamples(self):
        return self.samplesList
                    
                    
        