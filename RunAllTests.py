from Tests.unitTests.test_OfflineValidation import off_validation_test_suite
from Tests.unitTests.test_MiseqParser import parser_test_suite
from Tests.unitTests.test_ApiCalls import api_test_suite
# from Tests.integrationTests.test_ApiCalls_integration import (
#    api_integration_TestSuite)
from sys import argv
import unittest

"""
For running all tests or commenting out particular tests suites to only run
selected tests.
"""

if __name__ == "__main__":
    suiteList = []

    suiteList.append(off_validation_test_suite)
    suiteList.append(parser_test_suite)
    suiteList.append(api_test_suite)
    # suiteList.append(api_integration_TestSuite)

    fullSuite = unittest.TestSuite(suiteList)

    runner = unittest.TextTestRunner()
    runner.run(fullSuite)
