#!/usr/bin/env python
# Programmer: Chris Bunch (chris@appscale.com)


import unittest


# imports for appscale executable tests
from test_appscale import TestAppScale
from test_appscale_describe_instances import TestAppScaleDescribeInstances
from test_appscale_add_instances import TestAppScaleAddInstances
from test_appscale_add_keypair import TestAppScaleAddKeypair
from test_appscale_gather_logs import TestAppScaleGatherLogs
from test_appscale_remove_app import TestAppScaleRemoveApp
from test_appscale_reset_pwd import TestAppScaleResetPassword
from test_appscale_run_instances import TestAppScaleRunInstances
from test_appscale_upload_app import TestAppScaleUploadApp
from test_appscale_terminate_instances import TestAppScaleTerminateInstances


# imports for appscale library tests
from test_appscale_logger import TestAppScaleLogger
from test_local_state import TestLocalState
from test_node_layout import TestNodeLayout
from test_parse_args import TestParseArgs
from test_remote_helper import TestRemoteHelper


test_cases = [TestAppScale, TestAppScaleAddInstances, TestAppScaleAddKeypair,
  TestAppScaleDescribeInstances, TestAppScaleGatherLogs, TestAppScaleRemoveApp,
  TestAppScaleResetPassword, TestAppScaleRunInstances,
  TestAppScaleTerminateInstances, TestAppScaleUploadApp, TestAppScaleLogger,
  TestLocalState, TestNodeLayout, TestParseArgs, TestRemoteHelper]
appscale_test_suite = unittest.TestSuite()
for test_class in test_cases:
  tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
  appscale_test_suite.addTests(tests)

all_tests = unittest.TestSuite([appscale_test_suite])
unittest.TextTestRunner(verbosity=2).run(all_tests)
