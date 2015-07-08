import unittest
from os import path
from csv import reader

from Model.Sample import Sample
from Parsers.miseqParser import (parse_metadata, parse_samples, get_csv_reader,
                                 get_pair_files, parse_out_sequence_file,
                                 complete_parse_samples)
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError

path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'


class TestMiSeqParser(unittest.TestCase):

    def setUp(self):

        print "\nStarting " + self.__module__ + ": " + self._testMethodName

    def test_get_csv_reader_no_sample_sheet(self):

        data_dir = path.join(path_to_module, "fake_ngs_data", "Data")

        with self.assertRaises(SampleSheetError) as context:
            csv_reader = get_csv_reader(data_dir)

        self.assertTrue(
            "not a valid SampleSheet file" in str(context.exception))

    def test_get_csv_reader_valid_sheet(self):

        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "SampleSheet.csv")
        csv_reader = get_csv_reader(sheet_file)

    def test_parse_metadata(self):

        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "SampleSheet.csv")
        meta_data = parse_metadata(sheet_file)

        correct_metadata = {"readLengths": ["251", "250"],
                            "assay": "Nextera XT",
                            "description": "Superbug",
                            "application": "FASTQ Only",
                            "investigatorName": "Some Guy",
                            "adapter": "AAAAGGGGAAAAGGGGAAA",
                            "workflow": "GenerateFASTQ",
                            "reversecomplement": "0",
                            "iemfileversion": "4",
                            "date": "10/15/2013",
                            "experimentName": "1",
                            "chemistry": "Amplicon"}

        self.assertEqual(correct_metadata, meta_data)

    def test_complete_parse_samples(self):

        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "SampleSheet.csv")
        data_dir = path.join(path_to_module, "fake_ngs_data")

        sample_list = complete_parse_samples(sheet_file)
        self.assertEqual(len(sample_list), 3)

        required_data_headers = [
            "sampleName",
            "description",
            "sequencerSampleId",
            "sampleProject"]

        seq_file_headers = [
            "index",
            "I7_Index_ID",
            "Sample_Well",
            "Sample_Plate",
            "index2",
            "I5_Index_ID"]

        for sample in sample_list:

            # sample only has the 4 required data headers as keys
            self.assertEqual(
                len(sample.get_dict().keys()), len(required_data_headers))

            # check if all values in required_data_headers are found in the
            # sample's dictionary keys
            self.assertTrue(
                all([data_header in sample.get_dict().keys() for data_header in
                    required_data_headers]))

            # check if all values in seq_file_headers are found in the Sequence
            # File properties dict /Sample metadata
            self.assertTrue(
                all([data_header in sample.get_sample_metadata().keys()
                    for data_header in seq_file_headers]))

            self.assertEqual(len(sample.get_pair_files()), 2)
            pf_list = get_pair_files(data_dir, sample.get_id())
            self.assertEqual(pf_list, sample.get_pair_files())

    def test_parse_samples(self):

        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "SampleSheet.csv")
        sample_list = parse_samples(sheet_file)

        correct_samples = [
            {"Sample_Well": "01",
             "index": "AAAAAAAA",
             "Sample_Plate": "1",
             "I7_Index_ID": "N01",
             "sampleName": "01-1111",
             "sampleProject": "6",
             "sequencerSampleId": "01-1111",
             "I5_Index_ID": "S01",
             "index2": "TTTTTTTT",
             "description": "Super bug "},

            {"Sample_Well": "02",
             "index": "GGGGGGGG",
             "Sample_Plate": "2",
             "I7_Index_ID": "N02",
             "sampleName": "02-2222",
             "sampleProject": "6",
             "sequencerSampleId": "02-2222",
             "I5_Index_ID": "S02",
             "index2": "CCCCCCCC",
             "description": "Scary bug "},

            {"Sample_Well": "03",
             "index": "CCCCCCCC",
             "Sample_Plate": "3",
             "I7_Index_ID": "N03",
             "sampleName": "03-3333",
             "sampleProject": "6",
             "sequencerSampleId": "03-3333",
             "I5_Index_ID": "S03",
             "index2": "GGGGGGGG",
             "description": "Deadly bug "}
        ]

        sample_list_values = [sample.get_dict() for sample in sample_list]
        self.assertEqual(correct_samples, sample_list_values)

    def test_parse_out_sequence_file(self):

        sample = Sample({"Sample_Well": "03",
                         "index": "CCCCCCCC",
                         "Sample_Plate": "3",
                         "I7_Index_ID": "N03",
                         "sampleName": "03-3333",
                         "sampleProject": "6",
                         "sequencerSampleId": "03-3333",
                         "I5_Index_ID": "S03",
                         "index2": "GGGGGGGG",
                         "description": "Deadly bug "})

        correct_sample = {"description": "Deadly bug ",
                          "sampleName": "03-3333",
                          "sequencerSampleId": "03-3333",
                          "sampleProject": "6"}

        correct_seq_file = {"index": "CCCCCCCC",
                            "I7_Index_ID": "N03",
                            "Sample_Well": "03",
                            "Sample_Plate": "3",
                            "index2": "GGGGGGGG",
                            "I5_Index_ID": "S03"}

        seq_file = parse_out_sequence_file(sample)

        self.assertEqual(sample.get_dict(), correct_sample)
        self.assertEqual(seq_file, correct_seq_file)

    def test_get_pair_files_invalid_dir_and_id(self):

        invalid_dir = "+/not a directory/+"
        invalid_sample_id = "-1"

        with self.assertRaises(IOError) as context:
            pair_file_list = get_pair_files(invalid_dir, invalid_sample_id)

        self.assertTrue("Invalid directory" in str(context.exception))

    def test_get_pair_files_invalid_dir_valid_id(self):
        invalid_dir = "+/not a directory/+"
        valid_sample_id = "01-1111"

        with self.assertRaises(IOError) as context:
            pair_file_list = get_pair_files(invalid_dir, valid_sample_id)

        self.assertTrue("Invalid directory" in str(context.exception))

    def test_get_pair_files_valid_dir_invalid_id(self):

        valid_dir = path.join(path_to_module, "fake_ngs_data")
        invalid_sample_id = "-1"

        pair_file_list = get_pair_files(valid_dir, invalid_sample_id)

        self.assertEqual(len(pair_file_list), 0)

    def test_get_pair_files_valid_dir_valid_id(self):

        valid_dir = path.join(path_to_module, "fake_ngs_data")
        valid_sample_id = "01-1111"

        pair_file_list = get_pair_files(valid_dir, valid_sample_id)
        correct_pair_list = [
            path.join(path_to_module, "fake_ngs_data", "Data", "Intensities",
                      "BaseCalls", "01-1111_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module, "fake_ngs_data", "Data", "Intensities",
                      "BaseCalls", "01-1111_S1_L001_R2_001.fastq.gz")]
        self.assertEqual(correct_pair_list, pair_file_list)


def load_test_suite():

    parser_test_suite = unittest.TestSuite()

    parser_test_suite.addTest(
        TestMiSeqParser("test_get_csv_reader_no_sample_sheet"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_csv_reader_valid_sheet"))

    parser_test_suite.addTest(TestMiSeqParser("test_parse_metadata"))
    parser_test_suite.addTest(TestMiSeqParser("test_complete_parse_samples"))
    parser_test_suite.addTest(TestMiSeqParser("test_parse_samples"))
    parser_test_suite.addTest(TestMiSeqParser("test_parse_out_sequence_file"))

    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_invalid_dir_and_id"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_invalid_dir_valid_id"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_valid_dir_invalid_id"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_valid_dir_valid_id"))

    return parser_test_suite

if __name__ == "__main__":

    test_suite = load_test_suite()
    full_suite = unittest.TestSuite([test_suite])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
