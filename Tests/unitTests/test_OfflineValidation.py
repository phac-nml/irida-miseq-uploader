import unittest
from os import path

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

    def test_validate_sample_sheet_valid_sheet(self):

        csv_file = path.join(path_to_module, "fake_ngs_data",
                             "SampleSheet.csv")
        v_res = validate_sample_sheet(csv_file)
        self.assertTrue(v_res.is_valid())

    def test_validate_sample_sheet_empty_sheet(self):

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

    def test_validate_sample_sheet_missing_data_header(self):

        # has [Header]+[Data] but missing required data header (Sample_Project)
        csv_file = path.join(
            path_to_module, "testSampleSheets", "missingDataHeader.csv")
        v_res = validate_sample_sheet(csv_file)
        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)

        self.assertTrue(
            "Missing required data header(s): Sample_Project"
            in v_res.get_errors())

    def test_validate_sample_sheet_missing_header_sect(self):

        # has [Data] and required data headers but missing [Header]
        csv_file = path.join(
            path_to_module, "testSampleSheets", "missingHeaderSection.csv")
        v_res = validate_sample_sheet(csv_file)
        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)

        self.assertTrue(
            "[Header] section not found in SampleSheet" in v_res.get_errors())

    def test_validate_pair_files_valid(self):

        data_dir = path.join(path_to_module, "fake_ngs_data")

        sample_id = "01-1111"
        pf_list1 = get_pair_files(data_dir, sample_id)

        self.assertEqual(len(pf_list1), 2)
        v_res1 = validate_pair_files(pf_list1)

        self.assertTrue(v_res1.is_valid())
        self.assertEqual(v_res1.error_count(), 0)
        self.assertTrue("No error messages" in v_res1.get_errors())

        sample_id = "02-2222"
        pf_list2 = get_pair_files(data_dir, sample_id)

        self.assertEqual(len(pf_list2), 2)
        v_res2 = validate_pair_files(pf_list2)

        self.assertTrue(v_res2.is_valid())
        self.assertEqual(v_res2.error_count(), 0)
        self.assertTrue("No error messages" in v_res2.get_errors())

        pf_list3 = pf_list1 + pf_list2
        self.assertEqual(len(pf_list3), 4)

        v_res3 = validate_pair_files(pf_list3)
        self.assertTrue(v_res3.is_valid())
        self.assertEqual(v_res3.error_count(), 0)
        self.assertTrue("No error messages" in v_res3.get_errors())

    def test_validate_pair_files_invalid_odd_length(self):

        data_dir = path.join(path_to_module, "testSeqPairFiles", "oddLength")

        sample_id = "01-1111"
        pf_list = get_pair_files(data_dir, sample_id)

        self.assertEqual(len(pf_list), 1)
        v_res = validate_pair_files(pf_list)

        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)
        self.assertTrue(
            "The given file list has an odd number of files"
            in v_res.get_errors())

    def test_validate_pair_files_invalid_no_pair(self):

        data_dir = path.join(path_to_module, "testSeqPairFiles", "noPair")

        sample_id = "01-1111"
        pf_list1 = get_pair_files(data_dir, sample_id)
        # 01-1111_S1_L001_R1_001.fastq.gz, 01-1111_S1_L001_R9_001.fastq.gz

        self.assertEqual(len(pf_list1), 2)
        v_res1 = validate_pair_files(pf_list1)

        self.assertFalse(v_res1.is_valid())
        self.assertEqual(v_res1.error_count(), 1)
        self.assertTrue("No pair sequence file found" in v_res1.get_errors())

        sample_id = "02-2222"
        pf_list2 = get_pair_files(data_dir, sample_id)
        # 02-2222_S1_L001_R2_001.fastq.gz, 02-2222_S1_L001_R8_001.fastq.gz

        self.assertEqual(len(pf_list2), 2)
        v_res2 = validate_pair_files(pf_list2)

        self.assertFalse(v_res2.is_valid())
        self.assertEqual(v_res2.error_count(), 1)
        self.assertTrue("No pair sequence file found" in v_res2.get_errors())

        pf_list3 = pf_list1 + pf_list2
        self.assertEqual(len(pf_list3), 4)

        v_res3 = validate_pair_files(pf_list3)

        self.assertFalse(v_res3.is_valid())
        self.assertEqual(v_res3.error_count(), 1)
        self.assertTrue("No pair sequence file found" in v_res3.get_errors())

    def test_validate_pair_files_invalid_seq_files(self):

        data_dir = path.join(
            path_to_module, "testSeqPairFiles", "invalidSeqFiles")

        sample_id = "01-1111"
        pf_list1 = get_pair_files(data_dir, sample_id)
        # 01-1111_S1_L001_R0_001.fastq.gz, 01-1111_S1_L001_R3_001.fastq.gz

        self.assertEqual(len(pf_list1), 2)
        v_res1 = validate_pair_files(pf_list1)

        self.assertFalse(v_res1.is_valid())
        self.assertEqual(v_res1.error_count(), 1)
        self.assertTrue(
            "doesn't contain either 'R1' or 'R2' in filename"
            in v_res1.get_errors())

        sample_id = "02-2222"
        pf_list2 = get_pair_files(data_dir, sample_id)
        # 02-2222_S1_L001_R5_001.fastq.gz, 02-2222_S1_L001_R4_001.fastq.gz

        self.assertEqual(len(pf_list2), 2)
        v_res2 = validate_pair_files(pf_list2)

        self.assertFalse(v_res2.is_valid())
        self.assertEqual(v_res2.error_count(), 1)
        self.assertTrue(
            "doesn't contain either 'R1' or 'R2' in filename"
            in v_res2.get_errors())

        pf_list3 = pf_list1 + pf_list2

        self.assertEqual(len(pf_list3), 4)
        v_res3 = validate_pair_files(pf_list3)

        self.assertFalse(v_res3.is_valid())
        self.assertEqual(v_res3.error_count(), 1)
        self.assertTrue(
            "doesn't contain either 'R1' or 'R2' in filename"
            in v_res3.get_errors())

    def test_validate_sample_list_valid(self):

        csv_file = path.join(path_to_module, "fake_ngs_data",
                             "SampleSheet.csv")

        sample_list = parse_samples(csv_file)
        self.assertEqual(len(sample_list), 3)

        v_res = validate_sample_list(sample_list)
        self.assertTrue(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 0)
        self.assertTrue("No error messages" in v_res.get_errors())

    def test_validateSampleList_invalid_no_sample_proj(self):

        # missing Sample_Project
        csv_file = path.join(
            path_to_module, "testSeqPairFiles", "noSampleProj",
            "SampleSheet.csv")

        sample_list = parse_samples(csv_file)

        self.assertEqual(len(sample_list), 3)
        v_res = validate_sample_list(sample_list)

        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)
        self.assertTrue(
            "No sampleProject found for sample" in v_res.get_errors())

    def test_validateSampleList_invalid_empty(self):

        sample_list = []

        self.assertEqual(len(sample_list), 0)
        v_res = validate_sample_list(sample_list)

        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 1)
        self.assertTrue(
            "The given list of samples is empty" in v_res.get_errors())

    def test_validate_URL_form(self):

        url_list = [
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

        for item in url_list:
            is_valid = validate_URL_form(item["url"])
            self.assertEqual(is_valid, item["valid"])


def load_test_suite():

    off_validation_test_suite = unittest.TestSuite()

    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_sample_sheet_valid_sheet"))

    short_name1 = "test_validate_sample_sheet_missing_data_header"
    off_validation_test_suite.addTest(TestOfflineValidation(short_name1))

    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_sample_sheet_empty_sheet"))
    off_validation_test_suite.addTest(TestOfflineValidation(
        "test_validate_sample_sheet_missing_header_sect"))

    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_pair_files_valid"))
    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_pair_files_invalid_odd_length"))
    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_pair_files_invalid_no_pair"))
    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_pair_files_invalid_seq_files"))

    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_sample_list_valid"))

    short_name2 = "test_validateSampleList_invalid_no_sample_proj"
    off_validation_test_suite.addTest(TestOfflineValidation(short_name2))
    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validateSampleList_invalid_empty"))

    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_URL_form"))

    return off_validation_test_suite

if __name__ == "__main__":

    test_suite = load_test_suite()
    full_suite = unittest.TestSuite([test_suite])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
