#!/usr/bin/env python
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

from __future__ import print_function
from argparse import ArgumentParser
import datetime

from launchpadlib.launchpad import Launchpad
from lazr.restfulclient.errors import ServerError
import pytz


# Parameters
parser = ArgumentParser(
    description="Unset assignee/milestone for bugs with no activity in bulk")
parser.add_argument('projectname', help='The project to act on')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument("--days", type=int, default=365,
                    help='days without activity (default: %(default)s days)')
parser.add_argument("--tag", help='Tag bug without activity with this tag')
parser.add_argument('exceptions', type=int, nargs='*', help='Bugs to ignore')

args = parser.parse_args()

# Connect to Launchpad
print("Connecting to Launchpad...")
launchpad = Launchpad.login_with('openstack-gc', args.test)

# Retrieve bugs
print("Retrieving project...")
proj = launchpad.projects[args.projectname]
failed = set()

modified_before = (
    datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=args.days))

# Get bugtasks, older first
bugtasks = proj.searchTasks(order_by='date_last_updated')

# Process bugs
for bugtask in bugtasks:
    bug = bugtask.bug

    # Process bugs with no activity after modified_before
    if bug.date_last_updated > modified_before:
        break

    # Skip bugs which triggered timeouts in previous runs
    if bug.id in failed:
        continue

    bug_updated = False
    bugtask_updated = False

    print(bug.id, end='')
    if bug.id in args.exceptions:
        print(" - excepted")
        continue

    if bugtask.assignee:
        bugtask_updated = True
        print(" - unset assignee %s" % bugtask.assignee, end='')
        bugtask.assignee = None
    if bugtask.milestone:
        bugtask_updated = True
        print(" - unset milestone %s" % bugtask.milestone, end='')
        bugtask.milestone = None

    if args.tag and args.tag not in bug.tags:
        bug_updated = True
        bug.tags.append(args.tag)

    try:
        if bugtask_updated:
            bugtask.lp_save()
    except ServerError:
        print(" - TIMEOUT during bugtask save !", end='')
        failed.add(bug.id)
    except Exception as e:
        print(" - ERROR during bugtask save ! (%s)" % e, end='')
        failed.add(bug.id)
    else:
        try:
            if bug_updated:
                bug.lp_save()
        except ServerError:
            print(" - TIMEOUT during bug save !", end='')
            failed.add(bug.id)
        except Exception as e:
            print(" - ERROR during bug save ! (%s)" % e, end='')
            failed.add(bug.id)
    print()

if failed:
    print()
    print("Some bugs could not be automatically updated due to LP timeouts:")
    for bugid in failed:
        print("http://bugs.launchpad.net/bugs/%d" % bugid)
