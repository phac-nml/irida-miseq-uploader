from csv import reader 
from Metadata import Metadata
from Samples import Samples
from os import listdir, path

class SequencingRun:
    
    def __init__(self,dataDir):
        if path.isdir(dataDir):
        
            csvFile=self.__findCsvFile__(dataDir)
            csvReader=reader( open(csvFile, "rb" ) ) #open and read file in binary then send it to cvsReader
            
            self.metadata=Metadata(csvReader)
            self.samples=Samples(csvReader, dataDir)
        else:
            msg="Invalid directory "+ dataDir
            raise IOError(msg)
        
    
    def getSample(self, sampleID):
        return self.samples.getSample(sampleID)
    
    def getSamples(self):
        return self.samples.getSamples()
    
    def getMetadata(self):
        return self.metadata.getAllMetadata()
        
    
    def __findCsvFile__(self,dir):
        csvFile=""
        fList=listdir(dir)
        for f in fList:
            
            if path.splitext(f)[1]==".csv":
                csvFile=dir+"/"+f
                break
        return csvFile