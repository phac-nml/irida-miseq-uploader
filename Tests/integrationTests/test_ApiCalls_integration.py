import unittest
from os import path

from API.apiCalls import ApiCalls
from Model.Project import Project
from Model.Sample import Sample

from apiCalls_integration_data_setup import SetupIridaData

base_URL = "http://localhost:8080/api"
username = "admin"
password = "password1"
client_id = ""
client_secret = ""


class TestApiIntegration(unittest.TestCase):

    def setUp(self):
        print "\nStarting " + self.__module__ + ": " + self._testMethodName

    def test_connect_and_authenticate(self):

        api = ApiCalls(
            client_id=client_id,
            client_secret=client_secret,
            base_URL=base_URL,
            username=username,
            password=password
        )

    def test_get_sequence_files(self):

        api = ApiCalls(
            client_id=client_id,
            client_secret=client_secret,
            base_URL=base_URL,
            username=username,
            password=password
        )

        proj_list = api.get_projects()
        proj = proj_list[len(proj_list) - 1]
        sample_list = api.get_samples(proj)
        sample = sample_list[len(sample_list) - 1]

        seq_file_list = api.get_sequence_files(proj, sample)
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

        api = ApiCalls(
            client_id=client_id,
            client_secret=client_secret,
            base_URL=base_URL,
            username=username,
            password=password
        )

        proj_list = api.get_projects()
        self.assertTrue(len(proj_list) == 0)

        proj_name = "integration testProject"
        proj_description = "integration testProject description"
        proj = Project(proj_name, proj_description)
        server_response = api.send_project(proj)

        self.assertEqual(proj_name,
                         server_response["resource"]["name"])
        self.assertEqual(proj_description,
                         server_response["resource"]["projectDescription"])
        self.assertEqual("1",
                         server_response["resource"]["identifier"])

        proj_list = api.get_projects()
        self.assertTrue(len(proj_list) == 1)

        added_proj = proj_list[0]
        self.assertEqual(added_proj.get_name(), "integration testProject")
        self.assertEqual(
            added_proj.get_description(),
            "integration testProject description")

    def test_get_and_send_samples(self):

        api = ApiCalls(
            client_id=client_id,
            client_secret=client_secret,
            base_URL=base_URL,
            username=username,
            password=password
        )

        proj_list = api.get_projects()
        proj = proj_list[0]
        sample_list = api.get_samples(proj)
        self.assertTrue(len(sample_list) == 0)

        sample_dict = {
            "sampleName": "integration_testSample",
            "description": "integration_testSample description",
            "sequencerSampleId": "99-9999",
            "sampleProject": proj.get_id()
            # sequencer sample ID must have at least 3 characters
        }

        sample = Sample(sample_dict)
        server_response = api.send_samples([sample])
        #  sampleProject key already gets removed by `pop` in send_samples
        self.assertEqual(sample_dict["sampleName"],
                         server_response["resource"]["sampleName"])
        self.assertEqual(sample_dict["description"],
                         server_response["resource"]["description"])
        self.assertEqual(sample_dict["sequencerSampleId"],
                         server_response["resource"]["sequencerSampleId"])
        self.assertEqual("1",
                         server_response["resource"]["identifier"])

        sample_list = api.get_samples(proj)
        self.assertTrue(len(sample_list) == 1)

        added_sample = sample_list[0]
        for key in sample_dict.keys():
            self.assertEqual(sample[key], added_sample.get(key))


def load_test_suite():

    api_integration_test_suite = unittest.TestSuite()

    api_integration_test_suite.addTest(
        TestApiIntegration("test_connect_and_authenticate"))
    api_integration_test_suite.addTest(
        TestApiIntegration("test_get_and_send_project"))
    api_integration_test_suite.addTest(
        TestApiIntegration("test_get_and_send_samples"))
    # api_integration_test_suite.addTest(
    #    TestApiIntegration("test_get_sequence_files"))

    return api_integration_test_suite


def irida_setup(setup):

    setup.install_irida()
    setup.reset_irida_db()
    setup.run_irida()


def data_setup(setup):

    irida_setup(setup)

    setup.start_driver()
    setup.login()
    setup.set_new_admin_pw()
    setup.create_client()

    irida_secret = setup.get_irida_secret()
    setup.close_driver()

    return(setup.IRIDA_AUTH_CODE_ID, irida_secret, setup.IRIDA_PASSWORD)


def start_setup():

    global base_URL
    global username
    global password
    global client_id
    global client_secret

    setup = SetupIridaData(
        base_URL[:base_URL.index("/api")], username, password)
    client_id, client_secret, password = data_setup(setup)

    return setup


def main():

    setup_handler = start_setup()

    test_suite = load_test_suite()
    full_suite = unittest.TestSuite([test_suite])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)

    setup_handler.stop_irida()

if __name__ == "__main__":

    main()
