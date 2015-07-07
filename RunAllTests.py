import Tests.unitTests.test_OfflineValidation as test_OfflineValidation
import Tests.unitTests.test_MiseqParser as test_MiseqParser
import Tests.unitTests.test_ApiCalls as test_ApiCalls
import Tests.unitTests.test_IridaUploaderMain as test_IridaUploaderMain

import Tests.integrationTests.test_ApiCalls_integration as apiCalls_integration

import unittest
import platform
from os import system, path, listdir, getcwd

"""
For running all tests or commenting out particular tests suites to only run
selected tests.
"""


def run_integration_tests():

    if platform.system() == "Linux":
        print "Running integration tests"
        apiCalls_integration.main()


def run_unit_tests():

    print "Running unit tests"

    suiteList = []

    iu_main_ts = test_IridaUploaderMain.load_test_suite()
    suiteList.append(iu_main_ts)

    api_ts = test_ApiCalls.load_test_suite()
    suiteList.append(api_ts)

    miseq_ts = test_MiseqParser.load_test_suite()
    suiteList.append(miseq_ts)

    off_valid_ts = test_OfflineValidation.load_test_suite()
    suiteList.append(off_valid_ts)

    fullSuite = unittest.TestSuite(suiteList)

    runner = unittest.TextTestRunner()
    runner.run(fullSuite)


def run_verify_PEP8():

    if platform.system() == "Linux" and "scripts" in listdir(getcwd()):
        print "Running PEP8 verification"
        res = system("./scripts/verifyPEP8.sh")

        if res == 0:
            print "No PEP8 errors"


if __name__ == "__main__":

    # run_integration_tests()
    # disabled by default because it takes a long time to run...

    run_unit_tests()
    run_verify_PEP8()
