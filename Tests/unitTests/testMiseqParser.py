import unittest
import sys
sys.path.append("../../Parsers")
sys.path.append("../../Model")

from SamplesList import SamplesList
from Metadata import Metadata

from os import path
from csv import reader
from miseqParser import parseMetadata, parseSamples, getCsvReader, getPairFiles

class TestMiSeqParser(unittest.TestCase):

	def setUp(self):
		print "\nStarting ", self._testMethodName

		
	def test_getCsvReader_invalidDir(self):
		dataDir="+/not a directory/+"
		
		with self.assertRaises(IOError) as context:
			csvReader=getCsvReader(dataDir)
		
		self.assertTrue("Invalid directory" in str(context.exception))
	
	
	def test_getCsvReader_validDir(self):
		dataDir="fake_ngs_data"
		csvReader=getCsvReader(dataDir)
		
		csvFile="fake_ngs_data/SampleSheet.csv"
		expectedReader=reader(csvFile)
		
		self.assertTrue(csvReader, expectedReader)
	
	
	def test_parseMetadata(self):
		dataDir="fake_ngs_data"
		newMetadata=parseMetadata(dataDir)		
		metaData= Metadata(newMetadata)
		
		correctMetadata={'readLengths': ['251', '250'], 
		'Assay': 'Nextera XT', 
		'Description': 'Superbug', 
		'Application': 'FASTQ Only', 
		'Investigator Name': 'Some Guy', 
		'Adapter': 'AAAAGGGGAAAAGGGGAAA', 
		'Workflow': 'GenerateFASTQ', 
		'ReverseComplement': '0', 
		'IEMFileVersion': '4',
		'Date': '10/15/2013', 
		'Experiment Name': '1', 
		'Chemistry': 'Amplicon'}

		self.assertEqual(correctMetadata, metaData.getAllMetadata())
	
	
	def test_parseSamples(self):
		dataDir="fake_ngs_data"
		newSamples=parseSamples(dataDir)
		samplesList=SamplesList(newSamples)
		
		correctSamples=[
		{'index': 'AAAAAAAA', 
		'Description': 'Super bug ', 
		'Sample_Name': '01-1111', 
		'Sample_Plate': '1', 
		'I7_Index_ID': 'N01', 
		'Sample_Well': '01', 
		'Sample_Project': '6', 
		'Sample_ID': '01-1111', 
		'index2': 'TTTTTTTT', 
		'I5_Index_ID': 'S01'},
		
		{'index': 'GGGGGGGG', 
		'Description': 'Scary bug ', 
		'Sample_Name': '02-2222', 
		'Sample_Plate': '2', 
		'I7_Index_ID': 'N02', 
		'Sample_Well': '02', 
		'Sample_Project': '6', 
		'Sample_ID': '02-2222', 
		'index2': 'CCCCCCCC', 
		'I5_Index_ID': 'S02'},
		
		{'index': 'CCCCCCCC', 
		'Description': 'Deadly bug ', 
		'Sample_Name': '03-3333', 
		'Sample_Plate': '3', 
		'I7_Index_ID': 'N03', 
		'Sample_Well': '03', 
		'Sample_Project': '6', 
		'Sample_ID': '03-3333', 
		'index2': 'GGGGGGGG', 
		'I5_Index_ID': 'S03'}
		]
		
		sampleListValues=[sample.getDict() for sample in samplesList.getList()]
		self.assertEqual(correctSamples, sampleListValues )
	
		
	def test_getPairFiles_invalidDir_invalidID(self):
		
		invalidDir="+/not a directory/+"
		invalidSampleID= "-1"
		
		with self.assertRaises(IOError) as context:
			pairFileList=getPairFiles(invalidDir,invalidSampleID)
		
		self.assertTrue("Invalid directory" in str(context.exception))
	
	
	def test_getPairFiles_invalidDir_validID(self):
		invalidDir="+/not a directory/+"
		validSampleID="01-1111"
		
		with self.assertRaises(IOError) as context:
			pairFileList=getPairFiles(invalidDir,validSampleID)
		
		self.assertTrue("Invalid directory" in str(context.exception))

		
	def test_getPairFiles_validDir_invalidID(self):
		validDir="fake_ngs_data"
		invalidSampleID= "-1"
		
		with self.assertRaises(IndexError) as context:
			pairFileList=getPairFiles(validDir,invalidSampleID)
		
		self.assertTrue("No sequence pair files found" in str(context.exception))

		
	def test_getPairFiles_validDir_validID(self):
		validDir="fake_ngs_data"
		validSampleID="01-1111"
			
		pairFileList=getPairFiles(validDir,validSampleID)
		correctPairList=["fake_ngs_data/Data/Intensities/BaseCalls/01-1111_S1_L001_R1_001.fastq.gz","fake_ngs_data/Data/Intensities/BaseCalls/01-1111_S1_L001_R2_001.fastq.gz"]
		self.assertEqual(correctPairList,pairFileList)
	
		
if __name__=="__main__":
	suiteList=[]
	parserTestSuite= unittest.TestSuite()
	parserTestSuite.addTest( TestMiSeqParser("test_getCsvReader_invalidDir") )
	parserTestSuite.addTest( TestMiSeqParser("test_getCsvReader_validDir") )
	parserTestSuite.addTest( TestMiSeqParser("test_parseMetadata") )
	parserTestSuite.addTest( TestMiSeqParser("test_parseSamples") )
	parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_invalidDir_invalidID") )
	parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_invalidDir_validID") )
	parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_validDir_invalidID") )
	parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_validDir_validID") )
	
	
	suiteList.append(parserTestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)