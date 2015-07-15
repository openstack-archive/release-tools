#!/usr/bin/env python
#
# Script to close a Launchpad milestone
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
import datetime
import sys

from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print >> sys.stderr, errmsg
    sys.exit(code)


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description='Close the LP milestone')
    parser.add_argument('project', help='LP project (oslo.config)')
    parser.add_argument('milestones', nargs='+',
                        help='Milestone(s) being closed (1.1.0)')
    parser.add_argument("--test", action='store_const', const='staging',
                        default='production', help='Use LP staging server to test')
    args = parser.parse_args()

    # Connect to LP
    print "Connecting to Launchpad..."
    try:
        launchpad = Launchpad.login_with('openstack-releasing', args.test)
    except Exception as error:
        abort(2, 'Could not connect to Launchpad: ' + str(error))

    # Retrieve project
    print "Checking project..."
    try:
        lp_proj = launchpad.projects[args.project]
    except KeyError:
        abort(2, 'Could not find project: %s' % args.project)

    for milestone in args.milestones:
        lp_milestone = lp_proj.getMilestone(name=milestone)
        if lp_milestone is None:
            print >>sys.stderr, 'Could not find milestone: %s' % milestone
            continue

        # Mark milestone released
        print "Marking %s released..." % milestone
        rel_notes = "This is another milestone (%s) on the road to %s %s." \
                    % (milestone, args.project.capitalize(),
                       lp_milestone.series_target.name)

        if not lp_milestone.release:
            lp_release = lp_milestone.createProductRelease(
                date_released=datetime.datetime.utcnow(),
                release_notes=rel_notes)

        # Mark milestone inactive
        print "Marking %s inactive..." % milestone
        lp_milestone.is_active = False
        lp_milestone.lp_save()

    print "Done!"
