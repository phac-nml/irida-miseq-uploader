"""
Holds pair files and Sample metadata:
samplePlate
sampleWell
i7IndexID
index
i5IndexID
index2
etc.
"""


class SequenceFile:

    def __init__(self, newPropertiesDict, newPairFileList):
        self.propertiesDict = newPropertiesDict  # Sample metadata
        self.pairFileList = newPairFileList
        self.pairFileList.sort()

    def getProperties(self):
        return self.propertiesDict

    def get(self, key):
        retVal = None
        if self.propertiesDict in key:
            retVal = self.propertiesDict[key]
        return retVal

    def getPairFiles(self):
        return self.pairFileList

    def __str__(self):
        return str(self.propertiesDict) + str(self.pairFileList)
