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

release_date = target_milestone.date_targeted

if not release_date:
    abort(2, 'No release date for milestone: %s' % args.milestone)

# Sequence code is 1 if month between Nov and Apr, 2 if between May and Oct
sequence = (((release_date.month % 11) + 2) / 7) + 1

print "%d.%d.b%s" % (release_date.year, sequence, args.milestone[-1:])
