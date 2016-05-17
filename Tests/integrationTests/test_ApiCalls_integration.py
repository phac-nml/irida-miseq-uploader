import pytest
import ntpath
import logging
from os import path

from Model.Project import Project
from Model.Sample import Sample
from Parsers.miseqParser import complete_parse_samples
from API.directoryscanner import find_runs_in_directory

@pytest.mark.skipif(not pytest.config.getoption("--integration"), reason = "skipped integration tests")
class TestApiIntegration:

    def test_get_and_send_project(self, api):

        proj_list = api.get_projects()
        assert len(proj_list) == 0

        proj_name = "integration testProject"
        proj_description = "integration testProject description"
        proj = Project(proj_name, proj_description)
        server_response = api.send_project(proj)

        assert proj_name == server_response["resource"]["name"]
        assert proj_description == server_response["resource"]["projectDescription"]
        assert "1" == server_response["resource"]["identifier"]

        proj_list = api.get_projects()
        assert len(proj_list) == 1

        added_proj = proj_list[0]
        assert added_proj.get_name() == "integration testProject"
        assert added_proj.get_description() == "integration testProject description"

    def test_get_and_send_samples(self, api):

        proj_list = api.get_projects()
        proj = proj_list[0]
        sample_list = api.get_samples(proj)
        assert len(sample_list) == 0

        sample_dict = {
            "sampleName": "99-9999",
            "description": "integration_testSample description",
            "sampleProject": proj.get_id()
            # sequencer sample ID must have at least 3 characters
        }

        sample = Sample(sample_dict)
        server_response_list = api.send_samples([sample])
        assert len(server_response_list) == 1

        server_response = server_response_list[0]

        assert sample_dict["sampleName"] == server_response["resource"]["sampleName"]
        assert sample_dict["description"] == server_response["resource"]["description"]
        assert "1" == server_response["resource"]["identifier"]

        sample_list = api.get_samples(proj)
        assert len(sample_list) == 1

        added_sample = sample_list[0]
        del sample_dict["sampleProject"]
        for key in sample_dict.keys():
            assert sample[key] == added_sample[key]

    def test_create_seq_run(self, api):

        metadata_dict = {
            "workflow": "test_workflow",
            "readLengths": "1",
            "layoutType": "PAIRED_END"
        }

        seq_run_list = api.get_seq_runs()
        assert len(seq_run_list) == 0

        json_res = api.create_seq_run(metadata_dict)

        seq_run_list = api.get_seq_runs()
        assert len(seq_run_list) == 1

        upload_id = json_res["resource"]["identifier"]
        upload_status = json_res["resource"]["uploadStatus"]
        assert upload_id == "1"
        assert upload_status == "UPLOADING"

    def test_get_and_send_sequence_files(self, api):
        path_to_module = path.dirname(__file__)
        if len(path_to_module) == 0:
            path_to_module = '.'

        run = find_runs_in_directory(path.join(path_to_module, "fake_ngs_data")).pop()
        samples_list = run.sample_list

        # check that the sample with id 99-9999 (from SampleSheet.csv)
        # has no sequence files
        seq_file_list = []
        for sample in samples_list:
            res = api.get_sequence_files(sample)
            if len(res) > 0:
                seq_file_list.append(res)
        assert len(seq_file_list) == 0

        serv_res_list = api.send_sequence_files(samples_list)[0]

        # check that the sample with id 99-9999 (from SampleSheet.csv)
        # has the one that we just uploaded.
        seq_file_list = []
        for sample in samples_list:
            res = api.get_sequence_files(sample)
            logging.info(str(res))
            if len(res) > 0:
                seq_file_list.append(res)

        assert len(seq_file_list) == 1

        filename_list = [serv_resp["fileName"]
                         for serv_resp in
                         seq_file_list[0]]
        assert len(filename_list) == 2

        # check that the files in each sample are found
        # in the server response
        for sample in samples_list:
            assert ntpath.basename(sample.get_files()[0]) in filename_list
            assert ntpath.basename(sample.get_files()[1]) in filename_list

        assert len(serv_res_list) == len(samples_list)

    def test_set_seq_run_complete(self, api):
        api.set_seq_run_complete(identifier="1")
        seq_run_list = api.get_seq_runs()
        assert len(seq_run_list) == 1
        assert seq_run_list[0]["uploadStatus"] == "COMPLETE"
