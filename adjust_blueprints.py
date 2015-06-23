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

from argparse import ArgumentParser
from datetime import datetime, timedelta
from launchpadlib.launchpad import Launchpad
import pytz
import sys


# Parameters
parser = ArgumentParser(description="Update BPs on milestone closure")
parser.add_argument('project', help='The project to act on')
parser.add_argument('milestone', help='The milestone to set')
parser.add_argument("--dryrun", action='store_true', help='Do not do anything')
parser.add_argument("--no-clear", action='store_true',
                    help='Do not clear milestone from incomplete blueprints')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
args = parser.parse_args()

# Connect to Launchpad
print "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-releasing', args.test,
                                 version='devel')

project = launchpad.projects[args.project]
milestone = project.getMilestone(name=args.milestone)
if not milestone:
    parser.error('Target milestone %s does not exist' % args.milestone)
series = milestone.series_target

if (args.dryrun):
    print "Dry run mode -- this will actually not do anything"

# Get the blueprints
print "Retrieving blueprints...",
now = datetime.now(tz=pytz.utc)
to_clear = []
to_series = []
to_target = []
count = 0
bps = project.all_specifications
numbps = len(bps)
print "retrieved %d blueprints" % numbps

# Parse the blueprints
print "Parsing blueprints..."
for bp in bps:
    count = count + 1
    sys.stdout.write("\r%d%%" % int(count * 100 / numbps))
    sys.stdout.flush()
    if ((bp.implementation_status == 'Implemented') and
        ((now - bp.date_completed) < timedelta(days=92)) and
        (not bp.milestone or not bp.milestone.date_targeted or
         bp.milestone.date_targeted >= milestone.date_targeted)):
        to_target.append(bp)
    elif not bp.is_complete and bp.milestone == milestone:
        to_clear.append(bp)
print

if (to_target):
    print "Those are implemented: need milestone and/or series target added"
    for bp in to_target:
        print bp.web_link
        if not args.dryrun:
            bp.milestone = milestone
            bp.proposeGoal(goal=series)
            bp.lp_save()

if to_clear and not args.no_clear:
    print "Those are incomplete: need their milestone target cleared"
    for bp in to_clear:
        print bp.web_link
        if not args.dryrun:
            bp.milestone = None
            bp.lp_save()
else:
    print "Not clearing incomplete blueprints"
