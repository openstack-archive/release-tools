#!/usr/bin/env python
#
# Ensure the given milestone exists on Launchpad
#
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
from __future__ import unicode_literals

import argparse
import sys

from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print(errmsg, file=sys.stderr)
    sys.exit(code)


# Argument parsing
parser = argparse.ArgumentParser(description='Create milestones on LP')
parser.add_argument('project', help='launchpad project name')
parser.add_argument('series', help='release series')
parser.add_argument('milestone', help='milestone name (version number)')
args = parser.parse_args()

# Connect to LP
print("connecting to launchpad")
try:
    launchpad = Launchpad.login_with('openstack-releasing', 'production')
except Exception, error:
    abort(2, 'Could not connect to Launchpad: ' + str(error))

# Retrieve project
try:
    project = launchpad.projects[args.project]
except KeyError:
    abort(2, '  Could not find project: %s' % args.project)

# Retrieve or create the series
series = project.getSeries(name=args.series)
if series is None:
    print('creating series %r' % args.series)
    summary = 'This is the "%s" series.' % args.series
    series = project.newSeries(name=args.series,
                               summary=summary)
    series.status = 'Future'
    series.lp_save()
else:
    print('found series %r' % args.series)

print('looking for milestone %r' % args.milestone)
for milestone in series.all_milestones:
    if milestone.name == args.milestone:
        print('milestone %s exists' % args.milestone)
        break
else:
    print('creating milestone %r' % args.milestone)
    series.newMilestone(name=args.milestone,
                        date_targeted=None,
                        code_name=args.milestone)
    print("created milestone %s" % args.milestone)
