import unittest
import pytest
import ntpath
import logging
from os import path

from Model.Project import Project
from Model.Sample import Sample
from Parsers.miseqParser import complete_parse_samples

@pytest.mark.skipif(not pytest.config.getoption("--integration"), reason = "skipped integration tests")
@pytest.mark.usefixtures("api")
class TestApiIntegration(unittest.TestCase):

    def test_get_sequence_files(self):

        proj_list = self.api.get_projects()
        proj = proj_list[len(proj_list) - 1]
        sample_list = self.api.get_samples(proj)
        sample = sample_list[len(sample_list) - 1]

        seq_file_list = self.api.get_sequence_files(proj, sample)
        self.assertEqual(len(seq_file_list), 2)

        seq_file1 = seq_file_list[0]
        seq_file2 = seq_file_list[1]
        self.assertTrue("file" in seq_file1)
        self.assertTrue("file" in seq_file2)
        self.assertEqual(str(seq_file1["fileName"]),
                         "01-1111_S1_L001_R1_001.fastq")
        self.assertEqual(str(seq_file2["fileName"]),
                         "01-1111_S1_L001_R2_001.fastq")

    def test_get_and_send_project(self):

        proj_list = self.api.get_projects()
        self.assertTrue(len(proj_list) == 0)

        proj_name = "integration testProject"
        proj_description = "integration testProject description"
        proj = Project(proj_name, proj_description)
        server_response = self.api.send_project(proj)

        self.assertEqual(proj_name,
                         server_response["resource"]["name"])
        self.assertEqual(proj_description,
                         server_response["resource"]["projectDescription"])
        self.assertEqual("1",
                         server_response["resource"]["identifier"])

        proj_list = self.api.get_projects()
        self.assertTrue(len(proj_list) == 1)

        added_proj = proj_list[0]
        self.assertEqual(added_proj.get_name(), "integration testProject")
        self.assertEqual(
            added_proj.get_description(),
            "integration testProject description")

    def test_get_and_send_samples(self):

        proj_list = self.api.get_projects()
        proj = proj_list[0]
        sample_list = self.api.get_samples(proj)
        self.assertTrue(len(sample_list) == 0)

        sample_dict = {
            "sampleName": "99-9999",
            "description": "integration_testSample description",
            "sampleProject": proj.get_id()
            # sequencer sample ID must have at least 3 characters
        }

        sample = Sample(sample_dict)
        server_response_list = self.api.send_samples([sample])
        self.assertEqual(len(server_response_list), 1)

        server_response = server_response_list[0]

        self.assertEqual(sample_dict["sampleName"],
                         server_response["resource"]["sampleName"])
        self.assertEqual(sample_dict["description"],
                         server_response["resource"]["description"])
        self.assertEqual("1",
                         server_response["resource"]["identifier"])

        sample_list = self.api.get_samples(proj)
        self.assertTrue(len(sample_list) == 1)

        added_sample = sample_list[0]
        del sample_dict["sampleProject"]
        for key in sample_dict.keys():
            self.assertEqual(sample[key], added_sample[key])

    def test_create_seq_run(self):

        metadata_dict = {
            "workflow": "test_workflow",
            "readLengths": "1",
            "layoutType": "PAIRED_END"
        }

        seq_run_list = self.api.get_seq_runs()
        self.assertEqual(len(seq_run_list), 0)

        json_res = self.api.create_seq_run(metadata_dict)

        seq_run_list = self.api.get_seq_runs()
        self.assertEqual(len(seq_run_list), 1)

        upload_id = json_res["resource"]["identifier"]
        upload_status = json_res["resource"]["uploadStatus"]
        self.assertEqual(upload_id, "1")
        self.assertEqual(upload_status, "UPLOADING")

    def test_get_and_send_sequence_files(self):
        path_to_module = path.dirname(__file__)
        if len(path_to_module) == 0:
            path_to_module = '.'
        sample_sheet_file = path.join(path_to_module, "fake_ngs_data",
                                      "SampleSheet.csv")
        samples_list = complete_parse_samples(sample_sheet_file)

        # check that the sample with id 99-9999 (from SampleSheet.csv)
        # has no sequence files
        seq_file_list = []
        for sample in samples_list:
            res = self.api.get_sequence_files(sample)
            if len(res) > 0:
                seq_file_list.append(res)
        self.assertEqual(len(seq_file_list), 0)

        serv_res_list = self.api.send_sequence_files(samples_list)[0]

        # check that the sample with id 99-9999 (from SampleSheet.csv)
        # has the one that we just uploaded.
        seq_file_list = []
        for sample in samples_list:
            res = self.api.get_sequence_files(sample)
            if len(res) > 0:
                seq_file_list.append(res)

        self.assertEqual(len(seq_file_list), 1)

        filename_list = [serv_resp["resource"]["object"]["fileName"]
                         for serv_resp in
                         serv_res_list["resource"]["resources"]]
        self.assertEqual(len(filename_list), 2)

        # check that the files in each sample are found
        # in the server response
        for sample in samples_list:
            self.assertIn(ntpath.basename(sample.get_files()[0]),
                          filename_list)
            self.assertIn(ntpath.basename(sample.get_files()[1]),
                          filename_list)

        self.assertEqual(len(serv_res_list), len(samples_list))

    def test_set_seq_run_complete(self):
        self.api.set_seq_run_complete(identifier="1")
        seq_run_list = self.api.get_seq_runs()
        self.assertEqual(len(seq_run_list), 1)
        self.assertEqual(seq_run_list[0]["uploadStatus"], "COMPLETE")
