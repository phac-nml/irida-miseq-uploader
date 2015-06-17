import unittest
import sys
sys.path.append("../../")
from os import path

from API.apiCalls import ApiCalls
from Model.Project import Project
from Model.Sample import Sample
from apiCalls_integration_data_setup import SetupIridaData


base_URL = "http://localhost:8080/api"
username = "admin"
password = "password1"

class TestApiIntegration(unittest.TestCase):

	def setUp(self):
		print "\nStarting " + self.__module__ + ": " + self._testMethodName

	def test_connect_and_authenticate(self):

		api=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)

	def test_get_samples(self):

		api=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)

		proj_list = api.get_projects()
		proj = proj_list[len(proj_list)-1]
		sample_list = api.get_samples(proj)
		self.assertTrue(len(sample_list) > 0)

		sample = sample_list[len(sample_list)-1]
		self.assertEqual(sample.get("sampleName"), "integration_testSample")

		required_keys = ["sampleName","description","sequencerSampleId"]
		sample_dict = sample.getDict()
		for key in required_keys:
			self.assertTrue(key in sample_dict)

	def test_get_sequence_files(self):

		api=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)

		proj_list = api.get_projects()
		proj = proj_list[len(proj_list)-1]
		sample_list = api.get_samples(proj)
		sample = sample_list[len(sample_list)-1]

		seqFileList = api.get_sequence_files(proj, sample)
		self.assertEqual(len(seqFileList), 2)

		seqFile1 = seqFileList[0]
		seqFile2 = seqFileList[1]
		self.assertTrue("file" in seqFile1)
		self.assertTrue("file" in seqFile2)
		self.assertEqual(str(seqFile1["fileName"]),
						"01-1111_S1_L001_R1_001.fastq")
		self.assertEqual(str(seqFile2["fileName"]),
						"01-1111_S1_L001_R2_001.fastq")

	def test_get_and_send_project(self):

		api=ApiCalls(
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

		added_proj = proj_list[len(proj_list)-1]
		self.assertEqual(added_proj.getName(), "integration testProject")
		self.assertEqual(added_proj.getDescription(), "integration testProject description")


	def test_send_samples(self):

		api=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)

		proj_list = api.get_projects()
		proj = proj_list[0]

		starting_list_len = len(api.get_samples(proj))

		sample_dict = {
			"sampleName" : "sample1",
			"description" : "sample1 description",
			"sequencerSampleId" : str(starting_list_len)*3
			#sequencer sample ID must have at least 3 characters
		}

		sample = Sample(sample_dict)
		api.send_samples(proj, [sample])

		sample_list = api.get_samples(proj)
		new_list_len = len(sample_list)

		self.assertEqual(starting_list_len + 1, new_list_len)

		added_sample = sample_list[len(sample_list)-1]
		for key in sample_dict.keys():
			self.assertEqual(sample[key], added_sample.get(key))


api_integration_TestSuite = unittest.TestSuite()

api_integration_TestSuite.addTest(TestApiIntegration("test_connect_and_authenticate"))
api_integration_TestSuite.addTest(TestApiIntegration("test_get_and_send_project"))
#api_integration_TestSuite.addTest(TestApiIntegration("test_get_samples"))
#api_integration_TestSuite.addTest(TestApiIntegration("test_get_sequence_files"))
#api_integration_TestSuite.addTest(TestApiIntegration("test_send_project"))
#api_integration_TestSuite.addTest(TestApiIntegration("test_send_samples"))

def irida_setup(setup):
	setup.install_irida()
	setup.reset_irida_db()
	setup.run_irida()

def data_setup(setup):

	irida_setup()#

	setup.start_driver()
	setup.login()
	setup.set_new_admin_pw()
	setup.create_client()

	irida_secret = setup.get_irida_secret()
	setup.close_driver()

	return(setup.IRIDA_AUTH_CODE_ID, irida_secret, setup.IRIDA_PASSWORD)


if __name__=="__main__":

	setup = SetupIridaData(base_URL[:base_URL.index("/api")], username, password)
	client_id, client_secret, password = data_setup(setup)

	suiteList=[]

	suiteList.append(api_integration_TestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)

	setup.stop_irida()
