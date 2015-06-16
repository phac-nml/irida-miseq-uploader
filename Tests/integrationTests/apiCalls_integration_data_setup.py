# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from urlparse import urljoin
from os import path

class SetupIridaData:

	def __init__(self, base_url, user, password):

		self.base_URL = base_url
		self.driver = webdriver.Chrome()
		self.driver.implicitly_wait(30)
		self.user = user
		self.password = password

	def login(self):

		self.driver.get(urljoin(self.base_URL, "login"))
		self.driver.find_element_by_id("emailTF").clear()
		self.driver.find_element_by_id("emailTF").send_keys(self.user)
		self.driver.find_element_by_id("passwordTF").clear()
		self.driver.find_element_by_id("passwordTF").send_keys(self.password)
		self.driver.find_element_by_id("submitBtn").click()

	def create_project(self):

		print "Creating project"
		self.driver.get(urljoin(self.base_URL, "projects/all"))
		self.driver.find_element_by_xpath("//a[@id='newProjectBtn']/span[2]").click()
		self.driver.find_element_by_id("name").clear()
		self.driver.find_element_by_id("name").send_keys("integration testProject")
		self.driver.find_element_by_id("projectDescription").click()
		self.driver.find_element_by_id("projectDescription").clear()
		self.driver.find_element_by_id("projectDescription").send_keys("integration testProject description")
		WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID,'submitBtn')))
		self.driver.find_element_by_id("submitBtn").click()

	def create_sample(self):

		print "Creating sample"
		self.driver.get(self.driver.current_url.replace("metadata","/samples/new"))
		self.driver.find_element_by_id("sampleName").clear()
		self.driver.find_element_by_id("sampleName").send_keys("integration_testSample")
		WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID,"createBtn")))
		self.driver.find_element_by_id("createBtn").click()

	def upload_fake_sequence_files(self):

		print "Uploading sequence files"

		path_to_module = path.dirname(__file__)
		if len(path_to_module) == 0:
			path_to_module = "."

		upload_button_element=self.driver.find_element_by_xpath("//h1[@id='page-title']/file-upload/button")
		WebDriverWait(self.driver, 10).until(EC.visibility_of(upload_button_element))
		upload_button_element.click()

		self.driver.find_element_by_xpath("//div[2]/button").click()
		inp1 = self.driver.find_element_by_css_selector("input[type=\"file\"]")
		filePath1 = path_to_module.replace("integrationTests", path.join("unitTests", "fake_ngs_data",
		"Data","Intensities","BaseCalls","01-1111_S1_L001_R1_001.fastq.gz"))

		print "  Uploading: " + filePath1
		inp1.send_keys(filePath1)

		self.driver.find_element_by_xpath("//div[2]/button").click()
		inp2 = self.driver.find_element_by_css_selector("input[type=\"file\"]")
		filePath2 = path_to_module.replace("integrationTests", path.join("unitTests", "fake_ngs_data",
		"Data","Intensities","BaseCalls","01-1111_S1_L001_R2_001.fastq.gz"))

		print "  Uploading: " + filePath2
		inp2.send_keys(filePath2)

		self.driver.find_element_by_css_selector("button.btn.btn-primary").click()

	def close(self):
		self.driver.quit()


def data_setup(new_base_url, user, password):
	setup = SetupIridaData(new_base_url, user, password)
	setup.login()
	setup.create_project()
	setup.create_sample()
	setup.upload_fake_sequence_files()

	setup.close()
