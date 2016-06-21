import pytest
import logging

from os import path, remove
from wx.lib.pubsub import pub
from Model.Project import Project
from API.runuploader import upload_run_to_server
from API.directoryscanner import find_runs_in_directory

@pytest.mark.skipif(not pytest.config.getoption("--integration"), reason = "skipped integration tests")
class TestRunUploader:
    sample_count = 0

    def update_samples_counter(self, sample):
        self.sample_count += 1

    def test_upload_run_cached_projects(self, api):
        self.sample_count = 0
        # create a project first
        project = Project("project", "description")
        created_project = api.send_project(project)
        project_id = created_project["resource"]["identifier"]

        path_to_module = path.dirname(__file__)
        run_dir = path.join(path_to_module, "fake_ngs_data_with_sample_name")
        try:
            remove(path.join(run_dir, ".miseqUploaderInfo"))
        except:
            pass
        runs = find_runs_in_directory(run_dir)
        assert 1 == len(runs)

        run_to_upload = runs[0]
        for sample in run_to_upload.sample_list:
            sample.get_project_id = lambda: project_id
            pub.subscribe(self.update_samples_counter, sample.upload_completed_topic)

        upload_run_to_server(api, run_to_upload, None)

        assert 2 == self.sample_count

        self.sample_count = 0

        project = Project("project", "description")
        created_project = api.send_project(project, clear_cache=False)
        project_id = created_project["resource"]["identifier"]

        try:
            remove(path.join(run_dir, ".miseqUploaderInfo"))
        except:
            pass
        runs = find_runs_in_directory(run_dir)
        assert 1 == len(runs)

        run_to_upload = runs[0]
        for sample in run_to_upload.sample_list:
            sample.get_project_id = lambda: project_id
            pub.subscribe(self.update_samples_counter, sample.upload_completed_topic)

        upload_run_to_server(api, run_to_upload, None)

        assert 2 == self.sample_count


    def test_upload_run_with_sample_names(self, api):
        self.sample_count = 0
        # create a project first
        project = Project("project", "description")
        created_project = api.send_project(project)
        project_id = created_project["resource"]["identifier"]

        path_to_module = path.dirname(__file__)
        run_dir = path.join(path_to_module, "fake_ngs_data_with_sample_name")
        try:
            remove(path.join(run_dir, ".miseqUploaderInfo"))
        except:
            pass
        runs = find_runs_in_directory(run_dir)
        assert 1 == len(runs)

        run_to_upload = runs[0]
        for sample in run_to_upload.sample_list:
            sample.get_project_id = lambda: project_id
            pub.subscribe(self.update_samples_counter, sample.upload_completed_topic)

        upload_run_to_server(api, run_to_upload, None)

        assert 2 == self.sample_count

    def test_upload_run(self, api):
        self.sample_count = 0
        # create a project first
        project = Project("project", "description")
        created_project = api.send_project(project)
        project_id = created_project["resource"]["identifier"]

        path_to_module = path.dirname(__file__)
        run_dir = path.join(path_to_module, "fake_ngs_data")
        try:
            remove(path.join(run_dir, ".miseqUploaderInfo"))
        except:
            pass
        runs = find_runs_in_directory(run_dir)
        assert 1 == len(runs)

        run_to_upload = runs[0]
        for sample in run_to_upload.sample_list:
            sample.get_project_id = lambda: project_id
            pub.subscribe(self.update_samples_counter, sample.upload_completed_topic)

        upload_run_to_server(api, run_to_upload, None)

        assert 1 == self.sample_count

    def test_resume_upload(self, api):
        self.sample_count = 0
        project = Project("project", "description")
        created_project = api.send_project(project)
        project_id = created_project["resource"]["identifier"]

        path_to_module = path.dirname(__file__)
        run_dir = path.join(path_to_module, "half-uploaded-run")
        try:
            remove(path.join(run_dir, ".miseqUploaderInfo"))
        except:
            pass
        runs = find_runs_in_directory(run_dir)
        assert 1 == len(runs)

        run_to_upload = runs[0]

        assert 2 == len(run_to_upload.sample_list)

        for sample in run_to_upload.sample_list:
            sample.get_project_id = lambda: project_id

        original_files_method = run_to_upload.sample_list[1].get_files
        run_to_upload.sample_list[1].get_files = lambda: (_ for _ in ()).throw(Exception('foobar'))

        try:
            upload_run_to_server(api, run_to_upload, None)
        except:
            logging.info("Succeeded in failing to upload files.")
            run_to_upload.sample_list[1].get_files = original_files_method

        pub.subscribe(self.update_samples_counter, run_to_upload.sample_list[1].upload_completed_topic)
        upload_run_to_server(api, run_to_upload, None)

        assert 1 == self.sample_count
