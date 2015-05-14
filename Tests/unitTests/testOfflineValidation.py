import sys
sys.path.append("../../")

import unittest

from os import path
from Parsers.miseqParser import parseSamples,getPairFiles
from Validation.offlineValidation import validateSampleSheet, validatePairFiles, validateSampleList

pathToModule=path.dirname(__file__)
if len(pathToModule)==0:
	pathToModule='.'

class TestOfflineValidation(unittest.TestCase):

	def setUp(self):
		print "\nStarting ", self._testMethodName

	def test_validateSampleSheet_validSheet(self):
		csvFile=pathToModule+"/fake_ngs_data/SampleSheet.csv"
		self.assertTrue( validateSampleSheet(csvFile) )
	
	def test_validateSampleSheet_emptySheet(self):
		csvFile=pathToModule+"/testSampleSheets/emptySampleSheet.csv"
		self.assertFalse( validateSampleSheet(csvFile) )
		
	def test_validateSampleSheet_missing_DataHeaders(self):
		csvFile=pathToModule+"/testSampleSheets/missingDataHeader.csv"#has [Header]+[Data] but missing required data headers (Sample_Project)
		self.assertFalse( validateSampleSheet(csvFile) )
	
	def test_validateSampleSheet_missing_HeaderSection(self):
		csvFile=pathToModule+"/testSampleSheets/missingHeaderSection.csv"#has [Data] and required data headers but missing [Header]
		self.assertFalse( validateSampleSheet(csvFile) )
	
	def test_validatePairFiles_valid(self):
		dataDir=pathToModule+"/fake_ngs_data"
		
		sampleID="01-1111"
		pfList1=getPairFiles(dataDir,sampleID)
		
		self.assertEqual( len(pfList1), 2)
		self.assertTrue( validatePairFiles(pfList1) )
		
		sampleID="02-2222"
		pfList2=getPairFiles(dataDir,sampleID)
		
		self.assertEqual( len(pfList2), 2)
		self.assertTrue( validatePairFiles(pfList2) )
		
		pfList3= pfList1+pfList2
		self.assertEqual( len(pfList3), 4)
		self.assertTrue( validatePairFiles(pfList3) )
		
		
	def test_validatePairFiles_invalid_oddLength(self):
		dataDir=pathToModule+"/testSeqPairFiles/oddLength"
		
		sampleID="01-1111"
		pfList=getPairFiles(dataDir,sampleID)
		
		self.assertEqual( len(pfList), 1)
		self.assertFalse( validatePairFiles(pfList) )
		
	def test_validatePairFiles_invalid_noPair(self):
		dataDir=pathToModule+"/testSeqPairFiles/noPair"
		
		sampleID="01-1111"
		pfList1=getPairFiles(dataDir,sampleID)
		#01-1111_S1_L001_R1_001.fastq.gz, 01-1111_S1_L001_R9_001.fastq.gz
		
		self.assertEqual( len(pfList1), 2)
		self.assertFalse( validatePairFiles(pfList1) )
		
		sampleID="02-2222"
		pfList2=getPairFiles(dataDir,sampleID)
		#02-2222_S1_L001_R2_001.fastq.gz, 02-2222_S1_L001_R8_001.fastq.gz
		
		self.assertEqual( len(pfList2), 2)
		self.assertFalse( validatePairFiles(pfList2) )
		
		pfList3= pfList1+pfList2
		self.assertEqual( len(pfList3), 4)
		self.assertFalse( validatePairFiles(pfList3) )
		
	def test_validatePairFiles_invalid_seqFiles(self):
		dataDir=pathToModule+"/testSeqPairFiles/invalidSeqFiles"
		
		sampleID="01-1111"
		pfList1=getPairFiles(dataDir,sampleID)
		#01-1111_S1_L001_R0_001.fastq.gz, 01-1111_S1_L001_R3_001.fastq.gz
		
		self.assertEqual( len(pfList1), 2)
		self.assertFalse( validatePairFiles(pfList1) )
		
		sampleID="02-2222"
		pfList2=getPairFiles(dataDir,sampleID)
		#02-2222_S1_L001_R5_001.fastq.gz, 02-2222_S1_L001_R4_001.fastq.gz
		
		self.assertEqual( len(pfList2), 2)
		self.assertFalse( validatePairFiles(pfList2) )
		
		pfList3= pfList1+ pfList2
		self.assertEqual( len(pfList3),4 )
		self.assertFalse( validatePairFiles(pfList3) )
	
	def test_validateSampleList_valid(self):
		csvFile=pathToModule+"/fake_ngs_data/SampleSheet.csv"
		
		samplesList=parseSamples(csvFile)
		self.assertEqual( len(samplesList), 3)
		self.assertTrue( validateSampleList(samplesList))
		
	def test_validateSampleList_invalid(self):
		csvFile=pathToModule+"/testSeqPairFiles/noSampleProj/SampleSheet.csv"#missing Sample_Project
		
		samplesList=parseSamples(csvFile)
		self.assertEqual( len(samplesList), 3)
		self.assertFalse( validateSampleList(samplesList))
		
offValidationTestSuite= unittest.TestSuite()
	
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_validSheet") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_missing_DataHeaders") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_emptySheet") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_missing_HeaderSection") )

offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_valid") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_invalid_oddLength") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_invalid_noPair") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_invalid_seqFiles") )

offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleList_valid") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleList_invalid") )

	
if __name__=="__main__":
	suiteList=[]
	
	suiteList.append(offValidationTestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)