import unittest
from os import path
from sys import path as sysPath
sysPath.insert(0,"../..")


from Model.SequencingRun import SequencingRun

class TestSequencingRun(unittest.TestCase):
    
    def setUp(self):
        print "\nStarting ", self._testMethodName,
    
    def testInit_invalidDir(self):
        dataDir="+/not a directory/+"
        
        with self.assertRaises(IOError) as context:
            SequencingRun(dataDir)
        
        self.assertTrue("Invalid directory" in str(context.exception))
        
    def testInit_validDir(self):
        pass

if __name__=="__main__":
    suiteList=[]
    srSuite= unittest.TestSuite()
    srSuite.addTest( TestSequencingRun("testInit_invalidDir") )
    
    suiteList.append(srSuite)
    fullSuite = unittest.TestSuite(suiteList)
    
    runner = unittest.TextTestRunner()
    runner.run(fullSuite)