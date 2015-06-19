import sys
import unittest
from os import path

sys.path.append("../../")
from Parsers.miseqParser import parse_samples, get_pair_files
from Validation.offlineValidation import (validate_sample_sheet,
                                          validate_pair_files,
                                          validate_sample_list,
                                          validate_URL_form)

path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'


class TestOfflineValidation(unittest.TestCase):

    def setUp(self):
        print "\nStarting " + self.__module__ + ": " + self._testMethodName

    def test_validateSampleSheet_validSheet(self):
        csv_file = path.join(path_to_module, "fake_ngs_data",
                             "SampleSheet.csv")
        v_res = validate_sample_sheet(csv_file)
        self.assertTrue(v_res.is_valid())

    def test_validateSampleSheet_emptySheet(self):
        csv_file = path.join(
            path_to_module, "testSampleSheets", "emptySampleSheet.csv")
        v_res = validate_sample_sheet(csv_file)
        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 3)

        self.assertTrue(
            "Missing required data header(s): Sample_Project, Sample_Name," +
            " Description, Sample_ID" in v_res.get_errors())
        self.assertTrue(
            "[Header] section not found in SampleSheet" in v_res.get_errors())
        self.assertTrue(
            "[Data] section not found in SampleSheet" in v_res.get_errors())

    def test_validateSampleSheet_missing_DataHeader(self):
        # has [Header]+[Data] but missing required data header (Sample_Project)
        csv_file = path.join(
            path_to_module, "testSampleSheets", "missingDataHeader.csv")
        v_res = validate_sample_sheet(csv_file)
        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)

        self.assertTrue(
            "Missing required data header(s): Sample_Project"
            in v_res.get_errors())

    def test_validateSampleSheet_missing_HeaderSection(self):
        # has [Data] and required data headers but missing [Header]
        csv_file = path.join(
            path_to_module, "testSampleSheets", "missingHeaderSection.csv")
        v_res = validate_sample_sheet(csv_file)
        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)

        self.assertTrue(
            "[Header] section not found in SampleSheet" in v_res.get_errors())

    def test_validatePairFiles_valid(self):
        dataDir = path.join(path_to_module, "fake_ngs_data")

        sampleID = "01-1111"
        pfList1 = get_pair_files(dataDir, sampleID)

        self.assertEqual(len(pfList1), 2)
        vRes1 = validate_pair_files(pfList1)

        self.assertTrue(vRes1.is_valid())
        self.assertEqual(vRes1.error_count(), 0)
        self.assertTrue("No error messages" in vRes1.get_errors())

        sampleID = "02-2222"
        pfList2 = get_pair_files(dataDir, sampleID)

        self.assertEqual(len(pfList2), 2)
        vRes2 = validate_pair_files(pfList2)

        self.assertTrue(vRes2.is_valid())
        self.assertEqual(vRes2.error_count(), 0)
        self.assertTrue("No error messages" in vRes2.get_errors())

        pfList3 = pfList1 + pfList2
        self.assertEqual(len(pfList3), 4)

        vRes3 = validate_pair_files(pfList3)
        self.assertTrue(vRes3.is_valid())
        self.assertEqual(vRes3.error_count(), 0)
        self.assertTrue("No error messages" in vRes3.get_errors())

    def test_validatePairFiles_invalid_oddLength(self):
        dataDir = path.join(path_to_module, "testSeqPairFiles", "oddLength")

        sampleID = "01-1111"
        pfList = get_pair_files(dataDir, sampleID)

        self.assertEqual(len(pfList), 1)
        v_res = validate_pair_files(pfList)

        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)
        self.assertTrue(
            "The given file list has an odd number of files"
            in v_res.get_errors())

    def test_validatePairFiles_invalid_noPair(self):
        dataDir = path.join(path_to_module, "testSeqPairFiles", "noPair")

        sampleID = "01-1111"
        pfList1 = get_pair_files(dataDir, sampleID)
        # 01-1111_S1_L001_R1_001.fastq.gz, 01-1111_S1_L001_R9_001.fastq.gz

        self.assertEqual(len(pfList1), 2)
        vRes1 = validate_pair_files(pfList1)

        self.assertFalse(vRes1.is_valid())
        self.assertEqual(vRes1.error_count(), 1)
        self.assertTrue("No pair sequence file found" in vRes1.get_errors())

        sampleID = "02-2222"
        pfList2 = get_pair_files(dataDir, sampleID)
        # 02-2222_S1_L001_R2_001.fastq.gz, 02-2222_S1_L001_R8_001.fastq.gz

        self.assertEqual(len(pfList2), 2)
        vRes2 = validate_pair_files(pfList2)

        self.assertFalse(vRes2.is_valid())
        self.assertEqual(vRes2.error_count(), 1)
        self.assertTrue("No pair sequence file found" in vRes2.get_errors())

        pfList3 = pfList1 + pfList2
        self.assertEqual(len(pfList3), 4)

        vRes3 = validate_pair_files(pfList3)

        self.assertFalse(vRes3.is_valid())
        self.assertEqual(vRes3.error_count(), 1)
        self.assertTrue("No pair sequence file found" in vRes3.get_errors())

    def test_validatePairFiles_invalid_seqFiles(self):
        dataDir = path.join(
            path_to_module, "testSeqPairFiles", "invalidSeqFiles")

        sampleID = "01-1111"
        pfList1 = get_pair_files(dataDir, sampleID)
        # 01-1111_S1_L001_R0_001.fastq.gz, 01-1111_S1_L001_R3_001.fastq.gz

        self.assertEqual(len(pfList1), 2)
        vRes1 = validate_pair_files(pfList1)

        self.assertFalse(vRes1.is_valid())
        self.assertEqual(vRes1.error_count(), 1)
        self.assertTrue(
            "doesn't contain either 'R1' or 'R2' in filename"
            in vRes1.get_errors())

        sampleID = "02-2222"
        pfList2 = get_pair_files(dataDir, sampleID)
        # 02-2222_S1_L001_R5_001.fastq.gz, 02-2222_S1_L001_R4_001.fastq.gz

        self.assertEqual(len(pfList2), 2)
        vRes2 = validate_pair_files(pfList2)

        self.assertFalse(vRes2.is_valid())
        self.assertEqual(vRes2.error_count(), 1)
        self.assertTrue(
            "doesn't contain either 'R1' or 'R2' in filename"
            in vRes2.get_errors())

        pfList3 = pfList1 + pfList2

        self.assertEqual(len(pfList3), 4)
        vRes3 = validate_pair_files(pfList3)

        self.assertFalse(vRes3.is_valid())
        self.assertEqual(vRes3.error_count(), 1)
        self.assertTrue(
            "doesn't contain either 'R1' or 'R2' in filename"
            in vRes3.get_errors())

    def test_validateSampleList_valid(self):
        csv_file = path.join(path_to_module, "fake_ngs_data",
                             "SampleSheet.csv")

        samplesList = parse_samples(csv_file)
        self.assertEqual(len(samplesList), 3)

        v_res = validate_sample_list(samplesList)
        self.assertTrue(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 0)
        self.assertTrue("No error messages" in v_res.get_errors())

    def test_validateSampleList_invalid_noSampleProj(self):
        # missing Sample_Project
        csv_file = path.join(
            path_to_module, "testSeqPairFiles", "noSampleProj",
            "SampleSheet.csv")

        samplesList = parse_samples(csv_file)

        self.assertEqual(len(samplesList), 3)
        v_res = validate_sample_list(samplesList)

        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)
        self.assertTrue(
            "No sampleProject found for sample" in v_res.get_errors())

    def test_validateSampleList_invalid_Empty(self):
        samplesList = []

        self.assertEqual(len(samplesList), 0)
        v_res = validate_sample_list(samplesList)

        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)
        self.assertTrue(
            "The given list of samples is empty" in v_res.get_errors())

    def test_validateURLForm(self):
        urlList = [
            {"url": "http://google.com/",
             "valid": True},

            {"url": "http://localhost:8080/",
             "valid": True},

            {"url": "www.google.com/",
             "valid": False},

            {"url": "www.google.com",
             "valid": False},

            {"url": "google.com",
             "valid": False}
        ]

        for item in urlList:
            is_valid = validate_URL_form(item["url"])
            self.assertEqual(is_valid, item["valid"])


offValidationTestSuite = unittest.TestSuite()

offValidationTestSuite.addTest(
    TestOfflineValidation("test_validateSampleSheet_validSheet"))
offValidationTestSuite.addTest(
    TestOfflineValidation("test_validateSampleSheet_missing_DataHeader"))
offValidationTestSuite.addTest(
    TestOfflineValidation("test_validateSampleSheet_emptySheet"))
offValidationTestSuite.addTest(
    TestOfflineValidation("test_validateSampleSheet_missing_HeaderSection"))

offValidationTestSuite.addTest(
    TestOfflineValidation("test_validatePairFiles_valid"))
offValidationTestSuite.addTest(
    TestOfflineValidation("test_validatePairFiles_invalid_oddLength"))
offValidationTestSuite.addTest(
    TestOfflineValidation("test_validatePairFiles_invalid_noPair"))
offValidationTestSuite.addTest(
    TestOfflineValidation("test_validatePairFiles_invalid_seqFiles"))

offValidationTestSuite.addTest(
    TestOfflineValidation("test_validateSampleList_valid"))
offValidationTestSuite.addTest(
    TestOfflineValidation("test_validateSampleList_invalid_noSampleProj"))

offValidationTestSuite.addTest(TestOfflineValidation("test_validateURLForm"))


if __name__ == "__main__":
    suiteList = []

    suiteList.append(offValidationTestSuite)
    fullSuite = unittest.TestSuite(suiteList)

    runner = unittest.TextTestRunner()
    runner.run(fullSuite)
