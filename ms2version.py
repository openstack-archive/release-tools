#!/usr/bin/python
#
# Script to determine version number from milestone codename
#
# Copyright 2014 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import string
import sys

from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print >> sys.stderr, errmsg
    sys.exit(code)


# Argument parsing
parser = argparse.ArgumentParser(description='Convert milestone code names '
                                             '(juno-1) to version numbers '
                                             '(2014.2.b1)')
parser.add_argument('project', help='Project the milestone is defined in')
parser.add_argument('milestone', help='Milestone code name')
parser.add_argument('--onlycheck', action='store_true',
                    help='Only check milestone exists')
args = parser.parse_args()

# Connect to LP
try:
    launchpad = Launchpad.login_anonymously('openstack-releasing',
                                            'production')
except Exception, error:
    abort(2, 'Could not connect to Launchpad: ' + str(error))

# Retrieve milestone
try:
    lp_proj = launchpad.projects[args.project]
except KeyError:
    abort(2, 'Could not find project: %s' % args.project)

for target_milestone in lp_proj.all_milestones:
    if target_milestone.name == args.milestone:
        break
else:
    abort(2, 'Could not find milestone: %s' % args.milestone)

if args.onlycheck:
    sys.exit(0)

ind = string.lowercase.index(target_milestone.name[0:1])

if ind < 4:
    abort(2, 'This script does not support pre-essex numbers')

year = 2011 + (ind - 2) / 2
sequence = (ind % 2) + 1
qualifier = 'b'
if target_milestone.name[-3:-1].lower() == 'rc':
    qualifier = 'rc'

print "%d.%d.%s%s" % (year, sequence, qualifier, args.milestone[-1:])
