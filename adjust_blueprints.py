# Copyright 2015 Thierry Carrez <thierry@openstack.org>
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

from __future__ import print_function
import argparse
import datetime
import sys

import launchpadlib.launchpad
import pytz

# Parameters
parser = argparse.ArgumentParser(description="Update BPs on milestone closure")
parser.add_argument('project', help='The project to act on')
parser.add_argument('milestone', help='The milestone to set')
parser.add_argument("--target", action='store_true',
                    help='Set target and/or series goal for implemented BPs')
parser.add_argument("--clear", action='store_true',
                    help='Clear milestone from incomplete blueprints')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
args = parser.parse_args()

# Connect to Launchpad
print("Connecting to Launchpad...")
launchpad = launchpadlib.launchpad.Launchpad.login_with('openstack-releasing',
                                                        args.test, version='devel')

project = launchpad.projects[args.project]
milestone = project.getMilestone(name=args.milestone)
if not milestone:
    parser.error('Target milestone %s does not exist' % args.milestone)
series = milestone.series_target

# Get the blueprints
print("Retrieving blueprints...")
now = datetime.datetime.now(tz=pytz.utc)
to_clear = []
to_series = []
to_target = []
count = 0
bps = project.all_specifications
numbps = len(bps)
# Also get the series-targeted approved blueprints
seriesbps = series.valid_specifications
print("retrieved %d blueprints" % numbps)

# Parse the blueprints
print("Parsing blueprints...")
for bp in bps:
    count = count + 1
    sys.stdout.write("\r%d%%" % int(count * 100 / numbps))
    sys.stdout.flush()
    if ((bp.implementation_status == 'Implemented') and
        ((now - bp.date_completed) < datetime.timedelta(days=92)) and
        (not bp.milestone or not bp.milestone.date_targeted or
         bp.milestone.date_targeted >= milestone.date_targeted)):
        if bp not in seriesbps:
            to_series.append(bp)
        if bp.milestone != milestone:
            to_target.append(bp)
    elif not bp.is_complete and bp.milestone == milestone:
        to_clear.append(bp)
print()
if (to_target):
    print()
    print("Those are implemented: need milestone target added")
    for bp in to_target:
        print(bp.web_link)
        if args.target:
            bp.milestone = milestone
            bp.lp_save()

if (to_series):
    print()
    print("Those are implemented: need series goal added/approved")
    for bp in to_series:
        print(bp.web_link)
        if args.target:
            bp.proposeGoal(goal=series)

if (to_clear):
    print()
    print("Those are incomplete: need their milestone target cleared")
    for bp in to_clear:
        print(bp.web_link)
        if args.clear:
            bp.milestone = None
            bp.lp_save()
