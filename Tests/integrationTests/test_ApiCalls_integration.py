import unittest
import sys
sys.path.append("../../")
from ConfigParser import RawConfigParser
from os import path

from API.apiCalls import ApiCalls
from Model.Project import Project
from Model.Sample import Sample

path_to_module=path.dirname(__file__)
if len(path_to_module)==0:
	path_to_module="."

conf_Parser=RawConfigParser()
conf_Parser.read(path.join(path_to_module,"..","..","config.conf"))

client_id=conf_Parser.get("apiCalls","client_id")
client_secret=conf_Parser.get("apiCalls","client_secret")
base_URL="http://localhost:8080/api"
username="admin"
password="password1"

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

	def test_get_projects(self):

		api=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)

		proj_list = api.get_projects()
		self.assertTrue (len(proj_list) > 0)

	def test_get_samples(self):

		api=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)

		proj_list = api.get_projects()
		proj = proj_list[3]# first project to have samples in newly setup irida
		sample_list = api.get_samples(proj)
		self.assertTrue(len(sample_list) > 0)

		required_keys = ["sampleName","description","sequencerSampleId"]
		sample = sample_list[0]
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
		proj = proj_list[3]
		sample_list = api.get_samples(proj)
		sample = sample_list[50]

		seqFiles = api.get_sequence_files(proj, sample)

		self.assertTrue(len(seqFiles) > 0)
		self.assertTrue("file" in seqFiles[0])

	def test_send_project(self):

		api=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)

		proj_name = "new project1"
		proj_description = "new project1 description"
		proj = Project(proj_name, proj_description)

		starting_proj_len = len(api.get_projects())
		api.send_project(proj)

		proj_list = api.get_projects()
		new_proj_len = len(proj_list)
		self.assertEqual(starting_proj_len + 1, new_proj_len)

		added_proj = proj_list[len(proj_list)-1]
		self.assertEqual(proj_name, added_proj.getName())
		self.assertEqual(proj_description, added_proj.getDescription())

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
api_integration_TestSuite.addTest(TestApiIntegration("test_get_projects"))
api_integration_TestSuite.addTest(TestApiIntegration("test_get_samples"))
api_integration_TestSuite.addTest(TestApiIntegration("test_get_sequence_files"))
api_integration_TestSuite.addTest(TestApiIntegration("test_send_project"))
api_integration_TestSuite.addTest(TestApiIntegration("test_send_samples"))

if __name__=="__main__":
	suiteList=[]

	suiteList.append(api_integration_TestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
