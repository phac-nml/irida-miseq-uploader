import unittest
from os import path
from csv import reader
from StringIO import StringIO
from mock import patch

from Model.Sample import Sample
from Parsers.miseqParser import (
    parse_metadata, parse_samples, get_csv_reader,
    get_pair_files, get_all_fastq_files,
    parse_out_sequence_file,
    complete_parse_samples)
from Exceptions.SampleSheetError import SampleSheetError

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestMiSeqParser(unittest.TestCase):

    def setUp(self):

        print "\nStarting " + self.__module__ + ": " + self._testMethodName

    def test_get_csv_reader_no_sample_sheet(self):

        data_dir = path.join(path_to_module, "fake_ngs_data", "Data")

        with self.assertRaises(SampleSheetError) as context:
            get_csv_reader(data_dir)

        self.assertTrue(
            "not a valid SampleSheet file" in str(context.exception))

    def test_get_csv_reader_valid_sheet(self):

        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "SampleSheet.csv")
        get_csv_reader(sheet_file)

    def test_parse_metadata_extra_commas(self):

        sheet_file = path.join(path_to_module, "testValidSheetTrailingCommas",
                               "SampleSheet.csv")
        meta_data = parse_metadata(sheet_file)

        correct_metadata = {"readLengths": "301",
                            "assay": "TruSeq HT",
                            "description": "252",
                            "application": "FASTQ Only",
                            "investigatorName": "Investigator",
                            "adapter": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
			    "adapterread2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
                            "workflow": "GenerateFASTQ",
                            "reversecomplement": "0",
                            "iemfileversion": "4",
                            "date": "2015-11-12",
                            "experimentName": "252",
                            "chemistry": "Amplicon",
                            "layoutType": "PAIRED_END"}

        self.assertEqual(correct_metadata, meta_data)

    def test_parse_metadata(self):

        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "SampleSheet.csv")
        meta_data = parse_metadata(sheet_file)

        correct_metadata = {"readLengths": "251",
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
                            "chemistry": "Amplicon",
                            "layoutType": "PAIRED_END"}

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
            fastq_files = get_all_fastq_files(data_dir)
            pf_list = get_pair_files(fastq_files, sample.get_id())
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

    @patch("Parsers.miseqParser.get_csv_reader")
    def test_parse_samples_no_trail_comma(self, mock_csv_reader):

        headers = ("Sample_ID,Sample_Name,Sample_Plate,Sample_Well," +
                   "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project," +
                   "Description")

        field_values = (
            "15-0318,,2015-08-05-SE,A01,N701,TAAGGCGA,S502,CTCTCTAT,203\n" +
            "15-0455,,2015-08-05-SE,B01,N701,TAAGGCGA,S503,TATCCTCT,203\n" +
            "15-0462,,2015-08-05-SE,C01,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
        )

        file_contents_str = (
            "[Data]\n" +
            "{headers}\n" +
            "{field_values}"
        ).format(headers=headers, field_values=field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        sample_list = parse_samples(sample_sheet_file)
        self.assertEqual(len(sample_list), 3)

        for key in parse_samples.sample_key_translation_dict.keys():
            headers = headers.replace(
                key, parse_samples.sample_key_translation_dict[key])

        for sample in sample_list:

            self.assertEqual(len(headers.split(",")),
                             len(sample.get_dict().keys()))

            # check all translated header values are in Sample object
            # converted to set to remove ordering differences
            self.assertEqual(set(headers.split(",")),
                             set(sample.get_dict().keys()))

            # sample.get_dict() is an OrderedDict
            # so we can check each sample in the same order as the field_values
            # check that all the values in field_values are found in the sample
            i = sample_list.index(sample)
            self.assertEqual(set(field_values.split("\n")[i].split(",")),
                             set(sample.get_dict().values()))

            self.assertEqual(sample.get("description"), "")

    @patch("Parsers.miseqParser.get_csv_reader")
    def test_parse_samples_unequal_data_and_field_length(self,
                                                         mock_csv_reader):

        headers = ("Sample_ID,Sample_Name,Sample_Plate,Sample_Well," +
                   "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project," +
                   "Description")

        field_values = (
            "15-0318,,2015-08-05-SE,A01,N701,TAAGGCGA,S502,CTCTCTAT\n" +
            "15-0455,,2015-08-05-SE,B01,N701,TAAGGCGA,S503,TATCCTCT\n" +
            "15-0462,,2015-08-05-SE,C01,N701,TAAGGCGA,S505,GTAAGGAG\n"
        )

        file_contents_str = (
            "[Data]\n" +
            "{headers}\n" +
            "{field_values}"
        ).format(headers=headers, field_values=field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        with self.assertRaises(SampleSheetError) as context:
            parse_samples(sample_sheet_file)

        expected_err_msg = (
            "Number of values doesn't match number of " +
            "[Data] headers. " +
            ("Number of [Data] headers: {data_len}. " +
             "Number of values: {val_len}").format(
                data_len=len(headers.split(",")),
                val_len=len(field_values.split("\n")[0].split(","))
            )
        )

        self.assertEqual(expected_err_msg,
                         str(context.exception))

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

        with self.assertRaises(OSError) as context:
            fastq_files = get_all_fastq_files(invalid_dir)
            get_pair_files(fastq_files, invalid_sample_id)

        self.assertTrue("Invalid directory" in str(context.exception))

    def test_get_pair_files_invalid_dir_valid_id(self):
        invalid_dir = "+/not a directory/+"
        valid_sample_id = "01-1111"

        with self.assertRaises(OSError) as context:
            fastq_files = get_all_fastq_files(invalid_dir)
            get_pair_files(fastq_files, valid_sample_id)

        self.assertTrue("Invalid directory" in str(context.exception))

    def test_get_pair_files_valid_dir_invalid_id(self):

        valid_dir = path.join(path_to_module, "fake_ngs_data")
        invalid_sample_id = "-1~"

        fastq_files = get_all_fastq_files(valid_dir)
        pair_file_list = get_pair_files(fastq_files, invalid_sample_id)

        self.assertEqual(len(pair_file_list), 0)

    def test_get_pair_files_valid_dir_valid_id(self):

        valid_dir = path.join(path_to_module, "fake_ngs_data")
        valid_sample_id = "01-1111"

        fastq_files = get_all_fastq_files(valid_dir)
        pair_file_list = get_pair_files(fastq_files, valid_sample_id)
        correct_pair_list = [
            path.join(path_to_module, "fake_ngs_data", "Data", "Intensities",
                      "BaseCalls", "01-1111_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module, "fake_ngs_data", "Data", "Intensities",
                      "BaseCalls", "01-1111_S1_L001_R2_001.fastq.gz")]
        self.assertEqual(correct_pair_list, pair_file_list)

    def test_common_prefix_sample_names(self):
        sheet_file = path.join(path_to_module, "testCommonPrefixSampleName",
                               "SampleSheet.csv")
        sample_list = parse_samples(sheet_file)

	fastq_files = get_all_fastq_files(path.join(path_to_module, "testCommonPrefixSampleName"))

	for sample in sample_list:
		sample_id = sample['sequencerSampleId']
		pair_file_list = get_pair_files(fastq_files, sample_id)
		self.assertEquals(len(pair_file_list), 2)

    def test_parse_metadata_empty_description(self):

        sheet_file = path.join(path_to_module, "testValidSheetEmptyDescription",
                               "SampleSheet.csv")
        meta_data = parse_metadata(sheet_file)

        correct_metadata = {"readLengths": "301",
                            "assay": "TruSeq HT",
                            "description": "",
                            "application": "FASTQ Only",
                            "investigatorName": "Investigator",
                            "adapter": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
			    "adapterread2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
                            "workflow": "GenerateFASTQ",
                            "reversecomplement": "0",
                            "iemfileversion": "4",
                            "date": "2015-11-12",
                            "experimentName": "252",
                            "chemistry": "Amplicon",
                            "layoutType": "PAIRED_END"}

        self.assertEqual(correct_metadata, meta_data)



def load_test_suite():

    parser_test_suite = unittest.TestSuite()

    parser_test_suite.addTest(
        TestMiSeqParser("test_get_csv_reader_no_sample_sheet"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_csv_reader_valid_sheet"))

    parser_test_suite.addTest(TestMiSeqParser("test_parse_metadata"))
    parser_test_suite.addTest(TestMiSeqParser("test_complete_parse_samples"))
    parser_test_suite.addTest(TestMiSeqParser("test_parse_samples"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_parse_samples_no_trail_comma"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_parse_samples_unequal_data_and_field_length"))
    parser_test_suite.addTest(TestMiSeqParser("test_parse_out_sequence_file"))

    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_invalid_dir_and_id"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_invalid_dir_valid_id"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_valid_dir_invalid_id"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_get_pair_files_valid_dir_valid_id"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_parse_metadata_extra_commas"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_common_prefix_sample_names"))
    parser_test_suite.addTest(
        TestMiSeqParser("test_parse_metadata_empty_description"))

    return parser_test_suite

if __name__ == "__main__":

    test_suite = load_test_suite()
    full_suite = unittest.TestSuite([test_suite])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
