import sys
sys.path.append("../../")

import unittest

from os import path
from Parsers.miseqParser import parseSamples,getPairFiles
from Validation.offlineValidation import validateSampleSheet, validatePairFiles, validateSampleList, validateURLForm

pathToModule=path.dirname(__file__)
if len(pathToModule)==0:
	pathToModule='.'

class TestOfflineValidation(unittest.TestCase):

	def setUp(self):
		print "\nStarting ", self._testMethodName

	def test_validateSampleSheet_validSheet(self):
		csvFile=path.join(pathToModule,"fake_ngs_data","SampleSheet.csv")
		vRes=validateSampleSheet(csvFile)
		self.assertTrue( vRes.isValid() )

	def test_validateSampleSheet_emptySheet(self):
		csvFile=path.join(pathToModule,"testSampleSheets","emptySampleSheet.csv")
		vRes=validateSampleSheet(csvFile)
		self.assertFalse( vRes.isValid() )
		self.assertEqual( vRes.errorCount(), 3)

		self.assertTrue( "Missing required data header(s): Sample_Project, Sample_Name, Description, Sample_ID" in vRes.getErrors())
		self.assertTrue( "[Header] section not found in SampleSheet" in vRes.getErrors())
		self.assertTrue( "[Data] section not found in SampleSheet" in vRes.getErrors())

	def test_validateSampleSheet_missing_DataHeader(self):
		csvFile=path.join(pathToModule,"testSampleSheets","missingDataHeader.csv")#has [Header]+[Data] but missing required data header (Sample_Project)
		vRes=validateSampleSheet(csvFile)
		self.assertFalse( vRes.isValid() )
		self.assertEqual( vRes.errorCount(), 1)

		self.assertTrue( "Missing required data header(s): Sample_Project" in vRes.getErrors())

	def test_validateSampleSheet_missing_HeaderSection(self):
		csvFile=path.join(pathToModule,"testSampleSheets","missingHeaderSection.csv")#has [Data] and required data headers but missing [Header]
		vRes=validateSampleSheet(csvFile)
		self.assertFalse( vRes.isValid() )
		self.assertEqual( vRes.errorCount(), 1)

		self.assertTrue( "[Header] section not found in SampleSheet" in vRes.getErrors())

	def test_validatePairFiles_valid(self):
		dataDir=path.join(pathToModule,"fake_ngs_data")

		sampleID="01-1111"
		pfList1=getPairFiles(dataDir,sampleID)

		self.assertEqual( len(pfList1), 2)
		vRes1=validatePairFiles(pfList1)

		self.assertTrue( vRes1.isValid())
		self.assertEqual( vRes1.errorCount(), 0 )
		self.assertTrue("No error messages" in vRes1.getErrors())

		sampleID="02-2222"
		pfList2=getPairFiles(dataDir,sampleID)

		self.assertEqual( len(pfList2), 2)
		vRes2=validatePairFiles(pfList2)

		self.assertTrue( vRes2.isValid() )
		self.assertEqual( vRes2.errorCount(), 0 )
		self.assertTrue("No error messages" in vRes2.getErrors())

		pfList3= pfList1+pfList2
		self.assertEqual( len(pfList3), 4)

		vRes3=validatePairFiles(pfList3)
		self.assertTrue( vRes3.isValid() )
		self.assertEqual( vRes3.errorCount(), 0 )
		self.assertTrue("No error messages" in vRes3.getErrors())


	def test_validatePairFiles_invalid_oddLength(self):
		dataDir=path.join(pathToModule,"testSeqPairFiles","oddLength")

		sampleID="01-1111"
		pfList=getPairFiles(dataDir,sampleID)

		self.assertEqual( len(pfList), 1)
		vRes= validatePairFiles(pfList)

		self.assertFalse( vRes.isValid() )
		self.assertEqual( vRes.errorCount(), 1)
		self.assertTrue("The given file list has an odd number of files" in vRes.getErrors())

	def test_validatePairFiles_invalid_noPair(self):
		dataDir=path.join(pathToModule,"testSeqPairFiles","noPair")

		sampleID="01-1111"
		pfList1=getPairFiles(dataDir,sampleID)
		#01-1111_S1_L001_R1_001.fastq.gz, 01-1111_S1_L001_R9_001.fastq.gz

		self.assertEqual( len(pfList1), 2)
		vRes1=validatePairFiles(pfList1)

		self.assertFalse( vRes1.isValid() )
		self.assertEqual( vRes1.errorCount(), 1 )
		self.assertTrue( "No pair sequence file found" in vRes1.getErrors() )


		sampleID="02-2222"
		pfList2=getPairFiles(dataDir,sampleID)
		#02-2222_S1_L001_R2_001.fastq.gz, 02-2222_S1_L001_R8_001.fastq.gz

		self.assertEqual( len(pfList2), 2)
		vRes2=validatePairFiles(pfList2)

		self.assertFalse( vRes2.isValid() )
		self.assertEqual( vRes2.errorCount(), 1)
		self.assertTrue( "No pair sequence file found" in vRes2.getErrors() )

		pfList3= pfList1+pfList2
		self.assertEqual( len(pfList3), 4)

		vRes3=validatePairFiles(pfList3)

		self.assertFalse( vRes3.isValid() )
		self.assertEqual( vRes3.errorCount(), 1)
		self.assertTrue( "No pair sequence file found" in vRes3.getErrors() )


	def test_validatePairFiles_invalid_seqFiles(self):
		dataDir=path.join(pathToModule,"testSeqPairFiles","invalidSeqFiles")

		sampleID="01-1111"
		pfList1=getPairFiles(dataDir,sampleID)
		#01-1111_S1_L001_R0_001.fastq.gz, 01-1111_S1_L001_R3_001.fastq.gz

		self.assertEqual( len(pfList1), 2)
		vRes1=validatePairFiles(pfList1)

		self.assertFalse( vRes1.isValid() )
		self.assertEqual( vRes1.errorCount(), 1)
		self.assertTrue("doesn't contain either 'R1' or 'R2' in filename" in vRes1.getErrors())

		sampleID="02-2222"
		pfList2=getPairFiles(dataDir,sampleID)
		#02-2222_S1_L001_R5_001.fastq.gz, 02-2222_S1_L001_R4_001.fastq.gz

		self.assertEqual( len(pfList2), 2)
		vRes2=validatePairFiles(pfList2)

		self.assertFalse( vRes2.isValid() )
		self.assertEqual( vRes2.errorCount(), 1 )
		self.assertTrue("doesn't contain either 'R1' or 'R2' in filename" in vRes2.getErrors())

		pfList3= pfList1+ pfList2

		self.assertEqual( len(pfList3),4 )
		vRes3=validatePairFiles(pfList3)

		self.assertFalse( vRes3.isValid() )
		self.assertEqual( vRes3.errorCount(), 1 )
		self.assertTrue("doesn't contain either 'R1' or 'R2' in filename" in vRes3.getErrors())

	def test_validateSampleList_valid(self):
		csvFile=path.join(pathToModule,"fake_ngs_data","SampleSheet.csv")

		samplesList=parseSamples(csvFile)
		self.assertEqual( len(samplesList), 3)

		vRes=validateSampleList(samplesList)
		self.assertTrue( vRes.isValid() )
		self.assertEqual( vRes.errorCount(), 0 )
		self.assertTrue( "No error messages" in vRes.getErrors() )

	def test_validateSampleList_invalid_noSampleProj(self):
		csvFile=path.join(pathToModule,"testSeqPairFiles","noSampleProj","SampleSheet.csv")#missing Sample_Project

		samplesList=parseSamples(csvFile)

		self.assertEqual( len(samplesList), 3)
		vRes=validateSampleList(samplesList)

		self.assertFalse( vRes.isValid() )
		self.assertEqual( vRes.errorCount(), 1 )
		self.assertTrue( "No sampleProject found for sample" in vRes.getErrors() )

	def test_validateSampleList_invalid_Empty(self):
		samplesList=[]

		self.assertEqual( len(samplesList), 0)
		vRes=validateSampleList(samplesList)

		self.assertFalse( vRes.isValid() )
		self.assertEqual( vRes.errorCount(), 1 )
		self.assertTrue( "The given list of samples is empty" in vRes.getErrors() )

	def test_validateURLForm(self):
		urlList=[
			{"url":"http://google.com/",
			"valid":True},

			{"url":"http://localhost:8080/",
			"valid":True},

			{"url":"www.google.com/",
			"valid":False},

			{"url":"www.google.com",
			"valid":False},

			{"url":"google.com",
			"valid":False}
		]

		for item in urlList:
			isValid= validateURLForm( item["url"] )
			self.assertEqual( isValid, item["valid"] )


offValidationTestSuite= unittest.TestSuite()

offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_validSheet") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_missing_DataHeader") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_emptySheet") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleSheet_missing_HeaderSection") )

offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_valid") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_invalid_oddLength") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_invalid_noPair") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validatePairFiles_invalid_seqFiles") )

offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleList_valid") )
offValidationTestSuite.addTest( TestOfflineValidation("test_validateSampleList_invalid_noSampleProj") )

offValidationTestSuite.addTest( TestOfflineValidation("test_validateURLForm") )


if __name__=="__main__":
	suiteList=[]

	suiteList.append(offValidationTestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
