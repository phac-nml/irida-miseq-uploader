import unittest
from os import path

from Validation.offlineValidation import (
    validate_sample_sheet,
    validate_sample_list,
    validate_URL_form)
from Model.Sample import Sample

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

    def test_validate_sample_list_valid(self):

        sample1 = Sample({
            "sequencerSampleId": "01-1111",
            "sampleName": "01-1111",
            "Sample_Plate": "1",
            "Sample_Well": "01",
            "I7_Index_ID": "N01",
            "index": "AAAAAAAA",
            "I5_Index_ID": "S01",
            "index2": "TTTTTTTT",
            "sampleProject": "6",
            "description": "Super bug"
        })

        sample2 = Sample({
            "sequencerSampleId": "02-2222",
            "sampleName": "02-2222",
            "Sample_Plate": "2",
            "Sample_Well": "02",
            "I7_Index_ID": "N02",
            "index": "GGGGGGGG",
            "I5_Index_ID": "S02",
            "index2": "CCCCCCCC",
            "sampleProject": "6",
            "description": "Scary bug"
        })

        sample3 = Sample({
            "sequencerSampleId": "03-3333",
            "sampleName": "03-3333",
            "Sample_Plate": "3",
            "Sample_Well": "03",
            "I7_Index_ID": "N03",
            "index": "CCCCCCCC",
            "I5_Index_ID": "S03",
            "index2": "GGGGGGGG",
            "sampleProject": "6",
            "description": "Deadly bug"
        })

        sample_list = [sample1, sample2, sample3]

        v_res = validate_sample_list(sample_list)
        self.assertTrue(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 0)
        self.assertTrue("No error messages" in v_res.get_errors())

    def test_validate_sample_list_valid_empty_description(self):

        sample = Sample({"Sample_Well": "03",
                         "index": "CCCCCCCC",
                         "Sample_Plate": "3",
                         "I7_Index_ID": "N03",
                         "sampleName": "03-3333",
                         "sampleProject": "6",
                         "sequencerSampleId": "03-3333",
                         "I5_Index_ID": "S03",
                         "index2": "GGGGGGGG",
                         "description": ""})

        sample_list = [sample]

        v_res = validate_sample_list(sample_list)
        self.assertTrue(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 0)
        self.assertTrue("No error messages" in v_res.get_errors())

    def test_validateSampleList_invalid_missing_req_values(self):

        sample1 = Sample({
            "sequencerSampleId": "01-1111",
            "sampleName": "01-1111",
            "Sample_Plate": "1",
            "Sample_Well": "01",
            "I7_Index_ID": "N01",
            "index": "AAAAAAAA",
            "I5_Index_ID": "S01",
            "index2": "TTTTTTTT",
            "sampleProject": "",
            "description": "Super bug"
        })

        sample2 = Sample({
            "sequencerSampleId": "02-2222",
            "sampleName": "",
            "Sample_Plate": "2",
            "Sample_Well": "02",
            "I7_Index_ID": "N02",
            "index": "GGGGGGGG",
            "I5_Index_ID": "S02",
            "index2": "CCCCCCCC",
            "sampleProject": "6",
            "description": "Scary bug"
        })

        sample_list = [sample1, sample2]

        v_res = validate_sample_list(sample_list)
        self.assertFalse(v_res.is_valid())
        self.assertEqual(v_res.error_count(), 2)

        expected_err_msg1 = (
            "{sid} missing Sample_Project").format(
                sid=sample1.get_id())
        self.assertIn(expected_err_msg1, v_res.get_errors())

        expected_err_msg2 = (
            "{sid} missing Sample_Name").format(
                sid=sample2.get_id())
        self.assertIn(expected_err_msg2, v_res.get_errors())

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

    off_validation_test_suite.addTest(
        TestOfflineValidation(
            "test_validate_sample_sheet_missing_data_header"))

    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_sample_sheet_empty_sheet"))
    off_validation_test_suite.addTest(TestOfflineValidation(
        "test_validate_sample_sheet_missing_header_sect"))

    off_validation_test_suite.addTest(
        TestOfflineValidation("test_validate_sample_list_valid"))
    off_validation_test_suite.addTest(
        TestOfflineValidation(
            "test_validate_sample_list_valid_empty_description"))
    off_validation_test_suite.addTest(
        TestOfflineValidation(
            "test_validateSampleList_invalid_missing_req_values"))
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
