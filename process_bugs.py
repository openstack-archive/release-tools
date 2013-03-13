#!/usr/bin/python
#
# Script to apply bulk changes to Launchpad bugs
#
# Copyright 2011-2013 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from argparse import ArgumentParser
from launchpadlib.launchpad import Launchpad

# Parameters
parser = ArgumentParser(description="Change bugs status in bulk")
parser.add_argument('projectname', help='The project to act on')
parser.add_argument('--status', default='Fix Committed',
                    help='Which bug status to bulk-change')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument('--settarget',
                    help='ACTION: set the milestone to specified target')
parser.add_argument('--fixrelease', action='store_true',
                    help='ACTION: mark bugs fix released')
parser.add_argument('exceptions', type=int, nargs='*', help='Bugs to ignore')

args = parser.parse_args()

if args.settarget:
    if args.test == 'staging':
        site = "https://api.staging.launchpad.net/1.0"
    else:
        site = "https://api.launchpad.net/1.0"
    milestonelink = "%s/%s/+milestone/%s" \
                    % (site, args.projectname, args.settarget)

# Connect to Launchpad
print "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-releasing', args.test)

# Retrieve bugs
print "Retrieving project..."
proj = launchpad.projects[args.projectname]
changes = True

while changes:
    changes = False
    bugtasks = proj.searchTasks(status=args.status)

    # Process bugs
    for b in bugtasks:
        bug = b.bug
        # Skip already-milestoned bugs with a different milestone
        if args.settarget and b.milestone:
            if b.milestone.name != args.settarget:
                continue
        print bug.id,
        if bug.id in args.exceptions:
            print " - excepted"
            continue
        if args.settarget:
            if not b.milestone:
                changes = True
                b.milestone = milestonelink
                print " - milestoned",
            else:
                print " - milestone already set",
        if args.fixrelease:
            changes = True
            print " - fixreleased",
            b.status = 'Fix Released'
        b.lp_save()
        print
