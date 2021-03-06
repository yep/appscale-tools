#!/usr/bin/env python
# Programmer: Chris Bunch (chris@appscale.com)


# General-purpose Python library imports
import os
import re
import sys
import unittest


# Third party testing libraries
import boto
from flexmock import flexmock


# AppScale import, the library that we're testing here
lib = os.path.dirname(__file__) + os.sep + ".." + os.sep + "lib"
sys.path.append(lib)
from appscale_logger import AppScaleLogger
from node_layout import NodeLayout

from agents.ec2_agent import EC2Agent


class TestNodeLayout(unittest.TestCase):


  def setUp(self):
    # mock out logging, since it clutters out test output
    flexmock(AppScaleLogger)
    AppScaleLogger.should_receive('log').and_return()

    # next, pretend our ec2 credentials are properly set
    for credential in EC2Agent.REQUIRED_CREDENTIALS:
      os.environ[credential] = "baz"

    # finally, pretend that our ec2 image to use exists
    fake_ec2 = flexmock(name="fake_ec2")
    fake_ec2.should_receive('get_image').with_args('ami-ABCDEFG') \
      .and_return()
    flexmock(boto)
    boto.should_receive('connect_ec2').with_args('baz', 'baz').and_return(fake_ec2)

    # add in some instance variables so that we don't have
    # a lot IP addresses everywhere
    self.blank_input_yaml = None
    self.default_options = {
      'table' : 'cassandra'
    }
    self.ip_1 = '192.168.1.1'
    self.ip_2 = '192.168.1.2'
    self.ip_3 = '192.168.1.3'
    self.ip_4 = '192.168.1.4'
    self.ip_5 = '192.168.1.5'
    self.ip_6 = '192.168.1.6'
    self.ip_7 = '192.168.1.7'
    self.ip_8 = '192.168.1.8'

  def test_simple_layout_yaml_only(self):
    # Specifying one controller and one server should be ok
    input_yaml_1 = {
      'controller' : self.ip_1,
      'servers' : [self.ip_2]
    }
    options_1 = self.default_options.copy()
    options_1['ips'] = input_yaml_1
    layout_1 = NodeLayout(options_1)
    self.assertEquals(True, layout_1.is_valid())

    # Specifying one controller should be ok
    input_yaml_2 = {'controller' : self.ip_1}
    options_2 = self.default_options.copy()
    options_2['ips'] = input_yaml_2
    layout_2 = NodeLayout(options_2)
    self.assertEquals(True, layout_2.is_valid())

    # Specifying the same IP more than once is not ok
    input_yaml_3 = {'controller' : self.ip_1, 'servers' : [self.ip_1]}
    options_3 = self.default_options.copy()
    options_3['ips'] = input_yaml_3
    layout_3 = NodeLayout(options_3)
    self.assertEquals(False, layout_3.is_valid())
    self.assertEquals(NodeLayout.DUPLICATE_IPS, layout_3.errors())

    # Failing to specify a controller is not ok
    input_yaml_4 = {'servers' : [self.ip_1, self.ip_2]}
    options_4 = self.default_options.copy()
    options_4['ips'] = input_yaml_4
    layout_4 = NodeLayout(options_4)
    self.assertEquals(False, layout_4.is_valid())
    self.assertEquals(NodeLayout.NO_CONTROLLER, layout_4.errors())

    # Specifying more than one controller is not ok
    input_yaml_5 = {'controller' : [self.ip_1, self.ip_2], 'servers' : [self.ip_3]}
    options_5 = self.default_options.copy()
    options_5['ips'] = input_yaml_5
    layout_5 = NodeLayout(options_5)
    self.assertEquals(False, layout_5.is_valid())
    self.assertEquals(NodeLayout.ONLY_ONE_CONTROLLER, layout_5.errors())

    # Specifying something other than controller and servers in simple
    # deployments is not ok
    input_yaml_6 = {'controller' : self.ip_1, 'servers' : [self.ip_2],
      'boo' : self.ip_3}
    options_6 = self.default_options.copy()
    options_6['ips'] = input_yaml_6
    layout_6 = NodeLayout(options_6)
    self.assertEquals(False, layout_6.is_valid())
    self.assertEquals(["The flag boo is not a supported flag"],
      layout_6.errors())


  def test_simple_layout_options(self):
    # Using Euca with no input yaml, and no max or min images is not ok
    options_1 = self.default_options.copy()
    options_1['infrastructure'] = 'euca'
    layout_1 = NodeLayout(options_1)
    self.assertEquals(False, layout_1.is_valid())
    self.assertEquals(NodeLayout.NO_YAML_REQUIRES_MIN, layout_1.errors())

    options_2 = self.default_options.copy()
    options_2['infrastructure'] = "euca"
    options_2['max'] = 2
    layout_2 = NodeLayout(options_2)
    self.assertEquals(False, layout_2.is_valid())
    self.assertEquals(NodeLayout.NO_YAML_REQUIRES_MIN, layout_2.errors())

    options_3 = self.default_options.copy()
    options_3['infrastructure'] = "euca"
    options_3['min'] = 2
    layout_3 = NodeLayout(options_3)
    self.assertEquals(False, layout_3.is_valid())
    self.assertEquals(NodeLayout.NO_YAML_REQUIRES_MAX, layout_3.errors())

    # Using Euca with no input yaml, with max and min images set is ok
    options_4 = self.default_options.copy()
    options_4['infrastructure'] = "euca"
    options_4['min'] = 2
    options_4['max'] = 2
    layout_4 = NodeLayout(options_4)
    self.assertEquals(True, layout_4.is_valid())

    # Using virtualized deployments with no input yaml is not ok
    options_5 = self.default_options.copy()
    layout_5 = NodeLayout(options_5)
    self.assertEquals(False, layout_5.is_valid())
    self.assertEquals([NodeLayout.INPUT_YAML_REQUIRED], layout_5.errors())


  def test_advanced_format_yaml_only(self):
    input_yaml = {'master' : self.ip_1, 'database' : self.ip_1,
      'appengine' : self.ip_1, 'open' : self.ip_2}
    options = self.default_options.copy()
    options['ips'] = input_yaml
    layout_1 = NodeLayout(options)
    self.assertEquals(True, layout_1.is_valid())


  def test_dont_warn_users_on_supported_deployment_strategies(self):
    # all simple deployment strategies are supported
    input_yaml_1 = {'controller' : self.ip_1}
    options_1 = self.default_options.copy()
    options_1['ips'] = input_yaml_1
    layout_1 = NodeLayout(options_1)
    self.assertEquals(True, layout_1.is_supported())

    input_yaml_2 = {'controller' : self.ip_1, 'servers' : [self.ip_2]}
    options_2 = self.default_options.copy()
    options_2['ips'] = input_yaml_2
    layout_2 = NodeLayout(options_2)
    self.assertEquals(True, layout_2.is_supported())

    input_yaml_3 = {'controller' : self.ip_1, 'servers' : [self.ip_2, self.ip_3]}
    options_3 = self.default_options.copy()
    options_3['ips'] = input_yaml_3
    layout_3 = NodeLayout(options_3)
    self.assertEquals(True, layout_3.is_supported())

    # in advanced deployments, four nodes are ok with the following
    # layout: (1) load balancer, (2) appserver, (3) database,
    # (4) zookeeper
    advanced_yaml_1 = {
      'master' : self.ip_1,
      'appengine' : self.ip_2,
      'database' : self.ip_3,
      'zookeeper' : self.ip_4
    }
    options_1 = self.default_options.copy()
    options_1['ips'] = advanced_yaml_1
    advanced_layout_1 = NodeLayout(options_1)
    self.assertEquals(True, advanced_layout_1.is_valid())
    self.assertEquals(True, advanced_layout_1.is_supported())

    # in advanced deployments, eight nodes are ok with the following
    # layout: (1) load balancer, (2) appserver, (3) appserver,
    # (4) database, (5) database, (6) zookeeper, (7) zookeeper,
    # (8) zookeeper
    advanced_yaml_2 = {
      'master' : self.ip_1,
      'appengine' : [self.ip_2, self.ip_3],
      'database' : [self.ip_4, self.ip_5],
      'zookeeper' : [self.ip_6, self.ip_7, self.ip_8]
    }
    options_2 = self.default_options.copy()
    options_2['ips'] = advanced_yaml_2
    advanced_layout_2 = NodeLayout(options_2)
    self.assertEquals(True, advanced_layout_2.is_valid())
    self.assertEquals(True, advanced_layout_2.is_supported())


  def test_warn_users_on_unsupported_deployment_strategies(self):
    # don't test simple deployments - those are all supported
    # instead, test out some variations of the supported advanced
    # strategies, as those should not be supported
    advanced_yaml_1 = {
      'master' : self.ip_1,
      'appengine' : self.ip_1,
      'database' : self.ip_2,
      'zookeeper' : self.ip_2
    }
    options_1 = self.default_options.copy()
    options_1['ips'] = advanced_yaml_1
    advanced_layout_1 = NodeLayout(options_1)
    self.assertEquals(True, advanced_layout_1.is_valid())
    self.assertEquals(False, advanced_layout_1.is_supported())

    # four node deployments that don't match the only supported
    # deployment are not supported
    advanced_yaml_2 = {
      'master' : self.ip_1,
      'appengine' : self.ip_2,
      'database' : self.ip_3,
      'zookeeper' : self.ip_3,
      'open' : self.ip_4
    }
    options_2 = self.default_options.copy()
    options_2['ips'] = advanced_yaml_2
    advanced_layout_2 = NodeLayout(options_2)
    self.assertEquals(True, advanced_layout_2.is_valid())
    self.assertEquals(False, advanced_layout_2.is_supported())

    # eight node deployments that don't match the only supported
    # deployment are not supported
    advanced_yaml_3 = {
      'master' : self.ip_1,
      'appengine' : [self.ip_2, self.ip_3],
      'database' : [self.ip_4, self.ip_5],
      'zookeeper' : [self.ip_6, self.ip_7],
      'open' : self.ip_8
    }
    options_3 = self.default_options.copy()
    options_3['ips'] = advanced_yaml_3
    advanced_layout_3 = NodeLayout(options_3)
    self.assertEquals(True, advanced_layout_3.is_valid())
    self.assertEquals(False, advanced_layout_3.is_supported())
