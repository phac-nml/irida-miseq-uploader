import unittest
import sys
#temp until setup.py is created for defining/referencing paths
sys.path.append("../../")

from Model.Sample import Sample
from os import path
from csv import reader
from Parsers.miseqParser import parseMetadata, parseSamples, getCsvReader, getPairFiles, parseOutSequenceFile, completeParseSamples
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError

pathToModule=path.dirname(__file__)
if len(pathToModule)==0:
	pathToModule='.'

class TestMiSeqParser(unittest.TestCase):

	def setUp(self):
		print "\nStarting ", self._testMethodName

	def test_getCsvReader_noSampleSheet(self):
		dataDir=pathToModule+"/fake_ngs_data/Data"

		with self.assertRaises(SampleSheetError) as context:
			csvReader=getCsvReader(dataDir)

		self.assertTrue("not a valid SampleSheet file" in str(context.exception))


	def test_getCsvReader_validSheet(self):
		sheetFile=pathToModule+"/fake_ngs_data/SampleSheet.csv"
		csvReader=getCsvReader(sheetFile)


	def test_parseMetadata(self):
		sheetFile=pathToModule+"/fake_ngs_data/SampleSheet.csv"
		metaData=parseMetadata(sheetFile)

		correctMetadata={'readLengths': ['251', '250'],
		'assay': 'Nextera XT',
		'description': 'Superbug',
		'application': 'FASTQ Only',
		'investigatorName': 'Some Guy',
		'adapter': 'AAAAGGGGAAAAGGGGAAA',
		'workflow': 'GenerateFASTQ',
		'reversecomplement': '0',
		'iemfileversion': '4',
		'date': '10/15/2013',
		'experimentName': '1',
		'chemistry': 'Amplicon'}

		self.assertEqual(correctMetadata, metaData)

	def test_completeParseSamples(self):
		sheetFile=pathToModule+"/fake_ngs_data/SampleSheet.csv"
		dataDir=pathToModule+"/fake_ngs_data"

		samplesList=completeParseSamples(sheetFile)
		self.assertEqual( len(samplesList), 3)

		requiredDataHeaders=[
		"sampleName",
		"description",
		"sequencerSampleId",
		"sampleProject"]

		seqFileHeaders=[
		"index",
		"I7_Index_ID",
		"Sample_Well",
		"Sample_Plate",
		"index2",
		"I5_Index_ID"]

		for sample in samplesList:

			#sample only has the 4 required data headers as keys
			self.assertEqual( len(sample.getDict().keys()), len(requiredDataHeaders))

			#check if all values in requiredDataHeaders are found in the sample's dictionary keys
			self.assertTrue(
			all( [dataHeader in sample.getDict().keys() for dataHeader in requiredDataHeaders]) )
			#print [sample.getDict().keys() ]


			#check if all values in seqFileHeaders are found in the Sequence File properties dict /Sample metadata
			self.assertTrue(
			all( [dataHeader in sample.getSampleMetadata().keys() for dataHeader in seqFileHeaders]) )
			#print [sample.getSampleMetadata().keys()]


			self.assertEqual( len(sample.getPairFiles()), 2)
			pfList=getPairFiles(dataDir, sample.getID())
			self.assertEqual(pfList, sample.getPairFiles())

	def test_parseSamples(self):
		sheetFile=pathToModule+"/fake_ngs_data/SampleSheet.csv"
		samplesList=parseSamples(sheetFile)

		correctSamples=[
		{'Sample_Well': '01',
		'index': 'AAAAAAAA',
		'Sample_Plate': '1',
		'I7_Index_ID': 'N01',
		'sampleName': '01-1111',
		'sampleProject': '6',
		'sequencerSampleId': '01-1111',
		'I5_Index_ID': 'S01',
		'index2': 'TTTTTTTT',
		'description': 'Super bug '},

		{'Sample_Well': '02',
		'index': 'GGGGGGGG',
		'Sample_Plate': '2',
		'I7_Index_ID': 'N02',
		'sampleName': '02-2222',
		'sampleProject': '6',
		'sequencerSampleId': '02-2222',
		'I5_Index_ID': 'S02',
		'index2': 'CCCCCCCC',
		'description': 'Scary bug '},

		{'Sample_Well': '03',
		'index': 'CCCCCCCC',
		'Sample_Plate': '3',
		'I7_Index_ID': 'N03',
		'sampleName': '03-3333',
		'sampleProject': '6',
		'sequencerSampleId': '03-3333',
		'I5_Index_ID': 'S03',
		'index2': 'GGGGGGGG',
		'description': 'Deadly bug '}]

		sampleListValues=[sample.getDict() for sample in samplesList]
		self.assertEqual( correctSamples, sampleListValues)


	def test_parseOutSequenceFile(self):

		sample=Sample({'Sample_Well': '03',
		'index': 'CCCCCCCC',
		'Sample_Plate': '3',
		'I7_Index_ID': 'N03',
		'sampleName': '03-3333',
		'sampleProject': '6',
		'sequencerSampleId': '03-3333',
		'I5_Index_ID': 'S03',
		'index2': 'GGGGGGGG',
		'description': 'Deadly bug '})

		correctSample={'description': 'Deadly bug ',
		'sampleName': '03-3333',
		'sequencerSampleId': '03-3333',
		'sampleProject': '6'}

		correctSeqFile={'index': 'CCCCCCCC',
		'I7_Index_ID': 'N03',
		'Sample_Well': '03',
		'Sample_Plate': '3',
		'index2': 'GGGGGGGG',
		'I5_Index_ID': 'S03'}

		seqFile=parseOutSequenceFile(sample)

		self.assertEqual(sample.getDict(), correctSample)
		self.assertEqual(seqFile, correctSeqFile)


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
		validDir=pathToModule+"/fake_ngs_data"
		invalidSampleID= "-1"


		pairFileList=getPairFiles(validDir,invalidSampleID)

		self.assertEqual(len(pairFileList),0)


	def test_getPairFiles_validDir_validID(self):
		global pathToModule
		validDir=pathToModule+"/fake_ngs_data"
		validSampleID="01-1111"

		pathToModule=pathToModule.replace('/','\\')
		pairFileList=getPairFiles(validDir,validSampleID)
		correctPairList=[pathToModule+"\\fake_ngs_data\\Data\\Intensities\\BaseCalls\\01-1111_S1_L001_R1_001.fastq.gz",pathToModule+"\\fake_ngs_data\\Data\\Intensities\\BaseCalls\\01-1111_S1_L001_R2_001.fastq.gz"]
		self.assertEqual(correctPairList,pairFileList)


parserTestSuite= unittest.TestSuite()

parserTestSuite.addTest( TestMiSeqParser("test_getCsvReader_noSampleSheet") )
parserTestSuite.addTest( TestMiSeqParser("test_getCsvReader_validSheet") )

parserTestSuite.addTest( TestMiSeqParser("test_parseMetadata") )
parserTestSuite.addTest( TestMiSeqParser("test_completeParseSamples") )
parserTestSuite.addTest( TestMiSeqParser("test_parseSamples") )
parserTestSuite.addTest( TestMiSeqParser("test_parseOutSequenceFile") )

parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_invalidDir_invalidID") )
parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_invalidDir_validID") )
parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_validDir_invalidID") )
parserTestSuite.addTest( TestMiSeqParser("test_getPairFiles_validDir_validID") )


if __name__=="__main__":
	suiteList=[]

	suiteList.append(parserTestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
