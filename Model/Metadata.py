class Metadata:
    def __init__(self, csvReader):
        self.metadataDict={}
        self.metadataDict=self.__parseMetadata__(csvReader)

    def __parseMetadata__(self, csvReader):
        
        addNextLineToDict=False
        for line in csvReader:
            
            if any(["[Header]" in line, "[Reads]" in line, "[Settings]" in line ]):
                addNextLineToDict=True
            
            elif addNextLineToDict==True:
                
                if len(line)==2:
                    self.metadataDict[line[0]]=line[1]
                
                elif len(line)==1:#case for "[Reads]"
                    #I'm assuming that the first value under "Reads" is always LongestRead
                    if self.metadataDict.has_key("LongestRead")==False:
                        self.metadataDict["LongestRead"]=line[0]
                        
                    else:
                        self.metadataDict["ShortestRead"]=line[0]
                        addNextLineToDict=False
                    
                else:#if line==0 then current line is blank-end of section
                    addNextLineToDict=False
                    
            elif "[Data]" in line:
                break
                
        
        return self.metadataDict #returning just for readability
        
    def get(self,key):
        return self.metadataDict[key]
        
    def getAllMetadata(self):
        return self.metadataDict