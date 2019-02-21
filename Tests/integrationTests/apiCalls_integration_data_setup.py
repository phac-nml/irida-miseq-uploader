from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contextlib import contextmanager
from urllib2 import urlopen, URLError
from os import path
from time import time, sleep
import sys
import subprocess
import httplib


class SetupIridaData:

    def __init__(self, base_URL, user, password, branch):

        self.base_URL = base_URL
        self.user = user
        self.password = password
        self.driver = None
	self.branch = branch

        self.IRIDA_PASSWORD_ID = 'password_client'
        self.IRIDA_AUTH_CODE_ID = 'auth_code_client'
        self.IRIDA_USER = "admin"
        self.IRIDA_PASSWORD = "Password1!"  # new password

        self.TIMEOUT = 600  # seconds

        db_name = "irida_uploader_test"

        self.IRIDA_DB_RESET = 'echo '\
            '"drop database if exists ' + db_name + ';'\
            'create database ' + db_name + ';'\
            '"| mysql -u test -ptest'

        self.IRIDA_CMD = ['mvn', 'clean', 'jetty:run',
                          '-Djdbc.url=jdbc:mysql://localhost:3306/' + db_name,
                          '-Djdbc.username=test', '-Djdbc.password=test',
                          '-Dliquibase.update.database.schema=true',
                          '-Dhibernate.hbm2ddl.auto=',
                          '-Dhibernate.hbm2ddl.import_files=']

        self.IRIDA_STOP = 'mvn jetty:stop'

        self.PATH_TO_MODULE = path.dirname(__file__)
        if len(self.PATH_TO_MODULE) == 0:
            self.PATH_TO_MODULE = "."

        self.SCRIPT_FOLDER = path.join(self.PATH_TO_MODULE, "bash_scripts")
        self.INSTALL_IRIDA_EXEC = path.join(
            self.SCRIPT_FOLDER, "install_irida.sh")

        self.REPO_PATH = path.join(self.PATH_TO_MODULE, "repos")
        self.IRIDA_PATH = path.join(self.REPO_PATH, "irida")

    @contextmanager
    def wait_for_page_load(self, timeout=30):
        old_page = self.driver.find_element_by_tag_name('html')
        yield
        WebDriverWait(self.driver, timeout).until(
            EC.staleness_of(old_page)
        )

    def install_irida(self):
        install_proc = subprocess.Popen(
            [self.INSTALL_IRIDA_EXEC, self.branch], cwd=self.PATH_TO_MODULE)
        proc_res = install_proc.wait()
        if proc_res == 1:  # failed to execute
            sys.exit(1)

    def reset_irida_db(self):
        db_reset_proc = subprocess.Popen(self.IRIDA_DB_RESET, shell=True)
        proc_res = db_reset_proc.wait()

        if proc_res == 1:  # failed to execute
            print "Unable to execute:\n {cmd}".format(cmd=self.IRIDA_DB_RESET)
            sys.exit(1)

    def run_irida(self):
        subprocess.Popen(
            self.IRIDA_CMD, cwd=self.IRIDA_PATH)
        self.wait_until_up()

    def wait_until_up(self):

        start_time = time()
        elapsed = 0
        status_code = -1
        print "Waiting for " + self.base_URL

        while(status_code != httplib.OK and elapsed < self.TIMEOUT):

            try:
                status_code = urlopen(self.base_URL).getcode()
                elapsed = time() - start_time

            except URLError:
                sleep(10)

    def start_driver(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(30)

    def login(self):

        self.driver.get(self.base_URL + "/login")
        self.driver.find_element_by_id("emailTF").clear()
        self.driver.find_element_by_id("emailTF").send_keys(self.user)
        self.driver.find_element_by_id("passwordTF").clear()
        self.driver.find_element_by_id("passwordTF").send_keys(self.password)
        with self.wait_for_page_load(timeout=10):
                self.driver.find_element_by_id("submitBtn").click()

    def set_new_admin_pw(self):

        self.driver.find_element_by_id("password").clear()
        self.driver.find_element_by_id(
            "password").send_keys(self.IRIDA_PASSWORD)
        self.driver.find_element_by_id("confirmPassword").clear()
        self.driver.find_element_by_id(
            "confirmPassword").send_keys(self.IRIDA_PASSWORD)
        with self.wait_for_page_load(timeout=10):
            xpath = "//button[@type='submit']"
            submit = self.driver.find_element_by_xpath(xpath)
            submit.click()

    def create_client(self):

        self.driver.get(self.base_URL + "/clients/create")
        self.driver.find_element_by_id(
            "clientId").send_keys(self.IRIDA_AUTH_CODE_ID)

        self.driver.find_element_by_id("scope_write").click()  # for sending
        with self.wait_for_page_load(timeout=10):
            self.driver.find_element_by_id("create-client-submit").click()

    def get_irida_secret(self):

        self.driver.get(self.base_URL + "/clients")
        self.driver.find_element_by_xpath(
            "//*[contains(text(), '" + self.IRIDA_AUTH_CODE_ID + "')]").click()
        secret = self.driver.find_element_by_id(
            "client-secret").get_attribute("textContent")

        return secret

    def stop_irida(self):
        stopper = subprocess.Popen(
            self.IRIDA_STOP, cwd=self.IRIDA_PATH, shell=True)
        stopper.wait()

    def close_driver(self):
        self.driver.quit()
